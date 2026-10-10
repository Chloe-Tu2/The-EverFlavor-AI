"""Tests for the meal planner's flow (src/everflavor/crew.py) with a fake Chef: no CrewAI, no Ollama.

Run with `python -m pytest tests`, or alone:

    python tests/test_crew.py
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import crew
from everflavor.safety import UserProfile

HALAL_NO_PEANUT = UserProfile(avoid=("contains_peanut",), diets=("halal_friendly",), calories_per_meal=600)


def data():
    recipes = pd.DataFrame({
        "recipe_name": ["thai green curry", "pad thai"], "cuisine_family": ["Asian", "Asian"],
        "cuisine_raw": ["thai", "thai"], "origin_country": ["Thailand", "Thailand"],
        "origin_source": ["labeled", "labeled"], "origin_confidence": [1.0, 1.0],
        "ingredient_list": [["chicken", "coconut milk", "green curry paste"], ["rice noodles", "peanuts"]],
        "calories_per_serving": [580.0, 600.0], "nutrition_plausible": [True, True],
        "contains_peanut": [False, True], "halal_friendly": [True, True],
        "vegetarian": [False, False], "vegan": [False, False], "contains_gluten": [False, False]})
    products = pd.DataFrame({"ingredient": ["fish sauce"], "brands": ["Tiparos"], "home_country": ["Thailand"],
                             "sold_in_us": [True]})
    places = pd.DataFrame({"name": ["Thai Market"], "category": ["grocery"], "cuisine": [["thai"]], "name_hint": [""]})
    return {"recipes": recipes, "products": products, "places": places}


def writer(*drafts):
    """A fake Chef that returns the drafts in order and records the problems it was told to fix."""
    calls = []

    def write(request, problems):
        calls.append(list(problems))
        return drafts[min(len(calls), len(drafts)) - 1]
    return write, calls


SATAY = {"name": "Satay Bowl", "servings": 2, "ingredient_lines": ["2 cups rice", "3 tbsp satay sauce"], "steps": []}
SAFE = {"name": "Thai Basil Chicken", "servings": 2,
        "ingredient_lines": ["2 cups rice", "1 lb chicken", "2 tbsp fish sauce"], "steps": ["Cook."]}


def test_a_failed_recipe_goes_back_to_the_chef_with_the_problems():
    write, calls = writer(SATAY, SAFE)
    plan = crew.plan_meal("A Thai-style dinner", HALAL_NO_PEANUT, data(), write_recipe=write)
    assert plan["recipe"]["name"] == "Thai Basil Chicken" and plan["gate"]["passed"] and not plan["fallback"]
    assert [a["passed"] for a in plan["attempts"]] == [False, True]
    assert calls[0] == [] and "satay sauce" in calls[1][0]          # the second try was told what to fix
    assert plan["where_to_buy"][0]["home_brands"] == ["Tiparos"]    # from the tool, called by the code


def test_after_the_retries_the_user_gets_a_safe_recommended_dish():
    write, calls = writer(SATAY)
    plan = crew.plan_meal("A Thai-style dinner", HALAL_NO_PEANUT, data(), write_recipe=write, max_retries=2)
    assert len(calls) == 3 and plan["fallback"]
    assert plan["recipe"]["name"] == "thai green curry" and plan["gate"]["passed"]   # never the peanut pad thai


def test_a_chef_that_fails_to_answer_counts_as_a_failed_attempt():
    def broken(request, problems):
        raise RuntimeError("the Chef did not return a recipe")
    plan = crew.plan_meal("Dinner", HALAL_NO_PEANUT, data(), write_recipe=broken, max_retries=1)
    assert plan["fallback"] and plan["attempts"][0]["problems"] == ["the Chef did not return a recipe"]
    with pytest.raises(ValueError):
        crew.plan_meal("Dinner", HALAL_NO_PEANUT, data())   # no model and no writer


def test_a_safe_recipe_far_over_budget_goes_back_once_to_be_lightened():
    tables = data()
    tables["usda"] = pd.DataFrame({"ingredient": ["rice", "coconut milk"], "fdc_id": [1, 2], "kcal_100g": [360.0, 230.0]})
    tables["portions"] = {1: {"cup": 185.0}, 2: {"cup": 240.0}}
    heavy = {"name": "Rich Curry", "servings": 1, "ingredient_lines": ["2 cups rice", "2 cups coconut milk"], "steps": []}
    light = {"name": "Light Curry", "servings": 2, "ingredient_lines": ["1 cup rice", "1 cup coconut milk"], "steps": []}
    write, calls = writer(heavy, light)
    plan = crew.plan_meal("A Thai-style dinner", HALAL_NO_PEANUT, tables, write_recipe=write)
    assert plan["recipe"]["name"] == "Light Curry" and plan["attempts"][0]["kcal_per_serving"] > 750
    assert "about 600 kcal" in calls[1][0]
    write, _ = writer(heavy)   # never lighter: keep the safe recipe, not the fallback
    plan = crew.plan_meal("A Thai-style dinner", HALAL_NO_PEANUT, tables, write_recipe=write, max_retries=1)
    assert plan["recipe"]["name"] == "Rich Curry" and not plan["fallback"]


def test_origin_is_read_from_the_request():
    assert crew._origin("I want a Thai-style dinner!", ["Thailand", "Mexico"]) == "Thailand"
    assert crew._origin("Something tex-mex please", ["United States"]) == "United States"
    assert crew._origin("Anything warm", ["Thailand"]) is None


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
