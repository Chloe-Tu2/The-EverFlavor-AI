# Planner

**Start here** (team members and AI assistants picking up the work). What is done, what is in progress, what comes
next, grouped by version, with links to the plans behind each item. Update it whenever an item moves.

Last updated: 2026-10-22 (Claude, with med27-coder).

## How versions work

Semantic versions, beta below 1.0 (the full convention is at the top of [CHANGELOG.md](../../CHANGELOG.md)):

| Change | Version step | Example |
|---|---|---|
| Fixes, wording, small style changes | PATCH | 0.5.1 → 0.5.2 |
| A new feature, kitchen, notebook or data source | MINOR | 0.5.2 → 0.6.0 |
| The first finished release (final presentation), later a breaking change | MAJOR | 0.x → 1.0.0 |

How a version moves, as most teams do it:

1. **Plan:** the items for the next version are listed below (this planner is the "milestone").
2. **Branch:** the work happens on `release/<version>` (or one branch per feature, merged into it).
3. **Review:** the team tries the branch (`git checkout release/<version>`, `python -m streamlit run app/app.py`)
   and says what needs rework.
4. **Release:** `/release` (Claude Code) or the steps in `.claude/commands/release.md`: the version number,
   `CHANGELOG.md` and the app's What's new notes (`app/updates.py`) are updated together (a test checks they
   agree), merged into `main`, tagged `vX.Y.Z` and published as a GitHub Release.

## Status

| Version | State | Branch |
|---|---|---|
| 0.5.1 | **Released** 2026-10-22 (merged into `main`, tag `v0.5.1`) | `release/0.5.1` |
| 0.6.0 | **Planned** (below) | `release/0.6.0` |
| 0.7.1 | **Planned rename** of the 0.5.2 work (below) | `release/0.5.2` -> `release/0.7.1` |
| 1.0.0 | Final presentation | |

### 0.5.1 (released 2026-10-22)

The first numbered release: everything up to now. Details in [CHANGELOG.md](../../CHANGELOG.md).

- The EverFlavor Kitchen front end, the What's new bell, the concept sheet's layout.
- Cuisine kitchens (code-drawn drafts): Japanese, **Chinese**, Mediterranean, Mexican, Middle Eastern, **Moroccan**
  (the African family). Searching a cuisine family opens its kitchen.
- Recipe photo credits and the no-photo placeholder.
- Guards for keys and user data; `CLAUDE.md`.
- Kitchen art v5 (traced, lit, day and night; not in the app yet), the art archive and references, the data plan.

### Plan: the 0.5.2 work becomes 0.7.1 (decided by med27-coder, 2026-10-24; not done yet)

The work on `release/0.5.2` (living kitchens, chefs, search by country, dish names and the dish page) plus the
landing page, the Houston map and the dish information page are released together as **0.7.1**, since they add
several features (a MINOR step; 0.6.0 is skipped as a number, its planned items stay below). The team's sprites
come in through the team (med27-coder's teammates).

| Step | What | Where |
|---|---|---|
| 1 | Rename the branch `release/0.5.2` to `release/0.7.1` (GitHub keeps a redirect) | GitHub |
| 2 | Retitle the 0.5.2 and 0.5.3 sections below as 0.7.1 (the base kitchen stays a later item unless it is ready) | this planner |
| 3 | Build the landing page (option A, inside the app): **built** 2026-10-25 (`landing()` in `app/app.py`, `?start=1` skips it); wording still to sign off | [LANDING_PAGE.md](LANDING_PAGE.md) |
| 4 | Build the Houston map, after the team answers its questions; it opens from a third tab, **Map**, next to Find recipes and Check my recipe (with its own pixel icon, a map pin; planned for later) | [MAP.md](MAP.md) |
| 5 | Finish the dish information page: estimated times (notebook 01 rerun), pronunciation (a reviewed table of about 250 dishes: native name, respelling, a recording where one exists) | [COOKING_STEPS_AND_VIDEOS.md](COOKING_STEPS_AND_VIDEOS.md), [DISH_PRONUNCIATION.md](DISH_PRONUNCIATION.md) |
| 6 | README: a "Watch" section at the bottom for interested readers with the YouTube link to the team's cooking demo video (the team records it and sends the link) | `README.md` |
| 7 | README: bring the main README up to date (the app as it is now: kitchens and light, chefs, search, dish page, the data rule, the project tree) | `README.md` |
| 7b | Recipe photos: show each photo whole (not zoomed), keep the photos we have in the full data, hide logos and photos that are not the dish | [RECIPE_PHOTOS.md](RECIPE_PHOTOS.md) |
| 8 | Release: `__version__`, `CHANGELOG.md` (one 0.7.1 entry for all of it) and the What's new notes, all checks, merge into `main`, tag `v0.7.1` | `/release` |

Decided (med27-coder, 2026-10-25): the README links the team's cooking demo video; the American base kitchen
(0.5.3) is probably the version after 0.7.1, or in 0.7.1 if the sprites are ready; the map gets its own tab.

Open questions:

- **The README update** happens in the 0.7.1 release so `main` gets it with the code it describes (updating
  `main` alone first would describe features `main` does not have yet). A draft is ready:
  [README_0.7.1_draft.md](README_0.7.1_draft.md).

### Team checklist (2026-10-26): what needs a person

Everything below waits on a teammate, not on code. Tick an item when it is done.

- [ ] **Pronunciation:** check the 65 dishes in `data/reference/dish_pronunciation.csv` (only Claude has
  checked them). Mandarin tones first (10 dishes), then Japanese (7), Hindi (3), Arabic, Persian and Greek (1
  each). Put your name in `reviewed_by`. Rules in [DISH_PRONUNCIATION.md](DISH_PRONUNCIATION.md).
- [ ] **Photo check labels:** 126 of the 200 rows in `data/reference/photo_check_sample.csv` still need
  `matches_dish` (yes or no) and `checked_by`. Then `check_photos.py eval` re-tests the cutoff.
- [ ] **Dish photos:** spot-check the general dish photos in the app; add a row with `keep` = no to
  `data/reference/dish_photo_review.csv` for any that show the wrong dish (14 turned down so far).
- [ ] **Map:** answer the 8 open questions at the end of [MAP.md](MAP.md).
- [ ] **Landing page:** sign off the wording and answer the 7 open questions in [LANDING_PAGE.md](LANDING_PAGE.md).
- [ ] **"Cooking up a picture..." card:** look at it on a few recipes without a photo and say if it should change.
- [ ] **Send in:** chef sprites for more regions, the American base kitchen art (0.5.3), and the cooking demo video
  link (the README's "Watch" section).
- [ ] **README draft:** read [README_0.7.1_draft.md](README_0.7.1_draft.md) and mark what is wrong or missing.
- [ ] **Retrospective:** read the bugs-and-fixes retrospective (a shared doc from med27-coder) and add anything
  missed.

### Before the merge into `main` (planned 2026-10-26; nothing started)

The branch is 68 commits and about 600 files ahead of `main`, so it goes in four gates, in order. Each gate ends
with med27-coder's go before the next starts.

| Gate | What | How | Done when |
|---|---|---|---|
| 1. Code update | Finish the open work: the Food.com photos (download, logo marks, photo check), the team checklist items that change code, and anything the team's answers change | [RECIPE_PHOTOS.md](RECIPE_PHOTOS.md) steps; the checklist above | The app shows the new photos and nothing is half-built |
| 1b | Get ready to release: rename the branch to `release/0.7.1`; merge `main` into it if `main` moved; bump `__version__`, `CHANGELOG.md` and `app/updates.py` together; the README from the draft; retitle the 0.5.2 and 0.5.3 sections here | `/release` steps, `tests/test_version.py` | Version files agree; the README matches the app |
| 2. Code check | All CI checks; a code review of the whole branch against `main`, one area at a time (`src/everflavor`, `app`, `scripts`, `notebooks`, `design`); fix what it finds; click through the app end to end (landing, search, cards, dish page, Map) at desktop and phone widths | pytest, ruff, mypy, pymarkdown; `/code-review` (high); the Playwright browser | Checks green, review findings fixed or recorded, no broken screen |
| 3. Security check | A security review of the branch diff; a secrets sweep of every file and commit on the branch (not only what is staged): no keys, Kaggle token, `.env`, `data/user/`, `logs/`, `data/raw/`; every `unsafe_allow_html` escapes its text; outside links only to allowed hosts (Commons, OpenFreeMap, recipe sites); every new dataset's licence in `docs/sources.md` | `/security-review`; Claude Security scan of the changes; the commit hook's patterns over `git diff --name-only main...` and `git log -p main..` | No findings left open, or each one recorded with who decided |
| 4. Merge | A pull request `release/0.7.1` into `main` with a summary of the changes; CI green on the pull request; merge; tag `v0.7.1`; publish the GitHub release; mark 0.7.1 released here | GitHub (push via PowerShell) | `main` runs the new app and CI is green |

### Re-plan for the next session (2026-10-25): only what clearly improves the app

Picked from everything built and planned so far; in this order.

| # | Change | Why it matters | Effort |
|---|---|---|---|
| 1 | **Profile in the page on phones:** a "Your profile" panel above the search on small screens (the sidebar is hidden there; today the chef has to point at an arrow) | On a phone, people cannot see where to enter their allergies: the app's core step | Small |
| 2 | **Estimated cook times on the cards** (notebook 01 rerun with `cooking_time.py`, cell by cell) | 25% of recipes show no time; "About 40 min (estimated)" is right within half to double 84% of the time | Medium (a long run) |
| 3 | **Recipe photos:** connect the downloaded photos (`data/raw/recipe_photos/manifest.csv`) to the full data, hide logos and shared pictures, then the photo-matches-dish check | Photos make results easy to scan; wrong ones mislead | Medium |
| 4 | **"Why it's safe for you" on every card** (0.6.0 item 6): one line from the back end's check, e.g. "No peanuts or tree nuts; halal-friendly ingredients" | Trust: the user sees the check, not just a claim | Small to medium |
| 5 | **Results as a compact list first, details on tap** (name, country, time, calories; steps and video in "About this dish") | Cards are long now (steps, video, captions); five results fill several screens on a phone | Small |
| 6 | **Pronunciation for the top 50 dishes** after the team checks the draft table | Delight, low risk once reviewed | Small after review |
| 7 | **The Map tab** after the team's answers | A real new use (where to buy, where to eat) | Large |

Not worth doing now: moving the art scripts into a subfolder (churn), more chef lines (enough for now), a static
landing page (only when the app is hosted).

Done on 2026-10-25 before this re-plan: recipe photos shown whole (fitted, never cropped); the chef's welcome
points phone users to Your profile; All regions is the default search.

### 0.5.2 (in progress): the living kitchen

Branch `release/0.5.2`. The kitchens come alive first; the base kitchen follows in 0.5.3.

| # | Item | State |
|---|---|---|
| 1 | **v5 kitchens in the app**, in the visitor's time of day (morning, afternoon, evening, night) | in progress |
| 2 | **Interactive spots** (key ones, not everything): trees and plants shake and drop their own leaves (cherry blossom petals from the cherry tree, green leaves from others), lights switch on and off with their glow, stools and chairs wobble, some pots hop and steam; placed per kitchen so pieces that overlap still answer the right tap, by day and by night | in progress |
| 3 | **Regional chefs** in the foreground, from the team's four chef references (`design/pixel-art/references/chefs/`), a man and a woman cook per region, dressed after traditional cooks of that region; tap the chef to make them react | started: the four references are the Japanese, Chinese, Middle Eastern and default chefs (`make_chefs.py`); the woman cooks are drawn (`make_women_chefs.py`, one face per mood; Settings > Your chef). Other regions later |
| 4 | **Icons reworked** from the original set, to match the v5 art | planned |
| 5 | **A dish picture for recipes without a photo** (pixel art) and a **"cooking in progress" loading screen** | loading screen done (an egg frying, `make_loading.py`); dish picture done 2026-10-26 ("Cooking up a picture...", a spoon and a fork over a pan, `make_pixel_art.no_photo`) |

### 0.5.3 (planned): the base kitchen

| # | Item | State |
|---|---|---|
| 1 | **A fifth kitchen, American**, close to the original concept (the original kitchen), with the improved art and the same interactive spots | planned |
| 2 | It becomes the **base kitchen** people see when they first open the app | planned |

### 0.6.0 (planned)

Everything we are working on or have agreed to do next, in one place. Owners are filled in when someone takes an item.

| # | Item | Plan | Owner | State |
|---|---|---|---|---|
| 1 | **The team's own art** in the detailed concept style: kitchens and chefs dropped into `design/pixel-art/originals/`, objects mapped so they still move when tapped | [originals/README.md](../../design/pixel-art/originals/README.md) | team (art), Claude (mapping) | waiting for the pictures |
| 2 | **Regional kitchens:** art briefs for all regions; next kitchens Indian and Italian (most recipes) | [REGIONAL_KITCHENS.md](REGIONAL_KITCHENS.md) | | planned |
| 3 | **Kitchen by country, not only by family:** an Indian dish should open the Indian kitchen, not the Chinese one | [REGIONAL_KITCHENS.md](REGIONAL_KITCHENS.md#choosing-the-kitchen) | | planned |
| 4 | **Photo checks:** report-a-wrong-photo button, automatic image-text check, broken-link check | [RELIABILITY.md](RELIABILITY.md#2-recipe-photos) | | planned |
| 5 | **Fewer hallucinations** in the AI's explanations and the meal planner (grounding, more evaluation questions) | [RELIABILITY.md](RELIABILITY.md#1-hallucinations) | | planned |
| 6 | **UI round 2:** profile chips and the chef's three-question onboarding, "Why it's safe for you" on every card, Today's safe picks, faster first load, "How we check" page | [design/PLAN.md](../../design/PLAN.md#next-round-060) | | planned |
| 7 | **Local AI on this PC's NPU** (Foundry Local): time qwen2.5-7b and qwen3-4b against llama3.2 on notebook 09's questions; add as an option in `llm.py` if faster and as safe | [RELIABILITY.md](RELIABILITY.md#3-the-ai-models) | Claude | models downloaded |
| 8 | **Back-end fixes from the team's merge:** the inverted "vegan" line in `passes_safety_filter` (dead code today) and the dropped diet pre-filter (fewer results for halal and kosher searches) | [RELIABILITY.md](RELIABILITY.md#4-known-code-issues) | | to do |
| 9 | **README numbers:** the freshness models' final test results (fish 87.4%, produce 98.8%) in the main README | `notebooks/05` | | to do |
| 10 | **Freshness per-source check:** Fish Eyes FFE photos score 0.76 against 0.97 for the other fish source | [RELIABILITY.md](RELIABILITY.md#3-the-ai-models) | | planned |
| 11 | **Housekeeping:** move the Foundry agent folder (`my-agent-n6agvd/`) out of the repository folder | | med27-coder | to do |
| 12 | **Kitchen art v5, day and night:** each traced kitchen in morning, day, evening and night light (sky in the windows recolored, lanterns lit at night, the room's light shifted), picked by the visitor's clock or the theme. Lamps are off by day (morning, afternoon) and lit at evening and night. Drafts made with `design/pixel-art/day_night.py`; next: show them in the app | [archive/README.md](../../design/pixel-art/archive/README.md) | Claude | in progress |
| 13 | **More data for the models:** what each model is short of, candidate datasets with licenses, download order | [DATA_AND_MODELS.md](DATA_AND_MODELS.md) | | planned |
| 14 | **Kitchen art v6 (later):** a team concept sheet per kitchen (room, chefs, title sign, props), started with the colorful Saffron Market | [future-works/v6/](../../design/pixel-art/future-works/v6/README.md) | team (sheets), Claude | set aside |
| 15 | **Cuisines by country:** a Country list (53 countries with 50+ recipes) that opens the region's kitchen, and fixes to the country labels (state regions such as Louisiana kept; Taiwanese, Israeli, Persian labels) | [CUISINE_REGIONS.md](CUISINE_REGIONS.md) | Claude | Country list and label fixes done; next: notebook 01 rerun, the model kept inside each broad area (Caribbean and South American recipes are pushed into Mexico today), a hand-checked sample |
| 18 | **Dish names:** the dish's own name from posted titles ("Kittencal's Famous Lasagna" -> "Lasagna") on every card, the posted title underneath | [DISH_NAMES.md](DISH_NAMES.md) | Claude | done in the app; notebook 01 columns next |
| 16 | **Cook time, steps and YouTube links** on each recipe card (Food.com has them; the demo data does not) | [COOKING_STEPS_AND_VIDEOS.md](COOKING_STEPS_AND_VIDEOS.md) | | planned |
| 17 | **Houston map:** where to buy a recipe's ingredients and where to eat it, MapLibre with free OpenFreeMap tiles, local only | [MAP.md](MAP.md) | | planned; 8 questions for the team |

### Follow-up for the next session (2026-10-22)

1. **Bug report** (`EverFlavor_AI_Kitchen_Bug_Report.pdf`, the live demo site): four bugs analysed, fixes proposed,
   waiting for the team's choice. Same recipes every time (sorting by calorie distance only: add variety, memory of
   shown recipes, rename "Other"); wrong cuisines (the demo data's own site tags: run it through notebook 01's
   country logic, drop conflicts, show the country); Food Network logo photos (find shared pictures by fingerprint);
   "N/A minutes" (the demo data has no time column: hide unknown times, bring times from the full data).
2. **Kitchen art v5 (released in 0.5.1):** the team's four kitchens traced object by object
   (`design/pixel-art/trace_kitchens.py`, `drafts/traced-kitchens/<name>/`), lit, and in four hours
   (`day_night.py`). Earlier versions and the build steps are in `design/pixel-art/archive/`. Still open: 14 small
   objects lost their mask and stay in the backdrop (Mexican spoons, flowers, tap; Mediterranean jug, plates, barrel).

### Handoff for 0.5.2 (2026-10-22, branch `release/0.5.2`)

Where the living kitchen stands, for whoever picks it up next:

- **Done:** the v5 kitchens are the app's Chinese, Mediterranean, Mexican and Middle Eastern themes
  (`app/app.py` THEMES, `scene: v5_<name>`). `design/pixel-art/build_scenes.py` writes `assets/scene_v5_<name>.json`
  (four hours; per light, the pixels it changes on the room and on each piece) and `assets/kitchen_v5_<name>.png`
  (the still picture under it). `app/kitchen_scene.html` picks the hour from the visitor's clock (5-11 morning,
  11-17 afternoon, 17-20 evening, otherwise night) and makes the key pieces answer a tap by their own pixels:
  lanterns and candles switch on and off, plants and the trees seen through windows shake and drop their own
  leaves or petals (petals stay inside the window), stools rock, woks, pots and the tea set steam, pans swing.
  Which piece does what comes from its name (`KINDS` in `build_scenes.py`).
- **Lights off by day:** `day_night.lamps_off` darkens the lanterns' glass (Chinese paper lanterns turn matte red)
  and takes out the glow the team's art paints on the wall around each lantern (`paint_out_halos`). The lights-off
  picture has its own palette, so its colors are not pulled toward the lit ones.
- **After changing the art or `day_night.py`:** run `python design/pixel-art/day_night.py`, then
  `python design/pixel-art/build_scenes.py` (a few minutes; scene files are 0.8 to 1.4 MB each).
- **Testing:** check it in a real browser. The scene can be tried on its own by filling `__SCENE__` in
  `kitchen_scene.html` with a scene file and fixing the hour (`new Date().getHours()`).
- **Next, in order:** regional chefs in the foreground, a man and a woman cook per region, from the team's
  references in `design/pixel-art/references/chefs/` and photos of traditional cooks of each region (licenses
  recorded like `references/lanterns/README.md`), tappable; icons reworked to match the v5 art; a pixel-art dish for
  recipes without a photo and a "cooking in progress" loading screen. Then 0.5.3: the American base kitchen.
- **Open:** the title layout on the kitchens' sign (the test is archived, `archive/title-test_2026-10-22/`; Claude's
  pick is layout 4); the app still shows the title as before. The planner's version rule says new features are a
  MINOR step; the team chose to number this work 0.5.2 and 0.5.3.

### Later (1.0 and after)

Hosting and a landing page; My cookbook and sharing; the chef chat tab (`llm.ask_agent`); the meal planner in the
app (`crew.plan_meal`); achievements; animated kitchens (steam, the chef blinking); a phone-first redesign. See
[design/PLAN.md](../../design/PLAN.md) for the reasons and order.

## Handoff notes (for whoever picks this up)

- Read [CLAUDE.md](../../CLAUDE.md) first: the rules that must not be broken (keys, user data, safety decisions in the
  back end, flags only add cautions).
- Run every check before a push (CLAUDE.md lists them; CI runs the same).
- Front-end work: check it in a real browser, not only with Streamlit's test runner; Streamlit 1.65 changed several
  element names (tabs, cards, tags), and CSS that targets the old names silently does nothing.
- Pixel art: the v5 kitchens are traced from the team's art (`trace_kitchens.py`, `day_night.py`,
  `build_scenes.py`); the other themes are drawn in code (`make_pixel_art.py`, `cuisine_kitchens.py`). The team's
  own pictures in `originals/` take priority. Archive a picture before replacing it (`design/pixel-art/archive/`).
- Data and AI: [RELIABILITY.md](RELIABILITY.md) lists what can go wrong and what each fix costs.
