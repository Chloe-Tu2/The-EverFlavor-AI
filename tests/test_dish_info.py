"""The dish page's nutrition (app/dish_info.py): only the numbers the data has, estimates said plainly."""
import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dish_info", ROOT / "app" / "dish_info.py")
assert spec and spec.loader
dish_info = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dish_info)


def test_listed_nutrition_with_servings() -> None:
    row = pd.Series({"calories_per_serving": 412.4, "protein_g": 21.0, "fat_g": 9.0, "carbs_g": 50.0,
                     "sodium_mg": 300.0, "servings": 4.0, "nutrition_source": "listed", "nutrition_plausible": True})
    info = dish_info.nutrition_facts(row)
    assert info["listed"] and info["servings"] == 4 and info["range"] is None
    assert dish_info.nutrition_line(info) == "412 kcal · 21 g protein per serving · serves 4"


def test_estimates_are_marked_and_missing_numbers_left_out() -> None:
    row = pd.Series({"calories_per_serving": 300.0, "protein_g": float("nan"), "servings": float("nan"),
                     "nutrition_source": "estimated", "calories_est_min": 120.0, "calories_est_max": 560.0})
    info = dish_info.nutrition_facts(row)
    assert not info["listed"] and info["range"] == (120.0, 560.0) and info["servings"] is None
    assert info["facts"]["Protein"] is None and info["facts"]["Fat"] is None
    assert dish_info.nutrition_line(info) == "300 kcal per serving (estimated)"


def test_no_numbers_no_line() -> None:
    assert dish_info.nutrition_line(dish_info.nutrition_facts(pd.Series({}, dtype=object))) == ""


def test_dish_story_is_the_sourced_first_sentence_with_its_credit_link() -> None:
    entry = {"summary": "Bruschetta is an Italian appetizer. It is grilled bread.",
             "sources": [{"name": "Wikidata", "url": "https://www.wikidata.org/wiki/Q1"},
                         {"name": "Wikipedia: Bruschetta", "url": "https://en.wikipedia.org/wiki/Bruschetta"}]}
    assert dish_info.dish_story(entry) == ("Bruschetta is an Italian appetizer.",
                                           "https://en.wikipedia.org/wiki/Bruschetta")
    long_one = dict(entry, summary="word " * 60)
    text, _ = dish_info.dish_story(long_one, limit=40)
    assert len(text) <= 41 and text.endswith("…")


def test_no_summary_or_no_credit_link_means_no_story() -> None:
    assert dish_info.dish_story(None) is None and dish_info.dish_story({"summary": ""}) is None
    assert dish_info.dish_story({"summary": "A dish.", "sources": [{"name": "Wikidata", "url": "https://x"}]}) is None


def test_extra_facts_and_servings_from_the_recipes_own_listing() -> None:
    row = pd.Series({"calories_per_serving": 300.0, "protein_g": 10.0, "nutrition_source": "listed",
                     "nutrition_plausible": True, "sugar_g": 12.0, "fiber_g": 3.0, "saturated_fat_g": 2.5,
                     "cholesterol_mg": 40.0, "servings": float("nan"), "servings_listed": 6.0})
    info = dish_info.nutrition_facts(row)
    assert info["facts"]["Sugar"] == 12.0 and info["facts"]["Cholesterol"] == 40.0 and info["servings"] == 6
    assert set(info["facts"]) <= set(dish_info.UNITS)
    estimated = dish_info.nutrition_facts(row.copy().replace({"listed": "estimated"}))
    assert "Sugar" not in estimated["facts"]          # extra facts only beside the recipe's own listed numbers
