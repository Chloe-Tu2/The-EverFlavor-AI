"""Tests for the calorie calculator (src/everflavor/calories.py), roadmap step 1.

A tiny made-up USDA SR Legacy file stands in for the real download. Run with
`python -m pytest tests`, or alone:

    python tests/test_calories.py
"""
import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import sources
from everflavor.calories import (
    calorie_accuracy,
    grams_for,
    parse_ingredient_line,
    recipe_calories,
    usda_portions,
)


@pytest.mark.parametrize("line, amount, unit, ingredient", [
    ("1 1/2 cups chopped onion", 1.5, "cup", "onion"),
    ("1-1/2 cups milk", 1.5, "cup", "milk"),
    ("3/4 cup sugar", 0.75, "cup", "sugar"),
    ("½ tsp salt", 0.5, "tsp", "salt"),
    ("1 ½ cups flour", 1.5, "cup", "flour"),
    ("1 /2 teaspoon vanilla extract", 0.5, "tsp", "vanilla extract"),
    ("2-3 tablespoons olive oil", 2.5, "tbsp", "olive oil"),
    ("2 to 3 cloves garlic, minced", 2.5, "clove", "garlic"),
    ("2 large eggs", 2.0, "large", "egg"),
    ("1 T butter", 1.0, "tbsp", "butter"),
    ("1 t vanilla", 1.0, "tsp", "vanilla"),
    ("a pinch of nutmeg", 1.0, "pinch", "nutmeg"),
    ("1 (14 ounce) can diced tomatoes", 14.0, "oz", "tomato"),
    ("1/2 cup (35g) breadcrumbs", 35.0, "g", "breadcrumb"),
    ("1.5 kg potatoes", 1.5, "kg", "potato"),
    ("2 carrots, diced", 2.0, None, "carrot"),
    ("salt to taste", None, None, "salt"),
])
def test_parse_ingredient_line(line, amount, unit, ingredient):
    parsed = parse_ingredient_line(line)
    assert parsed["amount"] == pytest.approx(amount) if amount is not None else parsed["amount"] is None
    assert parsed["unit"] == unit
    assert parsed["ingredient"].startswith(ingredient)


def test_parse_ingredient_line_never_crashes_on_empty_input():
    for empty in (None, "", "   ", float("nan")):
        assert parse_ingredient_line(empty)["amount"] is None


def _food(fdc_id, description, category, kcal, portions):
    return {"fdcId": fdc_id, "description": description, "foodCategory": {"description": category},
            "foodNutrients": [{"nutrient": {"name": "Energy", "unitName": "kcal"}, "amount": kcal}],
            "foodPortions": [{"modifier": m, "amount": a, "gramWeight": g} for m, a, g in portions]}


@pytest.fixture
def usda_folder(tmp_path):
    foods = [
        _food(1, "Onions, raw", "Vegetables and Vegetable Products", 40,
              [("cup, chopped", 1, 160), ("large", 1, 150), ("medium (2-1/2 in dia)", 1, 110)]),
        _food(2, "Egg, whole, raw, fresh", "Dairy and Egg Products", 143, [("large", 1, 50), ("medium", 1, 44)]),
        _food(3, "Wheat flour, white, all-purpose", "Cereal Grains and Pasta", 364, []),   # no volume weight
        _food(4, "Garlic, raw", "Vegetables and Vegetable Products", 149, [("clove", 1, 3)]),
        _food(5, "Oil, olive", "Fats and Oils", 884, [("tbsp", 1, 13.5)]),
    ]
    url, key = sources.USDA_DOWNLOADS["sr_legacy"]
    with zipfile.ZipFile(tmp_path / url.rsplit("/", 1)[1], "w") as archive:   # download_usda finds it
        archive.writestr("sr_legacy.json", json.dumps({key: foods}))
    return tmp_path


def test_usda_portions_and_grams(usda_folder):
    portions = usda_portions(usda_folder)
    assert portions[1]["cup"] == 160 and portions[1]["each"] == 110          # "each" = the medium size
    assert portions[5]["cup"] == pytest.approx(13.5 * 16, rel=0.01)         # from the tbsp weight
    assert grams_for(2, "large", 2, portions) == (100, "usda portion")
    assert grams_for(1, None, 4, portions) == (3, "usda portion")           # "1 garlic clove"
    assert grams_for(8, "oz", None, portions)[1] == "mass"
    flour, how = grams_for(1, "cup", 3, portions)
    assert how == "category density" and flour == pytest.approx(236.588 * 0.55)   # not water's 236 g
    assert grams_for(None, "cup", 1, portions) == (None, "no amount")
    assert grams_for(1, "can", 1, portions)[1] == "standard size"


def test_recipe_calories_counts_and_lists_gaps(usda_folder):
    portions = usda_portions(usda_folder)
    kcal = {1: 40, 2: 143, 3: 364, 4: 149, 5: 884}
    matches = {"onion": 1, "egg": 2, "flour": 3, "garlic": 4, "olive oil": 5}
    lines = ["1 cup chopped onion", "2 large eggs", "salt to taste", "1 tbsp olive oil", "1 cup unobtainium"]
    out = recipe_calories(lines, 2, matches, kcal, portions)
    expected = 160 * 0.40 + 100 * 1.43 + 0 + 13.5 * 8.84
    assert out["kcal_total"] == pytest.approx(expected, abs=0.2)
    assert out["kcal_per_serving"] == pytest.approx(expected / 2, abs=0.2)
    assert out["counted_share"] == 0.8                                       # salt counts (negligible)
    assert out["not_counted"]["method"].tolist() == ["no USDA match"]       # listed, never a silent 0
    given = recipe_calories(["1 onion"], None, matches, kcal, portions, grams=[200.0], names=["onions"])
    assert given["kcal_total"] == 80.0 and given["kcal_per_serving"] is None


def test_calorie_accuracy():
    out = calorie_accuracy([100, 104, 120, 50], [100, 100, 100, 0])
    assert out["n"] == 3 and out["within"] == pytest.approx(2 / 3, abs=0.001)
    assert calorie_accuracy([], [])["n"] == 0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
