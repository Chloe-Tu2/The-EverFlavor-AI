"""Tests for the safety gate (src/everflavor/safety.py), roadmap steps 2 and 4.

Run with `python -m pytest tests`, or alone:

    python tests/test_safety.py
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.recommend import passes_safety_filter
from everflavor.safety import UserProfile, check_recipe


def test_profile_rejects_unknown_rules_and_round_trips():
    with pytest.raises(ValueError):
        UserProfile(avoid=("contains_kryptonite",))
    with pytest.raises(ValueError):
        UserProfile(diets=("not_a_diet",))
    with pytest.raises(ValueError):
        UserProfile(calories_per_meal=0)
    data = {"avoid": ["contains_peanut"], "diets": ["halal_friendly"], "calories_per_meal": 600, "theme": "dark"}
    profile = UserProfile.from_dict(data)
    assert profile.avoid == ("contains_peanut",) and profile.extra == {"theme": "dark"}
    assert UserProfile.from_dict(profile.to_dict()) == profile


def test_check_recipe_names_the_line_rule_and_word():
    profile = UserProfile(avoid=("contains_peanut",), diets=("halal_friendly",))
    report = check_recipe(["2 cups jasmine rice", "3 tbsp satay sauce", "4 oz pancetta, diced"],
                          "Thai Peanut Bowl", profile)
    assert not report["passed"]
    found = {(p["line"], p["rule"], p["flag"]) for p in report["problems"]}
    assert ("3 tbsp satay sauce", "contains_peanut", "contains_peanut") in found
    assert ("(dish name) Thai Peanut Bowl", "contains_peanut", "contains_peanut") in found
    assert ("4 oz pancetta, diced", "halal_friendly", "contains_pork") in found
    assert check_recipe(["2 cups jasmine rice", "1 tsp alcohol-free vanilla"], "Rice Pudding", profile)["passed"]


def test_kosher_meat_and_dairy_only_together():
    kosher = UserProfile(diets=("kosher_friendly",))
    assert not check_recipe(["1 lb chicken breast", "2 tbsp butter"], "Chicken", kosher)["passed"]
    assert check_recipe(["1 lb chicken breast", "2 tbsp olive oil"], "Chicken", kosher)["passed"]
    assert check_recipe(["2 cups milk", "1 cup rice"], "Rice Pudding", kosher)["passed"]


def test_pet_meat_is_always_refused():
    report = check_recipe(["1 lb dog meat"], "Stew", UserProfile())
    assert not report["passed"] and report["problems"][0]["rule"] == "never served (P24)"


@pytest.mark.parametrize("profile", [
    UserProfile(vegan=True), UserProfile(vegetarian=True, avoid=("contains_gluten",)),
    UserProfile(diets=("kosher_friendly",)), UserProfile(diets=("jain_friendly",)),
    UserProfile(diets=("halal_friendly",), avoid=("contains_tree_nut",)),
])
def test_same_answer_as_the_dataset_safety_filter(profile):
    recipes = [("Bacon Pasta", ["bacon", "pasta"]), ("Lentil Soup", ["lentil", "onion", "carrot"]),
               ("Cheeseburger", ["ground beef", "cheddar cheese", "bun"]), ("Fruit Salad", ["apple", "honey"]),
               ("Pesto Pasta", ["basil", "pine nuts", "parmigiano-reggiano"]), ("Rice", ["rice", "water"]),
               ("Tiramisu", ["mascarpone", "egg", "marsala wine", "ladyfingers"])]
    for name, items in recipes:
        row = pd.Series({"recipe_name": name, "ingredient_list": items})
        expected = passes_safety_filter(row, avoid=profile.avoid, vegetarian=profile.vegetarian,
                                        vegan=profile.vegan, diets=profile.diets)
        assert check_recipe(items, name, profile)["passed"] == expected, name


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
