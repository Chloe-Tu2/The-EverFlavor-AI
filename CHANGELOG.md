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

### Added

- **The atlas sprint** (decided by med27-coder, 2026-11-22; Africa first): 169 dishes and 75 foods from the Wikipedia
  cuisine pages of 74 more countries (Africa, the Pacific Islands, the Caribbean, Central America, Central Asia),
  with Wikidata facts; 90 countries now have a dish (53 before). The place tree gains 59 countries and four
  regions (Central Asia, Melanesia, Polynesia, Micronesia). A new country's page sets a dish's country only when
  Wikidata's origin or the dish's own intro names it. World culinary coverage: 36.3% (24.7% before); Africa 33.7%
  (6.9%).
- **Sprint 2, Oceania and Indigenous foods** (2026-11-23): the fetch also reads the paragraph links on sprint
  countries' cuisine pages (Fiji's page is prose) and "Cuisine of X" titles (Kenya, Sudan), keeping a dish found
  only in a paragraph when Wikidata's origin or its intro names the country; 12 more Oceania countries and
  territories in the place tree. 124 more entries; 103 countries have a dish, 112 country pages. Indigenous food
  traditions (Māori, Aboriginal Australian, Native American, Inuit, Native Hawaiian, Chamorro; Sámi, Ainu and
  Mapuche pages read, nothing tagged yet): a tag only when the tradition's page lists the food and the food's
  intro names the people; all wait for review (`docs/governance/indigenous_review.md`). World culinary coverage
  40.9%; Africa 41.0%, Oceania 27.9%.
- **Atlas metrics:** `scripts/knowledge/enrichment_impact.py` (before and after, `atlas_metrics.json`, a recovery
  chart and the README's generated Atlas progress block) and `region_pages.py` (one knowledge page per food
  region, validated).
- **Sprint 3, coverage recovery** (2026-11-23): the cuisine pages of 69 more countries (South America, Northern
  and Eastern Europe and the Balkans, Southern and Western Asia, the Caucasus, East and Southeast Asia, the
  Caribbean); 33 of them join the place tree. 650 more entries (377 dishes), none lost, 3 moved (review item 29).
  148 countries have a dish, 104 three or more; world culinary coverage 60.4% (40.9% after sprint 2); the
  Americas 60.3%, Asia 72.9%, Europe 81.7%. `scripts/knowledge/country_scores.py` scores each country for
  coverage, representation and enrichment and lists the weakly represented ones (47) as the next targets; the
  README dashboard shows the summary.
- **Sprint 4, coverage recovery** (2026-11-23): for the 91 weak or uncovered countries, the fetch also reads
  their Wikipedia categories ("Category:Kenyan cuisine" and its dish subcategories) and Wikidata's country of
  origin. A category only adds an article no page gives and keeps it only when it is a dish whose Wikidata origin
  or own intro names the country. 64 dishes added (Cambodia 14, Algeria 9), none moved or lost; 154 countries
  have a dish, 115 three or more; world coverage 63.7%, Africa 44.0%, Oceania 32.3%. Per-sprint impact reports
  (`enrichment_impact.py --sprint N`, `docs/audits/sprints/`), the sprint review checklist, a pull request
  template, an atlas sprint review issue form and an Indigenous tag review sheet.
- **Related dishes in Check my recipe** (0.8.0): when the dish name is one the knowledge notebook knows, a panel
  shows its family, versions and "more like this" from the Food Graph (Wikidata, CC0); not checked against the
  profile, and nothing pasted is saved.
- **Map cuisine tags for 23 more countries** (0.8.0): the OpenStreetMap cuisine word used 50 or more times
  (taginfo, 2026-11-23), such as georgian, ukrainian, nepalese, salvadoran and dominican; 79 of the 167 countries
  with dishes now have one. "dutch" and "georgian" are not shop-name hints.
- **Exact numbers beside coverage** in the README dashboard: how many countries have a dish and pass every basic
  check, per continent.
- **Cuisine photo fallbacks** (0.8.0, `scripts/knowledge/cuisine_images.py`): for a recipe with no photo, a photo
  of its country's cuisine (the image Wikidata names for the cuisine article), labelled "a photo of Kenyan cuisine,
  not this dish", with its Commons credit. 108 countries have one, 96 pass the photo rules; the app shows one only
  after a person's `keep` in `data/knowledge/review/cuisine_images.csv` (none yet).
- **Two country counts** (`scripts/knowledge/country_counts.py`, `docs/audits/country_counts.md`): our coverage
  count (200 CLDR countries and territories of 100,000 people or more, 154 with a dish) beside the usual one (the
  195 UN member and observer states, 149 with a dish), where they differ, and how the count grew by sprint.
- **Store locator, first step** (0.8.0, `docs/plans/MAP.md`): the map tab takes a Greater Houston ZIP code and a
  distance (2 to 25 miles) and lists the nearest places first (name, kind, cuisine, straight-line distance), 10 at
  a time; "Open" shows the place card, with its map link for directions. ZIP centres come from the Census 2025 ZCTA
  Gazetteer, stored locally (`data/reference/houston_zcta.csv`): no service is called, and the ZIP is not saved.
  `places.zip_center`, `miles_between` and `nearest_places` in the back end.
- **Review aids for people** (overnight, 2026-11-23; none decides anything): the cuisine photo sheet sorted by risk
  (13 likely wrong, 30 to look at, 65 probably right); the fact review rows ranked by how much the app shows them
  (`focus_review_priority.csv`: the first 100 cover 41 dishes and 1,509 linked recipes); the backlog of the 45 UN
  member states with no dish (`docs/audits/empty_country_backlog.md`: 6 easy, where Wikidata gives dishes filed
  under another country); and Walter's five questions per dish (`docs/audits/walter_five_questions.md`: 148
  dishes answer all five; versions are the gap).
- **Review decisions, 2026-11-25** (med27-coder): items 24, 28, 29 and 30 answered (the 0.8 review condition),
  36 (no), 37 (an intro stating where a dish comes from is story material) and 40. New
  `data/reference/dish_decisions.csv` keeps a person's decisions on dish entries: Kiwiburger, Goody Goody Gum Drops
  and Hagelslag leave New Zealand, and Haneeth counts for Yemen as well as Saudi Arabia.
- **Sprint 6, pipeline blind spots** (2026-11-25): Monaco, San Marino and Liechtenstein were never in the fetch
  lists or the place tree; with them, Barbajuan and U Pan de Natale (Monaco) and Torta Tre Monti (San Marino) bring
  the UN members with a dish to 163. Pick sheets for the empty countries (`cuisine_page_picks.py`, 520 articles),
  the campaign health table, debt efficiency and a headline in the handoff; review items 36 to 40.
- **Sprint 5, weak regions** (2026-11-25): nine more weak or empty countries in Wikidata's origin targets; one
  new dish (Chukuchuk, the Marshall Islands' first: 161 UN members with a dish) and two foods; none moved. The
  small gain confirms the shared-dish and origin routes are nearly used up for the empty countries (review
  item 35).
- **Story rule and Wikidata regions** (review items 34 and 33, decided by med27-coder, 2026-11-25): an intro
  sentence that states an origin, a date, a traditional association or a cultural significance counts as story
  material (`scripts/knowledge/story_rules.py`; ingredients, preparation and popularity never count); Wikidata's
  cuisine items become provisional culinary regions under five rules, counted only when one of our dishes is
  linked (`scripts/knowledge/wikidata_regions.py`: 542 regions, 59 linked, 2 disputed for a person). Countries
  without a story 43 to 32; atlas debt 567 to 538, 3.38 to 3.20 per country.
- **Landing page dish count** (asked by med27-coder, 2026-11-24): the landing says how many dishes the app works
  with right now (3,863), counted from the knowledge notebook's dish entries when the page loads, so it follows
  every data run.
- **Overnight curator reports** (2026-11-24; none decides anything): campaign A's candidates for the 33
  UN members still empty (`country_recovery_candidates.md`: the shared-dish route is used up, 3 weak
  candidates); Q2 story recovery (43 countries without a story, material for 5; review item 34); Q4 family
  recovery (17 countries, 3 candidates); Q1 phase 0 regional source research (Wikidata cuisine items reach 35
  of 115 countries; review item 33).
- **Multi-origin dish policy** (decided by med27-coder, 2026-11-24; review item 32): a dish counts for every
  country with sourced evidence (its listing country and Wikidata's countries of origin), never by page proximity
  or a guess; disputes stay with a person (`docs/governance/multi_origin_dish_policy.md`,
  `scripts/knowledge/dish_origins.py`). 500 dishes count for more than one country; 14 countries get their first
  dish, among them the six empty UN members of campaign A. World coverage 63.7% to 69.1%, Africa 44.0% to 51.2%
  (the 1.0 target), UN members with a dish 148 to 160. A person can drop any added country in
  `data/knowledge/review/shared_dish_origins.csv`.
- **Weighted atlas debt and the handoff report:** the debt is weighted (regions 3; story, family, one dish 2;
  photo, Walter 1) and followed per country (3.35 to 3.38: the new countries bring their own gaps), with the
  country priority list and the 20 weakest Walter countries; `curator_handoff.md` follows the session handoff
  format, compared snapshot to snapshot.
- **Continuous handoff** (2026-11-24): `atlas_health.py` also writes `docs/audits/curator_handoff.md` (what
  improved, regressed, is blocked, needs a person, is next, against a daily history) and
  `docs/audits/release_readiness.md`. The planner adds quality campaigns Q1 to Q4 against the atlas debt, one
  order for all campaigns and a session routine; review item 32 becomes a multi-origin dish policy.
- **Atlas health and atlas debt** (2026-11-24): `scripts/knowledge/atlas_health.py` writes
  `docs/audits/atlas_health.md` every run: the five measures, an atlas debt per country (227 points over 154
  countries; the most common gaps are no culinary region data, 101, and no story, 39) and release readiness
  (0.8: 4 of 9 done, 0.9: 2 of 10, 1.0: world coverage met, Africa and Oceania open). The charter now treats
  unattended work as curation and lowering the debt as a goal.
- **Campaign review aids** (2026-11-24; none decides anything): evidence packets for the six empty UN members
  (`docs/audits/empty_country_packets.md`: 21 Wikidata dishes, 19 shared dishes listed under a neighbour, 2 not in
  the atlas; review item 32); a Walter coverage score per country (average 3.43 of 5; the weakest are one- or
  two-dish countries); and a review impact report (`docs/audits/review_impact.md`) ranking the 11 open decisions
  by the release gate they unblock. The planner's atlas campaigns run apart from version numbers.
- **Indigenous tag verdicts are kept:** `culinary_coverage.py` rewrites the review sheet on every run, keeps
  people's verdicts, and marks a tag reviewed only with `keep` and a reviewer's name.

### Changed

- **The landing page shows the atlas's breadth and depth** (review item 21, med27-coder, 2026-11-25): how many of
  the 193 UN member states have a dish, then world culinary coverage as "coverage depth", the weighted score with
  its meaning unchanged, with a tooltip on what depth measures.
- Decorative emojis removed from the app, docs and comments (the safety engine still reads food emojis in
  recipes).

- World culinary coverage: a country with no culinary regions in the place tree has no level 2, and its
  regional-styles check does not apply (instead of counting as met).

## [0.7.2] - 2026-11-22

Phase 0 of the roadmap (the safety refactor), finished; the first step of phase 1; three 0.7.2 repairs; the
Middle Eastern kitchen fix; the maintenance audits and world culinary coverage as the headline metric.

### Added

- **World culinary coverage** (`docs/audits/world_culinary_coverage.md`, decided by med27-coder): how well each
  country's food tradition is represented (level 1: representative dishes, a family, a cuisine description, a food
  history, regional styles; level 2: its culinary regions; level 3: its families' versions), now the headline
  metric instead of the dish count. World 24.7%; Africa 6.9%. The counting rule is proposed.
- **Maintenance audits** (reports only): repository hygiene, a stricter provenance check (licence, version,
  attribution), the rich-dish upgrade and Walter enrichment queues, Food Graph validation (no broken links),
  coverage by continent, the documentation gaps and the CI guardrails; `docs/architecture/` draws the layers and
  explains the safety engine step by step.
- **Governance and security** (`docs/governance/`, `SECURITY.md`, `GOVERNANCE.md`): a secret scan of every tracked
  file (API keys, tokens, passwords, connection strings; values redacted) that fails CI on any finding; a PII
  audit (e-mails, phones, addresses, coordinates) for a person to review; the public data policy, the human
  approval workflow (two people for safety rules), the licence compliance summary, a release checklist and the
  list of questions waiting for the team. An "At a glance" section opens the README. A **provenance audit** checks
  that each of the 111 data files in `data/knowledge/` and `data/reference/` records its source and date (or a
  README names it); the tests fail on a gap.
- **Content quality sprint** (reports only, no app change): an **approved image queue** of 1,739 Wikidata dish
  photos that pass the photo pipeline's licence, credit and size rules (read from the Commons API, nothing
  downloaded); the **dish completeness report**, which shows rich dishes going from 505 to 654 and thin ones from
  1,365 to 728 once those photos are fetched and checked; and the **taxonomy validation**, which finds every one of
  the 92 countries in a zone and region that match its UN region. The image report is now
  `docs/audits/image_coverage_report.md`.
- **Global Culinary Atlas audit** (`docs/audits/global_culinary_atlas.md`, reports only): coverage by the UN's
  22 world regions (Unicode CLDR), a breadth-and-depth score per continent and subregion, the gaps (Western and
  Middle Africa, Central Asia, Melanesia, Micronesia and Polynesia have no dish yet), up to 500 ready next dishes
  per continent, 812 missing versions of dishes we show, and the 357-dish review queue grouped by problem.
- **Every recipe is a Food Graph node** (`FoodGraph.add_recipes`): `recipe_of` its dish, `named_for` a food or
  drink entry (a recipe called "Salmon"), else `recipe_from` the place its source's labels name. 83% of the
  291,755 recipes now reach the place tree, against 27% through a dish; 50,673 stay nodes without an edge, never a
  guessed one. Counts: `data/knowledge/recipe_graph_counts.json` (`scripts/knowledge/recipe_graph.py`).
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
- **Data audits** (`docs/audits/`, read-only; nothing in the app changed): how recipes link to dishes (80,741 of
  291,755), and world coverage by zone, country and culinary region, with the dish family and variant gaps, the
  indigenous foodways, proposed publishing rules and an expansion backlog of 3,689 Wikidata dishes (1,459 ready,
  357 to review, 1,873 blocked, among them brands and events), with the 500 to add first.
- **Recipe quality audit** (`docs/audits/recipe_quality.md`): 47% of recipes have ingredients, steps, servings
  and nutrition (all from Food.com); CulinaryDB and the Hugging Face set come without steps, 37% have no
  photo at all, 22% no country. Nothing was changed.
- **Quality sprint reports** (`docs/audits/`, reports only): a completeness score (0-100) for every dish (16% rich,
  42% fair, 43% thin), the dish image audit (33% can show a licensed photo of their own recipe, 60% only the
  placeholder, but 1,731 of those have a Commons image on Wikidata to fetch), the waiter's knowledge (no fact
  checked by a person yet), map, taxonomy, country and region coverage, and the publication queue checked again.
- **Graph assets** (`data/knowledge/`, not read by the app yet): the waiter's fixed lines for all 3,201 dishes,
  8 next dishes each with the reason and evidence, and the map's cuisine tag per country.
- **The map finds places for 27 more countries** (Poland, Portugal, Canada, Australia, Afghanistan, Venezuela...):
  each country's Wikidata demonym, where OpenStreetMap uses it as a cuisine tag 50+ times; 18 more pilot-area
  places now match a dish's country. 18 countries still have no tag.
- **Domain entities** (roadmap phase 1, step 1): `everflavor.domain` with `Dish`, `Recipe`, `Ingredient` and
  `Place`, built from today's tables, and the `KnowledgeGraph` that finds a recipe's dish as the app does (826 of
  the 3,000 demo recipes). Not used by the app yet; ingredient merges wait for the team's review.

### Changed

- **The Middle Eastern kitchen follows the place tree's food regions** (`app/themes.py`, `KITCHEN_REGIONS`; decided
  by med27-coder): kitchens are themes guided by the tree, not bound to it. It covers the Levant, Anatolia, Persian
  Region, Mesopotamia and the Arabian Peninsula, plus the Caucasus and Egypt; the tree gains Israel, Jordan, Yemen,
  Oman, the United Arab Emirates, Qatar, Kuwait, Bahrain and Georgia. No country lost its kitchen.
- The planner: 0.8.0 is coverage, images and the store locator; chat with the chef moves to 0.9.0.
- **A recipe named for a dish's flavour no longer links to that dish** (rule L1, proposed): "peanut butter fudge"
  is Fudge, "pumpkin pie bars" has no dish, "French dip sandwiches" stays French dip (its summary says it is a
  sandwich). 3,573 links changed: 3,171 wrong dishes dropped, 402 moved to the right one; every change, grouped, is
  in `docs/audits/dish_link_review.csv`. 77,560 of 291,755 recipes now link to a dish or food.
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

[0.7.2]: https://github.com/Chloe-Tu2/The-EverFlavor-AI/releases/tag/v0.7.2
[0.7.1]: https://github.com/Chloe-Tu2/The-EverFlavor-AI/releases/tag/v0.7.1
[0.5.1]: https://github.com/Chloe-Tu2/The-EverFlavor-AI/releases/tag/v0.5.1
