# WaveSort 1.0 — AI-Powered Music Recommender

A content-based music recommendation system extended with four applied AI features: Retrieval-Augmented Generation, an agentic self-correcting loop, a specialized domain-expert assistant, and a reliability test suite.

---

## Project Goals

- Build a working music recommender that scores songs against user preferences using weighted math
- Extend it with four AI techniques: RAG, agentic loop, LLM specialization, and reliability testing
- Keep the core engine deterministic and auditable — Claude handles only natural language tasks
- Prove the system works with automated tests, an evaluation harness, and confidence scoring

---

## What Was Added (New Features)

| Feature | File | Description | API Key? |
|---|---|---|---|
| RAG Pipeline | `src/rag.py` | Natural language query → scores catalog → Claude explains picks | Yes |
| Agentic Loop | `src/agent.py` | Auto-selects scoring mode, checks quality ≥ 0.55, retries if needed | No |
| Specialist Assistant | `src/music_assistant.py` | Claude with full catalog in system prompt, answers music questions | Yes |
| Reliability Tests | `tests/test_reliability.py` | 18 automated tests: determinism, bounds, diversity, edge cases | No |
| Eval Harness *(stretch)* | `scripts/run_eval.py` | 10-profile pass/fail table with confidence scores | No |
| RAG Enhancement *(stretch)* | `src/rag.py` + `data/genre_context.md` | Adds domain knowledge as a second retrieval source | Yes |
| Specialization Enhancement *(stretch)* | `src/music_assistant.py` | Few-shot examples enforce structured response format | Yes |
| Agentic Enhancement *(stretch)* | `src/agent_enhanced.py` | Claude drives tool-use loop with observable intermediate steps | Yes |

---

## Setup and Installation

### Prerequisites

- Python 3.9 or later
- An Anthropic API key — **required only for RAG, Agent Enhanced, and Specialist features**; the core recommender, tests, and eval harness run without one

### Step 1 — Clone the repository

```bash
git clone <your-repo-url>
cd applied-ai-system-final
```

### Step 2 — Create a virtual environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Add your API key (for AI features only)

```bash
# macOS / Linux
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows
set ANTHROPIC_API_KEY=sk-ant-...
```

---

## How to Run

### Run the core recommender

```bash
python -m src.main
```

To change the user profile, open [src/main.py](src/main.py) and set `ACTIVE_PROFILE` to one of:
- `"pop / happy"`
- `"lofi / chill"`
- `"classical / melancholic"`
- `"metal / aggressive"`

To change the scoring mode, set `CURRENT_MODE` to `"balanced"`, `"genre_first"`, `"mood_first"`, or `"energy_focused"`.

### Run the AI feature demos (requires API key)

In [src/main.py](src/main.py), set `DEMO_AI_FEATURES = True`, then run:

```bash
python -m src.main
```

This runs all four feature demos after the main recommendation table.

---

## How to Test

### Run the automated test suite

```bash
pytest tests/test_reliability.py -v
```

Expected output: **18 passed in ~0.03s** — no API key required.

### Run the evaluation harness

```bash
python scripts/run_eval.py                # balanced mode
python scripts/run_eval.py --mode genre_first
python scripts/run_eval.py --verbose      # show per-failure detail
```

Expected output: **10/10 passed, avg confidence 0.87** — no API key required.

---

## Sample Input and Output

### Example 1 — Core recommender (pop / happy profile, balanced mode)

**Input:**

```python
ACTIVE_PROFILE = "pop / happy"    # genre=pop, mood=happy, energy=0.80
CURRENT_MODE   = "balanced"
TOP_K          = 5
USE_DIVERSITY  = True
```

**Output:**

```
Loaded 18 songs from catalog.

  WaveSort 1.0  |  Profile: pop / happy  |  Mode: BALANCED  |  Diversity ON

╭───┬────────────────────┬─────────────┬───────────┬──────────────┬──────────────────────╮
│ # │ Title              │ Artist      │ Genre     │ Score        │ Why                  │
├───┼────────────────────┼─────────────┼───────────┼──────────────┼──────────────────────┤
│ 1 │ Sunrise City       │ The Dawners │ pop       │ 8.40/11.5    │ genre match; mood    │
│ 2 │ Rooftop Lights     │ Indie Glow  │ indie pop │ 6.21/11.5    │ mood match; energy   │
│ 3 │ Gym Hero           │ PowerBeats  │ pop       │ 6.08/11.5    │ genre match          │
│ 4 │ Island Echo        │ Tropic Wave │ reggae    │ 5.94/11.5    │ mood; energy fit     │
│ 5 │ Drop Zone          │ Bass Engine │ edm       │ 5.61/11.5    │ energy proximity     │
╰───┴────────────────────┴─────────────┴───────────┴──────────────┴──────────────────────╯
```

---

### Example 2 — RAG feature (natural language query → Claude explanation)

**Input:**

```python
from src.rag import rag_recommend

result = rag_recommend(
    query="upbeat songs for working out at the gym",
    catalog_path="data/songs.csv",
    k=3,
)
print(result)
```

**Output:**

```
Looking for high-energy tracks to power your gym session! Here are three
picks from the catalog that should keep you moving:

1. "Gym Hero" by PowerBeats — a pop track with an intense mood and energy
   of 0.93, practically built for pushing through a tough set.

2. "Drop Zone" by Bass Engine — euphoric EDM at 0.97 energy; the driving
   tempo makes it hard not to move faster.

3. "Storm Runner" by Thunder Road — rock with an aggressive mood and energy
   0.91; great for heavy lifts where you need the extra push.
```

---

### Example 3 — Specialist assistant (question → expert answer)

**Input:**

```python
from src.music_assistant import MusicAssistant

assistant = MusicAssistant("data/songs.csv")
print(assistant.ask("What is the best song for a late-night coding session?"))
```

**Output:**

```
For late-night coding, "Midnight Coding" by LoFi Lab is the clear pick.
It's a lofi track with a focused mood, energy 0.42, high acousticness
(0.85), and instrumentalness 0.80 — meaning almost no vocals to pull
your attention away. Its tempo is calm enough to settle into deep work
without feeling sleepy. "Library Rain" is a close second if you want
variety.
```

---

### Example 4 — Enhanced specialist (structured response format enforced)

**Input:**

```python
from src.music_assistant import MusicAssistantEnhanced

assistant = MusicAssistantEnhanced("data/songs.csv")
print(assistant.ask("Best song for a high-energy workout?"))
```

**Output:**

```
Top pick: Iron Curtain by Greywall (energy: 0.98)
Runner-up: Drop Zone by Circuit Fuse — euphoric EDM at 0.97, better for cardio than heavy lifts
Best for: heavy strength training where maximum intensity is needed
```

---

### Example 5 — Agentic enhancement (Claude drives tool-use loop)

**Input:**

```python
from src.recommender import load_songs
from src.agent_enhanced import ClaudeRecommendationAgent

songs = load_songs("data/songs.csv")
agent = ClaudeRecommendationAgent(songs)
result = agent.run({"genre": "lofi", "mood": "chill", "energy": 0.40, "acoustic": True}, k=3)
print(result["explanation"])
```

**Observable intermediate steps printed to console:**

```
[Tool Call]   check_catalog_coverage({"genre": "lofi"})
[Tool Result] {"genre": "lofi", "count": 3, "titles": ["Midnight Coding", "Library Rain",
               "Focus Flow"], "coverage": "good"}

[Tool Call]   score_and_rank({"prefs_dict": {"genre": "lofi", "mood": "chill",
               "energy": 0.4, "acoustic": true}, "mode": "balanced"})
[Tool Result] {"mode": "balanced", "genre_hit_rate": 1.0, "energy_fit": 0.952,
               "top_5": [{"title": "Midnight Coding", "confidence": 0.92}, ...]}

[Tool Call]   evaluate_quality({"genre_hit_rate": 1.0, "energy_fit": 0.952})
[Tool Result] {"quality": 0.976, "passes_threshold": true, "threshold": 0.55}
```

**Final explanation from Claude:**

```
The lofi catalog has excellent coverage with 3 songs available. Using balanced
mode, "Midnight Coding" leads with 0.92 confidence — a near-perfect match on
genre, chill mood, and low energy. Quality score of 0.976 comfortably exceeds
the 0.55 threshold. Strong recommendation set.
```

---

### Example 6 — Reliability tests

**Input:**

```bash
pytest tests/test_reliability.py -v
```

**Output:**

```
tests/test_reliability.py::test_scoring_is_deterministic                            PASSED
tests/test_reliability.py::test_recommend_order_is_deterministic                    PASSED
tests/test_reliability.py::test_all_modes_deterministic                             PASSED
tests/test_reliability.py::test_scores_are_non_negative                             PASSED
tests/test_reliability.py::test_score_does_not_exceed_mode_maximum                  PASSED
tests/test_reliability.py::test_diversity_enforces_artist_cap                       PASSED
tests/test_reliability.py::test_diversity_rerank_preserves_total_length             PASSED
tests/test_reliability.py::test_diversity_overflow_songs_appended_not_dropped       PASSED
tests/test_reliability.py::test_genre_first_scores_genre_match_higher_than_balanced PASSED
tests/test_reliability.py::test_energy_focused_scores_energy_match_higher_than_balanced PASSED
tests/test_reliability.py::test_all_modes_return_k_results                          PASSED
tests/test_reliability.py::test_pop_happy_profile_ranks_pop_happy_song_first        PASSED
tests/test_reliability.py::test_lofi_chill_profile_prefers_acoustic                 PASSED
tests/test_reliability.py::test_explain_recommendation_is_non_empty                 PASSED
tests/test_reliability.py::test_single_song_catalog_returns_one_result              PASSED
tests/test_reliability.py::test_k_larger_than_catalog_returns_all_songs             PASSED
tests/test_reliability.py::test_mismatched_prefs_still_returns_results_without_crashing PASSED
tests/test_reliability.py::test_empty_catalog_returns_empty_list                    PASSED

18 passed in 0.14s
```

---

### Example 7 — Evaluation harness

**Input:**

```bash
python scripts/run_eval.py
```

**Output:**

```
WaveSort 1.0 — Evaluation Harness  (mode: balanced)
Catalog: 18 songs   Cases: 10
-----------------------------------------------------------------------------
  CASE                       CONF    TOP RESULT                STATUS
-----------------------------------------------------------------------------
  pop / happy                0.83    Sunrise City (pop/happy)          ✓ PASS
  lofi / chill / acoustic    0.92    Midnight Coding (lofi/chill)      ✓ PASS
  rock / intense             0.84    Storm Runner (rock/intense)       ✓ PASS
  edm / euphoric             0.85    Drop Zone (edm/euphoric)          ✓ PASS
  classical / melancholic    0.88    Nocturne in Rain (classical/mel…  ✓ PASS
  metal / aggressive         0.83    Iron Curtain (metal/aggressive)   ✓ PASS
  jazz / relaxed             0.92    Coffee Shop Stories (jazz/relax…  ✓ PASS
  hip-hop / confident        0.84    Street Sage (hip-hop/confident)   ✓ PASS
  r&b / romantic             0.85    Slow Burn (r&b/romantic)          ✓ PASS
  folk / sad                 0.90    Empty Porch (folk/sad)            ✓ PASS
-----------------------------------------------------------------------------
Result: 10/10 passed   avg confidence: 0.87
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INPUTS                                   │
│  Natural language query │ User profile (genre/mood/energy) │ Question   │
└────────────┬────────────────────────┬───────────────────────┬───────────┘
             │                        │                       │
             ▼                        ▼                       ▼
┌────────────────────┐  ┌─────────────────────────┐  ┌───────────────────┐
│  Feature 1 — RAG   │  │  Feature 2 — Agent       │  │  Feature 3 —      │
│  rag.py            │  │  agent.py                │  │  Specialist       │
│                    │  │                          │  │  music_assistant  │
│ 1. Claude parses   │  │ Plan → choose mode       │  │                   │
│    query → prefs   │  │ Act  → core engine       │  │ Catalog embedded  │
│ 2. Core engine     │  │ Check→ quality score     │  │ in cached system  │
│    retrieves songs │  │ Adjust→ retry if < 0.55  │  │ prompt            │
│ 3. Claude explains │  │ Return→ final + trace    │  │ Claude answers as │
│    picks in NL     │  │                          │  │ WaveSort expert   │
└────────┬───────────┘  └───────────┬─────────────┘  └─────────┬─────────┘
         │                          │                           │
         └──────────────────────────┼───────────────────────────┘
                                    ▼
         ┌──────────────────────────────────────────────────────┐
         │           CORE ENGINE — recommender.py               │
         │  load_songs() → score_song() → recommend_songs()     │
         │                → diversity_rerank()                  │
         │                                                      │
         │  songs.csv (18 songs, 15 attributes)                 │
         └─────────────────────────┬────────────────────────────┘
                                   │
         ┌─────────────────────────▼────────────────────────────┐
         │         Feature 4 — Reliability Tests                │
         │         tests/test_reliability.py (18 tests)         │
         │                                                      │
         │  Determinism · Score bounds · Diversity              │
         │  Mode behavior · Regression · Edge cases             │
         └──────────────────────────────────────────────────────┘
```

The core engine is the single source of truth for all scoring. Every AI feature calls the same `recommend_songs()` function — no feature has its own scoring logic. Claude handles only natural language tasks.

---

## Design Decisions

### Why build on a deterministic core instead of using an LLM for everything?

The core scoring engine runs with no API calls, no latency, and no cost. Every result is fully explainable — you can see exactly which features contributed which points. Using an LLM as the retriever would have turned a debuggable process into a black box.

**Trade-off:** The scoring formula uses fixed hand-designed weights. A real system would learn weights from user behavior.

### Why use `ast.literal_eval()` for Claude's structured output?

In the RAG pipeline, Claude returns a Python dict literal as a string. Using `eval()` would be a security risk. `ast.literal_eval()` parses only literal structures (dicts, lists, strings, numbers) and raises a `ValueError` on anything else. A fallback default dict handles parsing failures gracefully.

### Why four scoring modes instead of one?

Different listening contexts have different priorities. A gym user wants energy match above all; a genre purist wants exact genre fidelity. The strategy pattern (`SCORING_MODES` dict) lets the system shift emphasis at runtime without rewriting scoring logic.

### Why use prompt caching on system prompts?

Both `MusicAssistant` and the RAG generation step use `cache_control: {"type": "ephemeral"}` on their system prompts. When the same system prompt is sent repeatedly, Anthropic's API reuses the cached prefix. The catalog-embedded system prompt is roughly 800 tokens; caching it reduces repeated-call costs by approximately 90%.

---

## Testing Summary

**18 out of 18 automated tests passed (0.03 s, zero API calls). 10 out of 10 eval harness cases passed (avg confidence 0.87). Human evaluation across 7 manually constructed profiles found 5 strong matches and 2 documented failure cases.**

### Automated tests — 18 / 18

| Category | Tests | What it checks |
|---|---|---|
| Determinism | 3 | Same input always produces the same ranked output |
| Score bounds | 2 | All scores are ≥ 0 and ≤ `max_possible_score(mode)` |
| Diversity | 3 | Per-artist cap enforced; overflow songs appended, not dropped |
| Mode behavior | 3 | `genre_first` > `balanced` on genre match; `energy_focused` > `balanced` on energy match |
| Regression | 3 | Known profiles always produce the same known top songs |
| Edge cases | 4 | Empty catalog, k > catalog size, unknown genre — all handled without crashing |

### Confidence scoring

Every recommendation includes a normalized confidence:

```
confidence = score / max_possible_score(mode)
```

Scores below 0.50 reliably predicted weak recommendations in human review. Both documented failure profiles scored 0.41 and 0.46 — the number warns you when to distrust the output.

### Human evaluation — 7 profiles

| Profile | Top song | Confidence | Feels right? |
|---|---|---|---|
| pop / happy | Sunrise City | 0.73 | Yes |
| lofi / chill / acoustic | Midnight Coding | 0.81 | Yes |
| rock / intense | Storm Runner | 0.74 | Yes |
| edm / euphoric | Drop Zone | 0.82 | Yes |
| classical / melancholic | Nocturne in Rain | 0.82 | Yes |
| ambient / sad / energy 0.90 (adversarial) | Spacewalk Thoughts | 0.41 | **No** — wrong energy |
| folk / uplifting / energy 0.95 (contradictory) | Empty Porch | 0.46 | **No** — mood mismatch |

**Root cause of failures:** a genre weight of 3.0 can beat combined energy + mood scores when a genre-matched song fails on everything else. Documented, reproducible, and traced to a single weight value.

### Known bug

`Recommender.recommend(diversity=True)` passes `Song` dataclass objects to `diversity_rerank()`, which expects plain dicts, causing `TypeError: 'Song' object is not subscriptable`. The functional API (`recommend_songs()` + `diversity_rerank()`) is unaffected. Tests use the functional API. Bug is documented rather than silently patched.

---

## Responsible AI

### Limitations and biases

**Genre-weight dominance.** A genre weight of 3.0 means a genre-matching song always earns 3 points before any other feature is evaluated. For contradictory profiles (ambient + high energy), genre wins even when the song fails every other dimension.

**Binary genre matching ignores relatedness.** "pop" and "indie pop" share zero scoring credit. The system cannot suggest adjacent genres.

**Catalog underrepresentation.** Seven genres have exactly one song. Any user requesting one of those genres always receives that one song regardless of fit. The system cannot distinguish "great match" from "only option."

**No global music representation.** The 18-song catalog covers only English-language Western genres. Latin, Afrobeats, K-pop, and other global genres are absent.

### Could this be misused?

**Filter-bubble amplification at scale.** Deployed to real users, the genre-weight system would steadily narrow recommendations for underrepresented genre communities. At scale, this quietly advantages some listeners based on catalog editorial choices.

**Prompt injection risk.** The RAG and specialist features send user queries to Claude. The current code partially mitigates this: `ast.literal_eval()` cannot execute arbitrary code; the system prompt constrains Claude to only reference retrieved songs. A production deployment would need input validation and rate limiting.

**Mitigations already built in:** confidence scores flag weak recommendations; diversity re-ranking prevents genre monopolies; reason strings make every decision auditable.

### What surprised me while testing

**`diversity_rerank()` appends, it does not truncate.** I expected a function enforcing artist caps to return a shorter list. It always returns the same length as its input, appending overflow songs to the end. My initial test sliced to the wrong index and produced a false failure; the code was correct and my assumption was wrong.

**Low confidence reliably predicts bad recommendations.** Every result below 0.50 corresponded to a recommendation that felt wrong; every result above 0.70 felt correct. The correlation was stronger than expected from a simple ratio.

### Collaboration with AI

**Helpful:** AI suggested `ast.literal_eval()` with a `try/except` fallback for parsing Claude's structured responses. This improved both security (no `eval()`) and resilience (pipeline never crashes on malformed output).

**Flawed:** AI-generated test code initially sliced reranked results to `[:3]` from a 3-song catalog, not realizing `diversity_rerank()` appends overflows rather than dropping them. The correct slice was `[:2]` (distinct artists). AI-generated test code still needs to be read and reasoned about, not just run.

---

## Reflection

**What building this project taught me about AI**

The most important realization was that "AI" in a production system is rarely one thing. This project has a pure-math scoring engine, a pattern-matching agent loop, a prompt-cached domain expert, and a RAG pipeline — and they serve different purposes. Learning to choose the right level of intelligence for each component changed how I think about system design.

Prompt caching was the biggest practical surprise. Discovering that a long system prompt can be cached across calls — reducing per-call cost by roughly 90% — reframed how I think about building assistants: investing in a rich, stable system prompt pays dividends at scale.

**What building this taught me about problem-solving**

The debugging process for the diversity test failure was a good reminder that "the tests are wrong" and "the code is wrong" are both live hypotheses when a test fails. The code was working exactly as designed; the test's assumption about it was the mistake. Testing does not just verify that things work — it makes failures reproducible and debuggable.

---

## Project Structure

```
applied-ai-system-final/
├── data/
│   ├── songs.csv               18-song catalog (15 attributes per song)
│   └── genre_context.md        Stretch 2: genre/mood knowledge base (second RAG source)
├── scripts/
│   └── run_eval.py             Stretch 1: evaluation harness (10 cases, pass/fail table)
├── src/
│   ├── recommender.py          Core engine: Song, UserProfile, scoring, ranking
│   ├── rag.py                  Feature 1 + Stretch 2: RAG + enhanced multi-source RAG
│   ├── agent.py                Feature 2: Deterministic self-correcting loop
│   ├── agent_enhanced.py       Stretch 4: Claude tool-use agentic loop
│   ├── music_assistant.py      Feature 3 + Stretch 3: Specialist + few-shot enhanced
│   └── main.py                 CLI entrypoint and display helpers
├── tests/
│   └── test_reliability.py     Feature 4: 18 reliability tests (all passing)
├── model_card.md               Bias analysis, evaluation, and limitations
├── reflection.md               Profile comparisons and behavioral analysis
└── requirements.txt            pandas, pytest, streamlit, tabulate, anthropic
```

---

## Requirements

```
pandas
pytest
streamlit
tabulate
anthropic
```

Install with `pip install -r requirements.txt`. The core recommender, tests, and eval harness have no Anthropic dependency — only the RAG, Agent Enhanced, and Specialist features require `ANTHROPIC_API_KEY`.
