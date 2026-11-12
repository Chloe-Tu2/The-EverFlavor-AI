"""Food.com details from the CC0 Kaggle set (recipe_details.py): times, servings, extra nutrition, names must match."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.recipe_details import DETAIL_COLUMNS, foodcom_details, iso_minutes


def test_iso_durations() -> None:
    assert iso_minutes("PT1H20M") == 80 and iso_minutes("PT45M") == 45 and iso_minutes("P1DT2H") == 26 * 60
    assert iso_minutes("PT0S") is None and iso_minutes(None) is None and iso_minutes("soon") is None
    assert iso_minutes("P10D") is None          # longer than three days: not a cooking time


def test_details_join_by_number_and_name_only() -> None:
    kaggle = pd.DataFrame({"RecipeId": [1, 2, 3], "Name": ["Bread Pudding", "Tacos", "Soup"],
                           "PrepTime": ["PT20M", "PT10M", None], "CookTime": ["PT45M", None, "PT30M"],
                           "TotalTime": ["PT1H5M", "PT10M", "PT30M"], "RecipeServings": [4.0, 0.0, 6.0],
                           "SugarContent": [12.5, 1.0, -1.0], "FiberContent": [1.0, 2.0, 3.0],
                           "SaturatedFatContent": [3.0, 1.0, 0.5], "CholesterolContent": [90.0, 5.0, 0.0]})
    ours = pd.DataFrame({"recipe_id": ["foodcom_1", "foodcom_2", "foodcom_3", "themealdb_9"],
                         "recipe_name": ["bread pudding", "tacos", "a different dish", "Soup"]})
    got = foodcom_details(kaggle, ours)
    assert list(got.columns) == DETAIL_COLUMNS
    assert got["recipe_id"].tolist() == ["foodcom_1", "foodcom_2"]           # foodcom_3's name differs
    first = got.iloc[0]
    assert (first.prep_minutes, first.cook_minutes, first.total_minutes, first.servings_listed) == (20, 45, 65, 4)
    assert first.sugar_g == 12.5 and pd.isna(got.iloc[1].servings_listed)     # 0 servings is not a number of servings
