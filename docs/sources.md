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

## Stores and products (notebook 03)

| Source | URL | License | Access method | Version / notes | Notebook |
|---|---|---|---|---|---|
| OpenStreetMap (Overpass API) | <https://www.openstreetmap.org/copyright> | ODbL (credit "(c) OpenStreetMap contributors") | Overpass API, no key; public servers tried in turn, every answer cached | Live, queried 2026-10-04 | 03, section 3 |
| Open Food Facts product export | <https://huggingface.co/datasets/openfoodfacts/product-database> | ODbL | `food.parquet` (7.9 GB): only the needed columns, a spread sample of 1,000 row groups (1,020,381 products) read over the network, or the whole file once downloaded | Read 2026-10-05 | 03, section 4 |
| Google Places API (New) | <https://developers.google.com/maps/documentation/places/web-service> | Google Maps Platform terms (only place IDs are stored) | API key in a request header (`GOOGLE_PLACES_API_KEY`); skipped without it | Not used yet (no key) | 03, section 2 |

## Food freshness images (notebook 05)

| Source | URL | License | Access method | Version / notes | Notebook |
|---|---|---|---|---|---|
| BananaImageBD | <https://doi.org/10.17632/ptfscwtnyz.2> | CC BY 4.0 (read from the dataset record) | Mendeley Data public API, no key; original photos only | Version 2, ripeness set (820 photos) | 05, section 2 |
| AgriFreshNET | <https://doi.org/10.17632/42m5tb7yv9> | CC BY 4.0 (read from the dataset record) | Mendeley Data public API; the dataset's own augmented copies skipped | 5,217 original photos, 8 items, fresh / semi-fresh / rotten | 05, section 2 |
| FruitNet | <https://doi.org/10.17632/b6fftwbr2v> | CC BY 4.0 (read from the dataset record) | Mendeley Data public API (the .zip; the same photos as .rar skipped) | 19,526 photos, 7 fruits, good / bad / mixed (mixed left unlabeled) | 05, section 2 |
| Multistage Fish Eyes | <https://doi.org/10.17632/67nmx3mhwh> | CC BY 4.0 (read from the dataset record) | Mendeley Data public API | 4,800 eye photos; "Highly Fresh" / "Fresh" / "Not Fresh" read as fresh / aging / spoiled (team rule) | 05, section 2 |
| Freshness of the Fish Eyes | <https://doi.org/10.17632/xzyx7pbr3w> | CC BY 4.0 (read from the dataset record) | Mendeley Data; loose photos, each saved in its Mendeley folder ("Chanos Chanos - Fresh") so the label stays readable | 4,390 eye photos, 8 species (read as milkfish, tilapia, mackerel, goatfish, croaker, threadfin), "Highly Fresh" / "Fresh" / "Not Fresh" read as fresh / aging / spoiled, as for Multistage Fish Eyes | 05, section 2 |
| DaFiF | <https://doi.org/10.17632/vx4ptwk3pb> | CC BY 4.0 (read from the dataset record) | Mendeley Data; labels in a separate file | Not downloaded yet (needs a label reader) | 05, section 2 |
| MeatScan | <https://zenodo.org/records/16764338> | CC BY 4.0 (read from the Zenodo record) | Zenodo API, one 25 GB .rar unpacked with the system's extractor (Windows: its own tar.exe) | 10,561 beef photos, fresh / spoiled ("CowMeat" read as beef); 439 files of zero bytes in Spoiled_CowMeat are skipped. Opt-in in notebook 05 (`DOWNLOAD_MEATSCAN`): about 50 GB free while it unpacks | 05, section 2 |
| Roboflow meat and bread mold | See notebook 05, section 2 | To confirm on the data records | Needs a Roboflow account | Not downloaded | 05, section 2 |

## Climate and season (notebook 08, planned)

| Source | URL | License | Access method | Status |
|---|---|---|---|---|
| Our World in Data: GHG emissions per kg of food (Poore & Nemecek 2018) | <https://ourworldindata.org/grapher/ghg-per-kg-poore> | CC BY | CSV download, no key | Planned |
| AGRIBALYSE 3.2 (ADEME) | <https://doc.agribalyse.fr/documentation-en/agribalyse-data/data-access> | Etalab Open License (credit the source and date) | CSV download, no key | Planned |
| USDA SNAP-Ed Seasonal Produce Guide | <https://wicworks.fns.usda.gov/resources/snap-ed-seasonal-produce-guide> | Not stated: to confirm | Web pages | Candidate |

## Planned or optional

| Source | URL | License | Access method | Status |
|---|---|---|---|---|
| RecipeDB (CoSyLab) | <https://cosylab.iiitd.edu.in/recipedb/> | CC BY-NC-SA 3.0 | API key from the CoSyLab team | Optional, not used yet (2.4.7) |

No website is scraped directly, and nothing behind a login is collected.
