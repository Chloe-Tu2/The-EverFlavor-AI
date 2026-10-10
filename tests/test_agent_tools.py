"""Tests for the agents' tools (src/everflavor/agent_tools.py) on tiny made-up tables.

Run with `python -m pytest tests`, or alone:

    python tests/test_agent_tools.py
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import agent_tools
from everflavor.safety import UserProfile

HALAL_NO_PEANUT = UserProfile(avoid=("contains_peanut",), diets=("halal_friendly",), calories_per_meal=600)


def recipes():
    return pd.DataFrame({
        "recipe_name": ["peanut noodles", "lemon rice", "pork belly"],
        "cuisine_family": ["Asian", "Asian", "Asian"],
        "ingredient_list": [["noodles", "peanuts"], ["rice", "lemon"], ["pork belly", "soy sauce"]],
        "calories_per_serving": [500.0, 450.0, 520.0], "nutrition_plausible": [True] * 3,
        "contains_peanut": [True, False, False], "contains_pork": [False, False, True],
        "vegetarian": [True, True, False], "vegan": [True, True, False], "contains_gluten": [True, False, True],
        "halal_friendly": [True, True, False]})


def test_recommend_keeps_the_profile_whatever_the_model_asks():
    tool = agent_tools.recommend_tool(recipes(), HALAL_NO_PEANUT)
    found = tool.run(cuisine="Asian", calories="500", how_many="9", avoid=[])   # the model tries to drop the rules
    assert [d["name"] for d in found] == ["lemon rice"]
    assert tool.schema()["function"]["parameters"]["properties"]["cuisine"]["enum"] == ["any", "Asian"]


def test_calories_compares_with_the_budget():
    usda = pd.DataFrame({"ingredient": ["rice", "chicken breast"], "fdc_id": [1, 2], "kcal_100g": [360.0, 120.0]})
    portions = {1: {"cup": 185.0}, 2: {}}
    tool = agent_tools.calories_tool(usda, portions, HALAL_NO_PEANUT)
    out = tool.run(ingredient_lines=["2 cups rice", "1 lb chicken breast", "1 pinch of love"], servings=2)
    assert out["kcal_total"] == round(2 * 185 * 3.6 + 453.6 * 1.2)
    assert out["share_of_lines_counted"] < 1 and any("love" in t for t in out["not_counted"])
    assert out["over_budget_by"] == out["kcal_per_serving"] - 600
    assert tool.run(ingredient_lines="2 cups rice", servings=None)["kcal_per_serving"] is None
    with pytest.raises(ValueError):
        tool.run(ingredient_lines=[])


def test_where_to_buy_warns_about_the_ingredient_itself():
    products = pd.DataFrame({"ingredient": ["fish sauce", "peanut butter"], "brands": ["Tiparos", "Jif"],
                             "home_country": ["Thailand", "United States"], "sold_in_us": [True, True]})
    places = pd.DataFrame({"name": ["Thai Market"], "category": ["grocery"], "cuisine": [["thai"]], "name_hint": [""]})
    tool = agent_tools.where_to_buy_tool(products, places, HALAL_NO_PEANUT)
    fish = tool.run(ingredient="Fish Sauce", origin_country="thailand")
    assert fish["home_brands"] == ["Tiparos"] and fish["fits_user"]["passed"]
    peanut = tool.run(ingredient="peanut butter", origin_country="United States")
    assert not peanut["fits_user"]["passed"] and peanut["fits_user"]["problems"][0]["rule"] == "contains_peanut"


def test_substitutions_leave_out_swaps_that_break_the_rules():
    subs = pd.DataFrame({"original": ["bacon"] * 3, "substitute": ["ham", "turkey bacon", "smoked tofu"],
                         "n_reviews": [9.0, 3.0, 2.0], "flags_removed": ["", "contains_pork", "contains_pork"],
                         "flags_added": ["", "contains_poultry", "contains_soy"], "source": ["food.com reviews"] * 3})
    out = agent_tools.substitutions_tool(subs, HALAL_NO_PEANUT).run(ingredient="Bacon")
    assert [s["substitute"] for s in out["swaps"]] == ["turkey bacon", "smoked tofu"]
    assert out["left_out_for_this_user"] == ["ham"]


def test_agent_tools_offers_only_what_has_data(tmp_path):
    assert [t.name for t in agent_tools.agent_tools({}, HALAL_NO_PEANUT)] == ["check_recipe"]
    names = [t.name for t in agent_tools.agent_tools({"recipes": recipes()}, HALAL_NO_PEANUT)]
    assert names == ["check_recipe", "recommend_recipes"]
    assert agent_tools.load_agent_data(tmp_path) == {}   # an empty project folder: nothing, no error


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
