"""
Test Harness — WaveSort 1.0 Evaluation Script

Runs the recommender against 10 predefined profiles and prints a
pass/fail table with per-case confidence scores.

Usage (from project root):
    python3 scripts/run_eval.py
    python3 scripts/run_eval.py --mode genre_first
    python3 scripts/run_eval.py --verbose
"""

import os
import sys
import argparse
from dataclasses import dataclass
from typing import Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.recommender import load_songs, recommend_songs, max_possible_score


# ---------------------------------------------------------------------------
# Evaluation cases
# ---------------------------------------------------------------------------

@dataclass
class EvalCase:
    name: str
    prefs: Dict
    expect_genre: str
    expect_mood: Optional[str] = None
    min_confidence: float = 0.60


EVAL_CASES: List[EvalCase] = [
    EvalCase("pop / happy",
             {"genre": "pop",       "mood": "happy",      "energy": 0.80},
             "pop",  "happy",  0.68),
    EvalCase("lofi / chill / acoustic",
             {"genre": "lofi",      "mood": "chill",      "energy": 0.40, "acoustic": True},
             "lofi", "chill",  0.75),
    EvalCase("rock / intense",
             {"genre": "rock",      "mood": "intense",    "energy": 0.91},
             "rock", "intense", 0.65),
    EvalCase("edm / euphoric",
             {"genre": "edm",       "mood": "euphoric",   "energy": 0.97},
             "edm",  "euphoric", 0.72),
    EvalCase("classical / melancholic",
             {"genre": "classical", "mood": "melancholic", "energy": 0.22, "acoustic": True},
             "classical", "melancholic", 0.72),
    EvalCase("metal / aggressive",
             {"genre": "metal",     "mood": "aggressive", "energy": 0.98},
             "metal", "aggressive", 0.65),
    EvalCase("jazz / relaxed",
             {"genre": "jazz",      "mood": "relaxed",    "energy": 0.37, "acoustic": True},
             "jazz", "relaxed", 0.65),
    EvalCase("hip-hop / confident",
             {"genre": "hip-hop",   "mood": "confident",  "energy": 0.78},
             "hip-hop", "confident", 0.65),
    EvalCase("r&b / romantic",
             {"genre": "r&b",       "mood": "romantic",   "energy": 0.55},
             "r&b", "romantic", 0.65),
    EvalCase("folk / sad",
             {"genre": "folk",      "mood": "sad",        "energy": 0.25, "acoustic": True},
             "folk", "sad", 0.60),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_eval(catalog_path: str, mode: str = "balanced", verbose: bool = False) -> int:
    """
    Run all evaluation cases against the catalog.
    Returns the number of failures (0 = all passed).
    """
    songs = load_songs(catalog_path)
    max_sc = max_possible_score(mode)

    passed = 0
    confidences = []
    failures = []

    col_w = max(len(c.name) for c in EVAL_CASES) + 2

    print(f"\nWaveSort 1.0 — Evaluation Harness  (mode: {mode})")
    print(f"Catalog: {len(songs)} songs   Cases: {len(EVAL_CASES)}")
    print("-" * (col_w + 52))
    print(f"  {'CASE'.ljust(col_w)}  CONF    TOP RESULT                STATUS")
    print("-" * (col_w + 52))

    for i, case in enumerate(EVAL_CASES, start=1):
        results = recommend_songs(case.prefs, songs, k=1, mode=mode)
        if not results:
            status = "FAIL (empty)"
            failures.append(case.name)
            print(f"  {case.name.ljust(col_w)}  ----    (no results)               FAIL")
            continue

        top_song, top_score, top_reasons = results[0]
        confidence = round(top_score / max_sc, 2)
        confidences.append(confidence)

        genre_ok = top_song["genre"] == case.expect_genre
        mood_ok  = (case.expect_mood is None) or (top_song["mood"] == case.expect_mood)
        conf_ok  = confidence >= case.min_confidence
        ok = genre_ok and mood_ok and conf_ok

        label = f'{top_song["title"]} ({top_song["genre"]}/{top_song["mood"]})'
        status = "PASS" if ok else "FAIL"
        indicator = "✓" if ok else "✗"

        print(f"  {case.name.ljust(col_w)}  {confidence:.2f}    {label[:32].ljust(33)} {indicator} {status}")

        if verbose and not ok:
            if not genre_ok:
                print(f"    ↳ expected genre={case.expect_genre!r}, got {top_song['genre']!r}")
            if not mood_ok:
                print(f"    ↳ expected mood={case.expect_mood!r}, got {top_song['mood']!r}")
            if not conf_ok:
                print(f"    ↳ confidence {confidence:.2f} < threshold {case.min_confidence:.2f}")
            if top_reasons:
                print(f"    ↳ scoring: {'; '.join(top_reasons[:3])}")

        if ok:
            passed += 1
        else:
            failures.append(case.name)

    print("-" * (col_w + 52))
    avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
    print(f"\nResult: {passed}/{len(EVAL_CASES)} passed   avg confidence: {avg_conf}\n")

    if failures:
        print("Failed cases:")
        for name in failures:
            print(f"  - {name}")
        print()

    return len(EVAL_CASES) - passed


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WaveSort evaluation harness")
    parser.add_argument("--mode", default="balanced",
                        choices=["balanced", "genre_first", "mood_first", "energy_focused"],
                        help="Scoring mode (default: balanced)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print per-failure diagnostics")
    args = parser.parse_args()

    catalog = os.path.join(os.path.dirname(__file__), "..", "data", "songs.csv")
    failures = run_eval(catalog, mode=args.mode, verbose=args.verbose)
    sys.exit(1 if failures else 0)
