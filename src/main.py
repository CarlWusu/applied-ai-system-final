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


if __name__ == "__main__":
    main()
