"""Foods a person doesn't eat (preferences.py): matched by name, kept apart from the safety checks."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.preferences import (
    clean_names,
    common_ingredients,
    drop_skipped,
    found_in,
    simplest,
)
from everflavor.safety import UserProfile, check_recipe


def test_names_are_cleaned_and_kept_once() -> None:
    assert clean_names(["  Mushroom ", "mushroom", "", "a", "<b>olive</b>"]) == ("mushroom", "b olive b")
    assert clean_names(["x" * 80])[0] == "x" * 40


def test_whole_words_singular_and_plural() -> None:
    assert found_in("2 cups chopped mushrooms", ["mushroom"]) == ["mushroom"]
    assert found_in("3 ripe tomatoes", ["tomato"]) == ["tomato"]
    assert found_in("1 cup peanuts", ["pea"]) == []          # "pea" is not "peanut"
    assert found_in("1 cup green peas", ["pea"]) == ["pea"]
    assert found_in(None, ["pea"]) == []


def test_recipes_that_mention_a_skipped_food_are_left_out() -> None:
    recipes = pd.DataFrame({
        "recipe_name": ["Mushroom Risotto", "Tomato Soup", "Plain Rice"],
        "ingredient_list": [["rice", "butter"], "['tomatoes', 'olive oil']", ["rice", "water"]],
    })
    kept = drop_skipped(recipes, ["mushroom", "olive oil"])
    assert kept["recipe_name"].tolist() == ["Plain Rice"]
    assert drop_skipped(recipes, []).equals(recipes)


def test_common_ingredients_come_most_used_first() -> None:
    recipes = pd.DataFrame({"ingredient_list": [["salt", "garlic"], "['salt', 'onion']", ["salt", "garlic"]]})
    assert common_ingredients(recipes) == ["salt", "garlic", "onion"]


def test_variants_fold_into_their_food_but_other_foods_stay() -> None:
    recipes = pd.DataFrame({"ingredient_list": [["mushroom", "olive"], ["button mushroom", "olive oil"],
                                                ["dried porcini mushroom", "soy sauce"]]})
    choices = common_ingredients(recipes)
    assert "mushroom" in choices and "button mushroom" not in choices and "dried porcini mushroom" not in choices
    assert "olive oil" in choices and "soy sauce" in choices


def test_a_skipped_food_is_noted_but_never_fails_the_safety_check() -> None:
    profile = UserProfile(skip=("mushroom",))
    result = check_recipe(["1 cup mushrooms", "2 eggs"], "Omelette", profile)
    assert result["passed"] is True
    assert result["skipped"] == [{"line": "1 cup mushrooms", "foods": ["mushroom"]}]
    assert UserProfile.from_dict({"skip": ["olive"]}).skip == ("olive",)


def test_names_another_name_covers_are_dropped() -> None:
    assert simplest(["mushroom", "mushroom soup", "condensed cream of mushroom soup", "olive oil"]) == (
        "mushroom", "olive oil")
    assert simplest(["olive oil", "olive"]) == ("olive",)
