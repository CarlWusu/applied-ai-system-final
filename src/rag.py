"""
Feature 1 — Retrieval-Augmented Generation (RAG)

Pipeline:
  Retrieve  — parse query into structured prefs, score catalog, select top-k songs
  Augment   — format retrieved songs as structured context for the LLM
  Generate  — ask Claude to explain the recommendations in natural language

The retrieval step uses the existing deterministic scoring engine (no LLM needed
there). Claude is only called for query parsing and for the final explanation,
so results are auditable and costs are bounded.
"""

import ast
import os
from typing import List, Dict, Optional, Tuple

import anthropic

from src.recommender import load_songs, recommend_songs

_EXTRACTION_SYSTEM = (
    "Extract music preferences from the user's query. "
    "Reply with ONLY a Python dict literal using these exact keys: "
    "genre (str, one of: pop, lofi, rock, jazz, classical, metal, hip-hop, r&b, "
    "country, edm, reggae, ambient, synthwave, folk, 'indie pop'), "
    "mood (str, one of: happy, chill, intense, focused, relaxed, euphoric, "
    "uplifting, romantic, confident, nostalgic, melancholic, aggressive, moody, sad), "
    "energy (float 0.0–1.0), "
    "acoustic (bool). "
    "Example: {'genre': 'lofi', 'mood': 'chill', 'energy': 0.4, 'acoustic': True}"
)

_GENERATION_SYSTEM = """\
You are WaveSort, a music recommendation assistant.
You receive the user's request and a list of songs retrieved from the catalog.

Your job:
1. Acknowledge what the user is looking for (1 sentence).
2. For each retrieved song, explain specifically why it fits — reference its genre,
   mood, and energy level.
3. Keep the entire response under 150 words.

Be warm and concise. Only mention songs from the retrieved list."""


def _extract_prefs(query: str, client: anthropic.Anthropic) -> Dict:
    """Parse a natural language query into a structured preferences dict."""
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=128,
        system=[{
            "type": "text",
            "text": _EXTRACTION_SYSTEM,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": query}],
    )
    raw = response.content[0].text.strip()
    try:
        prefs = ast.literal_eval(raw)
        if isinstance(prefs, dict):
            return prefs
    except Exception:
        pass
    return {"genre": "pop", "mood": "happy", "energy": 0.5, "acoustic": False}


def _load_genre_context(context_path: str) -> str:
    """Read genre_context.md; return empty string if the file is missing."""
    try:
        with open(context_path, encoding="utf-8") as f:
            return f.read()
    except (FileNotFoundError, OSError):
        return ""


_ENHANCED_GENERATION_SYSTEM = """\
You are WaveSort, a music recommendation assistant with access to two knowledge sources:
  1. A genre and mood knowledge base with domain-level context
  2. Songs retrieved from the WaveSort catalog

Your job:
1. Acknowledge what the user is looking for (1 sentence).
2. For each retrieved song, explain specifically why it fits — reference its genre,
   mood, and energy level. Draw on the genre knowledge base to explain domain
   characteristics (e.g. why a lofi track aids focus, or what makes EDM euphoric).
3. End with one sentence about the best use case for this set of songs.
4. Keep the entire response under 180 words.

Only mention songs from the retrieved list. Never invent attributes."""


def rag_recommend(
    query: str,
    catalog_path: str,
    k: int = 3,
    api_key: Optional[str] = None,
) -> str:
    """
    Full RAG pipeline: parse query → retrieve matching songs → generate explanation.

    Args:
        query:        Natural language request (e.g. "upbeat songs for the gym")
        catalog_path: Path to songs.csv
        k:            Number of songs to retrieve and explain
        api_key:      Anthropic API key (defaults to ANTHROPIC_API_KEY env var)

    Returns:
        A natural language recommendation string from Claude.
    """
    client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    # Step 1: Retrieve — parse query, score catalog, pick top-k
    prefs = _extract_prefs(query, client)
    songs = load_songs(catalog_path)
    top_k: List[Tuple[Dict, float, List[str]]] = recommend_songs(
        prefs, songs, k=k, mode="balanced"
    )

    # Step 2: Augment — format retrieved songs as LLM context
    context_lines = [f'User request: "{query}"', "", "Retrieved songs from catalog:"]
    for i, (song, score, reasons) in enumerate(top_k, 1):
        why = "; ".join(reasons) if reasons else "partial feature match"
        context_lines.append(
            f'  {i}. "{song["title"]}" by {song["artist"]}'
            f" (genre: {song['genre']}, mood: {song['mood']},"
            f" energy: {song['energy']:.2f}) — matched because: {why}"
        )
    augmented_prompt = "\n".join(context_lines)

    # Step 3: Generate — Claude explains the picks using the retrieved context
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=256,
        system=[{
            "type": "text",
            "text": _GENERATION_SYSTEM,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": augmented_prompt}],
    )
    return response.content[0].text.strip()


def rag_recommend_enhanced(
    query: str,
    catalog_path: str,
    context_path: str,
    k: int = 3,
    api_key: Optional[str] = None,
) -> str:
    """
    RAG pipeline with a second knowledge source: genre_context.md.

    Retrieve  — same as rag_recommend (Claude parses query → core engine scores)
    Augment   — retrieved songs + genre/mood knowledge base injected as context
    Generate  — Claude explains picks using BOTH sources; responses reference
                domain characteristics (e.g. energy norms, use-case pairings) that
                are absent from the CSV but present in genre_context.md.

    Args:
        query:        Natural language request
        catalog_path: Path to songs.csv
        context_path: Path to genre_context.md (second knowledge source)
        k:            Number of songs to retrieve and explain
        api_key:      Anthropic API key (defaults to ANTHROPIC_API_KEY env var)

    Returns:
        A natural language recommendation string enriched with domain knowledge.
    """
    client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    # Step 1: Retrieve (identical to base rag_recommend)
    prefs = _extract_prefs(query, client)
    songs = load_songs(catalog_path)
    top_k: List[Tuple[Dict, float, List[str]]] = recommend_songs(
        prefs, songs, k=k, mode="balanced"
    )

    # Step 2: Augment — two sources
    genre_context = _load_genre_context(context_path)

    context_lines = []
    if genre_context:
        context_lines.append("[KNOWLEDGE BASE]")
        context_lines.append(genre_context)
        context_lines.append("")

    context_lines.append("[CATALOG RESULTS]")
    context_lines.append(f'User request: "{query}"')
    context_lines.append("")
    context_lines.append("Retrieved songs from catalog:")
    for i, (song, score, reasons) in enumerate(top_k, 1):
        why = "; ".join(reasons) if reasons else "partial feature match"
        context_lines.append(
            f'  {i}. "{song["title"]}" by {song["artist"]}'
            f" (genre: {song['genre']}, mood: {song['mood']},"
            f" energy: {song['energy']:.2f}, acousticness: {song.get('acousticness', 0):.2f},"
            f" instrumentalness: {song.get('instrumentalness', 0):.2f})"
            f" — matched because: {why}"
        )
    augmented_prompt = "\n".join(context_lines)

    # Step 3: Generate — uses the knowledge-aware system prompt
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=320,
        system=[{
            "type": "text",
            "text": _ENHANCED_GENERATION_SYSTEM,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": augmented_prompt}],
    )
    return response.content[0].text.strip()
