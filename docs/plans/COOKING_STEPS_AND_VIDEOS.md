# Cooking Steps and Videos

How each recipe card shows its cooking time, its steps and a video. This is a plan; no code has changed yet.
It answers the "N/A minutes" bug in the [planner](README.md). Numbers come from `data/processed` and `data/demo`
as of 2026-10-24 (all splits).

## What the data has

The processed data has 291,755 recipes. Time, steps and links come from different sources.

| Source | Recipes | Minutes | Steps | Recipe link |
|---|---:|---:|---:|---:|
| Food.com (`foodcom`) | 218,024 | 100% | 100% | 0% |
| Hugging Face (`huggingface`) | 37,823 | 0% | 0% | 100% |
| CulinaryDB (`culinarydb`) | 35,325 | 0% | 0% | 0% |
| TheMealDB (`themealdb`) | 583 | 0% | 100% | 99.1% |
| **All** | **291,755** | **218,024 (74.7%)** | **218,607 (74.9%)** | **38,401 (13.2%)** |

Facts behind the table:

- Only Food.com has a time. It is one number, `minutes`, the total time. No source has active (hands-on) time
  apart from total time.
- `pipeline.py` already **drops** recipes over 24 hours (`MAX_MINUTES = 1440`), so the largest value left is 1,440.
- Food.com steps are text with one step per line (built from the Kaggle `steps` list in `pipeline.py`). They are
  lowercase with spaces before commas ("cut into half or fourths , remove seeds").
- TheMealDB steps are paragraphs split by `\r\n`; 26.9% of them have "step 1" lines as headings.
  86.8% of them mention a time in the text ("fry for 5 mins").
- Links: Hugging Face links point to the recipe's own site (Food Network 2,613, Food.com 2,565, Allrecipes 2,545,
  Food52 1,320 and more). TheMealDB links point to the source page.

### Why the app says "N/A minutes"

The app uses `data/demo` when the full data is missing. The 3,000 demo recipes are Hugging Face recipes
(2,967 of their links match Hugging Face rows). That source has no time and no steps, so the demo files have no
`minutes` and no `instructions` column. `stats()` in `app/app.py` then prints "N/A". Only 7 demo names match a
Food.com name, so times cannot be copied over from Food.com.

## 1. Time

### Food.com times

| Minutes | Recipes | Share of Food.com |
|---|---:|---:|
| 0 | 978 | 0.4% |
| 1 to 4 | 4,024 | 1.8% |
| 5 to 15 | 36,777 | 16.9% |
| 16 to 30 | 52,782 | 24.2% |
| 31 to 60 | 66,637 | 30.6% |
| 61 to 120 | 34,263 | 15.7% |
| 121 to 240 | 12,153 | 5.6% |
| 241 to 1,440 | 10,410 | 4.8% |

Median 38 minutes, middle half 20 to 65 minutes, 95th percentile 225 minutes.

### Cleaning rules

| Case | Rule | Shown as |
|---|---|---|
| 0 minutes (978) | Unknown, not instant | Estimate, or hidden |
| 1 to 4 minutes (4,024) | Keep (drinks, dips and no-cook dishes are real) | "3 min" |
| 5 minutes to 24 hours | Keep | "45 min", "1 h 30 min" |
| Over 24 hours | Today the pipeline drops the whole recipe. Proposed: keep the recipe, set the time to unknown | Estimate, or hidden |
| Missing | Estimate (below), labeled | "About 40 min (estimate)" |

Over 4 hours, add a short note: "includes waiting time (marinating, chilling or rising)", because Food.com gives
total time only.

### Estimated time when missing

The estimate is the median Food.com time for recipes with the same number of steps and ingredients. It is fitted
on the train split and checked on val and test (Food.com recipes with a known time).

| Estimate from | Within half to double of the real time | Median error |
|---|---:|---:|
| Steps count | 67.5% | 15 min |
| Ingredient count (`complexity`) | 65.2% | 18 min |
| Both | 68.6% | 15 min |

Median time by ingredient count (train): 2-4 ingredients 15 min, 5-7: 30 min, 8-10: 40 min, 11-14: 45 min,
15 or more: 60 min. Median by steps: 1-3 steps 10 min, 4-5: 25, 6-8: 35, 9-12: 40, 13-20: 50, 21 or more: 70.

The estimate is rough (one in three is off by more than double). So:

- Show it as a range word, not a precise number: "About 40 min (estimate)", rounded to 5 or 10 minutes.
- Never sort or filter by an estimated time as if it were real. Store it in its own column with `minutes_source`.
- The demo data and Hugging Face/CulinaryDB recipes have ingredients but no steps, so they use the
  ingredient-count estimate.
- Proposed policy (next free number, P26): "Estimated cooking times are shown, labeled as estimates"; or, if the
  team prefers, hide unknown times (the bug note's first idea). Who decides: the team.

### Active vs total time

Not possible from the data: no source has a separate active time. Show "Total time" only. A later idea: count the
time mentioned in steps ("bake 30 minutes") as cooking time, the rest as preparation. TheMealDB mentions times in
86.8% of its recipes, so this could also give TheMealDB a time. It needs a test set first.

## 2. Steps

### Parsing into numbered steps

| Source | Split on | Clean up | Steps (median, 95th pct, max) | Longest step (median, 95th pct) |
|---|---|---|---|---|
| Food.com | new lines | Capital first letter, " ," to ",", end with a full stop | 9, 21, 145 | 96, 172 characters |
| TheMealDB | `\r\n` | Drop "step N" heading lines; long paragraphs stay one step | 5, 16, 31 | 279, 594 characters |

1.1% of Food.com recipes and 3.9% of TheMealDB recipes have only one step. One Food.com recipe has empty
instructions. A shared function, for example `everflavor.cooking.split_steps(text) -> list[str]`, should do this
in `src/`, with tests, so the notebooks and the app use the same rules.

### How the card shows them

- A closed `st.expander("Cooking steps (9)")` under the ingredients. Inside, a numbered list.
- Show the first 25 steps (more than the 95th percentile of both sources). If there are more, add
  "Show all 145 steps" or a link to the source page.
- Cut a single step at 600 characters with "..." (about the TheMealDB 95th percentile).
- No steps (demo, Hugging Face, CulinaryDB): "Steps are on the recipe's page" with the source link when it exists;
  otherwise "No steps for this dish yet".
- Steps are shown as text (`st.markdown` with escaping), never as HTML from the data.
- Safety stays in the back end. The steps are only shown; the app does not rewrite them.

## 3. Videos

### Options

| | (a) YouTube search link | (b) YouTube Data API v3 | (c) Curated links |
|---|---|---|---|
| How | `https://www.youtube.com/results?search_query=` + recipe name + country + "recipe" | `search.list` for the top video, then show its title and link | The team picks a video per dish |
| Key needed | No | Yes, in `config/.env` or Colab Secrets, never committed | No |
| Limits | None | Default 100 `search.list` calls per day (its own bucket since the 2026 docs; older docs said 100 of 10,000 units per call, the same 100 searches) | Team time |
| Works in Colab and offline | Link always works; opens YouTube | Needs network and key; falls back to (a) | Yes |
| Quality | Viewer picks from YouTube's list | One video, may be the wrong dish | Best, but only a few dishes |
| Rules | None (a plain link) | 30-day cache limit, show "from YouTube", privacy policy linking Google's | Check each video's owner allows embedding |
| Cost to build | Hours | Days (key, cache, tests, policy page) | Ongoing |

YouTube API terms that matter (developer policies, checked 2026-10-24):

- Stored API data must be deleted or refreshed after 30 calendar days (III.E.4).
- Search results must say they come from YouTube and must not be changed (III.C.5, III.F.2).
- An app using the API must show a privacy policy that links to the Google Privacy Policy (III.A.2).
- The embedded player shares some user data with YouTube; autoplay sends it before the viewer acts (III.E.4.i).
- Made for Kids videos need tracking turned off (III.E.4.j).

TheMealDB's API also sends a `strYoutube` link per meal. `sources.py` keeps only `strSource` today. Keeping
`strYoutube` would give real, chosen videos for up to 583 recipes with no key (count it after the next download).

### Recommendation

1. **Now:** option (a), a "Watch on YouTube" link in the card, built from the recipe name and the country when it
   is known (78.9% of all recipes and 87.3% of Hugging Face recipes have a country). Plus TheMealDB's own
   `strYoutube` link where it exists.
2. **Later, optional:** option (b) behind a setting, off by default, only when a key is in `config/.env`. Cache
   results for at most 30 days in `data/user/` (never committed). Fall back to (a) on any error or when the quota
   is used up.
3. **Never autoplay.** The video opens only when the viewer clicks.
4. **Privacy:** links only for now. If embeds come later, use `https://www.youtube-nocookie.com/embed/<id>` and
   load the player only after a click. Log no searches in the audit log (it never records the user's words).
5. Add the YouTube note to `docs/ethics_privacy.md` when (b) or embeds are built.

## 4. Data work

| Step | Where | What |
|---|---|---|
| 1 | `src/everflavor/pipeline.py` | Keep recipes over 24 hours; set their time to unknown instead of dropping them (needs a policy note) |
| 2 | `src/everflavor/cooking.py` (or a new `steps.py`) | `split_steps()`, `estimate_minutes()` with tests in `tests/` |
| 3 | Notebook 01, section 5 (the cell that saves `data/processed/recipes_*.parquet`) | New columns: `steps` (list), `n_steps`, `minutes_clean`, `minutes_estimate`, `minutes_source` ("recipe", "estimate" or none), `video_url` (TheMealDB) |
| 4 | `src/everflavor/sources.py` | Keep `strYoutube` from TheMealDB |
| 5 | Demo data | Add `minutes_estimate` and `minutes_source = "estimate"` from ingredient count; steps stay on the source site (the demo has links for all 3,000) |
| 6 | `app/app.py` | Show "Total time", the estimate label, the steps expander and the video link; hide the time when none is known |
| 7 | Docs | `docs/data_dictionary.md`, `data/README.md`, the policy list, and the README numbers after the next full run |

The estimate table (median minutes per steps and ingredient bucket) is fitted in notebook 01 on the train split
only and saved with the data, so the app does not need Food.com to estimate. Notebook 01 runs for 30-45 minutes;
make the `src/` changes first, then run it cell by cell (no `src/` edits during the run).

The demo has no script in the repo that builds it. Building it again should be a small script or notebook cell
that takes the Hugging Face rows, adds the new columns and writes `data/demo/`, so it can be repeated.
