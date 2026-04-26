"""WaveSort 1.0 — Music Recommender Simulation CLI.

Run from the project root:
    python src/main.py
"""

import os
import sys
from typing import List, Tuple, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.recommender import (
    load_songs,
    recommend_songs,
    diversity_rerank,
    max_possible_score,
    SCORING_MODES,
)

# Challenge 4 — tabulate for pretty tables (falls back to ASCII if not installed)
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

# ---------------------------------------------------------------------------
# Config — change these to explore different behaviours
# ---------------------------------------------------------------------------

CURRENT_MODE = "balanced"   # "balanced" | "genre_first" | "mood_first" | "energy_focused"
USE_DIVERSITY = True        # True = apply artist/genre diversity filter
TOP_K        = 5

# ---------------------------------------------------------------------------
# User profiles — change ACTIVE_PROFILE to switch
# ---------------------------------------------------------------------------

PROFILES: Dict[str, Dict] = {
    "pop / happy": {
        "genre": "pop", "mood": "happy", "energy": 0.80,
        "popularity_target": 80, "preferred_decade": 2020,
        "instrumental_target": 0.1,
    },
    "lofi / chill": {
        "genre": "lofi", "mood": "chill", "energy": 0.40,
        "acoustic": True, "popularity_target": 55,
        "preferred_decade": 2020, "instrumental_target": 0.85,
    },
    "classical / melancholic": {
        "genre": "classical", "mood": "melancholic", "energy": 0.22,
        "acoustic": True, "popularity_target": 35,
        "preferred_decade": 2000, "instrumental_target": 0.90,
    },
    "metal / aggressive": {
        "genre": "metal", "mood": "aggressive", "energy": 0.98,
        "popularity_target": 60, "preferred_decade": 2010,
        "instrumental_target": 0.1,
    },
}

ACTIVE_PROFILE = "pop / happy"   # change this to switch profiles

# ---------------------------------------------------------------------------
# Feature demos — set DEMO_AI_FEATURES = True and provide ANTHROPIC_API_KEY
# to run the 4 AI feature demonstrations after the main recommendation table.
# ---------------------------------------------------------------------------

DEMO_AI_FEATURES = False  # flip to True to run all 4 feature demos

try:
    from src.rag import rag_recommend
    from src.agent import RecommendationAgent
    from src.music_assistant import MusicAssistant
    _AI_MODULES_AVAILABLE = True
except ImportError:
    _AI_MODULES_AVAILABLE = False


# ---------------------------------------------------------------------------
# Challenge 4 — Display helpers
# ---------------------------------------------------------------------------

def _truncate(text: str, max_len: int = 48) -> str:
    """Shorten a string with ellipsis if it exceeds max_len."""
    return text if len(text) <= max_len else text[: max_len - 1] + "..."


def display_table(
    results: List[Tuple],
    mode: str,
    profile_label: str,
    diversity_applied: bool,
) -> None:
    """Print recommendations as a formatted table (tabulate or ASCII fallback)."""
    max_sc = max_possible_score(mode)
    header_line = (
        f"  WaveSort 1.0  |  Profile: {profile_label}"
        f"  |  Mode: {mode.upper()}"
        + ("  |  Diversity ON" if diversity_applied else "")
    )
    print(f"\n{'-' * len(header_line)}")
    print(header_line)
    print(f"{'-' * len(header_line)}\n")

    rows = []
    for rank, (song, score, reasons) in enumerate(results, start=1):
        bar_len   = round((score / max_sc) * 16)
        score_bar = "#" * bar_len + "." * (16 - bar_len)
        top_why   = _truncate("; ".join(reasons) if reasons else "partial match")
        rows.append([
            rank,
            song["title"],
            song["artist"],
            song["genre"],
            f"{score:.2f}/{max_sc:.1f}",
            f"[{score_bar}]",
            top_why,
        ])

    headers = ["#", "Title", "Artist", "Genre", "Score", "Bar", "Why"]

    if HAS_TABULATE:
        print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))
    else:
        # ASCII fallback — fixed-width columns
        widths = [
            max(len(str(r[i])) for r in rows + [headers])
            for i in range(len(headers))
        ]
        sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
        hdr = "| " + " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers)) + " |"
        print(sep)
        print(hdr)
        print(sep)
        for row in rows:
            print("| " + " | ".join(str(v).ljust(widths[i]) for i, v in enumerate(row)) + " |")
        print(sep)

    print()


def display_mode_comparison(
    user_prefs: Dict, songs: list, profile_label: str
) -> None:
    """Show how the top-5 rankings shift across all 4 scoring modes side by side."""
    mode_names = list(SCORING_MODES.keys())

    all_results: Dict[str, List] = {}
    for mode in mode_names:
        res = recommend_songs(user_prefs, songs, k=TOP_K * 2, mode=mode)
        if USE_DIVERSITY:
            res = diversity_rerank(res)[:TOP_K]
        else:
            res = res[:TOP_K]
        all_results[mode] = res

    table_rows = []
    for rank in range(TOP_K):
        row = [f"#{rank + 1}"]
        for mode in mode_names:
            if rank < len(all_results[mode]):
                title = all_results[mode][rank][0]["title"]
                sc    = all_results[mode][rank][1]
                row.append(f"{title} ({sc:.1f})")
            else:
                row.append("—")
        table_rows.append(row)

    col_headers = ["Rank"] + [m.replace("_", "-") for m in mode_names]

    print(f"  Mode Comparison  |  Profile: {profile_label}\n")
    if HAS_TABULATE:
        print(tabulate(table_rows, headers=col_headers, tablefmt="rounded_outline"))
    else:
        # simple text fallback
        col_w = [max(len(str(r[i])) for r in table_rows + [col_headers]) for i in range(len(col_headers))]
        sep = "+-" + "-+-".join("-" * w for w in col_w) + "-+"
        print(sep)
        print("| " + " | ".join(str(h).ljust(col_w[i]) for i, h in enumerate(col_headers)) + " |")
        print(sep)
        for row in table_rows:
            print("| " + " | ".join(str(v).ljust(col_w[i]) for i, v in enumerate(row)) + " |")
        print(sep)
    print()


# ---------------------------------------------------------------------------
# Feature demos (Features 1–4)
# ---------------------------------------------------------------------------

def demo_features(catalog_path: str, songs: list) -> None:
    """Run all 4 AI feature demonstrations. Requires ANTHROPIC_API_KEY."""
    import os
    if not _AI_MODULES_AVAILABLE:
        print("\n[Demo] Could not import AI modules. Run: pip install anthropic\n")
        return
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n[Demo] Set ANTHROPIC_API_KEY to run the AI feature demos.\n")
        return

    user_prefs = PROFILES[ACTIVE_PROFILE]
    sep = "=" * 62

    print(f"\n{sep}")
    print("  AI FEATURE DEMOS")
    print(sep)

    # ------------------------------------------------------------------
    # Feature 1: Retrieval-Augmented Generation
    # ------------------------------------------------------------------
    print("\n[Feature 1] RAG — Retrieval-Augmented Generation")
    print("-" * 40)
    query = "upbeat songs for working out at the gym"
    print(f"  Natural language query: \"{query}\"")
    try:
        result = rag_recommend(query, catalog_path, k=3)
        print(f"\n  Claude's response:\n  {result}\n")
    except Exception as exc:
        print(f"  Error: {exc}\n")

    # ------------------------------------------------------------------
    # Feature 2: Agentic Workflow
    # ------------------------------------------------------------------
    print("[Feature 2] Agentic Workflow — plan → act → check → adjust")
    print("-" * 40)
    print(f"  Profile: {ACTIVE_PROFILE}")
    agent = RecommendationAgent(songs, max_iterations=3)
    outcome = agent.run(user_prefs, k=TOP_K)
    print(f"\n  {outcome['verdict']}")
    print(f"\n  Iteration trace:")
    for r in outcome["trace"]:
        print(
            f"    iter {r['iteration']}: mode={r['mode']:<16} "
            f"score={r['score']:.2f}  "
            f"genre_hit={r['genre_hit_rate']:.0%}  "
            f"energy_fit={r['energy_fit']:.2f}"
        )
    print(f"\n  Top picks (final mode: {outcome['final_mode']}):")
    for i, (song, score, _) in enumerate(outcome["recommendations"][:3], 1):
        print(f"    {i}. {song['title']} — {song['genre']}, score {score:.2f}")
    print()

    # ------------------------------------------------------------------
    # Feature 3: Specialized / Fine-Tuned Model
    # ------------------------------------------------------------------
    print("[Feature 3] Specialized Model — WaveSort AI expert")
    print("-" * 40)
    question = "What is the best song for a late-night coding session, and why?"
    print(f"  Question: \"{question}\"")
    try:
        assistant = MusicAssistant(catalog_path)
        answer = assistant.ask(question)
        print(f"\n  WaveSort AI:\n  {answer}\n")
    except Exception as exc:
        print(f"  Error: {exc}\n")

    # ------------------------------------------------------------------
    # Feature 4: Reliability Testing
    # ------------------------------------------------------------------
    print("[Feature 4] Reliability Testing")
    print("-" * 40)
    print("  Run the test suite to verify all reliability checks:")
    print("    pytest tests/test_reliability.py -v")
    print()
    print("  Checks included:")
    print("    - Determinism: same input → same ranked output")
    print("    - Score bounds: no score exceeds the mode maximum")
    print("    - Diversity: artist/genre caps enforced")
    print("    - Mode behavior: genre_first > balanced on genre matches")
    print("    - Regression: known profiles produce known top songs")
    print("    - Edge cases: empty catalog, k > catalog size, unknown genre")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Load catalog, run recommendations for the active profile, display results."""
    catalog_path = os.path.join(os.path.dirname(__file__), "..", "data", "songs.csv")
    songs = load_songs(catalog_path)
    print(f"\nLoaded {len(songs)} songs from catalog.")
    if not HAS_TABULATE:
        print("  tip: pip install tabulate for prettier output\n")

    user_prefs = PROFILES[ACTIVE_PROFILE]

    # Main recommendation table
    results = recommend_songs(user_prefs, songs, k=TOP_K * 2, mode=CURRENT_MODE)
    if USE_DIVERSITY:
        results = diversity_rerank(results)[:TOP_K]
    else:
        results = results[:TOP_K]

    display_table(results, CURRENT_MODE, ACTIVE_PROFILE, USE_DIVERSITY)

    # Mode comparison — shows how rankings shift when you change the strategy
    display_mode_comparison(user_prefs, songs, ACTIVE_PROFILE)

    # AI feature demos — runs when DEMO_AI_FEATURES = True
    if DEMO_AI_FEATURES:
        demo_features(catalog_path, songs)


if __name__ == "__main__":
    main()
