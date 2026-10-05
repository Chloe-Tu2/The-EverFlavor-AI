# Data Sources

Every dataset the pipeline uses, with its license and how it is accessed. The notebook (`notebooks/01_data_acquisition_EverFlavor_V3.ipynb`) downloads all of them; the exact versions of each run are recorded in `data/processed/dataset_info.json`.

**Access date:** 2026-10-03 (the last full run). Re-running the notebook updates the record.

## Recipe datasets

| Source | URL | License | Access method | Version / notes | Notebook |
|---|---|---|---|---|---|
| Food.com Recipes and User Interactions (Kaggle) | <https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions> | See the dataset page (research use) | `kagglehub` download | Dataset version 2 | 2.4.2 |
| Hugging Face: recipes-with-nutrition | <https://huggingface.co/datasets/datahiveai/recipes-with-nutrition> | See the dataset page | `datasets.load_dataset` | Revision `33ff70ba3dc1a1a77395fc477934b4ffb18a347d` | 2.4.3 |
| CulinaryDB (Complex Systems Lab, IIIT-Delhi) | <https://cosylab.iiitd.edu.in/culinarydb/> | CC BY-NC-SA 3.0 (non-commercial, with credit) | Official zip download | `CulinaryDB.zip` as downloaded | 2.4.5 |
| TheMealDB | <https://www.themealdb.com> | See the site's terms | Public JSON API (free test key `1`), paced requests | As collected | 2.4.6 |

## Nutrition and product data

| Source | URL | License | Access method | Version / notes | Notebook |
|---|---|---|---|---|---|
| USDA FoodData Central API | <https://fdc.nal.usda.gov/api-guide.html> | Public domain (U.S. government) | REST API with a free key (`USDA_API_KEY`) | Live API | 2.4.1 |
| USDA FNDDS (survey foods), bulk download | <https://fdc.nal.usda.gov/download-datasets> | Public domain | Zip download, no key | Release 2024-10-31 | 5.8.1 |
| USDA SR Legacy, bulk download | <https://fdc.nal.usda.gov/download-datasets> | Public domain | Zip download, no key | Release 2018-04 (final) | 5.8.1 |
| Open Food Facts | <https://world.openfoodfacts.org> | Open Database License (ODbL) | Public API, no key, rate-limited, with a descriptive User-Agent | Live API | 2.4.4 |

## Ingredient knowledge (notebook 04)

| Source | URL | License | Access method | Version / notes | Notebook |
|---|---|---|---|---|---|
| Wikidata | <https://query.wikidata.org> | CC0 | SPARQL query service, no key; batches of 40 names, a descriptive User-Agent, every answer cached | Live, queried 2026-10-04 | 04, section 2 |
| Food.com reviews (`RAW_interactions.csv`) | <https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions> | See the dataset page (research use) | Same `kagglehub` download as the recipes | Dataset version 2 | 04, section 3 |
| USDA FoodKeeper (FSIS) | <https://catalog.data.gov/dataset/fsis-foodkeeper-data> | CC0 (public domain) | JSON download, no key; USDA's server refuses some networks (HTTP 403), so the Internet Archive's copy of the same file is used then | Archive snapshot of 2025-07-02 | 04, section 5 |

## Planned or optional

| Source | URL | License | Access method | Status |
|---|---|---|---|---|
| RecipeDB (CoSyLab) | <https://cosylab.iiitd.edu.in/recipedb/> | CC BY-NC-SA 3.0 | API key from the CoSyLab team | Optional, not used yet (2.4.7) |
| Google Places API | <https://developers.google.com/maps/documentation/places/web-service> | Google Maps Platform terms | API key | Planned for the Sourcing Agent (2.4.8) |

No website is scraped directly, and nothing behind a login is collected.
