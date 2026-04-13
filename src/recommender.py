"""Music recommender simulation — content-based filtering using song attributes."""

from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
import csv


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Song:
    """A single song with its audio attributes and metadata."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # Challenge 1 — advanced features (default values keep old tests working)
    popularity: int = 50             # 0-100  Spotify-style popularity score
    release_decade: int = 2020       # e.g. 1980, 1990, 2000, 2010, 2020
    instrumentalness: float = 0.50   # 0=full vocals, 1=fully instrumental
    liveness: float = 0.10           # probability of being a live recording
    speechiness: float = 0.05        # ratio of spoken word content


@dataclass
class UserProfile:
    """A user's taste preferences used to score and rank songs."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # Challenge 1 — advanced preference fields (all optional with sensible defaults)
    target_popularity: int = 70      # 0=underground, 100=mainstream
    preferred_decade: int = 2020     # preferred release era
    target_instrumentalness: float = 0.50  # 0=want vocals, 1=want pure instrumental
    likes_live: bool = False         # True = bonus for live-feeling recordings


# ---------------------------------------------------------------------------
# Challenge 2 — Scoring Modes (Strategy Pattern)
#
# Each mode is a named weight configuration. Changing the mode shifts which
# feature matters most without rewriting any scoring math. The same
# score_song() function reads the right weights from this dict at runtime.
#
# Mode        | Emphasises           | Good for
# ------------|----------------------|----------------------------------
# balanced    | everything equally   | general use, default
# genre_first | genre above all      | users who never cross genres
# mood_first  | emotional feel       | playlist / context-driven use
# energy_focused | intensity match   | workout, study, party playlists
# ---------------------------------------------------------------------------

SCORING_MODES: Dict[str, Dict[str, float]] = {
    "balanced": {
        "genre": 3.0, "mood": 2.0,  "energy": 2.0,
        "valence": 1.5, "acoustic": 1.0,
        "popularity": 0.8, "decade": 0.6, "instrumental": 0.8, "live": 0.5,
    },
    "genre_first": {
        "genre": 6.0, "mood": 1.0,  "energy": 1.0,
        "valence": 0.5, "acoustic": 0.5,
        "popularity": 0.3, "decade": 0.3, "instrumental": 0.3, "live": 0.3,
    },
    "mood_first": {
        "genre": 1.5, "mood": 5.0,  "energy": 2.0,
        "valence": 2.5, "acoustic": 1.0,
        "popularity": 0.5, "decade": 0.3, "instrumental": 0.5, "live": 0.3,
    },
    "energy_focused": {
        "genre": 1.5, "mood": 1.0,  "energy": 5.0,
        "valence": 1.5, "acoustic": 0.5,
        "popularity": 0.5, "decade": 0.3, "instrumental": 0.3, "live": 0.3,
    },
}


def max_possible_score(mode: str = "balanced") -> float:
    """Return the theoretical maximum score for a given scoring mode."""
    w = SCORING_MODES.get(mode, SCORING_MODES["balanced"])
    return sum(w.values())


# ---------------------------------------------------------------------------
# Mood → implied valence lookup
# ---------------------------------------------------------------------------

MOOD_VALENCE_MAP: Dict[str, float] = {
    "happy":       0.80,
    "relaxed":     0.70,
    "chill":       0.62,
    "focused":     0.58,
    "moody":       0.48,
    "intense":     0.48,
    "euphoric":    0.90,
    "uplifting":   0.85,
    "romantic":    0.73,
    "confident":   0.72,
    "nostalgic":   0.60,
    "melancholic": 0.32,
    "aggressive":  0.32,
    "sad":         0.28,
}


# ---------------------------------------------------------------------------
# Step 1 — Load catalog
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv and return a list of dicts with numeric fields cast correctly."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            song: Dict = {
                "id":           int(row["id"]),
                "title":        row["title"],
                "artist":       row["artist"],
                "genre":        row["genre"],
                "mood":         row["mood"],
                "energy":       float(row["energy"]),
                "tempo_bpm":    float(row["tempo_bpm"]),
                "valence":      float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            }
            # Advanced columns — read if present, skip gracefully if not
            if "popularity"        in row: song["popularity"]        = int(row["popularity"])
            if "release_decade"    in row: song["release_decade"]    = int(row["release_decade"])
            if "instrumentalness"  in row: song["instrumentalness"]  = float(row["instrumentalness"])
            if "liveness"          in row: song["liveness"]          = float(row["liveness"])
            if "speechiness"       in row: song["speechiness"]       = float(row["speechiness"])
            songs.append(song)
    return songs


# ---------------------------------------------------------------------------
# Step 2 — Scoring Rule: judge ONE song against user preferences
#
# Challenge 1: scoring now includes 4 advanced features —
#   popularity proximity, release era proximity, instrumentalness proximity,
#   and a live-recording bonus.
#
# Challenge 2: all weights are read from SCORING_MODES[mode], so switching
#   the mode changes the entire weight configuration without touching this code.
#
# Proximity formula for 0-1 features:
#   points = weight * (1 - |song_value - target_value|)
#
# Proximity formula for popularity (0-100):
#   points = weight * (1 - |song_pop - target_pop| / 100)
#
# Proximity formula for decade (50-year span 1970-2020):
#   points = weight * (1 - |song_decade - target_decade| / 50)
# ---------------------------------------------------------------------------

def score_song(
    user_prefs: Dict,
    song: Dict,
    mode: str = "balanced",
) -> Tuple[float, List[str]]:
    """Score a single song against user preferences; return (total_score, reasons).

    Pass mode= to switch between 'balanced', 'genre_first', 'mood_first',
    or 'energy_focused' weight configurations (Challenge 2).
    """
    w = SCORING_MODES.get(mode, SCORING_MODES["balanced"])
    score = 0.0
    reasons: List[str] = []

    # --- Core features ---

    if song["genre"] == user_prefs.get("genre", ""):
        score += w["genre"]
        reasons.append(f"genre match (+{w['genre']})")

    if song["mood"] == user_prefs.get("mood", ""):
        score += w["mood"]
        reasons.append(f"mood match (+{w['mood']})")

    target_energy = user_prefs.get("energy", 0.5)
    energy_diff   = abs(song["energy"] - target_energy)
    energy_pts    = w["energy"] * (1.0 - energy_diff)
    score += energy_pts
    if energy_diff <= 0.20:
        reasons.append(f"energy {song['energy']:.2f} ~ {target_energy:.2f} (+{energy_pts:.2f})")

    target_valence = user_prefs.get(
        "valence", MOOD_VALENCE_MAP.get(user_prefs.get("mood", ""), 0.60)
    )
    valence_diff = abs(song["valence"] - target_valence)
    valence_pts  = w["valence"] * (1.0 - valence_diff)
    score += valence_pts
    if valence_diff <= 0.20:
        reasons.append(f"valence {song['valence']:.2f} ~ {target_valence:.2f} (+{valence_pts:.2f})")

    if user_prefs.get("acoustic", False) and song.get("acousticness", 0) > 0.6:
        score += w["acoustic"]
        reasons.append(f"acoustic feel {song.get('acousticness', 0):.2f} (+{w['acoustic']})")

    # --- Challenge 1: Advanced features ---

    # Popularity proximity: rewards songs close to user's mainstream preference
    target_pop = user_prefs.get("popularity_target", 70)
    if "popularity" in song:
        pop_diff = abs(song["popularity"] - target_pop) / 100.0
        pop_pts  = w["popularity"] * (1.0 - pop_diff)
        score += pop_pts
        if pop_diff <= 0.15:
            reasons.append(f"popularity {song['popularity']} ~ {target_pop} (+{pop_pts:.2f})")

    # Release decade proximity: rewards songs from the user's preferred era
    # Decade range spans ~50 years (1970–2020) so we normalise by 50
    preferred_decade = user_prefs.get("preferred_decade", 2020)
    if "release_decade" in song:
        decade_diff = abs(song["release_decade"] - preferred_decade) / 50.0
        decade_pts  = w["decade"] * (1.0 - decade_diff)
        score += decade_pts
        if song["release_decade"] == preferred_decade:
            reasons.append(f"era match {song['release_decade']} (+{decade_pts:.2f})")

    # Instrumentalness proximity: rewards songs matching the user's vocal preference
    target_inst = user_prefs.get("instrumental_target", 0.5)
    if "instrumentalness" in song:
        inst_diff = abs(song["instrumentalness"] - target_inst)
        inst_pts  = w["instrumental"] * (1.0 - inst_diff)
        score += inst_pts
        if inst_diff <= 0.20:
            reasons.append(
                f"instrumental feel {song['instrumentalness']:.2f} ~ {target_inst:.2f} (+{inst_pts:.2f})"
            )

    # Liveness bonus: flat reward when user likes live recordings
    if user_prefs.get("likes_live", False) and song.get("liveness", 0) > 0.3:
        score += w["live"]
        reasons.append(f"live feel {song.get('liveness', 0):.2f} (+{w['live']})")

    return score, reasons


# ---------------------------------------------------------------------------
# Step 3 — Ranking Rule
# ---------------------------------------------------------------------------

def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    mode: str = "balanced",
) -> List[Tuple[Dict, float, List[str]]]:
    """Score every song, sort descending, return top-k (song, score, reasons) tuples."""
    scored = [(song, *score_song(user_prefs, song, mode)) for song in songs]
    return sorted(scored, key=lambda item: item[1], reverse=True)[:k]


# ---------------------------------------------------------------------------
# Challenge 3 — Diversity Re-ranking
#
# Why needed: without this, the top-5 might be 3 lofi tracks by LoRoom and
# 2 pop tracks by Neon Echo — repetitive even if they scored highest.
#
# Strategy: walk down the ranked list in order. Accept a song only if it
# doesn't exceed the per-artist or per-genre cap. Songs that don't fit are
# pushed to the back so the list still has k results.
# ---------------------------------------------------------------------------

def diversity_rerank(
    results: List[Tuple[Dict, float, List[str]]],
    max_per_artist: int = 1,
    max_per_genre: int = 2,
) -> List[Tuple[Dict, float, List[str]]]:
    """Re-order results so no artist appears more than once and no genre more than twice."""
    artist_count: Dict[str, int] = {}
    genre_count:  Dict[str, int] = {}
    accepted: List[Tuple[Dict, float, List[str]]] = []
    overflow: List[Tuple[Dict, float, List[str]]] = []

    for item in results:
        song = item[0]
        a, g = song["artist"], song["genre"]
        if (artist_count.get(a, 0) < max_per_artist
                and genre_count.get(g, 0) < max_per_genre):
            accepted.append(item)
            artist_count[a] = artist_count.get(a, 0) + 1
            genre_count[g]  = genre_count.get(g, 0) + 1
        else:
            overflow.append(item)

    return accepted + overflow


# ---------------------------------------------------------------------------
# OOP interface — used by tests/test_recommender.py
# ---------------------------------------------------------------------------

class Recommender:
    """Content-based song recommender that scores and ranks a fixed catalog."""

    def __init__(self, songs: List[Song]):
        """Store the catalog; songs is a list of Song dataclass instances."""
        self.songs = songs

    def _user_to_prefs(self, user: UserProfile) -> Dict:
        """Convert a UserProfile to the dict format expected by score_song."""
        return {
            "genre":               user.favorite_genre,
            "mood":                user.favorite_mood,
            "energy":              user.target_energy,
            "acoustic":            user.likes_acoustic,
            "popularity_target":   user.target_popularity,
            "preferred_decade":    user.preferred_decade,
            "instrumental_target": user.target_instrumentalness,
            "likes_live":          user.likes_live,
        }

    def recommend(
        self,
        user: UserProfile,
        k: int = 5,
        mode: str = "balanced",
        diversity: bool = False,
    ) -> List[Song]:
        """Return top-k Song objects; optionally apply diversity re-ranking."""
        prefs  = self._user_to_prefs(user)
        scored = sorted(
            self.songs,
            key=lambda s: score_song(prefs, asdict(s), mode)[0],
            reverse=True,
        )
        if diversity:
            # Convert to (song, score, reasons) for diversity_rerank, then back
            full = [(s, score_song(prefs, asdict(s), mode)[0],
                     score_song(prefs, asdict(s), mode)[1]) for s in scored]
            reranked = diversity_rerank(full)
            return [item[0] for item in reranked[:k]]
        return scored[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-English explanation of why song was recommended to user."""
        prefs = self._user_to_prefs(user)
        _, reasons = score_song(prefs, asdict(song))
        if not reasons:
            return "Some features partially match your taste profile."
        return "Recommended because: " + "; ".join(reasons) + "."
