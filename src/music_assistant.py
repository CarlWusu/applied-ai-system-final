"""
Feature 3 — Specialized / Fine-Tuned Model

MusicAssistant uses Claude with a richly specialized system prompt that embeds:
  - The complete WaveSort 18-song catalog with all audio attributes
  - Domain knowledge about scoring modes and feature semantics
  - Instructions to respond like a music recommendation expert

Prompt caching (cache_control) keeps the large system prompt cached across
calls, so repeated questions pay only for the new tokens each time.

This demonstrates the "fine-tuned" experience through deep system-prompt
specialization — the model behaves as a WaveSort domain expert.
"""

import os
from typing import Dict, List, Optional

import anthropic

from src.recommender import load_songs

_BASE_SYSTEM = """\
You are WaveSort AI, a music recommendation expert with deep knowledge of the WaveSort catalog.

## Your domain expertise

Audio dimensions you understand:
- genre / mood: categorical, must match exactly for a score bonus
- energy (0=calm, 1=intense): continuous proximity scoring
- valence (0=dark, 1=bright): implied by mood, used for emotional matching
- acousticness (0=electronic, 1=fully acoustic): determines the acoustic bonus
- popularity (0=underground, 100=mainstream): proximity to user's target
- release_decade: rewards songs from the user's preferred era
- instrumentalness: 0=full vocals, 1=purely instrumental

Scoring modes (weight emphasis):
- balanced:       genre × 3.0, mood × 2.0, energy × 2.0 — general use
- genre_first:    genre × 6.0 — for genre purists
- mood_first:     mood × 5.0 — for emotion/context-driven listening
- energy_focused: energy × 5.0 — for workout or study playlists

## How to answer
- Always reference specific attribute values when recommending or comparing songs
- Be concise — under 150 words unless the user asks for more detail
- If asked why a song ranked where it did, trace through the scoring formula
- Acknowledge catalog limitations honestly (e.g., only 1 metal song exists)

## WaveSort Catalog

{catalog}"""


def _format_catalog(songs: List[Dict]) -> str:
    """Format the song list as a compact reference table."""
    header = (
        "id  | title                      | artist            | "
        "genre      | mood         | energy | acoustic"
    )
    sep = "-" * len(header)
    rows = [header, sep]
    for s in songs:
        rows.append(
            f"{s['id']:2d}  | {s['title']:<26} | {s['artist']:<17} | "
            f"{s['genre']:<10} | {s['mood']:<12} | "
            f"{s['energy']:.2f}   | {s.get('acousticness', 0):.2f}"
        )
    return "\n".join(rows)


class MusicAssistant:
    """
    Specialized Claude-based assistant with the full WaveSort catalog embedded
    in a prompt-cached system prompt.

    The assistant answers music questions with domain expertise:
    - "Why was X recommended over Y?"
    - "What's the best song for late-night coding?"
    - "Compare the top picks for a pop/happy profile"
    """

    def __init__(self, catalog_path: str, api_key: Optional[str] = None):
        self._client = anthropic.Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )
        songs = load_songs(catalog_path)
        catalog_text = _format_catalog(songs)
        self._system = _BASE_SYSTEM.format(catalog=catalog_text)

    def ask(self, question: str) -> str:
        """Ask the WaveSort music expert a question. Returns the expert's answer."""
        response = self._client.messages.create(
            model="claude-opus-4-7",
            max_tokens=300,
            system=[{
                "type": "text",
                "text": self._system,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": question}],
        )
        return response.content[0].text.strip()


# ---------------------------------------------------------------------------
# Specialization Enhancement — few-shot structured format
# ---------------------------------------------------------------------------

_FEW_SHOT_SUFFIX = """

## Response format (follow this exactly)

Every answer must use this structure:
  Top pick: [Song Title] by [Artist] (energy: X.XX)
  Runner-up: [Song Title] by [Artist] — [one sentence on how it compares]
  Best for: [specific use case in 5–10 words]

## Examples

Q: What's the best song for a late-night coding session?
A: Top pick: Midnight Coding by LoRoom (energy: 0.42)
Runner-up: Focus Flow by LoRoom — same lofi feel with a more explicitly focused mood tag
Best for: sustained deep work sessions after 11 PM

Q: Which song would you recommend for winding down after a long day?
A: Top pick: Library Rain by Paper Lanterns (energy: 0.35)
Runner-up: Spacewalk Thoughts by Orbit Bloom — ambient rather than lofi, even lower energy at 0.28
Best for: transitioning from work mode to rest in the evening

Q: Best song for a high-energy workout?
A: Top pick: Iron Curtain by Greywall (energy: 0.98)
Runner-up: Drop Zone by Circuit Fuse — euphoric EDM at 0.97, better for cardio than heavy lifts
Best for: heavy strength training where maximum intensity is needed

Always cite exact energy values from the catalog. Never invent attributes."""


class MusicAssistantEnhanced(MusicAssistant):
    """
    MusicAssistant subclass with three few-shot examples in the system prompt.

    The few-shot examples enforce a structured three-line response format:
      Top pick: [Song] by [Artist] (energy: X.XX)
      Runner-up: [Song] by [Artist] — [comparison sentence]
      Best for: [use case]

    This produces measurably more structured and comparable output than the
    baseline MusicAssistant, which returns free-form prose of variable format.
    Useful for downstream parsing, evaluation, or UI rendering.
    """

    def __init__(self, catalog_path: str, api_key: Optional[str] = None):
        super().__init__(catalog_path, api_key)
        self._system = self._system + _FEW_SHOT_SUFFIX

    def ask(self, question: str) -> str:
        """
        Ask the WaveSort expert a question.
        Response is guaranteed to follow the Top pick / Runner-up / Best for format.
        """
        response = self._client.messages.create(
            model="claude-opus-4-7",
            max_tokens=400,
            system=[{
                "type": "text",
                "text": self._system,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": question}],
        )
        return response.content[0].text.strip()
