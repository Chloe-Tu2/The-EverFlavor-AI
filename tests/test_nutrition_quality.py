"""Tests for nutrition quality (src/everflavor/nutrition_quality.py), notebook 07.

A tiny made-up USDA SR Legacy file stands in for the real download. Run with
`python -m pytest tests`, or alone:

    python tests/test_nutrition_quality.py
"""
import json
import sys
import zipfile
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import sources
from everflavor.nutrition_quality import (
    ingredient_micronutrients,
    macro_quality,
    recipe_rich_in,
)


def _food(fdc_id, description, category, nutrients):
    return {"fdcId": fdc_id, "description": description, "foodCategory": {"description": category},
            "foodNutrients": [{"nutrient": {"name": n, "unitName": u}, "amount": a} for n, u, a in nutrients]}


@pytest.fixture
def usda_folder(tmp_path):
    foods = [
        _food(1, "Lentils, raw", "Legumes and Legume Products",
              [("Energy", "kcal", 352), ("Iron, Fe", "mg", 6.5), ("Fiber, total dietary", "g", 10.7),
               ("Folate, DFE", "µg", 479)]),
        _food(2, "Spices, cinnamon, ground", "Spices and Herbs", [("Iron, Fe", "mg", 8.3), ("Calcium, Ca", "mg", 1002)]),
        _food(3, "Milk, whole", "Dairy and Egg Products", [("Calcium, Ca", "mg", 113)]),
    ]
    url, key = sources.USDA_DOWNLOADS["sr_legacy"]
    with zipfile.ZipFile(tmp_path / url.rsplit("/", 1)[1], "w") as archive:   # download_usda finds it, no download
        archive.writestr("sr_legacy.json", json.dumps({key: foods}))
    return tmp_path


def test_rich_in_tags_skip_small_amount_foods(usda_folder):
    matches = pd.DataFrame({"ingredient": ["lentil", "cinnamon", "milk"], "fdc_id": [1, 2, 3],
                            "match": ["automatic", "automatic", "hand-checked"]})
    out = ingredient_micronutrients(matches, usda_folder).set_index("ingredient")
    assert out.loc["lentil", "rich_in"] == ["fiber", "iron", "folate"]
    assert out.loc["lentil", "iron_dv"] == pytest.approx(6.5 / 18, abs=0.001)
    assert out.loc["cinnamon", "rich_in"] == []                       # a spice: used by the teaspoon
    assert out.loc["milk", "rich_in"] == [] and out.loc["milk", "match"] == "hand-checked"   # 9% DV per 100 g
    recipes = pd.DataFrame({"ingredient_list": [["lentil", "onion"], ["milk"], []]})
    assert recipe_rich_in(recipes, out.reset_index()).tolist() == [["fiber", "folate", "iron"], [], []]


def test_macro_quality_shares_and_labels():
    recipes = pd.DataFrame({"calories_per_serving": [400.0, 300.0, 0.0], "protein_g": [30.0, 5.0, 0.0],
                            "fat_g": [10.0, 20.0, 0.0], "carbs_g": [40.0, 25.0, 0.0], "sodium_mg": [300.0, 900.0, 0.0]})
    out = macro_quality(recipes)
    assert out.loc[0, ["protein_pct_kcal", "fat_pct_kcal", "carb_pct_kcal"]].sum() == pytest.approx(100, abs=0.2)
    assert out.loc[0, "protein_pct_kcal"] == pytest.approx(32.4, abs=0.1)
    assert out["high_protein"].tolist() == [True, False, False]
    assert out["lower_fat"].tolist() == [True, False, False]          # 0 kcal: no label, not "low"
    assert out["lower_sodium_density"].tolist() == [True, False, False]
    assert recipes.columns.tolist() == ["calories_per_serving", "protein_g", "fat_g", "carbs_g", "sodium_mg"]
    with pytest.raises(ValueError):
        macro_quality(recipes.drop(columns="sodium_mg"))


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
