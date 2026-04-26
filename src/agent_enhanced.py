"""
Agentic Workflow Enhancement — Claude Tool-Use Recommendation Agent

Extends the deterministic RecommendationAgent with real Anthropic tool use.
Claude drives the loop by calling three tools in sequence:

  check_catalog_coverage(genre)          — how many songs exist for this genre
  score_and_rank(prefs_dict, mode)       — run the scoring engine, return top-5
  evaluate_quality(genre_hit_rate, energy_fit) — compute quality score

Each tool call is an observable intermediate step printed to stdout (or
captured in the returned trace). After all tool calls complete, Claude
produces a final natural language explanation and recommendation verdict.

This demonstrates multi-step reasoning with observable, auditable steps.
"""

import json
import os
from typing import Dict, List, Optional, Tuple

import anthropic

from src.recommender import recommend_songs, max_possible_score, SCORING_MODES

# ---------------------------------------------------------------------------
# Tool definitions (JSON Schema)
# ---------------------------------------------------------------------------

_TOOLS = [
    {
        "name": "check_catalog_coverage",
        "description": (
            "Check how many songs in the catalog match a given genre and return their titles. "
            "Call this first to understand how much catalog depth is available before scoring."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "genre": {"type": "string", "description": "Genre to check (e.g. 'lofi', 'pop')"}
            },
            "required": ["genre"],
        },
    },
    {
        "name": "score_and_rank",
        "description": (
            "Score and rank all catalog songs against user preferences using the specified mode. "
            "Returns the top-5 results with title, genre, mood, energy, and normalised confidence."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prefs_dict": {
                    "type": "object",
                    "description": "User preferences: genre, mood, energy (float 0-1), acoustic (bool)",
                },
                "mode": {
                    "type": "string",
                    "enum": list(SCORING_MODES.keys()),
                    "description": "Scoring mode to use",
                },
            },
            "required": ["prefs_dict", "mode"],
        },
    },
    {
        "name": "evaluate_quality",
        "description": (
            "Compute a quality score for the current recommendation set from two metrics. "
            "Returns a combined quality score and whether it exceeds the acceptance threshold."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "genre_hit_rate": {
                    "type": "number",
                    "description": "Fraction of top results matching the target genre (0.0–1.0)",
                },
                "energy_fit": {
                    "type": "number",
                    "description": "Average energy proximity across top results (0.0–1.0)",
                },
            },
            "required": ["genre_hit_rate", "energy_fit"],
        },
    },
]

_SYSTEM_PROMPT = """\
You are a music recommendation agent with access to three tools. Use them in this order:

1. check_catalog_coverage — call with the user's requested genre to understand how many
   songs are available. If coverage is thin (< 2 songs), note this to the user.
2. score_and_rank — call with the user's preferences and an appropriate mode (start with
   "balanced"; switch to "genre_first" if coverage is good, "energy_focused" if the user
   has an extreme energy target).
3. evaluate_quality — call with the genre_hit_rate and energy_fit from the ranking results
   to verify quality. If quality < 0.55, explain the limitation to the user.

After all three tools report back, give your final recommendation verdict in 2-3 sentences,
referencing the specific songs and confidence scores from the tool results.
Be concise and specific. Do not repeat the tool outputs verbatim."""


class ClaudeRecommendationAgent:
    """
    Music recommendation agent that uses Claude tool use for multi-step reasoning.

    Observable intermediate steps:
      [Tool Call]   tool_name(inputs)
      [Tool Result] {output}

    Claude decides which mode to use, then verifies quality — all visible.
    """

    MAX_TOOL_ITERATIONS = 8
    QUALITY_THRESHOLD = 0.55

    def __init__(self, songs: List[Dict], api_key: Optional[str] = None):
        self.songs = songs
        self._client = anthropic.Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(
        self,
        user_prefs: Dict,
        k: int = 5,
        verbose: bool = True,
    ) -> Dict:
        """
        Run the tool-use recommendation loop.

        Returns:
          recommendations  — list of (song, score, reasons) from best mode
          tool_calls       — ordered list of {tool, input, output} dicts
          explanation      — Claude's final natural language verdict
          error            — error message if API is unavailable (else None)
        """
        messages = [
            {
                "role": "user",
                "content": (
                    f"Find the top {k} songs for a user with these preferences: "
                    f"{json.dumps(user_prefs)}. "
                    "Use the tools in order to check coverage, score, and verify quality."
                ),
            }
        ]

        tool_calls: List[Dict] = []
        last_recommendations: List[Tuple] = []

        try:
            for _ in range(self.MAX_TOOL_ITERATIONS):
                response = self._client.messages.create(
                    model="claude-opus-4-7",
                    max_tokens=1024,
                    system=_SYSTEM_PROMPT,
                    tools=_TOOLS,
                    messages=messages,
                )

                if response.stop_reason == "end_turn":
                    explanation = next(
                        (b.text for b in response.content if hasattr(b, "text")), ""
                    )
                    return {
                        "recommendations": last_recommendations,
                        "tool_calls": tool_calls,
                        "explanation": explanation,
                        "error": None,
                    }

                if response.stop_reason != "tool_use":
                    break

                # Collect all tool_use blocks in this response
                tool_result_content = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    result_str = self._dispatch(block.name, block.input)

                    if verbose:
                        print(f"[Tool Call]   {block.name}({json.dumps(block.input)})")
                        print(f"[Tool Result] {result_str}\n")

                    tool_calls.append({
                        "tool": block.name,
                        "input": block.input,
                        "output": result_str,
                    })

                    # Cache the last score_and_rank result so we can return it
                    if block.name == "score_and_rank":
                        prefs = block.input.get("prefs_dict", user_prefs)
                        mode = block.input.get("mode", "balanced")
                        last_recommendations = recommend_songs(
                            prefs, self.songs, k=k, mode=mode
                        )

                    tool_result_content.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })

                # Append assistant turn + tool results user turn
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_result_content})

        except (anthropic.AuthenticationError, anthropic.APIConnectionError) as exc:
            return {
                "recommendations": [],
                "tool_calls": tool_calls,
                "explanation": "",
                "error": str(exc),
            }

        return {
            "recommendations": last_recommendations,
            "tool_calls": tool_calls,
            "explanation": "",
            "error": None,
        }

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def _dispatch(self, tool_name: str, inputs: Dict) -> str:
        """Route a tool call to its implementation; return result as JSON string."""
        if tool_name == "check_catalog_coverage":
            return self._check_coverage(inputs["genre"])
        if tool_name == "score_and_rank":
            return self._score_and_rank(inputs["prefs_dict"], inputs["mode"])
        if tool_name == "evaluate_quality":
            return self._evaluate_quality(
                inputs["genre_hit_rate"], inputs["energy_fit"]
            )
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def _check_coverage(self, genre: str) -> str:
        matches = [s for s in self.songs if s.get("genre") == genre]
        return json.dumps({
            "genre": genre,
            "count": len(matches),
            "titles": [s["title"] for s in matches],
            "coverage": "good" if len(matches) >= 2 else "thin" if matches else "none",
        })

    def _score_and_rank(self, prefs: Dict, mode: str) -> str:
        safe_mode = mode if mode in SCORING_MODES else "balanced"
        results = recommend_songs(prefs, self.songs, k=5, mode=safe_mode)
        max_sc = max_possible_score(safe_mode)
        target_genre = prefs.get("genre", "")
        target_energy = prefs.get("energy", 0.5)

        genre_hits = sum(1 for s, _, _ in results if s.get("genre") == target_genre)
        energy_fit = round(
            sum(1.0 - abs(s.get("energy", 0.5) - target_energy) for s, _, _ in results)
            / max(len(results), 1), 3
        )

        return json.dumps({
            "mode": safe_mode,
            "genre_hit_rate": round(genre_hits / max(len(results), 1), 3),
            "energy_fit": energy_fit,
            "top_5": [
                {
                    "title": s["title"],
                    "genre": s["genre"],
                    "mood": s["mood"],
                    "energy": s["energy"],
                    "confidence": round(sc / max_sc, 2),
                }
                for s, sc, _ in results
            ],
        })

    def _evaluate_quality(self, genre_hit_rate: float, energy_fit: float) -> str:
        quality = round(0.5 * genre_hit_rate + 0.5 * energy_fit, 3)
        return json.dumps({
            "quality": quality,
            "passes_threshold": quality >= self.QUALITY_THRESHOLD,
            "threshold": self.QUALITY_THRESHOLD,
            "breakdown": {
                "genre_hit_rate": round(genre_hit_rate, 3),
                "energy_fit": round(energy_fit, 3),
            },
        })
