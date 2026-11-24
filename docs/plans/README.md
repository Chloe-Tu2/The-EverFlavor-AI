# Planner

**Start here** (team members and AI assistants picking up the work). What is done, what is in progress, what comes
next, grouped by version, with links to the plans behind each item. Update it whenever an item moves.

Last updated: 2026-11-19 (Claude, with med27-coder).

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
| 0.7.1 | **Ready to release** 2026-11-17: the 0.5.2 and 0.6.3 work and PRs #10 to #20 are on `main`; version, CHANGELOG, What's new and READMEs updated; the tag waits for med27-coder's go | `release/0.7.1` |
| 0.7.2 | Next: speed (scene files cached), `st.iframe` for the kitchen, a clearer profile button, UI clean-up, Check my recipe phases 2-3, an "Open in maps" button. Local branch `fix/0.7.2-repairs` (not pushed, 2026-11-17): scene files cached, profile button, Open in maps | |
| After 0.7.2 | **Order of work** (below): foundations first, then discovery | |
| 0.8.0 | **Planned** (below; decided by med27-coder, 2026-11-22): sign off the staged photos, cuisine and country image fallbacks, world culinary coverage as the headline metric, the 18 map cuisine tags, related dishes in Check my recipe; the real store locator | |
| 0.9.0 | **Planned** (below): chat with the chef (moved from 0.8.0 by med27-coder, 2026-11-22), the Africa sprint (38 ready dishes first), Walter's five questions | |
| 1.0.0 | Final presentation | |

The 0.6.0 items below that were not built stay planned; 0.6.0 is skipped as a number.

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

### Front end: the professional pass (done 2026-10-26, for 0.7.1)

From research on what makes AI-built pages look professional (Anthropic's frontend-design guidance, v0, Lovable,
WCAG 2.2, Nielsen Norman Group); the lessons are kept as a personal skill, `pro-ui-design`. Checked in the browser
at desktop and phone width.

| # | Change | Where |
|---|---|---|
| 1 | A safety summary above the results (what they were checked for, the calories, the filters) with Edit | `app/app.py` Find tab |
| 2 | "Checked for you" is each card's badge; the other names, "Posted as" and how to say it moved to the dish page | cards, `dish_page()` |
| 3 | A note when a changed choice clears the results, instead of results vanishing | Find tab |
| 4 | Check tab: one verdict panel, problems grouped by ingredient line, placeholders instead of a prefilled demo | Check tab |
| 5 | A contrast test for every theme (all pass WCAG AA); no faded text (captions at full strength) | `tests/test_app_contrast.py`, `app/themes.py` |
| 6 | The Map tab says "Houston" | tabs |
| 7 | The landing shows the tagline once, with three trust chips | `landing()` |
| 8 | No results: one-tap fixes for the filters and the search, and how many recipes each strict choice holds back (never a one-tap way to drop an allergy or a diet) | `recommend.what_blocks` |
| 9 | A three-question setup on the first visit (and from Edit), filling the sidebar's profile | `setup_profile()` |
| 10 | One spacing, type and shadow scale; button labels in the pixel font; pixel-style dialogs and filter pills | `style()` |
| 11 | Save recipes for the visit, with a download (nothing is stored) | Saved, top right |
| 12 | Filters (under 30 min, high protein), Sort by, and "Show 5 more" instead of "How many ideas?" | `baseline_recommend` |

Also: diet names say "-friendly" everywhere they are picked (`nice_diet`), and outside text in Markdown is escaped
without HTML codes, so "Mac & Cheese" shows as written (`plain()`).

### After the photo downloads (planned by med27-coder, 2026-10-27; nothing started)

Start once the photo rounds, the Openverse run and their review are committed. Plan only, no code yet.

| # | What | Why | Where |
|---|---|---|---|
| 1 | **Lag:** find where the app is slow (first load, search, switching tabs, the kitchen scene). Measured 2026-10-29 in Edge: every kitchen change re-sends the whole scene with its pictures inside the page (1.1-1.9 MB per click, 2-3 s); a plain click sends nothing. Fix idea: serve the scene files as static files the browser caches, so a change sends only the scene's name; then measure again, also on a phone. **Done 2026-11-17:** the scenes are served from `app/static/scenes/` (static serving on, copies made by the app, git-ignored) and fetched by the kitchen page, which fell from about 1 MB to 11 KB; the browser keeps each kitchen. Phone measurement still to do | The page feels slow, phones most | `app/app.py` (`scene_page`, `kitchen_scene`), `app/kitchen_scene.html` |
| 2 | **Terminal messages:** read what Streamlit prints while the app runs (warnings, deprecations, errors) and fix or explain each one. Found 2026-10-27: on every rerun Streamlit warns that `st.components.v1.html` (the kitchen scene, `kitchen_scene()`) is deprecated and to use `st.iframe` instead. Switch it, then test that the scene still reaches the page (the phone profile button, the hour, the lights) **Done** (`st.iframe` since 0.7.1) | A clean log; a later Streamlit may remove the old call, and the kitchen would vanish | the terminal output, `app/app.py` `kitchen_scene()` |
| 3 | **UI clean-up:** go through every screen, fix what is unclear or broken, and make labels and steps plain | Clearer for first-time users | `app/app.py`, `style()` |
| 4 | **Check my recipe:** improve the tab (clearer input, clearer verdict, what each problem means and what to swap, the same profile as Find recipes) | It is the second main use of the app | Check tab, `src/everflavor/safety.py` (results only shown, the back end still decides) |
| 5 | **Profile button more visible:** the button that opens the sidebar to edit allergies and diets gets colours that contrast with the background in every theme and time of day (light and dark kitchens), with a contrast test like the other theme colours. **Done 2026-11-17:** Streamlit's small open-sidebar arrow is now a "Your profile" button in the theme's button colour (the phone button too), tested in `test_app_contrast.py` | People must find where to enter their allergies: the app's core step | the open-profile button CSS, `app/themes.py`, `tests/test_app_contrast.py` |

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
| 5 | **A dish picture for recipes without a photo** (pixel art) and a **"cooking in progress" loading screen** | loading screen done (an egg frying, `make_loading.py`); dish picture done 2026-10-26 ("Cooking up a picture...", a cast-iron skillet with two spatulas, 64 px, `skillet_from_concept.py`; history in `design/pixel-art/archive/no-photo_2026-10-26/`) |

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

### Order of work after 0.7.2 (agreed by med27-coder, 2026-11-19)

Foundations first, so later features do not need rewrites. No new chefs, kitchen themes, waiter tones, settings
or profile options until step 6 is done; repairs are not features.

1. **Safety engine** (done, PR #22); its last known gap: allergen words in Spanish, French and Italian.
2. **Domain entities:** Dish, Recipe, Ingredient and Place (`src/everflavor/domain/`, step 1 built); next, the
   ingredient merges after the team's review. The waiter is a service that reads these, not a store of facts.
3. **Food Taxonomy graph:** dishes and recipes attached to the 150 taxonomy places. A new level (food zone, state,
   cuisine style) is added only where a published source draws it.
4. **Recipe page redesign** (with the 0.7.2 UI clean-up): the desktop space used for the story, origin, related
   dishes, where to buy and swaps; every swap goes through the profile check.
5. **Discovery:** safety, then taxonomy, preferences, novelty and variety.
6. **The map from a recipe:** ingredients to the kinds of shop nearby that usually stock them, with the confidence
   level (OpenStreetMap does not list a shop's stock).
7. **Chat with the waiter** (0.9.0 below), then **My Cookbook** collections and notes.

### Data and coverage work (asked by med27-coder, 2026-11-21; reports first, no app changes)

In order. Each makes a report and, where useful, an asset in `data/knowledge/`, with tests for any data change.
Nothing is invented: only our data, Wikidata and notebook 15.

1. Allergen words in Spanish, French and Italian (in progress; review sheet
   `docs/flag_review/allergen_words_es_fr_it.csv`, policy P26).
2. Recipe to dish linking: how many recipes the app's dish match finds, and where it fails.
3. Taxonomy coverage: which places, countries and regions have dishes, families and recipes.
4. The waiter's context: the graph's fixed lines for every dish, ready for the chat in 0.9.0.
5. Discovery paths, a recipe quality audit and the map's preparation data.
6. Coverage audit and expansion backlog, Europe first: country, culinary region and dish family gaps, the
   indigenous cuisines, and the rules every future dish must pass (source, licence, place, family or "unknown",
   provenance), with an approval step (ready, needs review, blocked). Nothing is published by it.
7. Quality sprint (done, PR #33): the dish completeness score, the image audit and the coverage reports.
8. Recipe to dish improvements (done 2026-11-22): rule L1, a dish named before a kind of dish is that dish's
   flavour ("peanut butter fudge" is Fudge); the review sheet `docs/audits/dish_link_review.csv` waits for the
   team. Every recipe is now a Food Graph node (`recipe_of`, `named_for` a food entry, else `recipe_from` its
   place).
9. Global Culinary Atlas audit (done 2026-11-22): the UN's regions from Unicode CLDR (Wikidata's links to them
   were too patchy), a score per continent and subregion, per-continent next-dish lists, missing versions and the
   review queue (`docs/audits/global_culinary_atlas.md`). The Balkans and Siberia wait for a published source
   that draws them.
10. Content quality sprint (done 2026-11-22): the approved image queue (1,739 photos pass the rules), the dish
    completeness projection (rich 505 to 654 once they are fetched) and the taxonomy validation. **Next, with
    the team's OK:** run the photo pipeline on the approved queue, check the photos by eye, then rerun the
    quality reports. (The OK was given 2026-11-22: the photos are fetched to a staging folder,
    `scripts/dish_photos/fetch_approved.py`; they reach the app only after the check by eye.)
11. Governance sprint (2026-11-22): secret scan in CI, PII audit, the policies in `docs/governance/`, `SECURITY.md`,
    `GOVERNANCE.md`, a README "At a glance". The open questions are in
    `docs/governance/needs_human_review.md`.

### 0.8.0 (re-planned 2026-11-22 by med27-coder): coverage, images and the store locator

Nothing built yet. Coverage replaces the dish count as the headline
([world_culinary_coverage.md](../audits/world_culinary_coverage.md): world 24.7%, Africa 6.9%).

| Feature | From | First step |
|---|---|---|
| Sign off the staged photos (203 dishes become rich) | [approved_photos_check.md](../audits/approved_photos_check.md) | a person reads the 72 passed contact sheets |
| Cuisine and country image fallbacks, labelled as such | the photo pipeline's licence and credit rules | a Commons fetch round, checked by a person |
| World culinary coverage in the README and the app | `scripts/knowledge/culinary_coverage.py` | confirm its counting rule (review item 21) |
| The 18 countries without a map cuisine tag | [map_validation_report.md](../audits/map_validation_report.md) | OpenStreetMap's wiki (Key:cuisine); only tags in use |
| Related dishes in Check my recipe, stored nowhere | `waiter.Knowledge.find`, the Food Graph | a small back-end function, then the panel |

#### Release gates (med27-coder, 2026-11-23): a version ships when its outcome is reached

A version answers "what can a person do now that they could not before?", not "which issues closed". It ships as
beta when every condition is met. GitHub milestones v0.8 to v2.0 track them; "person" means a team member must do
it (Claude cannot sign off for people). Numbers come from `data/knowledge/atlas/atlas_metrics.json`.

**Progress (2026-11-23):** 0.8 has 4 of 9 conditions met; 0.9 has 2 of 10. Most blockers are reviews by people.

**0.8.0 beta, Atlas Foundations.** Done when a person can browse countries, dishes, maps, photos and related foods
with confidence.

| Area | Condition | Who | State |
|---|---|---|---|
| Coverage | Coverage counting rule confirmed (review item 21), then world coverage shown in the app | person, then Claude | open |
| Coverage | README dashboard (with exact counts), metrics and sprint impact reports generated automatically | Claude | met |
| Images | Staged photos signed off (the 72 passed contact sheets), then linked: about 203 dishes become rich | person, then Claude | open |
| Images | Cuisine image fallbacks, checked by a person; no broken image path | Claude, then person | built: 96 pass the rules, waiting for a person (`data/knowledge/review/cuisine_images.csv`) |
| Discovery | Related dishes in Check my recipe | Claude | met (branch `release/0.8.0`) |
| Discovery | Map cuisine tags for every country OpenStreetMap has a word for (50+ uses) | Claude | met: 23 added; the other 88 have no such word yet |
| Discovery | The store locator works (ZIP search, details, directions) | Claude | met in Python (ZIP, distance, nearest list, card with map link); clustering, "search this area" and "use my location" wait for the MapLibre step |
| Reviews | Items 24, 28, 29 and 30 (moved dishes, country scores, sprint entries) answered | person | open |
| Release | CI green; the team tries `release/0.8.0` and approves | person | after the above |

**0.9.0 beta, Atlas Experience.** Done when a person can explore regions, traditions and food culture, not only
dishes.

| Area | Condition | Who | State |
|---|---|---|---|
| Knowledge | Walter's five questions, from the graph's fixed lines | Claude | open |
| Knowledge | Region pages generated for every region with a dish | Claude | met (30) |
| Knowledge | Region pages shown in the app; representative-dish rule accepted (item 27) | person, then Claude | open |
| Preservation | Indigenous tags reviewed by the rubric (item 26) before the app shows any | person | open |
| Enrichment | At least 100 reviewed dish facts (`data/knowledge/review/focus_review.csv`) | person | open (0) |
| Enrichment | Coverage, representation, enrichment and preservation metrics generated | Claude | met |
| Safety | Chat with the chef ([CHEF_CHAT.md](CHEF_CHAT.md)) with its red-team tests green; Walter says only sourced, reviewed facts | Claude, then person | open |
| Experience | Nice-to-have: the loading screen (issues #48 to #52) | Claude | open |
| Experience | Store locator polish, if not finished in 0.8 | Claude | open |
| Release | CI green; the team tries `release/0.9.0` and approves | person | after the above |

**1.0.0, Culinary Atlas.** Represent the world's culinary traditions, not only collect recipes. Targets, against
2026-11-23: world coverage at least 50% (60.4%, met), Africa at least 50% (41.0%), Oceania at least 35% (27.9%),
every country in the app with a dish, country and region pages complete, the Food Graph and dish families stable,
Walter's knowledge reviewed, no open critical review item, and the sprint checklist and release process in use.

**2.0.0, Community Layer.** Preserve living food culture: accounts, family recipes, sharing, stories, community
contributions and moderation. Only after 1.0.

**Atlas health, every sprint:** coverage, representation, enrichment and preservation should go up and
governance should not slip (open review items logged, none silently closed). The sprint impact report
(`docs/audits/sprints/`) shows all five.

### 0.9.0 (planned): chat with the chef, the Africa sprint, Walter's five questions

Chat with the chef moved here from 0.8.0 (med27-coder, 2026-11-22). The Africa sprint starts with the 38 ready
dishes in `data/knowledge/atlas/Africa_Next_500.json`; Walter's five questions are what a dish is, where it is
from, why it matters, similar dishes and its versions.

| Feature | Plan | In short | First steps |
|---|---|---|---|
| Chat with the chef | [CHEF_CHAT.md](CHEF_CHAT.md) | A bubble bottom-right; the chef answers by calling the project's own functions (find, check, substitutions, where to buy), never from its own judgment; every recipe re-checked by the safety gate; rules-only answers when the local AI is off; no chat history saved | `chat.py` with a rules router and red-team tests, then the bubble |
| Loading screen (asked by med27-coder, 2026-11-23; nice-to-have) | GitHub issues #48 to #52 (EF-901 to EF-905) | Only where the app really waits (the first data load, a slow page): a pixel-art chef, or Walter, stirring a comically large pot, in the kitchen's art style (no emojis); steam rises, the spoon bends, a vegetable jumps out. Its lines rotate ("Checking the atlas...", "Finding related dishes...") and can name what is loading ("Exploring Sichuan cuisine..."). A "Did you know?" line uses reviewed facts only, with their source | the art on a branch first (`design/`), then a `st.empty` placeholder around the first load in `app.py`; later a pot per region (a copper pot for the Middle East, a cauldron for the Nordic countries) |
| Store locator | [MAP.md](MAP.md), "Making it a real store locator" | A list beside the map, ZIP search from the Census table (no paid API), a details card with directions, "Where to buy" from a recipe; MapLibre later; Greater Houston coverage | back-end `map_places` and `zip_center`, then the wider data |

[CHEF_CHAT.md](CHEF_CHAT.md) lists open questions for the team at its end.

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
