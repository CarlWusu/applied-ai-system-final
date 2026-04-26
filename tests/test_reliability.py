"""
Feature 4 — Reliability and Testing System

Tests that verify the recommender behaves consistently and correctly:

  1. Determinism   — same input always produces the same ranked output
  2. Score bounds  — all scores are non-negative and within the mode maximum
  3. Diversity     — re-ranking constraints are enforced in the output
  4. Mode behavior — genre_first rewards genre matches more than balanced mode
  5. Regression    — known profiles produce known top songs (no silent regressions)
  6. Edge cases    — single-song catalog, k > catalog size, unknown genre
"""

import pytest
from dataclasses import asdict

from src.recommender import (
    Song,
    UserProfile,
    Recommender,
    score_song,
    recommend_songs,
    diversity_rerank,
    max_possible_score,
    SCORING_MODES,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def pop_song():
    return Song(
        id=1, title="Pop Hit", artist="Artist A", genre="pop", mood="happy",
        energy=0.85, tempo_bpm=128, valence=0.90, danceability=0.80,
        acousticness=0.10, popularity=82, release_decade=2020,
        instrumentalness=0.05, liveness=0.08, speechiness=0.04,
    )


@pytest.fixture
def lofi_song():
    return Song(
        id=2, title="Lofi Loop", artist="Artist B", genre="lofi", mood="chill",
        energy=0.38, tempo_bpm=80, valence=0.60, danceability=0.50,
        acousticness=0.85, popularity=45, release_decade=2020,
        instrumentalness=0.80, liveness=0.10, speechiness=0.03,
    )


@pytest.fixture
def pop_user():
    return UserProfile(
        favorite_genre="pop", favorite_mood="happy",
        target_energy=0.85, likes_acoustic=False,
        target_popularity=80, preferred_decade=2020,
        target_instrumentalness=0.05,
    )


@pytest.fixture
def four_song_recommender(pop_song, lofi_song):
    """Small catalog with 4 songs for diversity and ordering tests."""
    second_pop = Song(
        id=3, title="Another Pop", artist="Artist C", genre="pop", mood="happy",
        energy=0.80, tempo_bpm=120, valence=0.85, danceability=0.75,
        acousticness=0.15, popularity=75, release_decade=2020,
        instrumentalness=0.08, liveness=0.07, speechiness=0.05,
    )
    same_artist_pop = Song(
        id=4, title="Artist A Again", artist="Artist A", genre="pop", mood="intense",
        energy=0.90, tempo_bpm=135, valence=0.65, danceability=0.85,
        acousticness=0.05, popularity=80, release_decade=2020,
        instrumentalness=0.05, liveness=0.09, speechiness=0.06,
    )
    return Recommender([pop_song, lofi_song, second_pop, same_artist_pop])


# ---------------------------------------------------------------------------
# 1. Determinism — same input always produces the same ranked output
# ---------------------------------------------------------------------------

def test_scoring_is_deterministic(pop_song, pop_user):
    prefs = {
        "genre": pop_user.favorite_genre,
        "mood": pop_user.favorite_mood,
        "energy": pop_user.target_energy,
        "acoustic": pop_user.likes_acoustic,
    }
    score1, reasons1 = score_song(prefs, asdict(pop_song))
    score2, reasons2 = score_song(prefs, asdict(pop_song))
    assert score1 == score2
    assert reasons1 == reasons2


def test_recommend_order_is_deterministic(four_song_recommender, pop_user):
    results1 = four_song_recommender.recommend(pop_user, k=4)
    results2 = four_song_recommender.recommend(pop_user, k=4)
    assert [s.id for s in results1] == [s.id for s in results2]


def test_all_modes_deterministic(pop_song, lofi_song, pop_user):
    prefs = {
        "genre": pop_user.favorite_genre,
        "mood": pop_user.favorite_mood,
        "energy": pop_user.target_energy,
        "acoustic": pop_user.likes_acoustic,
    }
    songs = [asdict(pop_song), asdict(lofi_song)]
    for mode in SCORING_MODES:
        r1 = recommend_songs(prefs, songs, k=2, mode=mode)
        r2 = recommend_songs(prefs, songs, k=2, mode=mode)
        assert [s["id"] for s, _, _ in r1] == [s["id"] for s, _, _ in r2], (
            f"Mode '{mode}' produced different orderings on repeated calls"
        )


# ---------------------------------------------------------------------------
# 2. Score bounds — scores are non-negative and within the mode maximum
# ---------------------------------------------------------------------------

def test_scores_are_non_negative(pop_song, lofi_song, pop_user):
    prefs = {
        "genre": pop_user.favorite_genre,
        "mood": pop_user.favorite_mood,
        "energy": pop_user.target_energy,
        "acoustic": pop_user.likes_acoustic,
    }
    for song in (pop_song, lofi_song):
        score, _ = score_song(prefs, asdict(song))
        assert score >= 0.0, f"Score for '{song.title}' was negative: {score}"


def test_score_does_not_exceed_mode_maximum(pop_song, pop_user):
    prefs = {
        "genre": pop_user.favorite_genre,
        "mood": pop_user.favorite_mood,
        "energy": pop_user.target_energy,
        "acoustic": pop_user.likes_acoustic,
        "popularity_target": pop_user.target_popularity,
        "preferred_decade": pop_user.preferred_decade,
        "instrumental_target": pop_user.target_instrumentalness,
    }
    for mode in SCORING_MODES:
        score, _ = score_song(prefs, asdict(pop_song), mode=mode)
        maximum = max_possible_score(mode)
        assert score <= maximum + 0.001, (
            f"Score {score:.4f} exceeded max {maximum:.4f} in mode '{mode}'"
        )


# ---------------------------------------------------------------------------
# 3. Diversity — re-ranking respects per-artist and per-genre caps
# ---------------------------------------------------------------------------

def test_diversity_enforces_artist_cap(pop_song, lofi_song, pop_user):
    """With diversity re-ranking, no artist should appear more than once."""
    same_artist = Song(
        id=4, title="Same Artist Again", artist="Artist A", genre="pop",
        mood="intense", energy=0.90, tempo_bpm=135, valence=0.65,
        danceability=0.85, acousticness=0.05, popularity=80,
        release_decade=2020, instrumentalness=0.05, liveness=0.09,
        speechiness=0.06,
    )
    prefs = {
        "genre": pop_user.favorite_genre,
        "mood": pop_user.favorite_mood,
        "energy": pop_user.target_energy,
        "acoustic": pop_user.likes_acoustic,
    }
    # Use the functional API — diversity_rerank operates on dicts
    songs_dicts = [asdict(s) for s in [pop_song, lofi_song, same_artist]]
    results = recommend_songs(prefs, songs_dicts, k=6, mode="balanced")
    # Cap at 2: we have 2 distinct artists, so the 2 accepted slots must differ
    reranked = diversity_rerank(results)[:2]

    artists = [s["artist"] for s, _, _ in reranked]
    for artist in set(artists):
        count = artists.count(artist)
        assert count <= 1, f"Artist '{artist}' appeared {count} times — cap violated"


def test_diversity_rerank_preserves_total_length():
    songs = [
        {"artist": "A", "genre": "pop", "title": "S1"},
        {"artist": "A", "genre": "pop", "title": "S2"},
        {"artist": "B", "genre": "pop", "title": "S3"},
        {"artist": "C", "genre": "rock", "title": "S4"},
    ]
    results = [(s, float(i), []) for i, s in enumerate(songs)]
    reranked = diversity_rerank(results)
    assert len(reranked) == len(results), "diversity_rerank must preserve total count"


def test_diversity_overflow_songs_appended_not_dropped():
    """Songs that exceed the cap must be appended to the end, not removed."""
    songs = [
        {"artist": "Same", "genre": "pop", "title": f"Song {i}"}
        for i in range(4)
    ]
    results = [(s, float(10 - i), []) for i, s in enumerate(songs)]
    reranked = diversity_rerank(results, max_per_artist=1)
    assert len(reranked) == 4


# ---------------------------------------------------------------------------
# 4. Mode behavior — weight emphasis produces expected relative changes
# ---------------------------------------------------------------------------

def test_genre_first_scores_genre_match_higher_than_balanced(pop_song):
    # pop_song matches genre but not mood; genre_first should score it higher
    prefs = {"genre": "pop", "mood": "chill", "energy": 0.5, "acoustic": False}
    score_balanced, _ = score_song(prefs, asdict(pop_song), mode="balanced")
    score_genre_first, _ = score_song(prefs, asdict(pop_song), mode="genre_first")
    assert score_genre_first > score_balanced, (
        "genre_first (genre weight 6.0) should outscore balanced (genre weight 3.0) "
        "when the song has a genre match"
    )


def test_energy_focused_scores_energy_match_higher_than_balanced(pop_song):
    # pop_song has energy 0.85; target 0.85 → perfect energy match
    prefs = {"genre": "lofi", "mood": "chill", "energy": 0.85, "acoustic": False}
    score_balanced, _ = score_song(prefs, asdict(pop_song), mode="balanced")
    score_energy, _ = score_song(prefs, asdict(pop_song), mode="energy_focused")
    assert score_energy > score_balanced, (
        "energy_focused (energy weight 5.0) should outscore balanced (energy weight 2.0) "
        "on a song with a perfect energy match"
    )


def test_all_modes_return_k_results(four_song_recommender, pop_user):
    for mode in SCORING_MODES:
        results = four_song_recommender.recommend(pop_user, k=3, mode=mode)
        assert len(results) == 3, f"Mode '{mode}' returned {len(results)} results, expected 3"


# ---------------------------------------------------------------------------
# 5. Regression — known profiles always produce known top songs
# ---------------------------------------------------------------------------

def test_pop_happy_profile_ranks_pop_happy_song_first(pop_song, lofi_song, pop_user):
    """A pop/happy user must always get the pop/happy song as their top pick."""
    rec = Recommender([pop_song, lofi_song])
    results = rec.recommend(pop_user, k=2)
    assert results[0].genre == "pop", "pop/happy user should get a pop song first"
    assert results[0].mood == "happy", "pop/happy user should get a happy song first"


def test_lofi_chill_profile_prefers_acoustic(lofi_song, pop_song):
    """An acoustic lofi user should score the acoustic lofi song higher."""
    lofi_user = UserProfile(
        favorite_genre="lofi", favorite_mood="chill",
        target_energy=0.40, likes_acoustic=True,
    )
    rec = Recommender([lofi_song, pop_song])
    results = rec.recommend(lofi_user, k=2)
    assert results[0].genre == "lofi", "acoustic lofi user should prefer the lofi song"


def test_explain_recommendation_is_non_empty(pop_song, pop_user):
    rec = Recommender([pop_song])
    explanation = rec.explain_recommendation(pop_user, pop_song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ---------------------------------------------------------------------------
# 6. Edge cases — single-song catalog, k > catalog, mismatched prefs
# ---------------------------------------------------------------------------

def test_single_song_catalog_returns_one_result(pop_song, pop_user):
    rec = Recommender([pop_song])
    results = rec.recommend(pop_user, k=1)
    assert len(results) == 1
    assert results[0].id == pop_song.id


def test_k_larger_than_catalog_returns_all_songs(pop_song, lofi_song, pop_user):
    rec = Recommender([pop_song, lofi_song])
    results = rec.recommend(pop_user, k=100)
    assert len(results) == 2


def test_mismatched_prefs_still_returns_results_without_crashing(lofi_song):
    """An unknown genre/mood should not crash — scoring falls back gracefully."""
    prefs = {
        "genre": "unknown_genre_xyz",
        "mood": "unknown_mood_xyz",
        "energy": 0.5,
        "acoustic": False,
    }
    results = recommend_songs(prefs, [asdict(lofi_song)], k=1)
    assert len(results) == 1
    score = results[0][1]
    assert score >= 0.0


def test_empty_catalog_returns_empty_list(pop_user):
    rec = Recommender([])
    results = rec.recommend(pop_user, k=5)
    assert results == []
