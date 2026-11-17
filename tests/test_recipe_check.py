"""Check my recipe's back end (recipe_check.py): paste anything, keep the ingredient lines, three levels."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.recipe_check import extract_ingredients, review
from everflavor.safety import UserProfile, check_recipe

WEBSITE = """Easy Peanut Chicken Bowls
Prep time: 10 minutes
Ingredients
- 1 lb chicken breast
- 2 tbsp satay sauce
For the rice:
1. 1 cup jasmine rice
2. 2 cups water
▢ 1 tbsp teriyaki sauce
Instructions
Cook the rice in the water for 15 minutes.
Stir the sauce into the chicken and grill until done.
Notes
Leftovers keep 3 days."""


def test_a_whole_recipe_keeps_only_the_ingredient_lines() -> None:
    got = extract_ingredients(WEBSITE)
    assert got["mode"] == "recipe"
    assert got["ingredients"] == ["1 lb chicken breast", "2 tbsp satay sauce", "1 cup jasmine rice", "2 cups water",
                                  "1 tbsp teriyaki sauce"]
    assert got["sections"] == ["For the rice"]
    assert "Cook the rice in the water for 15 minutes." in got["ignored"]
    assert "Easy Peanut Chicken Bowls" in got["ignored"]          # before the Ingredients heading


def test_a_plain_list_and_steps_without_headings() -> None:
    got = extract_ingredients("chickpeas\n* garlic\n2 tbsp olive oil\nAdd everything to a blender and pulse well.")
    assert got["mode"] == "list"
    assert got["ingredients"] == ["chickpeas", "garlic", "2 tbsp olive oil"]
    assert got["ignored"] == ["Add everything to a blender and pulse well."]
    assert extract_ingredients("")["ingredients"] == []
    assert extract_ingredients("add salt")["ingredients"] == ["add salt"]   # too short to be a step


def test_three_levels_from_the_rules() -> None:
    lines = extract_ingredients(WEBSITE)["ingredients"]
    peanut = UserProfile(avoid=("contains_peanut",))
    report = check_recipe(lines, "bowl", peanut)
    got = review(report, lines, watching=True)
    assert got["level"] == "conflict" and got["conflict_lines"] == ["2 tbsp satay sauce"]
    assert {c["line"] for c in got["to_check"]} == {"1 tbsp teriyaki sauce"}   # satay is a conflict, not a "check"
    safe_lines = ["chickpeas", "1 tbsp teriyaki sauce"]
    assert review(check_recipe(safe_lines, "x", peanut), safe_lines, watching=True)["level"] == "review"
    assert review(check_recipe(safe_lines, "x", UserProfile()), safe_lines, watching=False)["level"] == "clear"
    plain = ["chickpeas", "garlic"]
    assert review(check_recipe(plain, "x", peanut), plain, watching=True) == {"level": "clear", "to_check": [],
                                                                               "conflict_lines": []}
