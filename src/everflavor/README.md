# everflavor (shared code)

The Python package behind everything: the notebooks, the starter app and, later, the agents all import it,
so a rule is written once. Import it with `from everflavor.<module> import <name>`; the notebooks and the app
add `src/` to the path for you.

## Modules

| Group | Module | What it is for |
|---|---|---|
| **Safety** | `flags.py` | Restriction flags: keyword rules per allergen, meat, alcohol ... (the largest file) |
| | `diets.py` | Diet profiles (halal, kosher, vegan, Jain ...) built from the flags |
| | `safety.py` | `UserProfile` and `check_recipe`: the gate every agent-written recipe passes |
| | `review.py` | Blind hand-check samples for the flags |
| **Recipes and data** | `sources.py` | Download helpers: USDA, Open Food Facts, CulinaryDB, TheMealDB |
| | `pipeline.py` | Cleaning, combining, splitting, validation (`run_pipeline`) |
| | `ingredients.py` | Cleaning and normalizing ingredient names |
| | `cuisine.py` | Cuisine families, country and region of origin |
| | `parsing.py` | Lists and labels stored as text |
| | `features.py` | Text features shared by the models |
| **Food knowledge** | `nutrition.py` | Nutrition per serving, plausibility, USDA matching |
| | `nutrition_quality.py` | Macro labels, nutrient-rich ingredients (notebook 07) |
| | `calories.py` | Calorie calculator: ingredient lines to grams to calories |
| | `cooking.py` | Cooking methods and fats (notebook 02) |
| | `knowledge.py` | Pairings, substitutions, shelf life, names (notebook 04) |
| | `variants.py` | Diet versions of each dish (notebook 06) |
| | `stores.py` | Stores and products, where to buy (notebook 03) |
| | `seasons.py` | Meat supply season and pasture season (notebook 08) |
| | `freshness.py` | Freshness photos: labels, duplicates, split, training (notebook 05) |
| **Agents and app** | `recommend.py` | Baseline recommender and its safety filter |
| | `llm.py` | Local models through Ollama (VS Code / Antigravity only); the answer guard |
| | `agent_tools.py` | The agents' tools: recipes, calories, where to buy, substitutions (profile from code) |
| **Helpers** | `checks.py`, `environment.py`, `progress.py`, `charts.py`, `reporting.py` | Input checks, keys, progress bars, charts, tables |

## Rules for this code

- Public functions have type hints and a docstring; names starting with `_` are internal.
- Functions never change the table they are given; they return a new one.
- Rule tables (keywords, maps, limits) are `UPPER_CASE` constants at the top of each module.
- Flags only ever add cautions: when unsure, flag.
- Every change gets a test in [tests](../../tests/README.md). Full rules: [docs/CONTRIBUTING.md](../../docs/CONTRIBUTING.md).
- New module? Add it to `EVERFLAVOR_MODULES` in every notebook (Colab downloads that list).
