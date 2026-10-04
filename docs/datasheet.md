# Datasheet: EverFlavor AI Combined Recipe Dataset

This document follows the "Datasheets for Datasets" format. It describes the recipe table built by `notebooks/01_data_acquisition_EverFlavor_V3.ipynb` (sections 2.4 and 5.1–5.12). The notebook also writes the exact versions and counts of each run to `data/processed/dataset_info.json`.

## Motivation

- **Purpose:** to give the EverFlavor AI agents a clean recipe table. The Nutritionist Agent uses it for calorie targets and dietary restrictions, the Chef Agent for recipes, ingredients and cuisine, and the Sourcing Agent for specialty ingredients by cuisine.
- **Created by:** team EverGlow, ITAI 2277 capstone (Weeks 4–6).

## Composition

| | |
|---|---|
| Recipes | 291,771 (after cleaning and removing duplicates) |
| Sources | Food.com 218,034 · Hugging Face 37,826 · CulinaryDB 35,328 · TheMealDB 583 |
| Cuisine families | European 48,151 · Asian 20,788 · Latin American 15,706 · Middle Eastern 3,406 · African 3,179 · Other (no cuisine label) 200,541 |
| Splits | Train 204,112 · Validation 43,885 · Test 43,774 (70/15/15) |
| Nutrition | 255,860 recipes list calories (Food.com and Hugging Face) and 245,463 of them pass all plausibility checks (`nutrition_source` = `listed`). The other 46,308 are estimated (`estimated`), see Preprocessing. |

**Each recipe has:**

- `recipe_id`, `source`, `recipe_name`
- `cuisine_family` and `cuisine_raw`
- `ingredient_list` (normalized names) and `complexity` (number of unique ingredients)
- nutrition per serving: `calories_per_serving`, `protein_g`, `fat_g`, `carbs_g`, `sodium_mg`
- `servings`, `minutes`, `instructions`, `url`
- 13 restriction flags: `contains_pork`, `contains_alcohol`, `contains_gluten`, `contains_dairy`, `contains_egg`, `contains_peanut`, `contains_tree_nut`, `contains_fish`, `contains_shellfish`, `contains_soy`, `contains_sesame`, `vegetarian` and `vegan`
- quality columns: `has_nutrition`, `nutrition_plausible`, `cuisine_labeled`, `ingredient_group` and `split`
- origin: `origin_country` (`Unknown` if not known), `origin_region` (only when the source names it), `origin_source` (`labeled`, `predicted` or `unknown`) and `origin_confidence`
- diet profiles: `halal_friendly`, `kosher_friendly`, `pescatarian`, `no_beef`, `jain_friendly`, `lower_sodium`, `low_carb`, and their base flags `contains_meat`, `contains_beef`, `contains_red_meat`, `contains_poultry`, `contains_processed_meat`, `contains_gelatin`, `contains_honey`, `contains_root_vegetable`, `contains_allium`
- nutrition provenance: `nutrition_source` (`listed` or `estimated`), `calories_est_min` and `calories_est_max` (likely range of an estimate), `usda_dish` and `usda_dish_kcal` (closest USDA FNDDS dish and its calories per typical serving)

**What's missing:**

- **Listed nutrition:** CulinaryDB and TheMealDB publish none, and CulinaryDB lists no ingredient amounts or servings. Their values, and those of recipes whose listed values failed the plausibility checks, are estimates.
- **Grams for Food.com:** Food.com gives macros only as percent of daily value; they are converted to grams using the FDA reference values (65 g fat, 300 g carbs, 50 g protein, 2,400 mg sodium). The converted grams match the listed calories within about 2% for a typical recipe.
- **Instructions:** Hugging Face and CulinaryDB recipes have no instructions.

**No personal data:** the table has none. Food.com user IDs are not used.

## Collection

| Source | How collected | Version |
|---|---|---|
| Food.com Recipes and Interactions (Kaggle) | `kagglehub` download | Dataset version 2 |
| Hugging Face `datahiveai/recipes-with-nutrition` | `datasets` library | Revision recorded in `dataset_info.json` |
| CulinaryDB (CoSyLab, IIIT-Delhi) | Official zip download | As downloaded (date recorded) |
| TheMealDB | Public API, test key, 36 requests with pauses | As collected (date recorded) |

No website was scraped directly.

## Preprocessing

| Step | What it does |
|---|---|
| Cleaning | Drops missing names, ingredients or nutrition. Drops duplicate titles within each source, cook times over 24 hours, Hugging Face recipes with 0 or more than 50 servings, and recipes over 3,000 kcal per serving. |
| Calories | Hugging Face calories are converted from whole-recipe totals to per serving. |
| Cuisine | One map converts Hugging Face labels, Food.com cuisine tags, CulinaryDB regions and TheMealDB countries into five families or "Other". |
| Restriction flags | Whole-word keyword matching with exception phrases (for example "coconut milk" is not dairy). For Hugging Face, the dataset's "X-Free" health labels are combined with the keywords. When the two disagree, a flag leans toward "contains". |
| Ingredients | Quantities, units, preparation words and notes are removed, then synonyms are merged and plurals made singular. |
| Combining | Recipes with the same title across sources are kept once, in this order of preference: Hugging Face, Food.com, TheMealDB, CulinaryDB. Recipes with fewer than 2 ingredients are dropped. |
| Nutrition quality | `nutrition_plausible` requires at least 10 kcal, at most 5,000 mg sodium, at most 150 g protein, and macros within 30% of the listed calories. Recipes that fail are marked, not removed. |
| Missing nutrition (5.8) | Recipes without listed, plausible nutrition get estimates. A ridge model on title and ingredient words, plus a gradient-boosted model that adds USDA evidence (closest FNDDS dishes' calories per typical serving, SR Legacy energy density of the ingredients), trained on the training split only. On validation recipes with real values: average error 186 kcal per serving vs 230 kcal for guessing the median; the 80% likely range (estimate × 0.47 to × 2.11) contains the real value 79% of the time. Protein, fat and carbs are scaled to add up to the estimated calories. |
| Country of origin (5.4.6, 5.9) | Source labels that name one country are mapped to it ("italian", "Italy" -> Italy); a region is kept only when the source names it. Broad labels ("asian", "caribbean") give no country. For the rest, a logistic regression on title and ingredient words (training split only, 37 countries with 100+ labeled recipes, restricted to the recipe's cuisine family) predicts a country when at least 70% confident: on validation recipes it is right 89.6% of the time and covers 75% of them. |
| Diet profiles (5.4.7) | Rules over the ingredient flags, defined once in `DIET_PROFILES`. "-friendly" means no forbidden ingredients, not certified. Nutrition-based diets (lower sodium: at most 600 mg; low carb: at most 15 g per serving) only count listed, plausible nutrition. |
| Split | Stratified by cuisine family. Recipes with exactly the same ingredients are kept in the same split, so there is no near-duplicate leakage. |
| Validation | 12 automatic checks, and the notebook stops if any fails. |

## Known limitations and biases

- **Uneven cuisine coverage.** 69% of recipes have no cuisine label, and African (1.1%) and Middle Eastern (1.2%) recipes are scarce. Most are American-site recipes, written for a US audience.
- **Approximate restriction flags.** On the latest fresh blind 200-recipe check (round 3, `docs/flag_review/`, section 5.12) they catch 96–100% of real cases for every flag, including the diet flags (meat, beef, gelatin, honey, root vegetables, onion and garlic), except shellfish (83%, 10 of 12). The rarer flags have fewer than 15 cases each in the sample. They agree with Food.com's own dietary tags 79–98% of the time, depending on the tag.
- **Ingredient names still vary.** About 46,000 unique names remain after normalizing.
- **Cuisine labels come from recipe authors and sites.** They are not checked for authenticity.

## Uses

- **Intended:** recipe recommendation, cuisine classification and restriction filtering for the EverFlavor AI prototype.
- **Not intended:** medical or allergy advice. The restriction flags must always be followed by the system's hard-coded safety filter.

## Licenses

| Source | Terms |
|---|---|
| CulinaryDB, RecipeDB | CC BY-NC-SA 3.0: non-commercial use, with credit |
| Open Food Facts | ODbL |
| USDA FoodData Central | Public domain |
| Food.com (Kaggle), Hugging Face, TheMealDB | See each source's page |

This dataset is used for a non-commercial student project.

## Maintenance

The dataset is rebuilt by running the notebook top to bottom. Generated files are not committed. `data/processed/dataset_info.json` records the versions and settings of each run.
