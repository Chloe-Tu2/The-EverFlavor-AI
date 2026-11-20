# everflavor (shared code)

The Python package behind everything: the notebooks, the starter app and, later, the agents all import it,
so a rule is written once. Import it with `from everflavor.<module> import <name>`; the notebooks and the app
add `src/` to the path for you.

## Modules

| Group | Module | What it is for |
|---|---|---|
| **Safety** | `flags.py` | Restriction flags: keyword rules per allergen, meat, alcohol ... (the largest file); `reveal_hidden_words` reads disguised and foreign food words ("p0rk", 🐖, "cerdo") for every check |
| | `diets.py` | Diet profiles (halal, kosher, vegan, Jain ...) built from the flags |
| | `dish_names.py` | The dish's own name from a posted title ("Kittencal's Famous Lasagna" -> "Lasagna"), for showing only; the flags read the posted title |
| | `safety.py` | `UserProfile` and `check_recipe`: the gate every agent-written recipe passes |
| | `confidence.py` | How sure a finding is, kept apart from how serious it is: verified (listed), likely or possible (a food usually or sometimes made with it, from the sourced may-contain table), unknown (a product whose contents the name does not show); `severity_for` reads both with the person's answer (strict, avoid, warn, ignore; allergies and medical screens always strict) and never softens the gate's call |
| | `preparation.py` | How a dish is made, as a risk of its own: raw or undercooked (medium-rare, sushi, tartare, ceviche...) and fermented, named in the dish name, the lines or the steps; `step_sentences` lets the safety gate read the steps for foods the lines don't show (beer in a batter) |
| | `review.py` | Blind hand-check samples for the flags |
| **Recipes and data** | `sources.py` | Download helpers: USDA, Open Food Facts, CulinaryDB, TheMealDB |
| | `pipeline.py` | Cleaning, combining, splitting, validation (`run_pipeline`); `refresh_flags` works the flags out again after a rule change |
| | `ingredients.py` | Cleaning and normalizing ingredient names |
| | `cuisine.py` | Cuisine families, country and region of origin |
| | `parsing.py` | Lists and labels stored as text |
| | `places.py` | The Food Discovery Map's claims: each diet tag at an evidence level (verified needs a checked record with a link; likely from OpenStreetMap tags or the business's name; unknown otherwise), cuisine indicators with their source; never authenticity, freshness or "best". The recipe -> ingredient -> store link: `specialty_in` (the "Look for" list) and `find_stores_for` (stores whose own cuisine or name says they likely carry that food, each with its reason); `map_places`, the Map tab's rows with their words; `map_url`, the place's pin on OpenStreetMap ("Open in maps") |
| | `preferences.py` | Foods a person doesn't eat (not allergies): matched by name only, never a safety check; the "Foods I don't eat" choices |
| | `recipe_details.py` | Food.com recipes' own prep and cook times, servings, sugar, fibre, saturated fat and cholesterol from the CC0 Kaggle set (joined by number and name; its unit-less quantities are not used) |
| | `features.py` | Text features shared by the models; training weights by group (`balanced_weights`) and results by group (`results_by_group`) |
| **Food knowledge** | `nutrition.py` | Nutrition per serving, plausibility, USDA matching (hand-checked list, then automatic matches that must cover every word of the name) |
| | `nutrition_quality.py` | Macro labels, nutrient-rich ingredients (notebook 07) |
| | `calories.py` | Calorie calculator: ingredient lines to grams to calories |
| | `cooking.py` | Cooking methods and fats (notebook 02) |
| | `cooking_time.py` | Cook-time estimates for recipes without a time (`estimate_minutes`, `time_label`): gradient boosting on the times in the steps and similar Food.com names; `minutes_source` says "recipe" or which estimate, real times are never replaced |
| | `knowledge.py` | Pairings, substitutions, shelf life, names (notebook 04) |
| | `dish_knowledge.py` | The waiter's dish knowledge (0.6.3): tidies the collected facts (sources' words only), sorts them by topic, writes one page per country (notebook 11) |
| | `waiter.py` | Walter, the AI waiter (0.6.3): finds a recipe's dish in the knowledge notebook, answers with skills (fun fact, inspiration, origin, history, ingredients, allergy explained from the back end's flags, learn more, recommendation) weighted by the user's style and told in their tone (Fun, Funny, Just the facts, Key points, Broad, Simple; picked in Settings, on his panel or by asking "make it funny"); screens questions (prompt injection, length), rate-limits them and counts problems without the words; optionally retold by a local model (`reword`, in the tone's form, checked: no new names, numbers, foods or links, the fact itself kept, then `llm.guard_answer`; "Just the facts" is never retold) |
| | `saved_recipes.py` | Saved recipes kept in the user's own browser (0.6.3 beta): the JSON kept in local storage and in the backup file, and checking what comes back (malformed entries left out, text and count capped) |
| | `variants.py` | Diet versions of each dish (notebook 06) |
| | `stores.py` | Stores and products, where to buy (notebook 03): OpenStreetMap places in an area's box or circle (`count_places` first), with address, phone and the shop's own kind |
| | `seasons.py` | Meat supply season and pasture season (notebook 08) |
| | `freshness.py` | Freshness photos: labels, duplicates, split, training (notebook 05); for long Colab runs: cached duplicate check (`image_hashes`), resumable training (`train_all_groups`), a results zip (`pack_results`); the epoch to keep (`pick_best_epoch`) and what the computer can handle (`system_check`, `system_verdict`); the final test on the test split with the spoiled threshold (`final_test`, `choose_spoiled_threshold`) |
| **Agents and app** | `recommend.py` | Baseline recommender and its safety filter |
| | `llm.py` | Local models through Ollama (VS Code / Antigravity only): model choice (`llama3.2` first), the answer guard, prompt-injection defenses (`clean_text`, `tool_message`), `ask_agent` |
| | `crew.py` | Meal planner: a CrewAI Chef writes, the code checks, retries and falls back (VS Code / Antigravity); picks `granite4.1:3b` by itself (`CREW_MODELS`, faster in CrewAI) |
| | `agent_tools.py` | The agents' tools: recipes, calories, where to buy, substitutions (profile from code) |
| | `refresh.py` | Rules fingerprint, whether the saved data is current, refreshing the flags in about 20-25 minutes instead of an hour (`python -m everflavor.refresh`) |
| | `evaluation.py` | Agent evaluation (notebook 09): 33 questions (13 attacks), scored by code (leaks, right tool, right calories, attacks) |
| **Domain** | `domain/` | Roadmap phase 1: the entities every feature will read, each fact with one owner and links by id. `Dish` (Wikidata QID, else a country slug; sourced facts, pronunciation), `Recipe` (lines with amounts, steps, nutrition; no flags), `Ingredient` (risks computed now: verified from the flag rules, likely or possible from the may-contain table), `Place` (diet claims with their evidence). `KnowledgeGraph.load()` builds them from today's tables and finds a recipe's dish as the app does (826 of the 3,000 demo recipes find one), and reads notebook 15's dish families: `families_of(dish)` and `related(dish)` (closest family first, only links Wikidata states). **`FoodGraph`** (`food_graph.py`) joins it all in one graph from World to a recipe: places, dish families, dishes, variants and recipes as nodes; edges `part_of`, `in_family`, `variant_of`, `origin` (Wikidata), `eaten_in` (the cuisine list) and `recipe_of`, each with its evidence; traversal `ancestors`, `children`, `siblings`, `families_of`, `variants_of`, `recipes_of`, `countries_of`, `related`, `path`. The dish page reads it for "Dish family", "Versions" and "More like this". **`services.py`** reads the graph for every feature: `GraphRecommendationService` (related dishes and variants with the reason for each, family members, cuisine, country and region neighbours, `discovery_candidates`, the `discover_*` calls for Explore and World Tour, `dishes_at` a place), `WalterContextService` (the waiter's context and fixed-template sentences, names only from the graph), `CookbookGrouping` (saved dishes by family or country) and `MapLinks` (map places for a dish, an ingredient's kinds of shop, places of a region). A place's dishes are those whose Wikidata origin is there, or with no origin, its cuisine list; only dishes, not foods and drinks |
| **Helpers** | `checks.py`, `environment.py`, `progress.py`, `charts.py`, `reporting.py` | Input checks, keys, progress bars, charts, tables |

## Rules for this code

- Public functions have type hints and a docstring; names starting with `_` are internal.
- Functions never change the table they are given; they return a new one.
- Rule tables (keywords, maps, limits) are `UPPER_CASE` constants at the top of each module.
- Flags only ever add cautions: when unsure, flag.
- A language model never decides safety: the gate (plain code) decides, the model only proposes or explains,
  and every answer it writes is screened (`llm.guard_answer`). Tools take the user's rules from the code.
- Every change gets a test in [tests](../../tests/README.md). Full rules: [docs/CONTRIBUTING.md](../../docs/CONTRIBUTING.md).
- New module? Add it to `EVERFLAVOR_MODULES` in every notebook (Colab downloads that list).
