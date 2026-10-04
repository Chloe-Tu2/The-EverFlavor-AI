"""Text features shared by the models (5.8 nutrition, 5.9 origin): TF-IDF of the
ingredient names and of the title words."""
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer

from .ingredients import unique_ingredients


class TextFeatures:
    """Ingredient names and title words as one sparse matrix.

    Fit on the training rows only (`fit_transform`), then `transform` any other rows.
    """

    def __init__(self, title_min_df=3, title_sublinear_tf=False, ingredient_min_df=2):
        self.ingredients = TfidfVectorizer(analyzer=unique_ingredients, min_df=ingredient_min_df,
                                           sublinear_tf=True)
        self.titles = TfidfVectorizer(token_pattern=r"[a-z]{3,}", ngram_range=(1, 2), min_df=title_min_df,
                                      sublinear_tf=title_sublinear_tf)

    def fit_transform(self, rows):
        return sparse.hstack([self.ingredients.fit_transform(rows["ingredient_list"]),
                              self.titles.fit_transform(rows["recipe_name"].str.lower().tolist())]).tocsr()

    def transform(self, rows):
        return sparse.hstack([self.ingredients.transform(rows["ingredient_list"]),
                              self.titles.transform(rows["recipe_name"].str.lower().tolist())]).tocsr()
