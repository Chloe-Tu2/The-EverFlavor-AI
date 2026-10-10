"""Checks on the real data that notebook 01 builds (skipped when the data is not on this computer).

GitHub has no data, so it skips this file; run it locally after rerunning a notebook. The other
test files use small made-up tables; these catch what only shows on the full tables: a wrong USDA
match for a common ingredient, or the safety gate and the dataset filter disagreeing on a real recipe.
They read the saved tables and take about 30 seconds.

    python -m pytest tests/test_real_data.py
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.nutrition import (
    INGREDIENT_USDA,
    PROCESSING_WORDS,
    _brand_words,
    _norm_text,
)
from everflavor.recommend import passes_safety_filter
from everflavor.safety import UserProfile, check_recipe
from everflavor.sources import usda_table

USDA_TABLE = ROOT / "data/processed/usda_ingredient_nutrition.csv"
RECIPES = ROOT / "data/interim/recipes_all.parquet"
SPLITS = {name: ROOT / f"data/processed/recipes_{name}.parquet" for name in ("train", "val", "test")}
USDA_DIR = ROOT / "data/raw/usda_fdc"


def need(*paths: Path) -> None:
    missing = [str(p.relative_to(ROOT)) for p in paths if not p.exists()]
    if missing:
        pytest.skip(f"real data not on this computer (run notebook 01 first): {missing}")


@pytest.fixture(scope="module")
def usda() -> pd.DataFrame:
    need(USDA_TABLE)
    return pd.read_csv(USDA_TABLE)


@pytest.fixture(scope="module")
def recipes() -> pd.DataFrame:
    need(RECIPES)
    return pd.read_parquet(RECIPES, columns=None)


# ------------------------------------------------------------------ USDA ingredient matches
# Calories per 100 g that the most-used ingredients must have (USDA SR Legacy)
KCAL_PER_100G = {"salt": (0, 0), "water": (0, 0), "olive oil": (880, 900), "sugar": (380, 400),
                 "flour": (350, 370), "butter": (700, 730), "egg": (140, 150), "garlic": (140, 155),
                 "onion": (38, 42), "milk": (58, 64), "rice": (355, 370), "chicken breast": (110, 130),
                 "tomato paste": (75, 90), "pork": (190, 230), "lemon juice": (20, 25)}
# Food groups an automatic match should never land in unless the name asks for them
NEVER_AUTOMATIC = {"candies", "cookies", "snacks", "fast foods", "restaurant", "babyfood", "cereals ready-to-eat"}


@pytest.mark.parametrize("name,low_high", KCAL_PER_100G.items())
def test_common_ingredients_have_believable_calories(usda, name, low_high):
    row = usda[usda["ingredient"] == name]
    assert len(row) == 1, f"{name} has no USDA match"
    assert low_high[0] <= row["kcal_100g"].iloc[0] <= low_high[1], row["usda_description"].iloc[0]


def test_top_automatic_matches_are_plain_foods(usda):
    wrong = []
    for _, row in usda.head(300)[usda.head(300)["match"] == "automatic"].iterrows():
        asked = set(_norm_text(row["ingredient"]).split())
        words = set(_norm_text(row["usda_description"]).split())
        group = row["usda_description"].split(",")[0].lower()
        if (words & PROCESSING_WORDS) - asked or _brand_words(row["usda_description"]) - asked or (
                group in NEVER_AUTOMATIC and not asked & set(_norm_text(group).split())):
            wrong.append(f'{row["ingredient"]} -> {row["usda_description"]}')
    assert wrong == [], "hand-check these in nutrition.INGREDIENT_USDA"


def test_hand_checked_matches_exist_in_the_usda_download():
    need(USDA_DIR)
    foods = usda_table("sr_legacy", USDA_DIR)
    assert set(INGREDIENT_USDA.values()) - set(foods["description"]) == set()


# ------------------------------------------------------------------ splits
def test_the_saved_splits_match_the_recipe_table(recipes):
    need(*SPLITS.values())
    ids = {name: set(pd.read_parquet(path, columns=["recipe_id"])["recipe_id"]) for name, path in SPLITS.items()}
    assert not (ids["train"] & ids["val"] or ids["train"] & ids["test"] or ids["val"] & ids["test"])
    assert ids["train"] | ids["val"] | ids["test"] == set(recipes["recipe_id"]), "rerun notebook 01 to the end"


# ------------------------------------------------------------------ safety on real recipes
PROFILES = [UserProfile(vegan=True), UserProfile(vegetarian=True, avoid=("contains_gluten",)),
            UserProfile(diets=("halal_friendly",), avoid=("contains_peanut", "contains_shellfish")),
            UserProfile(diets=("kosher_friendly",)), UserProfile(diets=("jain_friendly",)),
            UserProfile(avoid=("contains_dairy", "contains_egg", "contains_tree_nut", "contains_sesame"))]


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: "+".join((*p.diets, *p.avoid)) or
                         ("vegan" if p.vegan else "vegetarian"))
def test_the_gate_and_the_dataset_filter_agree_on_real_recipes(recipes, profile):
    # The agents check written recipes with the gate, the recommender filters the dataset: same rules
    sample = recipes.sample(1000, random_state=11)
    differ = [row["recipe_name"] for _, row in sample.iterrows()
              if check_recipe(list(row["ingredient_list"]), row["recipe_name"], profile)["passed"]
              != passes_safety_filter(row, avoid=profile.avoid, vegetarian=profile.vegetarian,
                                      vegan=profile.vegan, diets=profile.diets)]
    assert differ == []


def test_hugging_face_lists_keep_restriction_words(recipes):
    # "3 tbsp groundnut oil" must not become plain "oil" (notebook 01 rerun, 2026-10-10)
    hf = recipes[recipes["source"] == "huggingface"]
    names = {i for items in hf["ingredient_list"] for i in items}
    assert {"oil", "bacon"} <= names                     # the plain names still exist ...
    assert any("groundnut" in n or "peanut oil" in n for n in names)
    assert any(n.startswith("turkey bacon") for n in names)   # ... and the qualified ones are kept


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
