# Model Card: Country-of-Origin Model

Built in section 5.9 of `notebooks/01_data_acquisition_EverFlavor_V3.ipynb`. The model lives only in the notebook session (it is not saved to `models/`); running the notebook rebuilds it and writes its predictions into the recipe table.

## What it does

Predicts the country a recipe comes from (`origin_country`) for recipes whose source does not name one country. Section 5.4.6 first maps the sources' own labels ("italian", "Italy", "iranian-persian") to countries; this model fills in the rest when it is confident enough. Every recipe gets `origin_source`: `labeled`, `predicted` or `unknown`. Regions (`origin_region`) are never predicted.

## Model

- **Features:** TF-IDF of the ingredient names and of the title words (single words and pairs).
- **Classifier:** multinomial `LogisticRegression` (C = 4), over the **37 countries** with at least 100 labeled training recipes.
- **Cuisine-family rule:** countries from a different cuisine family than the recipe's are ruled out (an "Asian" recipe is never predicted as Italian); recipes in "Other" can get any country.
- **Confidence threshold:** a prediction is kept only when the model is at least **70%** confident; otherwise the country stays `Unknown`.
- **Training data:** 83,911 training-split recipes with a labeled country. Fitted on the training split only.

## Results (validation split, 18,167 recipes with a labeled country)

- **Top guess, no threshold:** right 80.8% of the time.
- **At the 70% threshold:** 74.9% of recipes get a country, and it is right **89.6%** of the time.

| Confidence at least | Recipes kept | Correct |
|---|---|---|
| 0.5 | 89% | 85.5% |
| 0.6 | 82% | 87.8% |
| **0.7 (used)** | **75%** | **89.6%** |
| 0.8 | 65% | 91.2% |
| 0.9 | 51% | 93.2% |

By predicted country at 70%: United States 95% right, Spain 97%, Morocco 95%, Greece 92%, Thailand 92%, India 91%, Japan 91%, Italy 87%, China 87%, United Kingdom 84%, Canada 84%, France 81%, Mexico 77%.

**In the full table:** 121,456 recipes labeled by their source, 108,559 predicted, 61,756 `Unknown`.

## Limitations

- **The United States dominates** (about 46% of labeled recipes), so the overall accuracy flatters the model; smaller countries are less reliable, and countries with fewer than 100 labeled recipes are never predicted.
- **Neighboring cuisines are confused** (Mexico vs United States for Tex-Mex dishes, France vs Italy).
- **Labels reflect the recipe sites,** often a US view of each cuisine.
- **A wrong country can be hurtful.** Show predicted countries as "probably ...", and prefer `labeled` recipes when authenticity matters (see `ethics_privacy.md`).

## How to use it

- Filter on `origin_source == "labeled"` for authentic-dish searches; include `predicted` for broader browsing.
- `origin_confidence` (0.7 to 1) can rank predicted recipes.

## Ideas for Week 7

- Add more labeled recipes for under-represented countries (RecipeDB covers 74 countries).
- Calibrate the confidence per country instead of one global threshold.
- Try text embeddings, and predict regions where enough labeled examples exist.
