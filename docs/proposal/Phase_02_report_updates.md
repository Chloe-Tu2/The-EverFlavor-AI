# Phase 02 Report: Suggested Updates

The Phase 02 report (`Phase_02_EverGlow_ITAI_2277.pdf`) was written before several pipeline changes. The paragraphs below match the current notebook and can be pasted into the report. Section numbers refer to the report.

## 2.1 Identified Data Sources: add TheMealDB

**TheMealDB** (https://www.themealdb.com) — a free public recipe API with full instructions and the country of each dish. We collected about 790 recipes through its search endpoint, with paced requests; 583 remain after removing duplicates of recipes from the other sources. It adds dishes from countries the other sources rarely cover (for example Cambodia, Algeria, Jamaica).

## 2.2 Data Collection Methods: replace the CulinaryDB/RecipeDB bullet, add USDA bulk data

- **CulinaryDB:** downloaded from the official CoSyLab zip (35,328 recipes kept after cleaning). RecipeDB remains optional.
- **TheMealDB:** collected through its public API (test key), 36 paced requests.
- **USDA bulk downloads:** besides the API sample, the free FNDDS (2024-10-31) and SR Legacy (2018-04) downloads, which need no key, provide official nutrition for about 5,400 prepared dishes and 7,800 ingredients.

## 2.5 Initial Data Documentation: files now present

`docs/sources.md`, `docs/data_dictionary.md` and `docs/ethics_privacy.md` exist as described, together with `docs/datasheet.md` and model cards for the three models (`model_card.md`, `model_card_nutrition.md`, `model_card_origin.md`).

## 3.1 Data Cleaning: replace the last two sentences

Recipes whose listed nutrition failed the checks are marked, not removed. Missing or unbelievable nutrition (46,308 recipes) is then estimated from similar recipes and official USDA data (USDA FNDDS dishes matched by title and SR Legacy ingredients). Estimates are labeled `estimated`, carry a likely calorie range, and name the closest USDA dish. On validation recipes with real values, the average error is 186 kcal per serving, compared with 230 kcal for guessing the median; the likely range contains the real value 79% of the time.

## 3.2 Feature Engineering: add three items

6. **Country and region of origin.** Source labels that name one country are mapped to it (121,456 recipes); a region is kept only when the source names it (14,770 recipes, for example Sichuan, Louisiana, Quebec). For the rest, a logistic regression on title and ingredient words predicts the country when it is at least 70% confident (108,559 recipes; right about 90% of the time on validation). Every recipe records whether its country is labeled, predicted or unknown.
7. **More restriction flags.** Beyond pork, alcohol, gluten, dairy, egg, vegetarian and vegan, the flags now cover peanut, tree nut, fish, shellfish, soy and sesame, plus meat, beef, gelatin, honey, root vegetables and onion/garlic. They read the recipe name as well as the ingredients.
8. **Diet profiles.** Halal-friendly, kosher-friendly, Jain-friendly, pescatarian, no beef, lower sodium (at most 600 mg per serving) and low carb (at most 15 g per serving), defined once as rules over the flags and shared by the data, the validation checks and the safety filter. "Friendly" means no forbidden ingredients, not certified.

## 3.4 Train / Validation / Test Splitting: replace the first sentence

The cleaned recipe set was split 70/15/15 by **ingredient group**: recipes with exactly the same ingredients always land in the same split, so near-duplicates cannot leak from training into testing. Groups are stratified by cuisine family. A check confirms that no group appears in two splits, and the random seed (42) is recorded in `dataset_info.json`.

## 4.1 Statistical Analysis: add one finding

Recipes with more ingredients have more calories per serving (median about 200 kcal with 3 ingredients, about 500 kcal with 20; rank correlation +0.24), while their ingredients are on average slightly less energy-dense (−0.14): longer recipes are fuller dishes, not richer ones.

## 4.2 Pattern Identification: update item 1

1. Cuisine coverage is uneven. After combining all sources, the table holds 291,771 recipes: European 48,151, Asian 20,788, Latin American 15,706, Middle Eastern 3,406 and African 3,179, with the rest unlabeled. CulinaryDB, Food.com's cuisine tags and TheMealDB now supply African recipes, which the Hugging Face data alone lacked.

## 4.3 Baseline Model Creation: add evaluation results

Two baselines were evaluated:
- the **rule-based recommender** (filters, calorie ranking and a final safety filter that re-checks ingredients and names, now also for diet profiles such as halal-friendly);
- a **cuisine classifier** (logistic regression on ingredients, leak-free pipeline): macro-F1 0.62 and accuracy 0.77 on the validation split. African and Middle Eastern are the hardest families (F1 about 0.35 each).

## New: Restriction Flag Accuracy

Blind samples of 200 recipes (50 per source) were labeled independently of the flags. Round 1 showed that gluten was caught in only 81% of the recipes containing it, because wheat is often hidden in product names (crackers, pastry, spaghetti, buns). After extending the keyword lists, a fresh round 2 sample measured gluten at 96% recall and 97% precision; dairy, egg, pork, alcohol, fish and tree nuts were 98–100%, while the rarer peanut, shellfish, soy and sesame (5–11 cases each) were 67–91%. The labels were produced by an AI assistant and are marked for spot-checking by the team.

## 5. Preprocessed Dataset Deliverable: replace the first bullet

- Cleaned recipe table (291,771 recipes) with engineered features: cuisine family, country and region of origin, 19 restriction flags, 7 diet profiles, nutrition per serving (listed or estimated, with provenance), cleaned ingredient lists and complexity. 21 automatic validation checks pass before the data is saved.
