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

## Results (validation split, 18,136 recipes with a labeled country)

- **Top guess, no threshold:** right 81.0% of the time.
- **At the 70% threshold:** 75.7% of recipes get a country, and it is right **89.4%** of the time.

| Confidence at least | Recipes kept | Correct |
|---|---|---|
| 0.5 | 90% | 85.4% |
| 0.6 | 83% | 87.6% |
| **0.7 (used)** | **76%** | **89.4%** |
| 0.8 | 66% | 91.3% |
| 0.9 | 51% | 93.3% |

By predicted country at 70%: United States 95% right, Morocco 92%, India 91%, Greece 90%, Spain 90%, Thailand 89%, Italy 87%, Japan 87%, China 84%, Canada 83%, United Kingdom 82%, France 81%, Mexico 79%.

By real country at 70% (share of its validation recipes given the right country): Mexico 99%, Morocco 95%, India
88%, Italy 84%, Thailand 84%, China 82%, Greece 74%, Japan 72%, United States 68%, Spain 60%, France 57%, Germany 51%,
United Kingdom 47%, Australia 17%, Canada 8%. Canadian and Australian recipes look American or British, so they are
rarely recognized.

**Weighting tested, not used (2026-10-10):** giving smaller countries more weight (`balanced_weights`, capped at 2, 3
or 10 times an average recipe) dropped the top-guess accuracy from 81% to about 70%, the recipes given a country from
76% to 55%, and the United States recipes found from 68% to about 20% (most were labeled Mexican, Italian or French
instead): more wrong countries, which the limitations below warn are hurtful.

**In the full table:** 121,450 recipes labeled by their source, 109,051 predicted, 61,254 `Unknown`.

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
- Add Canadian and Australian recipes (or merge them with United States / United Kingdom), since the model cannot
  tell them apart today.
- Try text embeddings, and predict regions where enough labeled examples exist.
