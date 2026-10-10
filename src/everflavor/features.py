"""Text features shared by the models (5.8 nutrition, 5.9 origin): TF-IDF of the
ingredient names and of the title words; training weights and results by group."""
from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer

from .ingredients import unique_ingredients

__all__ = [
    "TextFeatures",
    "balanced_weights",
    "results_by_group",
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


def balanced_weights(groups: pd.Series, cap: float = 10.0) -> np.ndarray:
    """Training weights that give small groups (a country, a cuisine) more say, within limits.

    Each row gets total / (number of groups x rows in its group), the same as scikit-learn's
    "balanced", but no row counts more than `cap` times an average row (a group of 20 recipes
    should not outweigh thousands), and the weights average 1.

    Args:
        groups: One group label per training row.
        cap: Largest weight, relative to an average row.

    Returns:
        One weight per row, in the order of `groups`.
    """
    sizes = groups.map(groups.value_counts()).to_numpy(dtype=float)
    weights = np.minimum(len(groups) / (groups.nunique() * sizes), cap)
    return weights / weights.mean()


def results_by_group(groups: pd.Series, score: Callable[[np.ndarray], float], min_rows: int = 30,
                     name: str = "score") -> pd.DataFrame:
    """A score per group (country, source ...), to show where a model is weak.

    Args:
        groups: One group label per checked row.
        score: Turns the positions of one group's rows into a number (e.g. median error).
        min_rows: Groups with fewer rows are left out (too few to trust).
        name: Column name for the score.

    Returns:
        One row per group: rows and score, the largest groups first.
    """
    positions = pd.Series(np.arange(len(groups)), index=groups.index).groupby(groups.to_numpy())
    table = pd.DataFrame({"rows": positions.size(),
                          name: positions.apply(lambda p: score(p.to_numpy()))})
    return table[table["rows"] >= min_rows].sort_values("rows", ascending=False)
