# Model Card: Baseline Cuisine Classifier

Built in section 6.6 of `notebooks/01_data_acquisition_EverFlavor_V3.ipynb` and saved to `models/cuisine_baseline.joblib`. That file is git-ignored; the notebook recreates it.

## What it does

The classifier predicts a recipe's cuisine family (African, Asian, European, Latin American or Middle Eastern) from its normalized ingredient list. It is a **baseline**: a reference point for Week 7 models and a test of the leak-free feature pipeline. It is not meant to go into the final product.

## Model

- **Pipeline:** a scikit-learn `Pipeline` with two steps:
  1. `CountVectorizer`: each normalized ingredient is one feature; ingredients in fewer than 5 training recipes are dropped, leaving a vocabulary of 4,624.
  2. `LogisticRegression` with `class_weight="balanced"`.
- **Training data:** 63,831 training-split recipes with a real cuisine label. "Other" is treated as unlabeled.
- **Leakage:** the vocabulary and weights are fitted on the training split only. Recipes with the same ingredients never appear in two splits.

## Results (validation split, 13,700 recipes)

| | Precision | Recall | F1 |
|---|---|---|---|
| European | 0.91 | 0.79 | 0.85 |
| Asian | 0.88 | 0.80 | 0.84 |
| Latin American | 0.74 | 0.77 | 0.76 |
| Middle Eastern | 0.25 | 0.55 | 0.35 |
| African | 0.25 | 0.52 | 0.34 |
| **Macro average** | 0.61 | 0.69 | **0.62** |

- **Overall:** accuracy 0.77; macro-F1 0.62.
- **By source:** macro-F1 is 0.65 on CulinaryDB, 0.65 on Food.com, 0.48 on Hugging Face and 0.54 on TheMealDB.

The **test split has not been used**; it is reserved for the final Week 7 comparison.

## Limitations

- **African and Middle Eastern scores are low.** They share many ingredients (cumin, lamb, couscous, chickpeas), and each has few examples. The most common mistakes are European recipes predicted as Middle Eastern, Latin American or African.
- **Ingredients only.** The recipe title is ignored, so "african beef curry" can be predicted as Middle Eastern.
- **Unknown ingredients are ignored.** Ingredients the model has never seen, such as "berbere spice" and "injera", have no effect; the notebook's `check_user_ingredients()` lists them.
- **Biased labels.** The cuisine labels come from recipe sites and may reflect a US view of each cuisine.

## How to use it

```python
import sys
sys.path.insert(0, "src")   # the model uses everflavor.ingredients.ingredient_tokens

import joblib
from everflavor.ingredients import normalize_ingredient_list

model = joblib.load("models/cuisine_baseline.joblib")
model.predict([normalize_ingredient_list(["basmati rice", "lamb shoulder", "Chopped Onions"])])
```

Normalize user input with `normalize_ingredient_list()` first, so it matches the training data.

**Only load model files you created yourself** (by running section 6.6). `joblib.load` can run code hidden inside a file, so never load a `.joblib` file downloaded from someone else or the internet.

Load the model with the same scikit-learn version that saved it. A model saved in one environment (for example scikit-learn 1.9 locally) still loads in another (1.6 in Colab), but scikit-learn warns that results may differ. Running section 6.6 refits and saves the model in the current environment.

## Ideas for Week 7

- **Use more information:** add the recipe title and tags as features.
- **Try stronger models:** for example linear SVM, gradient boosting or text embeddings.
- **More data for the small families:** collect more African and Middle Eastern recipes (RecipeDB), or oversample them.
- **Use the test split once,** for the final comparison only.
