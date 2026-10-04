"""Text features shared by the models (5.8 nutrition, 5.9 origin): TF-IDF of the
ingredient names and of the title words."""
from __future__ import annotations

import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer

from .ingredients import unique_ingredients

__all__ = [
    "TextFeatures",
]


class TextFeatures:
    """Ingredient names and title words as one sparse matrix.

    Fit on the training rows only (`fit_transform`), then `transform` any other rows.
    """

    def __init__(self, title_min_df: int = 3, title_sublinear_tf: bool = False, ingredient_min_df: int = 2) -> None:
        """Set up the two vectorizers.

        Args:
            title_min_df: Title words (and word pairs) in fewer training recipes are ignored.
            title_sublinear_tf: Dampen repeated title words (log of the count).
            ingredient_min_df: Ingredients in fewer training recipes are ignored.
        """
        self.ingredients = TfidfVectorizer(analyzer=unique_ingredients, min_df=ingredient_min_df,
                                           sublinear_tf=True)
        self.titles = TfidfVectorizer(token_pattern=r"[a-z]{3,}", ngram_range=(1, 2), min_df=title_min_df,
                                      sublinear_tf=title_sublinear_tf)

    def fit_transform(self, rows: pd.DataFrame) -> sparse.csr_matrix:
        """Learn the vocabulary from `rows` (training data only) and return their features."""
        return sparse.hstack([self.ingredients.fit_transform(rows["ingredient_list"]),
                              self.titles.fit_transform(rows["recipe_name"].str.lower().tolist())]).tocsr()

    def transform(self, rows: pd.DataFrame) -> sparse.csr_matrix:
        """Return the features of `rows` with the vocabulary learned in `fit_transform`."""
        return sparse.hstack([self.ingredients.transform(rows["ingredient_list"]),
                              self.titles.transform(rows["recipe_name"].str.lower().tolist())]).tocsr()
