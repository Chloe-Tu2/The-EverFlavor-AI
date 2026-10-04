# Model Card: Missing-Nutrition Estimator

Built in section 5.8 of `notebooks/01_data_acquisition_EverFlavor_V3.ipynb`. The models live only in the notebook session (they are not saved to `models/`); running the notebook rebuilds them and writes their estimates into the recipe table.

## What it does

Estimates calories, protein, fat, carbs and sodium per serving for the 46,308 recipes that have no listed, believable nutrition: all of CulinaryDB and TheMealDB, plus Food.com and Hugging Face recipes whose listed values failed the plausibility checks. Every estimate is labeled `nutrition_source = "estimated"` and comes with a likely calorie range.

## Model

1. **Ridge regression** on the words of the title and the ingredient names (TF-IDF), predicting the logarithm of calories per serving.
2. **Gradient-boosted trees** (`HistGradientBoostingRegressor`, absolute error) combining the ridge prediction with official USDA evidence:
   - the calories per typical serving of the 5 closest **USDA FNDDS** dishes (matched by title, weighted by similarity);
   - the energy density (kcal per 100 g) of the recipe's ingredients from **USDA SR Legacy**;
   - the number of ingredients.
3. **Macros:** one ridge model each for protein, fat, carbs and sodium; protein, fat and carbs are then scaled so they add up to the estimated calories (4, 9 and 4 kcal per gram).
4. **Likely range:** the 10th to 90th percentile of the errors on half of the validation recipes: estimate × 0.47 to estimate × 2.11.

- **Training data:** 171,719 training-split recipes with listed, plausible nutrition.
- **Leakage:** fitted on the training split only; the ridge predictions fed to the second model come from 5-fold cross-validation.
- **USDA data:** free bulk downloads (FNDDS 2024-10-31, SR Legacy 2018-04), no API key; see `sources.md`.

## Results (validation recipes with real calories, half not used for the range)

| Method | Average error (kcal) | Typical error (kcal) | Within 20% |
|---|---|---|---|
| Guess the median | 230 | 152 | 21% |
| Closest USDA dishes only | 256 | 154 | 17% |
| Similar recipes (title + ingredients) | 189 | 106 | 29% |
| **Similar recipes + USDA (used)** | **186** | **104** | **29%** |

- The real value is inside the likely range 79% of the time (target 80%), and 76-80% in every cuisine family.
- Typical macro errors: protein 3.7 g, fat 5.5 g, carbs 10.5 g, sodium 163 mg.

## Limitations

- **Portion size is unknown.** CulinaryDB lists no amounts or servings, so no method can compute exact calories; this is why errors stay large.
- **Estimates pull toward the middle.** The model aims at the typical recipe, so very light or very rich dishes are under- or over-estimated, and estimated averages run lower than listed ones.
- **USDA adds little here** (about 1%), because a USDA "typical serving" and a recipe author's serving are different things.
- **Not for medical use.** Diet profiles that depend on nutrition (`lower_sodium`, `low_carb`) never count estimated values.

## How to use the estimates

- Prefer recipes with `nutrition_source = "listed"` when calories matter (the baseline recommender in 6.3 does).
- Show estimates as a range: "about 330 kcal (likely 155-700)", using `calories_est_min` and `calories_est_max`.
- `usda_dish` and `usda_dish_kcal` give an official reference to show next to the estimate.

## Ideas for Week 7

- Parse TheMealDB's ingredient amounts ("800g", "2 tbsp") with USDA values for those 583 recipes.
- Predict servings first, then calories per recipe.
- Try text embeddings instead of word counts.
