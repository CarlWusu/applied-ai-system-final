# Model Card: VibeFinder 1.0

---

## 1. Model Name

**VibeFinder 1.0** — a content-based music recommender simulation.

---

## 2. Intended Use

VibeFinder suggests songs from a small catalog based on a user's stated musical preferences. It is designed for classroom exploration, not for real users. It assumes the user can describe what they want in four simple values: a preferred genre, a preferred mood, a target energy level (0.0 = calm, 1.0 = intense), and whether they like acoustic-sounding music. The model makes no use of listening history, other users' behavior, or any data the user has not explicitly provided.

---

## 3. How the Model Works

Think of VibeFinder as a judge at a talent show with a scoring rubric. Every song in the catalog walks onstage and gets rated against the same four questions:

1. **Is this song in the right genre?** If yes, award 3 points. If no, 0.
2. **Does this song have the right mood?** If yes, award 2 points. If no, 0.
3. **How close is this song's energy to what the listener wants?** Award up to 2 points — a perfect match earns the full 2, a song at the opposite end of the energy scale earns 0, and anything in between gets a fraction.
4. **How positive does this song feel emotionally?** Award up to 1.5 points using the same closeness math as energy.
5. **Does this song sound acoustic, and does the listener prefer that?** If both are true, award a bonus 1 point.

After all songs are scored, they are sorted from highest to lowest. The top results are shown with the exact reasons they ranked where they did. The maximum possible score is 9.5.

---

## 4. Data

The catalog contains **18 songs** across **11 genres** and **14 moods**, loaded from `data/songs.csv`.

**Genres:** pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, classical, r&b, edm, country, reggae, metal, folk

**Moods:** happy, chill, intense, relaxed, focused, moody, confident, melancholic, romantic, euphoric, nostalgic, uplifting, aggressive, sad

Each song has 7 numeric or categorical features: genre, mood, energy, tempo\_bpm, valence, danceability, acousticness. Tempo and danceability are loaded but not used in the current scoring formula.

**What the data reflects:** The catalog skews toward English-language Western genres. Latin, Afrobeats, K-pop, and other global genres are absent. Within each genre, there are only 1–3 songs, which severely limits the variety of recommendations a user can receive.

Eight songs (IDs 11–18) were manually added to expand genre and mood coverage beyond the original 10-song starter file.

---

## 5. Strengths

- **Well-served profiles:** Users with preferences matching the most-represented genres (lofi, pop) receive consistently good recommendations. A "lofi / chill" user gets Midnight Coding and Library Rain at the top — both feel intuitively correct.
- **Transparent scoring:** Every recommendation shows the exact features and points that drove it, so the user always knows *why* a song appeared. This is a real advantage over black-box systems.
- **Graceful degradation for unknown genres:** When a user asks for a genre not in the catalog (e.g., blues), the system does not crash or return nothing. It falls back to mood + energy + acoustic matching and still finds sensible results — lofi and ambient chill tracks for a blues listener who wants calm acoustic music.
- **Conflicting profiles get partially useful results:** Even for contradictory inputs (high energy + ambient genre), the scoring produces a ranked list, and the reasons show clearly why each song appeared.

---

## 6. Limitations and Bias

**1. Genre over-dominance creates filter bubbles.**
The genre weight (3.0) is so strong that a genre-matching song can beat a much better-fitting song on every other dimension. In testing, an "ambient + sad mood + high energy 0.90" profile ranked *Spacewalk Thoughts* (ambient, energy 0.28) first — despite its energy being 0.62 away from the target — simply because no other ambient song exists in the catalog. A high-energy metal song with far better feature alignment ranked lower. When genre weight was halved (to 1.5) and energy weight doubled (to 4.0), the conflicting profile correctly surfaced high-energy songs instead. The current weights prioritize genre loyalty over all-around fit.

**2. Binary genre matching ignores related genres.**
"pop" and "indie pop" are treated as completely different genres (0 shared points). A pop fan receives no credit for indie pop songs even though the genres overlap substantially. The same applies to "r&b" vs "soul", or "lofi" vs "ambient". Real recommenders use genre embeddings or hierarchical genre trees so that adjacent genres share partial credit.

**3. One song per genre means no within-genre diversity.**
Several genres — folk, metal, classical, reggae, r&b, country, edm — have exactly one song in the catalog. Any user who specifies one of these genres will always see that single song at #1, regardless of whether the other features match. This is not a scoring logic problem; it is a data scarcity problem.

**4. Energy proximity alone cannot distinguish emotional intensity.**
A user asking for "folk + high energy" gets *Empty Porch* (folk, sad, energy 0.25) at the top because it is the only folk song and earns the genre + acoustic bonus. No high-energy folk song exists to recommend. The system cannot distinguish "I want upbeat folk" from "I want folk at all."

**5. Acoustic preference is a binary opt-in, not a spectrum.**
Users who do not explicitly set `acoustic: True` are never rewarded for acoustic songs, even if they would enjoy them. There is no "slightly prefers acoustic" option — it is all-or-nothing.

---

## 7. Evaluation

**Profiles tested and what they revealed:**

| Profile | Top Result | Score | Observation |
|---|---|---|---|
| pop / happy / energy 0.80 | Sunrise City | 8.40 | Perfect match on all four dimensions — intuition confirmed |
| lofi / chill / energy 0.40 / acoustic | Midnight Coding (tie) | 9.37 | Two songs tied; system correctly surfaces all three lofi tracks in top 3 |
| rock / intense / energy 0.91 | Storm Runner | 8.50 | Correct genre/mood match; but Gym Hero (pop/intense) ranks #2 via mood alone — cross-genre mood matching |
| ambient / sad / energy 0.90 (adversarial) | Spacewalk Thoughts | 4.71 | **Bug found:** genre wins despite 0.62 energy gap; high-energy songs ranked far below |
| blues / chill (unknown genre) | Midnight Coding | 6.37 | Graceful degradation — mood+energy+acoustic steer correctly without genre match |
| reggae / happy (1-song genre) | Island Echo | 6.14 | Works but only by 0.68 margin over Rooftop Lights |
| folk / uplifting / energy 0.95 (contradictory) | Empty Porch | 5.25 | Folk wins on genre+acoustic even though its energy (0.25) is opposite of target |

**Weight-shift experiment — doubling energy weight (2→4) and halving genre weight (3→1.5):**

- Pop/happy profile: Sunrise City still #1. Night Drive Loop (synthwave) appears in top 5 via energy similarity alone — arguably a false positive.
- Rock/intense profile: Storm Runner still #1. Iron Curtain (metal) rises from #4 to #3. Drop Zone (EDM, high energy) enters the top 5 — questionable for a rock fan.
- Conflicting profile (ambient + sad + energy 0.90): **Most revealing.** With original weights, Spacewalk Thoughts won via genre despite being low-energy. With doubled energy weights, Storm Runner and Iron Curtain correctly rise to #1 and #2 based on energy proximity. The genre signal was overriding what the user actually wanted.

**Conclusion from experiment:** The original genre weight is too strong for users with conflicting or edge-case profiles. A weight of 3.0 makes genre nearly deterministic for any user whose genre appears in the catalog, regardless of how poorly the song matches on other dimensions. A weight around 2.0–2.5 would allow high-performing cross-genre matches to compete while still rewarding genre affinity.

---

## 8. Intended Use and Non-Intended Use

**This system IS intended for:**
- Classroom exploration of how content-based recommendation logic works
- Learning how feature weights, proximity scoring, and ranking interact
- Understanding why real-world systems behave the way they do (e.g., why Spotify Discover Weekly feels genre-locked)
- Prototyping and testing new scoring ideas quickly on a small, readable dataset

**This system is NOT intended for:**
- Recommending music to real users — the catalog is too small (18 songs) and the scoring is too simple to reflect actual taste
- Any production or commercial environment
- Representing the preferences of any specific real person or demographic
- Making decisions about which artists or songs get promoted — the catalog biases toward certain genres by design
- Replacing human editorial judgment about what music fits a mood or context

---

## 9. Future Work

- **Fuzzy genre matching:** Use a genre similarity table (e.g., pop–indie pop score 0.6, rock–metal score 0.5) instead of binary matching. This would prevent the "pop user gets 0 credit for indie pop" problem.
- **Paired feature modeling:** Treat genre+mood as a joint signal rather than two independent checks. "Rock + intense" should reward songs differently than "rock + chill" — right now both earn the same 3.0 for genre match.
- **Expand the catalog:** 18 songs means 1–3 songs per genre. A real simulation needs 50–100 songs per genre to give the ranking rule meaningful differentiation to work with.
- **Soft acoustic scoring:** Replace the binary acoustic bonus with a continuous score based on how close `song.acousticness` is to a user-declared preferred acousticness level.
- **Diversity constraint:** Add a rule that prevents any single genre from occupying more than 2 of the top-5 slots. This would force variety in the lofi profile (which currently gets 3 lofi songs in the top 3).
- **Session context:** Use time of day or activity as an additional filter layer — same user, same genre preferences, but "3 AM" should produce different energy recommendations than "9 AM workout."

---

## 10. Personal Reflection

**Biggest learning moment:**
The most important thing I learned is that a recommender system is not one algorithm — it is two separate ideas that must both work. The scoring rule answers "how good is this one song for this user?" The ranking rule answers "which songs should I show?" You need both. Before building this, I thought recommendation was about finding "the best song." After building it, I understand it is about *comparing every song against the same standard* and then sorting. That reframing changed how I think about every AI decision system.

**How AI tools helped, and when I needed to double-check them:**
AI-assisted design helped most during the planning phase — thinking through weight rationale, proximity scoring formulas, and what adversarial profiles might expose. It was less reliable when generating specific numeric recommendations. For example, early suggestions for weight values didn't account for the fact that genre at 3.0 could dominate across the entire 0–9.5 range. The weight-shift experiment, which I ran myself, revealed that clearly. The general principle (use proximity scoring for continuous features) was solid; the specific tuning required testing against real outputs. The rule I developed: accept AI-suggested frameworks, verify them with actual data.

**What surprised me about how a simple algorithm can still "feel" like recommendations:**
The scoring formula has no understanding of music whatsoever. It cannot hear a song. It does not know that "intense rock" and "aggressive metal" are related. It just adds up numbers. And yet, for a well-represented profile like "lofi / chill / acoustic," the results feel eerily accurate — *Midnight Coding* and *Library Rain* at the top feel like exactly what a late-night study session needs. That surprised me. The "feeling" does not come from intelligence in the algorithm; it comes from the algorithm consistently applying the user's own stated preferences back to them. It is a mirror, not a mind.

**What I would try next:**
The most interesting next step would be to replace binary genre matching with a genre similarity matrix — so that "pop" gives partial credit to "indie pop", "rock" gives partial credit to "metal", and "lofi" gives partial credit to "ambient." That single change would fix the cross-genre bleed problem (Gym Hero ranking #2 for a rock user via mood alone) and reduce the dominance of exact genre matches. After that, I would expand the catalog to 5–10 songs per genre so that within-genre ranking becomes meaningful rather than a single-song default.
