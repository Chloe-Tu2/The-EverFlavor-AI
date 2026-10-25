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

## Estimating missing times: measured

Measured on 2026-10-24 with a prototype script (not in the repo; no `src/` or notebook change). Fitted on the
Food.com train split (152,083 recipes with 1 to 1,440 minutes) and scored on val (32,369) and test (32,594).
Val and test agree within 1 point; the table shows test. "Half to double" means the estimate is between half
and twice the real time.

| Method | Median error | Within ±25% | Half to double | Coverage |
|---|---:|---:|---:|---:|
| Global median (38 min) | 20 min | 23.1% | 63.7% | 100% |
| (d) Plan baseline: steps x ingredient count | 15 min | 29.9% | 68.7% | 100% |
| (d') Ingredient count only | 17 min | 27.0% | 64.5% | 100% |
| (a1) Sum of times written in the steps | 18 min | 30.0% | 61.3% | 80.8% |
| (a2) Sum of the largest time per step | 18 min | 30.2% | 61.3% | 80.8% |
| (a3) (a2) times a ratio fitted on train | 11 min | 50.1% | 79.5% | 80.8% |
| (b) Median of the 80 most similar names (TF-IDF) | 15 min | 36.2% | 72.4% | 100% |
| (c1) Gradient boosting, steps + name neighbors | **8 min** | **52.6%** | **83.7%** | needs steps |
| (c2) Gradient boosting, name neighbors + ingredient count | 12 min | 36.3% | 73.7% | 100% |
| (c3) Ridge, same features as (c1) | 10 min | 41.1% | 78.5% | needs steps |
| (c4) (c1) without name neighbors | 8 min | 51.9% | 82.5% | needs steps |

What the runs show:

- Times written in the steps miss preparation, so the raw sum is worse than the baseline. Scaled by a fitted
  ratio (a3), they become the strongest single signal. 19.2% of Food.com recipes mention no time at all.
- Name neighbors (b) beat the baseline without needing steps. k = 5, 10, 20, 40 and 80 gave 69.0%, 70.8%,
  71.8%, 72.7% and 72.8% half to double on val. 94% of Food.com names have a neighbor with similarity 0.5 or more.
- With steps, the name neighbors add little (c1 83.7% vs c4 82.5%). Without steps, they are the main signal.
- Gradient boosting (on log minutes, absolute error) beats ridge. Its median estimate/real ratio is 1.00, so it
  is not biased up or down.

### Where it fails (val + test, half to double)

| Group | Recipes | Real median | (d) baseline | (b) names | (c1) steps | (c2) no steps |
|---|---:|---:|---:|---:|---:|---:|
| Slow cooker (steps or name) | 2,149 | 370 min | 8.2% | 44.3% | 87.2% | 60.6% |
| Marinate | 1,641 | 50 min | 58.3% | 61.1% | 63.5% | 60.0% |
| "Overnight" in the steps | 2,256 | 65 min | 53.0% | 53.1% | 61.7% | 54.0% |
| Bread with yeast | 925 | 110 min | 45.6% | 42.1% | 70.9% | 52.5% |
| Chill or freeze | 14,649 | 40 min | 60.2% | 60.1% | 66.7% | 60.5% |
| Real time over 4 hours | 3,043 | 380 min | 0.0% | 26.2% | 57.8% | 38.1% |
| Real time 10 min or less | 7,992 | 6 min | 38.5% | 26.5% | 59.8% | 40.4% |

- Food.com authors usually leave waiting out of the total. Recipes that say "overnight" have a median of 65
  minutes, so counting overnight as 8 hours is wrong 84% of the time.
- Slow cooker dishes are the clearest case: without steps, only the word in the name gives them away.
- Marinating, chilling and rising are counted or not counted by each author, so no method does well there.

### Other sources

- Hugging Face (37,823) and CulinaryDB (35,325) have no steps, so only (c2) applies. 90% and 87% of their names
  have a Food.com neighbor with similarity 0.5 or more (Food.com itself: 94%). Median estimate 33 and 38 min.
  These sources have no real times, so their accuracy is not measured; the Food.com number is the best guess.
- TheMealDB (583) has steps: 91.3% mention a time and (c1) can run. Its steps are paragraphs (median 6 per
  recipe, Food.com 9), so (c1) is used outside what it learned from. Its median estimate (44 min) is close to
  (c2) (43 min). Not measured either: there are no real times.
- Food.com recipes with 0 minutes (978) or over 24 hours (if kept) use (c1).

### Recommended estimate

Use gradient boosting on log minutes, with two feature sets: (c1) when a recipe has steps, (c2) when it has
only a name and ingredients. Expected accuracy (Food.com test): with steps 8 min median error, 83.7% within
half to double; without steps (most recipes that need it) 12 min, 73.7%. That is better than the plan baseline
(15 min, 68.7%), but only about one in three no-steps estimates is within ±25%.

- **Label:** "About 40 min, estimated from similar recipes" (rounded to 5 min under 1 hour, 15 min above).
  Over 4 hours, show "Several hours (estimate)" instead of a number: only 38% of those are within half to double.
- **Code:** `src/everflavor/cooking.py`, with `parse_step_minutes(text) -> list[float]` and
  `estimate_minutes(df, reference) -> pd.Series`, plus tests. The name neighbors come from Food.com train names
  only, so no recipe sees its own time.
- **Notebook 01:** fit on the train split; add `minutes_estimate` and `minutes_source` ("recipe" or
  "estimate") next to `minutes`. The neighbor search took about 6 minutes for train and 3 for the other sources.
- **Demo data:** copy `minutes_estimate` from the Hugging Face rows, so the app never needs Food.com to run.
- Keep the policy above: estimates are never used to sort or filter as if they were real (P26, team decision).
