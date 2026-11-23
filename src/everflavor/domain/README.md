# everflavor.domain

The food entities and the Food Graph: one place every feature reads dishes, recipes, ingredients and places from.

## Purpose

Each fact has one owner, and entities link by id instead of copying data: a dish's origin and story belong to the
`Dish`, amounts and steps to the `Recipe`, allergy risks to the `Ingredient`, diet claims to the `Place`. The
`FoodGraph` joins them to the Food Taxonomy, from World down to each recipe, so discovery, the waiter and the map
all read the same edges. Nothing is inferred: an edge exists only when a source states it.

| File | What it holds |
|---|---|
| `entities.py` | The frozen dataclasses: `Dish`, `Recipe` (with `RecipeLine`, `Nutrition`), `Ingredient`, `Place` and their facts, claims and sources |
| `loaders.py` | Build an entity from one table record (`dish_from_record`, `recipe_from_row`, ...), checking the fields; a missing value stays empty |
| `graph.py` | `KnowledgeGraph`: loads the entities from today's tables and finds a recipe's dish as the app does (`waiter.Knowledge.find`, rule L1) |
| `food_graph.py` | `FoodGraph`: places, dish families, dishes, versions and every recipe as nodes; edges `part_of`, `in_family`, `variant_of`, `origin`, `eaten_in`, `recipe_of`, `named_for`, `recipe_from`, each with its evidence |
| `services.py` | What reads the graph: `GraphRecommendationService`, `WalterContextService`, `CookbookGrouping`, `MapLinks`; every suggestion says why it is made |

## Inputs

- `data/knowledge/dishes.jsonl` (the knowledge notebook: Wikipedia CC BY-SA, Wikidata CC0) and
  `data/knowledge/dish_families.json` (notebook 15, Wikidata "subclass of").
- `data/reference/food_taxonomy.csv` (the place tree) through `everflavor.taxonomy`.
- The processed recipe tables (`data/processed/recipes_*.parquet`, notebook 01) or the demo tables
  (`data/demo/`), and the places table for the map.

## Outputs

Python objects only: this package writes no files. Scripts that read it write the assets in `data/knowledge/`
(`graph_assets.py`, `recipe_graph.py`, `quality_reports.py`).

## Dependencies

`pandas` (reading the tables) and these `everflavor` modules: `waiter` (the dish match), `taxonomy` (the place
tree), `flags` (an ingredient's risks come from the flag rules, never decided here), `confidence` (may-contain),
`places` (diet evidence, specialty ingredients), `calories`, `dish_names`, `ingredients` and `parsing`.
Used by the app (`app/app.py`: the dish page's "Dish family", "Versions" and "More like this") and the scripts in
`scripts/knowledge/`.

## Tests

`tests/test_domain.py`, `tests/test_food_graph.py`, `tests/test_graph_services.py`.

## Ownership

Team EverGlow. A change to how dishes match recipes is a recorded policy (rule L1 in
`docs/audits/recipe_dish_linking.md`); safety decisions are not made here but in the safety engine
(`flags.py`, `safety.py`, `recommend.py`).

## Future work

- The ingredient merges, after the team's review (`docs/flag_review/HOW_TO_REVIEW_INGREDIENT_MERGES.md`).
- A cuisine-style level in the graph, once a published source draws one (reserved in `food_graph.py`).
- The Balkans and Siberia as regions, once a source draws them (`docs/audits/global_culinary_atlas.md`).
