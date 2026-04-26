# WaveSort Genre & Mood Knowledge Base

This document provides domain-level context about genres, moods, and listening use cases.
It is used as a second retrieval source to enrich RAG-generated explanations beyond raw
audio attributes.

---

## Genre Profiles

**lofi**
Characterised by deliberate low-fidelity production: vinyl crackle, tape saturation, subtle
background noise. Typical energy range: 0.30–0.50. Instrumentalness usually above 0.80,
meaning very few or no vocals. Tempo sits around 70–90 BPM — slow enough to fade into the
background. High acousticness (>0.70) is common. The genre was designed for sustained
attention tasks: studying, coding, reading. The muted imperfections signal "background" to
the brain and reduce auditory distraction.

**ambient**
Purely textural; energy almost always below 0.35. Instrumentalness near 1.0. No defined
melody in most tracks — focuses on atmosphere and space. Valence is typically neutral
(0.50–0.65). Good for: meditation, sleep, deep creative focus. Poor match for high-energy
activities or upbeat moods; the genre cannot deliver on energy targets above 0.60.

**pop**
Mainstream-oriented with strong melody, vocals, and hook structure. Energy range: 0.65–0.95.
Typically high popularity score (70+). Valence skews positive (0.70–0.90 for happy subgenre).
Short song structures (3–4 min) optimised for repeated listening. Broad appeal means it pairs
with many moods; the "happy" and "uplifting" moods are most naturally expressed here.

**indie pop**
Shares pop's melodic sensibility but with more production experimentation and lower commercial
polish. Energy slightly lower than pop (0.65–0.80). Moderate popularity (60–75). Often blends
acoustic and electronic elements; acousticness around 0.30–0.50. Good for: relaxed social
settings, morning routines, reflective listening.

**rock**
Guitar-driven with emphasis on rhythm and intensity. Energy typically 0.75–0.95. Live
recording probability is higher than most genres (liveness 0.20–0.35). Valence varies
widely by subgenre — intense/aggressive rock tends toward low valence (0.30–0.55). Best for:
workouts, commutes, tasks requiring sustained motivation.

**metal**
Extreme end of the rock family: maximum energy (0.95–1.0), aggressive mood, very low valence
(0.20–0.40), and fast tempos (150–180 BPM). Low acousticness, high liveness probability.
Niche genre in most catalogs; if a user requests metal, expect limited catalog coverage.
Best for: high-intensity exercise, channelling strong negative emotions productively.

**edm / electronic dance music**
Club-oriented with driving four-on-the-floor beats, synthesised timbres, and engineered
euphoria. Energy: 0.85–1.0. High danceability (0.85–0.95). Valence peaks at euphoric
subgenre (0.85–0.95). Instrumentalness often moderate (0.50–0.75) despite no traditional
vocals — vocal chops and samples are common. Best for: dancing, pre-event energy, high-BPM
workouts.

**synthwave**
Nostalgic 1980s electronic aesthetic: pulsing synths, arpeggios, cinematic scope. Energy:
0.60–0.80. Mood often moody or nostalgic rather than euphoric. Instrumentalness moderate to
high. Valence is darker than EDM (0.40–0.60). Best for: night driving, atmospheric gaming
sessions, focused creative work that benefits from steady rhythmic texture.

**jazz**
Acoustic-forward, improvisational, complex harmonic structure. Energy typically low (0.30–0.55).
High acousticness (0.75–0.95). Liveness probability elevated because live jazz recordings are
common. Valence is neutral to positive. Tempo varies widely (slow ballads at 60 BPM; uptempo
swing at 180 BPM). Best for: casual social settings, dinner background, relaxed focus work.

**classical**
Fully acoustic, fully instrumental. Instrumentalness near 1.0. Energy range enormous
(0.10 for solo piano nocturnes to 0.90 for full orchestral climaxes). The WaveSort catalog
skews toward quieter classical pieces (energy 0.15–0.30). Typical mood tags: melancholic,
romantic, focused. Best for: deep reading, emotional processing, sleep.

**hip-hop**
Beat-driven with significant vocal/rap presence (high speechiness: 0.20–0.40). Energy:
0.65–0.85. Valence varies by subgenre — confident/braggadocio hip-hop scores 0.65–0.80;
melancholic hip-hop can drop to 0.30. Danceability is consistently high. Best for: commuting,
energised daily tasks, social settings.

**r&b (rhythm and blues)**
Smooth vocal performances over warm, groove-oriented production. Energy: 0.45–0.70. High
valence in romantic subgenre (0.70–0.80). Moderate acousticness and low instrumentalness —
vocals are the focal point. Best for: romantic evenings, relaxed social settings, winding down
after high-energy activities.

**country**
Acoustic-forward storytelling genre. Energy: 0.40–0.65. High acousticness (0.60–0.80).
Vocals are central. Common moods: nostalgic, relaxed, uplifting. Liveness probability
moderate — country live recordings are widely released. Best for: road trips, relaxed outdoor
settings, nostalgic listening.

**reggae**
Syncopated rhythm with emphasis on the offbeat ("skank"). Energy: 0.50–0.70. Positive,
uplifting mood dominates. High valence (0.75–0.90). Moderate acousticness. Best for: relaxed
outdoor settings, social gatherings, warm-weather activities.

**folk**
Stripped-back acoustic production: guitar, voice, minimal instrumentation. High acousticness
(0.85–0.97). Low to moderate energy (0.20–0.50). Instrumentalness low (vocals are essential).
Liveness moderate (intimate live recordings are authentic to the genre). Mood often sad,
nostalgic, or reflective. Best for: quiet evenings, emotional processing, acoustic-first
listening environments.

---

## Mood × Use-Case Pairings

| Mood | Best for | Energy range | Avoid |
|---|---|---|---|
| happy | social gatherings, morning routines | 0.65–0.90 | metal, ambient |
| chill | studying, casual reading | 0.30–0.55 | edm, metal |
| focused | deep work, coding, writing | 0.30–0.55 | high-energy pop |
| intense | workouts, competitive gaming | 0.80–1.0 | classical, ambient |
| euphoric | dancing, celebrations | 0.85–1.0 | lofi, folk |
| melancholic | introspection, creative writing | 0.15–0.45 | edm, pop |
| romantic | intimate dinners, quiet evenings | 0.40–0.65 | metal, edm |
| aggressive | heavy lifting, extreme sports | 0.90–1.0 | lofi, classical |
| nostalgic | reminiscing, solo evenings | 0.35–0.60 | euphoric edm |
| relaxed | winding down, background listening | 0.25–0.55 | metal, intense rock |
| confident | commuting, task preparation | 0.65–0.85 | ambient, sad folk |
| uplifting | morning energy, outdoor activity | 0.60–0.80 | melancholic, sad |

---

## Energy × Activity Guide

- **0.00–0.30** — Sleep, meditation, passive relaxation
- **0.30–0.50** — Deep focus work (coding, reading, writing)
- **0.50–0.65** — Casual background, social settings, commuting
- **0.65–0.80** — Active daily tasks, light exercise, social energy
- **0.80–0.95** — Cardio workouts, high-focus sprints, dancing
- **0.95–1.00** — Heavy lifting, interval training, maximum intensity
