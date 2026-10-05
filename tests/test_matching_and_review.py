"""Tests for USDA matching (src/everflavor/nutrition.py) and the flag review tools
(src/everflavor/review.py), on small made-up tables.

Run from the project folder with `python -m pytest tests`, or this file alone (needs pytest):

    python tests/test_matching_and_review.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.nutrition import (
    INGREDIENT_USDA,
    dish_features,
    ingredient_nutrition_table,
    match_dishes,
    match_ingredients,
    missing_hand_checked,
)
from everflavor.review import (
    DISAGREEMENT_COLUMNS,
    EVIDENCE_COLUMNS,
    compound_candidates,
    compound_evidence,
    declared_allergens,
    disagreement_file,
    labeled_file,
    make_review_samples,
    sample_file,
    save_disagreements,
    score_flags,
)

# ------------------------------------------------------------------ USDA dishes (5.8.2)
DISHES = pd.DataFrame({
    "description": ["Rice, fried, with chicken", "Soup, chicken noodle", "Cake, chocolate, with icing",
                    "Chicken, fried"],
    "kcal_serving": [330.0, 120.0, 400.0, 300.0],
    "kcal_100g": [165.0, 50.0, 370.0, 250.0],
})


def test_dish_titles_match_the_dish_they_name():
    titles = ["Easy Chicken Fried Rice", "Grandma's Chicken Noodle Soup", "Xyzzy Plover"]
    scores, positions = match_dishes(titles, DISHES)
    assert scores.shape == positions.shape == (3, 5)
    assert positions[0, 0] == 0 and positions[1, 0] == 1    # the main word ("rice", "soup") wins
    assert (scores[2] == 0).all()                             # nothing in common: no match
    assert (np.diff(scores[:2], axis=1) <= 0).all()           # best first
    features = dish_features(DISHES, scores, positions)
    kcal = features["dish_kcal"].tolist()
    assert np.isnan(kcal[2]) and features["dish_score"].tolist()[2] == 0
    assert 120 <= kcal[1] <= 330         # a weighted mix of matched dishes


# ------------------------------------------------------------------ USDA ingredients (5.8.3)
FOODS = pd.DataFrame({
    "fdc_id": [1, 2, 3, 4],
    "description": [INGREDIENT_USDA["rice"], "Lentils, raw", "Lentils, mature seeds, cooked, boiled, with salt",
                    "Beverages, coffee, brewed"],
    "kcal_100g": [365.0, 352.0, 114.0, 1.0],
})


def test_ingredients_match_hand_checked_then_raw_generic_foods():
    matches = match_ingredients(["rice", "lentil", "unobtainium"], FOODS)
    assert matches["rice"] == (0, "hand-checked")
    assert matches["lentil"] == (1, "automatic")              # raw and short beats cooked with details
    assert "unobtainium" not in matches


def test_processed_foods_lose_unless_the_name_asks_for_them():
    foods = pd.DataFrame({"description": ["Lamb, cured, smoked", "Lamb, shoulder, whole, separable lean and fat, raw"]})
    assert match_ingredients(["lamb"], foods)["lamb"][0] == 1               # not the cured, smoked one
    assert match_ingredients(["smoked cured lamb"], foods)["smoked cured lamb"][0] == 0


def test_ingredient_table_lists_the_most_used_first():
    lists = pd.Series([["rice", "lentil"], ["rice", "rice"], ["unobtainium"]])
    table, counts = ingredient_nutrition_table(lists, FOODS, ["kcal_100g"])
    assert table["ingredient"].tolist() == ["rice", "lentil"]
    assert table["recipes"].tolist() == [2, 1]                # "rice" twice in one recipe counts once
    assert table.loc[0, "match"] == "hand-checked" and table.loc[1, "kcal_100g"] == 352.0
    assert counts["unobtainium"] == 1


def test_missing_hand_checked_entries_are_reported():
    missing = missing_hand_checked(FOODS)
    assert INGREDIENT_USDA["rice"] not in missing
    assert INGREDIENT_USDA["flour"] in missing


# ------------------------------------------------------------------ blind review samples (5.12)
def _recipes(n_per_source: int = 6) -> pd.DataFrame:
    rows = [{"recipe_id": f"{s}_{i}", "source": s, "recipe_name": f"Dish {s} {i}",
             "ingredient_list": ["flour", "egg"] if i % 2 else ["rice", "beans"], "url": None,
             "contains_egg": bool(i % 2), "vegetarian": True, "vegan": False}
            for s in ("foodcom", "huggingface") for i in range(n_per_source)]
    return pd.DataFrame(rows)


def test_review_rounds_never_repeat_a_recipe_or_overwrite_a_sample(tmp_path):
    df = _recipes()
    make_review_samples(df, {1: 1, 2: 2}, ["contains_egg"], folder=tmp_path, per_source=2)
    first, second = pd.read_csv(sample_file(1, tmp_path)), pd.read_csv(sample_file(2, tmp_path))
    assert len(first) == len(second) == 4
    assert first["source"].value_counts().tolist() == [2, 2]
    assert not set(first["recipe_id"]) & set(second["recipe_id"])
    assert first["contains_egg"].isna().all()                 # blind: left for the reviewer
    before = sample_file(1, tmp_path).read_bytes()
    make_review_samples(df, {1: 99, 3: 3}, ["contains_egg"], folder=tmp_path, per_source=2)
    assert sample_file(1, tmp_path).read_bytes() == before
    third = pd.read_csv(sample_file(3, tmp_path))
    assert not set(third["recipe_id"]) & (set(first["recipe_id"]) | set(second["recipe_id"]))


def test_flags_are_scored_against_the_answers(tmp_path):
    df = _recipes()
    labeled = df.loc[[0, 1, 2, 3], ["recipe_id", "recipe_name"]].assign(
        ingredients=["rice | beans", "flour | egg", "rice | beans", "flour | egg"],
        contains_egg=["0", "yes", "1", ""],                   # one wrong flag, one blank answer
        vegetarian=["1", "1", "1", "0"])
    labeled.to_csv(labeled_file(1, tmp_path), index=False)
    scores, disagreements = score_flags(labeled_file(1, tmp_path), df, ["contains_egg", "vegetarian", "vegan"])
    assert scores.loc["contains_egg", "reviewed"] == 3
    assert scores.loc["contains_egg", "recall"] == 0.5 and scores.loc["contains_egg", "precision"] == 1.0
    assert "not vegetarian" in scores.index and "not vegan" not in scores.index
    assert list(disagreements.columns) == DISAGREEMENT_COLUMNS
    egg = disagreements[disagreements["flag"] == "contains_egg"].iloc[0]
    assert egg["answer"] == 1 and egg["pipeline_flag"] == 0 and egg["why_flagged"].startswith("no keyword")


def test_scoring_an_unlabeled_round_says_so(tmp_path):
    df = _recipes()
    df.loc[[0], ["recipe_id", "recipe_name"]].assign(ingredients="rice", contains_egg="").to_csv(
        labeled_file(1, tmp_path), index=False)
    with pytest.raises(ValueError, match="no answers yet"):
        score_flags(labeled_file(1, tmp_path), df, ["contains_egg"])


def test_disagreements_are_not_overwritten_once_a_reviewer_starts(tmp_path):
    first = pd.DataFrame([{"recipe_id": "a", "team_check": ""}])
    save_disagreements(first, 1, tmp_path)
    pd.DataFrame([{"recipe_id": "a", "team_check": "answer"}]).to_csv(disagreement_file(1, tmp_path), index=False)
    save_disagreements(pd.DataFrame([{"recipe_id": "b", "team_check": ""}]), 1, tmp_path)
    assert pd.read_csv(disagreement_file(1, tmp_path))["team_check"].tolist() == ["answer"]


# ------------------------------------------------------------------ ready-made ingredients (5.13)
def test_compound_candidates_are_frequent_ready_made_products():
    df = pd.DataFrame({"ingredient_list": [["ranch dressing", "lettuce"], ["ranch dressing"], ["lettuce", "salt"]]})
    out = compound_candidates(df, min_recipes=2)
    assert out.to_dict("records") == [{"ingredient": "ranch dressing", "recipes": 2}]


def test_declared_allergens_count_only_products_named_like_the_ingredient():
    products = [{"product_name": "Ranch Dressings", "allergens_tags": ["en:milk", "en:eggs"]},
                {"product_name": "Classic ranch dressing", "allergens_tags": ["en:milk", "en:unknown"]},
                {"product_name": "Salad kit with ranch", "allergens_tags": ["en:gluten"]}]
    assert declared_allergens("ranch dressing", products) == (2, {"contains_dairy": 1.0, "contains_egg": 0.5})


def test_compound_evidence_suggests_flags_and_keeps_team_decisions():
    candidates = pd.DataFrame({"ingredient": ["ranch dressing", "egg noodle", "mystery sauce"], "recipes": [300, 200, 100]})
    ranch = [{"product_name": "Ranch dressing", "allergens_tags": ["en:milk", "en:eggs"]}] * 5

    def search(text):
        if text == "mystery sauce":
            raise TimeoutError("offline")
        return ranch if text == "ranch dressing" else []

    out = compound_evidence(candidates, search)
    assert list(out.columns) == EVIDENCE_COLUMNS
    rows = out.set_index("ingredient").astype(str)
    assert rows.loc["ranch dressing", "suggested_flags"] == "contains_dairy contains_egg"
    assert "contains_egg" in str(rows.loc["egg noodle", "rule_flags"]).split()       # the keyword rules already flag it
    assert rows.loc["mystery sauce", "products"] == "-1"
    assert rows.loc["mystery sauce", "declared_shares"] == "lookup_failed=TimeoutError"

    previous = out.assign(team_decision=["approved", "", ""], reviewed_by=["med27-coder", "", ""])
    calls: list[str] = []

    def search_again(text: str) -> list[dict]:
        calls.append(text)
        return []

    again = compound_evidence(candidates, search_again, previous=previous)
    assert calls == ["mystery sauce"]                         # only the failed lookup runs again
    assert again.set_index("ingredient").loc["ranch dressing", "team_decision"] == "approved"
    assert again.set_index("ingredient").loc["ranch dressing", "suggested_flags"] == "contains_dairy contains_egg"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
