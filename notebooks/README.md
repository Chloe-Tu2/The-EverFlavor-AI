# Notebooks

The data pipeline, one step per notebook. Each runs unchanged in **Colab, VS Code and Antigravity**
(setup: [main README](../README.md#running-the-notebook)). The real logic lives in
[src/everflavor](../src/everflavor/README.md); the notebooks call it, show the results and save the tables.

## Run order

Run **01 first**: notebooks 02, 03, 04, 06 and 07 read its recipe table (`data/interim/recipes_all.parquet`).
Notebook **05** and notebook 08's meat section need no other notebook: they download their own data.
After 01, the rest can run in any order, except where the table says "needs".

| # | Notebook | What it does | Saves (in `data/`) |
|---|---|---|---|
| 01 | [Data acquisition](01_data_acquisition_EverFlavor_V3.ipynb) | Downloads Food.com, Hugging Face, CulinaryDB, TheMealDB, USDA and Open Food Facts; cleans, labels (cuisine, origin, nutrition, restriction flags), splits; trains the baseline cuisine classifier; shows the calorie and country models' accuracy by source, cuisine family and country | `interim/recipes_all.parquet`, `processed/recipes_train/val/test.parquet`, `processed/usda_ingredient_nutrition.csv`, `processed/dataset_info.json`, `models/cuisine_baseline.joblib` |
| 02 | [Cooking methods and fats](02_cooking_methods_and_fats.ipynb) | Cooking method per recipe, cooking-fat reference, alcohol left after cooking | `interim/recipe_cooking_labels.parquet`, `processed/cooking_fats_reference.csv` |
| 03 | [Stores and products](03_stores_and_products.ipynb) | Houston stores (OpenStreetMap; Google Places with a key), products by country (Open Food Facts) | `processed/places.parquet`, `products_by_country.parquet`, `ingredient_products.parquet`, `region_coverage_stores.csv` |
| 04 | [Ingredient knowledge](04_ingredient_knowledge.ipynb) | Names in other languages (Wikidata), substitutions, pairings, shelf life (FoodKeeper) | `processed/ingredient_names/substitutions/pairings/shelf_life.parquet` |
| 05 | [Computer vision: freshness](05_computer_vision_freshness.ipynb) | Indexes 45k fruit, meat and fish photos; near-duplicates, licenses, leak-free split; training (needs a GPU: use Colab) | `processed/freshness_images.parquet`, `freshness_coverage.csv` |
| 06 | [Dish variants](06_dish_variants.ipynb) | Halal, vegan, gluten-free ... version of each dish. Needs 04 (substitutions) | `processed/recipe_variants.parquet`, `recipe_variants_summary.csv` |
| 07 | [Nutrition quality](07_nutrition_quality.ipynb) | Macro labels, nutrient-rich ingredients, calorie calculator check | `processed/recipe_nutrition_quality.parquet`, `ingredient_micronutrients.csv` |
| 08 | [Climate and season](08_climate_and_season.ipynb) | Meat: when each meat is most plentiful and when animals graze fresh grass, by region (built; first run downloads about 10 minutes of weather). Carbon footprint and produce seasons: planned | `processed/meat_supply_seasons.csv`, `pasture_seasons.csv` |
| 09 | [Agent evaluation](09_agent_evaluation.ipynb) | The same 25 questions (5 profiles, 5 attacks) for every local model, scored by code: leaks, right tool, right calories, attacks pushed back; each run compared with the last. VS Code / Antigravity only (needs Ollama) | `processed/agent_eval/agent_eval_<date>.csv` |

## Run times

Measured on a laptop CPU with the downloads already saved (October 2026); each notebook also shows its own
at the top. Colab's free runtime takes about as long, or a little longer. First-run download times are estimates.

| # | Re-run | First run adds | Slowest part |
|---|---|---|---|
| 01 | about 20-35 min | 10-30 min of downloads | 5.5.2, the pipeline on every source (about 15 min) |
| 02 | about 2 min | little (reuses 01's Food.com download) | Section 3, cooking methods |
| 03 | about 2 min | 30-60 min (Open Food Facts export, OpenStreetMap) | Section 5, linking ingredients to products |
| 04 | under 1 min | 10-30 min (Wikidata, FoodKeeper) | Section 3 |
| 05 | about 32 min | hours (photos: several GB, about 32 GB with MeatScan); training 1-3 h on a GPU | Section 4, near-duplicates in 45,000 photos (about 30 min) |
| 06 | about 6 min | nothing (needs 01 and 04) | Section 3, variants for every dish |
| 07 | under 1 min | nothing (uses 01's USDA files) | Section 6, calorie calculator check |
| 08 | about 2 min | 10-12 min (10 years of weather for 11 regions) | Section 3b |
| 09 | about 16 min (two small models) | pulling the models (`ollama pull`, a few GB) | Section 4, the questions (10-50 s each) |

All nine on a fresh computer: plan for an afternoon (most of it notebook 05's photos); re-running all of
them takes about an hour.

## Good to know

- **Keys:** only notebook 01 needs one (`USDA_API_KEY`); Google Places (03) is optional. Keys come from Colab
  Secrets or `config/.env`, never from the notebook. See [config](../config/README.md).
- **Re-running is cheap:** downloads already on disk are reused; only what is missing is fetched.
- **Big download:** notebook 05's photos are about 32 GB. MeatScan is opt-in (`DOWNLOAD_MEATSCAN`).
- **Shared code in Colab:** each notebook downloads the files listed in `EVERFLAVOR_MODULES`. When you add a
  module to `src/everflavor`, add it to that list in every notebook (a test checks this).
- **GPU for notebook 05's training:** in Colab, Runtime > Change runtime type > T4 GPU, then `TRAIN = True`
  (Kaggle Notebooks are a free alternative with more GPU hours).
- **AI agents:** `llm.py`, `agent_tools.py` and `crew.py` run in VS Code / Antigravity. Only notebook 09 uses
  them, and in Colab it says so and stops, so Colab is never affected.
- **Before you push:** clear large outputs and run the checks in the [main README](../README.md#using-the-shared-code).
