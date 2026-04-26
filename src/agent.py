"""
Feature 2 — Agentic Workflow

The RecommendationAgent runs a plan → act → check → adjust loop:

  Plan    — choose the best initial scoring mode based on user preferences
  Act     — generate recommendations using the current mode
  Check   — evaluate quality: genre hit rate + energy fit → combined score
  Adjust  — if quality is below threshold, try a different mode and repeat
  Return  — final recommendations with a full reasoning trace

No LLM is required — the agent uses deterministic quality metrics. This
demonstrates how an agentic system can self-correct without API calls.
"""

from typing import Dict, List, Optional, Tuple

from src.recommender import recommend_songs, diversity_rerank

QualityReport = Dict  # {score, genre_hit_rate, energy_fit, mode, iteration}


class RecommendationAgent:
    """
    Self-correcting recommendation agent with a plan → act → check → adjust loop.

    Quality is measured as:
        score = 0.5 × genre_hit_rate + 0.5 × avg_energy_fit

    The agent iterates until score ≥ QUALITY_THRESHOLD or all modes are tried.
    """

    QUALITY_THRESHOLD = 0.55

    def __init__(self, songs: List[Dict], max_iterations: int = 3):
        self.songs = songs
        self.max_iterations = max_iterations

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(
        self,
        user_prefs: Dict,
        k: int = 5,
        diversity: bool = True,
    ) -> Dict:
        """
        Execute the agentic loop.

        Returns a dict with:
          recommendations  List of (song, score, reasons) tuples
          final_mode       Scoring mode used for the final results
          iterations       Number of loop iterations taken
          trace            Per-iteration quality reports
          verdict          Human-readable summary of what the agent did
        """
        trace: List[QualityReport] = []
        modes_tried: List[str] = []
        results: List[Tuple] = []
        mode = self._plan(user_prefs)

        for iteration in range(1, self.max_iterations + 1):
            # Act
            results = recommend_songs(user_prefs, self.songs, k=k * 2, mode=mode)
            if diversity:
                results = diversity_rerank(results)[:k]
            else:
                results = results[:k]

            # Check
            report = self._evaluate(results, user_prefs, mode, iteration)
            trace.append(report)
            modes_tried.append(mode)

            if report["score"] >= self.QUALITY_THRESHOLD:
                break

            # Adjust — try the next untried mode
            next_mode = self._adjust(modes_tried)
            if next_mode is None:
                break
            mode = next_mode

        return {
            "recommendations": results,
            "final_mode": mode,
            "iterations": len(trace),
            "trace": trace,
            "verdict": self._summarize(trace, modes_tried),
        }

    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------

    def _plan(self, user_prefs: Dict) -> str:
        """Choose the initial scoring mode based on the strongest preference signal."""
        energy = user_prefs.get("energy", 0.5)
        mood = user_prefs.get("mood", "")

        if energy >= 0.85 or energy <= 0.25:
            return "energy_focused"
        if mood in ("melancholic", "aggressive", "euphoric", "romantic", "sad"):
            return "mood_first"
        return "balanced"

    def _evaluate(
        self,
        results: List[Tuple],
        user_prefs: Dict,
        mode: str,
        iteration: int,
    ) -> QualityReport:
        """
        Compute a quality score for the current recommendation set.

        Metrics:
          genre_hit_rate — fraction of results matching the user's target genre
          energy_fit     — average proximity to the user's target energy (0–1)
          score          — equal-weight combination of both metrics
        """
        if not results:
            return {
                "score": 0.0, "genre_hit_rate": 0.0, "energy_fit": 0.0,
                "mode": mode, "iteration": iteration,
            }

        target_genre = user_prefs.get("genre", "")
        target_energy = user_prefs.get("energy", 0.5)

        genre_hits = sum(1 for s, _, _ in results if s.get("genre") == target_genre)
        genre_hit_rate = genre_hits / len(results)

        energy_fit = sum(
            1.0 - abs(s.get("energy", 0.5) - target_energy)
            for s, _, _ in results
        ) / len(results)

        return {
            "score": round(0.5 * genre_hit_rate + 0.5 * energy_fit, 3),
            "genre_hit_rate": round(genre_hit_rate, 3),
            "energy_fit": round(energy_fit, 3),
            "mode": mode,
            "iteration": iteration,
        }

    def _adjust(self, modes_tried: List[str]) -> Optional[str]:
        """Return the next mode to try, or None when all modes have been tried."""
        for mode in ["balanced", "mood_first", "energy_focused", "genre_first"]:
            if mode not in modes_tried:
                return mode
        return None

    def _summarize(self, trace: List[QualityReport], modes_tried: List[str]) -> str:
        if not trace:
            return "Agent produced no results."
        best = max(trace, key=lambda r: r["score"])
        if len(trace) == 1:
            return (
                f"Agent selected '{modes_tried[0]}' mode on the first pass "
                f"(quality: {best['score']:.2f}, genre hit rate: "
                f"{best['genre_hit_rate']:.0%}, energy fit: {best['energy_fit']:.2f})."
            )
        tried = " → ".join(modes_tried)
        return (
            f"Agent tried {len(trace)} modes ({tried}) and settled on "
            f"'{best['mode']}' (quality: {best['score']:.2f}, "
            f"genre hit rate: {best['genre_hit_rate']:.0%}, "
            f"energy fit: {best['energy_fit']:.2f})."
        )
