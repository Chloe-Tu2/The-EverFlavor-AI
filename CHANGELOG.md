# Changelog

Notable changes to EverFlavor AI, newest first, in the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
format with [semantic versions](https://semver.org/) (MAJOR.MINOR.PATCH):

- **PATCH** (0.5.1 → 0.5.2): fixes, small wording or style changes.
- **MINOR** (0.5.2 → 0.6.0): a new feature, notebook or data source.
- **MAJOR** (0.x → 1.0.0): the first finished release (planned for the final presentation); after that, a change
  that breaks how people use the app or the saved data.

Versions below 1.0 are the **beta**. The version lives in `src/everflavor/__init__.py` (`__version__`); the
notes people see in the app's "What's new" bell are in `app/updates.py`; `tests/test_version.py` checks that all
three agree. Each release is merged to `main`, tagged (`v0.5.1`) and published as a GitHub Release.

## [Unreleased]

Phase 0 of the roadmap (the safety refactor), finished; the first step of phase 1; three 0.7.2 repairs.

### Added

- **Allergen words in Spanish, French and Italian** (policy P26, proposed): 549 words such as leche, huevos,
  crevettes, cozze and harina, each a name of the same Wikidata item as an English allergen word, with the plurals
  the matcher does not make and 94 exception phrases (lait de coco, harina de arroz). 240 recipes gain a caution,
  none loses one. Every word kept or left out, with its reason:
  `docs/flag_review/allergen_words_es_fr_it.csv`; the change report: `docs/flag_review/allergen_words_change_report.md`.
- **Open in maps** on each place card of the Map: the place's pin on OpenStreetMap, which offers directions;
  only the place's location is in the link.
- **Notebook 14: cooking yields and nutrient retention** (USDA, CC0): raw to cooked weight for 173 cuts of meat
  and poultry, nutrients kept for 270 foods and preparations, and a profile per cooking method. Not used by the
  app yet; safe cooking temperatures wait for the FSIS chart.
- **Notebook 15: dish families and variants** (Wikidata, CC0): 564 families (dumpling, biryani, flatbread...), 39
  categories by main ingredient and 49 groupings; 2,634 of our dishes in a family, and 5,220 members we do not
  have yet listed as gaps. The `KnowledgeGraph` reads them (`families_of`, `related`); the app does not yet.
- **The Food Graph** (`everflavor.domain.FoodGraph`): one graph from World down to a recipe (places, dish families,
  dishes, variants, recipes), every edge with its source, and the walks every feature can share (ancestors,
  siblings, families, variants, countries, related dishes).
- **Dish family, Versions and More like this** on About this dish, straight from the graph's Wikidata links
  (gazpacho: ajoblanco, salmorejo, okroshka); a dish without links shows nothing.
- **The app reads the Food Graph:** each search result says what the dish is a kind of, its versions and its food
  region; Explore by place lists the place's dishes by family. Services for discovery, the waiter's context, the
  cookbook's groups and the map (`everflavor.domain.services`), every suggestion with its reason and source.
- A version's page lists the other versions of its dish (Hyderabadi biryani: Kolkata and Sindhi biryani), and
  Explore shows how many versions a dish has. Versions keep their own Wikidata country (Sindhi biryani: Pakistan).

- **"Checked against"** under Check my recipe's profile: what was read (the lines, the steps, the nutrition) and
  against which rules and tables, next to what could not be checked.
- **A typed result** for Check my recipe (`restrictions.RecipeAnalysis`, with `Finding`, `FindingItem` and
  `LineSummary`): one contract for the app, the notebooks and later the waiter.
- Rum cake in the may-contain table (rum, eggs, butter, flour; Wikipedia): 37 rows for 23 foods.
- **Domain entities** (roadmap phase 1, step 1): `everflavor.domain` with `Dish`, `Recipe`, `Ingredient` and
  `Place`, built from today's tables, and the `KnowledgeGraph` that finds a recipe's dish as the app does (826 of
  the 3,000 demo recipes). Not used by the app yet; ingredient merges wait for the team's review.

### Changed

- **Faster kitchen changes:** the kitchen scenes are served as files the browser keeps (`app/static/scenes/`),
  so switching kitchen or hour sends about 11 KB instead of 1 to 1.5 MB of pictures.
- **A clearer profile button:** when the sidebar is closed, the small arrow is now a "Your profile" button in the
  kitchen's button colour, on computers and phones.
- Severities are named as in the roadmap: Critical, Warning, Review, Info (the signs stay the same).
- The profile has seven groups: allergies, medical conditions, religious requirements, ethical preferences,
  personal preferences, goals, cooking preferences. Each rule is offered in one place only (medical diets were
  offered twice); personal rules (no pork, no honey...) can now be picked.

### Fixed

- The live site no longer fails with an AttributeError (Python 3.14, `@dataclass`) when several visitors open
  it at once after a deploy: the fresh-code reload ran in two sessions together and one deleted the modules the
  other was loading. It now runs once, under a lock, before the imports.
- Find recipes now leaves out recipes that break a medical screen or a strict alcohol setting, not only the
  allergy list and diets.

## [0.7.1] - 2026-11-17

The living kitchen, the waiters, the map and Check my recipe as a safety assistant. It sums up the work since
0.5.1, including the branches planned as 0.5.2 and 0.6.3 (0.6.0 was skipped as a number; its items stay in the
planner).

### Added

- **A welcome page** before the kitchen: the promise, one button in, how it works and how we check.
- **Living kitchens** (Japanese, Chinese, Mediterranean, Mexican, Middle Eastern, Moroccan, Classic): the light
  follows your clock or a time you pick, and you can tap the plants, lamps, pots and stools. Each region has a chef,
  as a man or a woman, with greetings in the region's language and 13 checked quotes from chefs of that region.
- **Search by dish, country or region**, Browse by region and **Explore by place**, on the new **Food Taxonomy**
  (`data/reference/food_taxonomy.csv`, 150 places from world to culinary region, placed by the UN M49 regions).
- **The dish page**: the dish's clean name, how to say it (65 dishes), the steps one at a time, cookware, estimated
  cook times, Food.com's own times, servings and extra nutrition (CC0), "Where to buy" and a YouTube search.
- **Walter or Nathalie, the waiter**: a dish's story from open data (Wikipedia and Wikidata, 4,885 dishes and
  foods), never invented; six tones; every question screened (71-question injection test set); an optional local
  retelling that is thrown away if it adds or loses a fact.
- **Check my recipe as a safety assistant**: reads anything pasted; each finding has a pixel sign for how serious
  it is and says how sure we are (verified, likely, possible, unknown); "may contain" foods (33 sourced rows),
  preparation risks (raw, fermented, charred, aged), a nutrition estimate for the servings given, and an alcohol
  setting (cooked-in and extracts as the person's own choices).
- **The profile in levels**, in four groups; each rule can be strict, avoid, warn or ignore (allergies and medical
  screens always strict).
- **Map: Houston**: 5,473 OpenStreetMap places with the evidence for each diet or cuisine claim, a one-tap address
  copy and a link to the place's website.
- **Photos**: Food.com's own photos (CC0, 111,803 recipes), free general dish photos from Wikimedia Commons (3,327
  photos for 48,172 recipes, labelled "not this recipe"), logos and wrong photos hidden, and a pixel-art
  "Cooking up a picture..." card when there is none.
- **Saved recipes** in the browser (beta), with a backup file; **Report a bug / Suggest a feature** forms.
- **Notebooks 10 to 13**: recipe photos, dish knowledge, the safety engine check (10,000 recipes) and the taxonomy
  and map coverage.
- **The live site's demo data** has the map, recipe origins and the USDA tables (`scripts/demo_extras.py`).

### Changed

- Severity is shown with pixel signs (stop sign, warning, caution, information, green circle) instead of emoji.
- All regions is the default search; the Check tab speaks plain English (no rule names or codes).
- uv and a lock file (`config/requirements.lock`) install every library at a tested version; CI installs from it.

### Fixed

- The live site no longer fails with an ImportError after a deploy (it reloads the project's code when it changed).
- Your kitchen pick is kept after a refresh.
- A recipe card no longer fails when its photo check is missing.

### Security

- Dependabot, osv-scanner, dependency review and CodeQL run on every push; Actions are pinned by commit.
- oauthlib 4.0.1 (GHSA-3jp2-3mrg-2vxc) and later dependency updates.
- Ingredient parsing can no longer be slowed for minutes by a crafted pasted line (three CodeQL ReDoS alerts).
- The commit hook refuses Kaggle keys anywhere in the project.

## [0.5.1] - 2026-10-22

The first numbered release (beta). It sums up the work since the project started in September 2026.

### Added

- **The EverFlavor Kitchen front end** (`app/`): a pixel-art kitchen you can touch (curtains close, jars shake,
  the pot puffs steam), a pixel chef who reads out every result, pixel icons instead of emoji, four color themes
  (Classic is the team's original palette), real food photos in the recipe cards, a disclaimer and contributor
  footer, and a "What's new" bell for updates. Design notes, art generator and references in `design/`.
- **Cuisine kitchens (draft)**: Japanese, Mediterranean, Mexican and Middle Eastern kitchens recreated from the team's
  concept art, plus Chinese (Asian) and Moroccan (African), each with its own chef; with "Match the kitchen to the
  cuisine" on, searching a cuisine family opens its kitchen. All keep the title "EverFlavor Kitchen".
- **The planner** (`docs/plans/`): versions 0.5.1, 0.6.0 and later in one place, regional kitchens (data, order,
  art briefs) and reliability (hallucinations, photos, the AI models, regional specialization), with pros and cons.
- Recipe photos are credited and link to the recipe's website, so anyone can check them.
- **Data pipelines** (notebooks 01-09): recipes from several sources with allergen and diet flags, USDA nutrition,
  Open Food Facts hidden allergens, ingredient features, food freshness from photos (models for produce and fish),
  recipe variants, seasons and footprint, and the evaluation of the local AI agents.
- **The back end** (`src/everflavor/`): the calorie calculator, the safety gate, local models through Ollama, five
  agent tools, the answer guard, the CrewAI meal planner, and 200+ red-team checks.
- **Kitchen art v5** (`design/pixel-art/`, not in the app yet): the team's four full kitchens traced object by
  object at their real angles (`trace_kitchens.py`), with a lighting pass (lanterns, windows, fire, shaded edges),
  and morning, afternoon, evening and night versions of each (`day_night.py`): the sky in the windows changes, the
  window sun moves with the hour and becomes a moon, and the lanterns are off by day and lit at evening and night.
- **Art references:** real-kitchen and lantern photos (lit and unlit) with their licenses, and the team's
  Saffron Market concept cut into chefs, title sign and props, kept for a later version (`future-works/v6/`).
- **The art archive** (`design/pixel-art/archive/`): every earlier version (v1 to v4), the v5 build steps and the
  title card test (four title layouts on desktop and phone), labelled, with progress sheets per kitchen.
- **Data plan** (`docs/plans/DATA_AND_MODELS.md`): what each model is short of, candidate datasets with licenses,
  and the download order (DaFiF fish photos first).
- A sample Foundry multi-agent workflow (`my-agent-n6agvd/`; to be moved out of the repository).
- **Guards for keys and user data**: a Claude Code hook and a git pre-commit hook refuse to commit `config/.env`,
  key files or user data (`.claude/hooks/`); project rules in `CLAUDE.md`.

### Changed

- Readable pixel fonts (Jersey 10 and VT323) replace the first pixel font, whose letters and numbers were hard to read.
- Clicks in the app update the page in about 0.05 s instead of 1.5 s.
- The concept sheet's layout: the kitchen stays in view under the title, and the chef stands at the bottom of the
  sidebar (in the page on phones). The team's own detailed art replaces the code-drawn kitchens and chefs once it is
  added to `design/pixel-art/originals/`; the code-drawn ones are archived.

### Fixed

- On computers in dark mode, the app showed white text on its cream background.
- Chosen allergy and diet tags, and the recipe cards, were not styled in Streamlit 1.65.
- Recipe cards without a photo showed an empty space (for example Poblano Posole); they now show a covered dish.

[0.7.1]: https://github.com/Chloe-Tu2/The-EverFlavor-AI/releases/tag/v0.7.1
[0.5.1]: https://github.com/Chloe-Tu2/The-EverFlavor-AI/releases/tag/v0.5.1
