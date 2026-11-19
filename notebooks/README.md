# Notebooks

The data pipeline, one step per notebook. Each runs unchanged in **Colab, VS Code and Antigravity**
(setup: [main README](../README.md#running-the-notebook)). The real logic lives in
[src/everflavor](../src/everflavor/README.md); the notebooks call it, show the results and save the tables.

## Run order

Run **01 first**: notebooks 02, 03, 04, 06, 07 and 12 read its recipe table (`data/interim/recipes_all.parquet`
or its splits). Notebook **05** and notebook 08's meat section need no other notebook: they download their own
data. After 01, the rest can run in any order, except where the table says "needs". The numbers stay as they
are (links, Colab badges and tests point at them); the stages below group them by what they are for.

### 1. Recipes

The recipe table everything else reads, and what is in each recipe.

| # | Notebook | What it does | Saves (in `data/`) |
|---|---|---|---|
| 01 | [Data acquisition](01_data_acquisition_EverFlavor_V3.ipynb) | Downloads Food.com, Hugging Face, CulinaryDB, TheMealDB, USDA and Open Food Facts; cleans, labels (cuisine, origin, nutrition, restriction flags), splits; trains the baseline cuisine classifier; shows the calorie and country models' accuracy by source, cuisine family and country | `interim/recipes_all.parquet`, `processed/recipes_train/val/test.parquet`, `processed/usda_ingredient_nutrition.csv`, `processed/dataset_info.json`, `models/cuisine_baseline.joblib` |
| 02 | [Cooking methods and fats](02_cooking_methods_and_fats.ipynb) | Cooking method per recipe, cooking-fat reference, alcohol left after cooking | `interim/recipe_cooking_labels.parquet`, `processed/cooking_fats_reference.csv` |
| 07 | [Nutrition quality](07_nutrition_quality.ipynb) | Macro labels, nutrient-rich ingredients, calorie calculator check | `processed/recipe_nutrition_quality.parquet`, `ingredient_micronutrients.csv` |
| 10 | [Recipe photos](10_recipe_photos.ipynb) | Food.com's own photo links from a CC0 Kaggle dataset (irkaal), joined by recipe number; optional photo download, logo fingerprint and the photo-matches-dish check. Run 2026-10-25/26: 111,614 photos downloaded, 303 hidden as logos or icons, and the photo check (`scripts/recipe_photos/check_photos.py`) hides 445 more that do not show the dish | `processed/foodcom_photo_links.parquet`, `processed/foodcom_photos.parquet` |

### 2. Food knowledge

What the app knows about ingredients and dishes, beyond the recipes.

| # | Notebook | What it does | Saves (in `data/`) |
|---|---|---|---|
| 04 | [Ingredient knowledge](04_ingredient_knowledge.ipynb) | Names in other languages (Wikidata), substitutions, pairings, shelf life (FoodKeeper) | `processed/ingredient_names/substitutions/pairings/shelf_life.parquet` |
| 06 | [Dish variants](06_dish_variants.ipynb) | Halal, vegan, gluten-free ... version of each dish. Needs 04 (substitutions) | `processed/recipe_variants.parquet`, `recipe_variants_summary.csv` |
| 08 | [Climate and season](08_climate_and_season.ipynb) | Meat: when each meat is most plentiful and when animals graze fresh grass, by region (built; first run downloads about 10 minutes of weather). Carbon footprint and produce seasons: planned | `processed/meat_supply_seasons.csv`, `pasture_seasons.csv` |
| 11 | [Dish knowledge](11_dish_knowledge.ipynb) | The waiter's knowledge notebook (0.6.3): dishes of the countries and regions the app shows, collected from Wikipedia lists, intros and story sections and Wikidata (`scripts/knowledge/fetch_knowledge.py`); fun facts tidied and sorted by topic, with "more fun facts" and learn-more links; nothing invented, sources and licences per dish | `knowledge/dishes.jsonl`, `knowledge/dishes/` |

### 3. Places

Where to find the food.

| # | Notebook | What it does | Saves (in `data/`) |
|---|---|---|---|
| 03 | [Stores and products](03_stores_and_products.ipynb) | Houston stores (OpenStreetMap; Google Places with a key), products by country (Open Food Facts) | `processed/places.parquet`, `products_by_country.parquet`, `ingredient_products.parquet`, `region_coverage_stores.csv` |

### 4. Models and checks

The models, and the checks that say whether the app can be trusted.

| # | Notebook | What it does | Saves (in `data/`) |
|---|---|---|---|
| 05 | [Computer vision: freshness](05_computer_vision_freshness.ipynb) | Indexes 45k fruit, meat and fish photos; near-duplicates, licenses, leak-free split; training (needs a GPU: use Colab, which saves results to Google Drive and resumes after a disconnect; section 7 zips the results to share) | `processed/freshness_images.parquet`, `freshness_coverage.csv` |
| 09 | [Agent evaluation](09_agent_evaluation.ipynb) | The same 33 questions (5 profiles, 13 attacks) for every local model, scored by code: leaks, right tool, right calories, attacks pushed back; each run compared with the last. VS Code / Antigravity only (needs Ollama) | `processed/agent_eval/agent_eval_<date>.csv` |
| 12 | [Safety engine check](12_safety_engine_check.ipynb) | Runs Check my recipe's engine on 10,000 test recipes for four sample profiles: results by level and by confidence (verified, likely, possible, unknown), the most common may-contain foods, unknown products and preparation risks, agreement with the stored flags by source (Food.com: 0 missed), and a hand-check sample for the team. Needs 01 | `processed/safety_engine_report.csv`, `processed/safety_engine_handcheck.csv` |
| 13 | [Food Taxonomy and map coverage](13_taxonomy_and_map_coverage.ipynb) | Recipes per branch of the Food Taxonomy, recipe countries and regions the tree lacks (run 2026-11-17: 38 found and added, now 0), and for each country its recipes and the map's places with that cuisine; the thin spots (Indonesia and Egypt: 200+ recipes, no places in the pilot area). Needs 01 and 03 | `processed/taxonomy_map_coverage.csv` |
| 14 | [Cooking yields and nutrient retention](14_cooking_yields_and_retention.ipynb) | Two USDA tables (CC0): raw to cooked weight with water and fat change for 173 cuts of meat and poultry, and how much of 26 nutrients is kept for 270 foods and preparations, each in the project's cooking-method names; method profiles built from both. Safe cooking temperatures (USDA FSIS) wait for the saved chart | `processed/cooking_yields.json`, `processed/nutrient_retention.json`, `processed/cooking_method_profiles.json`, `processed/knowledge_assets.json` (the list of knowledge files) |
| 15 | [Dish families and variants](15_dish_families_and_variants.ipynb) | Which dishes belong together, from Wikidata (CC0) "subclass of": run 2026-11-19, 564 families, 39 categories by main ingredient (chicken dish, rice dish) and 49 groupings by how or when a food is made (fried food, Christmas dessert), all filed under food or dish on Wikidata; 2,634 of our dishes in a family; 5,220 members with an English Wikipedia article that EverFlavor does not have yet, listed as gaps; a hand check (biryani, dumpling, taco, curry, pasta, flatbread). Needs 11 | `knowledge/dish_families.json` (committed, read by the app), an entry in `processed/knowledge_assets.json` |

## Run times

Measured on a laptop CPU with the downloads already saved (October 2026); each notebook also shows its own
at the top. Colab's free runtime takes about as long, or a little longer. First-run download times are estimates.

| # | Re-run | First run adds | Slowest part |
|---|---|---|---|
| 01 | about 30-45 min | 10-30 min of downloads | 5.5.2, the pipeline on every source (about 15 min) |
| 02 | about 2 min | little (reuses 01's Food.com download) | Section 3, cooking methods |
| 03 | about 2 min | 30-60 min (Open Food Facts export, OpenStreetMap) | Section 5, linking ingredients to products |
| 04 | under 1 min | 10-30 min (Wikidata, FoodKeeper) | Section 3 |
| 05 | about 25 min the first time, then about 2 min (saved hashes) | hours (photos: several GB, about 32 GB with MeatScan); training 1-3 h on a GPU | Section 4, perceptual hashes of 45,000 photos (about 23 min, once) |
| 06 | about 6 min | nothing (needs 01 and 04) | Section 3, variants for every dish |
| 07 | under 1 min | nothing (uses 01's USDA files) | Section 6, calorie calculator check |
| 08 | about 2 min | 10-12 min (10 years of weather for 11 regions) | Section 3b |
| 09 | about 30 min (two small models) | pulling the models (`ollama pull`, a few GB) | Section 4, the questions (10-50 s each) |
| 10 | a few minutes for the links; a few hours for all the photos (off by default) | the recipes file from Kaggle (part of 1.55 GB) | Section 4, the photo download |
| 11 | seconds (uses the collected file) | about 2 hours to recollect with `COLLECT` (cached after) | Section 2 |
| 12 | about 5 minutes (10,000 recipes, four profiles) | nothing (needs 01) | Section 3, the checks |
| 13 | under 10 seconds | nothing (needs 01 and 03) | Section 2 |
| 14 | under a minute | about 0.5 MB from data.gov, once | Section 3, the retention profiles |
| 15 | seconds (saved Wikidata answers) | a few minutes of Wikidata queries, once (cached in `data/raw/dish_families/`) | Section 4, the missing members |

All of them on a fresh computer: plan for an afternoon (most of it notebook 05's photos); re-running all of
them takes about an hour.

## When the rules change

The saved tables hold the flags and nutrition of the day notebook 01 ran. Notebook 01 saves a fingerprint of
the rules in `dataset_info.json`; when the code's rules differ, the agents warn ("Saved recipes are out of
date") and `tests/test_real_data.py` fails with what to do. Safety never depends on it: the tools check
every recipe with the current rules before showing it.

| What changed | What to run | Time |
|---|---|---|
| Flag words, diet rules (`flags.py`, `diets.py`) | `python -m everflavor.refresh` from the project folder, with `src` on the path (PowerShell: `$env:PYTHONPATH="src"`), then notebooks 02, 04 and 06 | about 20-25 minutes, then about 10 |
| Ingredient names, USDA matches (`ingredients.py`, `nutrition.py`) | Notebook 01, then 02, 03, 04, 06 and 07 | about 1 hour |
| Not sure | `python -m everflavor.refresh`: it says which | seconds |

When the logic itself changes (not only the word lists), raise `FLAG_LOGIC_VERSION` or
`PIPELINE_LOGIC_VERSION` in `refresh.py` so the fingerprint notices.

## Good to know

- **Keys:** only notebook 01 needs one (`USDA_API_KEY`); Google Places (03) is optional. Keys come from Colab
  Secrets or `config/.env`, never from the notebook. See [config](../config/README.md).
- **Re-running is cheap:** downloads already on disk are reused; only what is missing is fetched.
- **Big download:** notebook 05's photos are about 32 GB. MeatScan is opt-in (`DOWNLOAD_MEATSCAN`).
- **Shared code in Colab:** each notebook downloads the files listed in `EVERFLAVOR_MODULES`. When you add a
  module to `src/everflavor`, add it to that list in every notebook (a test checks this).
- **GPU for notebook 05's training:** open it in Colab with the badge at its top, Runtime > Change runtime type >
  T4 GPU, allow Google Drive, then `TRAIN = True`. Results (the duplicate check, each finished model, scores) go
  to `MyDrive/EverFlavor/freshness_results/`, so running all again after a disconnect continues where it stopped;
  section 7 zips them to share. Kaggle Notebooks are a free alternative with more GPU hours.
- **AI agents:** `llm.py`, `agent_tools.py` and `crew.py` run in VS Code / Antigravity. Only notebook 09 uses
  them, and in Colab it says so and stops, so Colab is never affected.
- **Before you push:** clear large outputs and run the checks in the [main README](../README.md#using-the-shared-code).
