# Data Dictionary

Columns of the processed recipe table: `data/interim/recipes_all.parquet` (all recipes) and `data/processed/recipes_{train,val,test}.parquet` (the splits). One row per recipe; 291,771 rows in the last run. See `datasheet.md` for how the table was built and its limitations.

## Identity and source

| Column | Type | Description |
|---|---|---|
| `recipe_id` | text | Unique ID. Source prefix plus the source's own ID. |
| `source` | text | `foodcom`, `huggingface`, `culinarydb` or `themealdb`. |
| `recipe_name` | text | Recipe title. |
| `url` | text | Link to the original recipe, where the source has one. |
| `instructions` | text | Cooking steps (Food.com and TheMealDB only; missing elsewhere). |

## Cuisine

| Column | Type | Description |
|---|---|---|
| `cuisine_family` | text | One of `Asian`, `European`, `Latin American`, `African`, `Middle Eastern`, or `Other` (no usable label). |
| `cuisine_raw` | text | The source's own cuisine or region label before mapping (for example `french`), where there is one. |
| `cuisine_labeled` | true/false | True when `cuisine_family` is not `Other`. Lets models treat `Other` as unlabeled. |

## Origin

| Column | Type | Description |
|---|---|---|
| `origin_country` | text | Country the dish comes from (for example `Iran`, `Morocco`, `United States`). `Unknown` when neither the source nor the model can say. Never empty. |
| `origin_region` | text | Region within the country, only when the source names it (for example `Sichuan`, `Louisiana`, `Quebec`, `Oaxaca`, `Scotland`). Empty otherwise; never predicted. |
| `origin_source` | text | `labeled` (the source names the country, section 5.4.6), `predicted` (a model guessed it, section 5.9) or `unknown`. |
| `origin_confidence` | number | For `predicted` countries, the model's confidence (0.7 to 1). Empty otherwise. Treat predicted countries as a good guess, not a fact. |

## Ingredients

| Column | Type | Description |
|---|---|---|
| `ingredient_list` | list of text | Normalized ingredient names: lowercase, singular, quantities, units and preparation words removed, synonyms merged (section 5.4.4). |
| `complexity` | integer | Number of unique ingredients (at least 2). |
| `ingredient_group` | text | Recipes with exactly the same ingredients share a group, so near-duplicates stay in one split. |

## Nutrition (per serving)

| Column | Type | Unit | Description |
|---|---|---|---|
| `calories_per_serving` | number | kcal | Listed value, or an estimate where `nutrition_source` is `estimated`. Never missing. |
| `protein_g` | number | g | Exact for Hugging Face; converted from % daily value for Food.com; estimated otherwise. |
| `fat_g` | number | g | Same as above. |
| `carbs_g` | number | g | Same as above. |
| `sodium_mg` | number | mg | Same as above. |
| `servings` | number | servings | Hugging Face only (1 to 50). |
| `minutes` | number | minutes | Cook time, where the source gives one (at most 24 hours). |
| `has_nutrition` | true/false | | The source listed calories. |
| `nutrition_plausible` | true/false | | The listed values passed every check: at least 10 kcal, at most 5,000 mg sodium and 150 g protein, macros within 30% of the calories. |
| `nutrition_source` | text | | `listed` (real, plausible values) or `estimated` (section 5.8). |
| `calories_est_min` | number | kcal | Low end of an estimate's likely range (8 in 10 real values fall inside). Empty for listed values. |
| `calories_est_max` | number | kcal | High end of that range. Empty for listed values. |
| `usda_dish` | text | | Closest USDA FNDDS dish by title (a reference, not the recipe itself). Empty when nothing matched. |
| `usda_dish_kcal` | number | kcal | That USDA dish's calories per typical serving. |

## Restriction flags (true/false)

Derived from keywords in the ingredients and the recipe name, plus Hugging Face health labels where they exist (section 5.4.2), plus the hidden allergens of ready-made ingredients such as "ranch dressing" (`COMPOUND_INGREDIENTS`, checked against Open Food Facts in section 5.13). They are a first filter, not a guarantee: the system's safety filter re-checks every recipe. Measured accuracy is in `flag_review/labeling_notes.md`; the definitions that are a matter of policy (oats, gelatin, plain "nut", red meat ...) are in `flag_review/flag_policies.csv`.

| Column | True when the recipe... |
|---|---|
| `contains_pork` | contains pork (bacon, ham, jamón, prosciutto, sausage...) |
| `contains_alcohol` | contains alcohol (wine, beer, spirits, liqueur, mirin, sake...) |
| `contains_gluten` | contains wheat, barley or rye, or oats not labeled gluten-free (team policy P1) |
| `contains_dairy` | contains milk or milk products |
| `contains_egg` | contains egg |
| `contains_peanut` | contains peanut |
| `contains_tree_nut` | contains tree nuts (almond, walnut, pecan, cashew...) |
| `contains_fish` | contains fish (including fish sauce) |
| `contains_shellfish` | contains shellfish |
| `contains_soy` | contains soy |
| `contains_sesame` | contains sesame |
| `vegetarian` | contains no meat, poultry, fish or shellfish |
| `vegan` | is vegetarian and contains no dairy, egg or honey |
| `contains_meat` | contains meat or poultry (fish does not count) |
| `contains_beef` | contains beef or veal |
| `contains_red_meat` | contains red meat: meat from mammals, pork, lamb, goat, venison and organ meat included (USDA, WHO / IARC) |
| `contains_poultry` | contains poultry ("white meat": chicken, turkey, duck, goose...). Fish and shellfish are their own flags, not white meat |
| `contains_processed_meat` | contains processed meat: cured, salted, smoked or fermented (bacon, ham, sausage, salami, jerky, hot dogs), poultry products included (WHO / IARC) |
| `contains_gelatin` | contains gelatin (also marshmallows, gummies, aspic) |
| `contains_honey` | contains honey |
| `contains_root_vegetable` | contains vegetables that grow underground (potato, carrot, beet, radish, fresh ginger...) |
| `contains_allium` | contains onion, garlic, leek, shallot, scallion or chive |

## Diet profiles (true/false)

Rules over the flags above, defined once in `DIET_PROFILES` (section 5.4.7). "-friendly" means the ingredients contain nothing the diet forbids; it never means certified (slaughter method and certification cannot be seen in an ingredient list).

| Column | True when the recipe has no... |
|---|---|
| `halal_friendly` | pork, alcohol or gelatin |
| `kosher_friendly` | pork, shellfish or gelatin, and does not combine meat with dairy |
| `pescatarian` | meat or poultry (fish allowed) |
| `no_beef` | beef or gelatin |
| `jain_friendly` | meat, fish, egg, honey, alcohol, root vegetables, onion or garlic |
| `lower_sodium` | more than 600 mg sodium per serving; listed nutrition only |
| `low_carb` | more than 15 g carbohydrate per serving; listed nutrition only |

## Split

| Column | Type | Description |
|---|---|---|
| `split` | text | `train` (70%), `val` (15%) or `test` (15%), by ingredient group, stratified by cuisine family. |

## Other files

| File | Contents |
|---|---|
| `data/processed/usda_ingredient_nutrition.csv` | One row per matched ingredient name: `ingredient`, `recipes` (how many use it), `match` (`hand-checked` or `automatic`), `fdc_id`, `usda_description`, and per 100 g: `kcal_100g`, `protein_100g`, `fat_100g`, `carbs_100g`, `sodium_mg_100g`. |
| `data/processed/dataset_info.json` | Run record: date, library and source versions, settings, row counts, nutrition estimate and country model accuracy, diet counts. |
