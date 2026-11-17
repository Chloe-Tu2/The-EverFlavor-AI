"""The recommender finds recipes for strict diets, and still re-checks every one it returns.

Before 2026-11-16 baseline_recommend never filtered on the stored diet columns: the safety filter read only the
best-ranked top_n * 20 recipes, so a strict diet (Jain, Ital) that few of those fit got nothing, though
thousands of recipes fit it. Small made-up tables, no data needed.

Run with `python -m pytest tests`, or alone:

    python tests/test_recommend_diets.py
"""
import logging
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import recommend
from everflavor.diets import DIET_PROFILES
from everflavor.flags import FLAG_COLUMNS
from everflavor.recommend import (
    SORT_ORDERS,
    baseline_recommend,
    passes_safety_filter,
    what_blocks,
)

FITS_EVERY_DIET = ["rice", "lentil", "spinach"]
# One list that breaks every diet profile, so the same table tests them all
BREAKS_EVERY_DIET = ["pork chop", "beef steak", "shrimp", "shark", "raw egg", "onion", "potato", "mushroom",
                     "asafoetida", "honey", "red wine", "coffee", "salt", "fava bean", "tomato", "brie", "liver",
                     "aged cheddar", "gelatin", "sushi", "catfish", "rabbit"]
DECOYS = 150   # more than top_n * 20, the only recipes the safety filter used to read


def diet_table(diet: str | None, good: int = 6) -> pd.DataFrame:
    """150 recipes that rank first in every order and break the diet, then `good` recipes that fit it. The
    stored diet column (left out when `diet` is None) is what the data pipeline would have saved."""
    rows = []
    for i in range(DECOYS):
        rows.append({"recipe_name": f"Feast {i}", "ingredient_list": BREAKS_EVERY_DIET, "calories_per_serving": 500,
                     "protein_g": 90, "minutes": 1})
    for i in range(good):
        rows.append({"recipe_name": f"Dal {i}", "ingredient_list": FITS_EVERY_DIET, "calories_per_serving": 540,
                     "protein_g": 12, "minutes": 40})
    df = pd.DataFrame(rows)
    for column in FLAG_COLUMNS:
        df[column] = False
    df["vegetarian"] = df["vegan"] = df["recipe_name"].str.startswith("Dal")
    df["cuisine_family"], df["nutrition_plausible"], df["minutes_estimate"] = "Asian", True, None
    if diet:
        # every "Feast" has the same ingredients, and every "Dal": one check of each fills the column
        fits = {name: passes_safety_filter(pd.Series({"ingredient_list": ingredients, "recipe_name": name}),
                                           diets=(diet,))
                for name, ingredients in (("Feast", BREAKS_EVERY_DIET), ("Dal", FITS_EVERY_DIET))}
        df[diet] = df["recipe_name"].str.split().str[0].map(fits).astype(bool)
    return df


@pytest.mark.parametrize("diet", sorted(DIET_PROFILES))
def test_each_diet_finds_its_recipes_behind_many_that_do_not_fit(diet):
    df = diet_table(diet)
    assert df[diet].sum() == 6 and not df[diet].iloc[:DECOYS].any()     # the table is what the test says it is
    for sort_by in SORT_ORDERS:
        out = baseline_recommend(df, calorie_target=500, diets=(diet,), top_n=5, sort_by=sort_by)
        assert len(out) == 5 and out["recipe_name"].str.startswith("Dal").all(), (diet, sort_by)
        assert all(passes_safety_filter(row, diets=(diet,)) for _, row in out.iterrows())


@pytest.mark.parametrize("diet", ["jain_friendly", "ital_friendly", "halal_friendly"])
def test_a_diet_without_a_stored_column_is_found_by_the_safety_filter_alone(diet):
    # no stored column: the candidates are read a chunk at a time until top_n pass (150 decoys come first)
    df = diet_table(None)
    out = baseline_recommend(df, calorie_target=500, diets=(diet,), top_n=5, sort_by="protein")
    assert out["recipe_name"].tolist() == [f"Dal {i}" for i in range(5)]


def test_a_wrong_stored_diet_column_cannot_let_a_recipe_through():
    df = diet_table("jain_friendly")
    df["jain_friendly"] = True                    # stale data: every recipe claims to fit
    df["vegetarian"] = True
    out = baseline_recommend(df, calorie_target=500, diets=("jain_friendly",), top_n=5)
    assert len(out) == 5 and out["recipe_name"].str.startswith("Dal").all()
    df["jain_friendly"] = ~df["recipe_name"].str.startswith("Dal")   # worse: only the wrong ones claim to fit
    assert baseline_recommend(df, calorie_target=500, diets=("jain_friendly",), top_n=5).empty


def test_two_diets_and_an_allergy_together():
    df = diet_table("jain_friendly")
    df["ital_friendly"] = df["jain_friendly"]
    lists = df["ingredient_list"].tolist()
    lists[DECOYS] = ["rice", "lentil", "peanut"]               # Dal 0: its stored peanut flag is wrong
    df["ingredient_list"] = lists
    out = baseline_recommend(df, calorie_target=500, diets=("jain_friendly", "ital_friendly"),
                             avoid=("contains_peanut",), top_n=5, sort_by="quickest")
    assert out["recipe_name"].tolist() == [f"Dal {i}" for i in range(1, 6)]


def test_fewer_than_top_n_gives_what_there_is_and_none_gives_the_same_columns():
    out = baseline_recommend(diet_table("ital_friendly", good=2), calorie_target=500, diets=("ital_friendly",), top_n=5)
    assert out["recipe_name"].tolist() == ["Dal 0", "Dal 1"]
    none = baseline_recommend(diet_table("ital_friendly", good=0), calorie_target=500, diets=("ital_friendly",))
    assert none.empty and {"recipe_name", "calorie_distance", "ital_friendly"} <= set(none.columns)
    unread = baseline_recommend(diet_table(None, good=0), calorie_target=500, diets=("ital_friendly",))
    assert unread.empty and "calorie_distance" in unread.columns
    assert baseline_recommend(diet_table("ital_friendly"), diets=("ital_friendly",), top_n=0).empty


def test_missing_values_in_stored_columns_never_count_as_fitting():
    df = diet_table("jain_friendly")
    df["jain_friendly"] = df["jain_friendly"].astype("boolean")
    df.loc[DECOYS, "jain_friendly"] = pd.NA                    # Dal 0: not known
    df["contains_peanut"] = df["contains_peanut"].astype("boolean")
    df.loc[DECOYS + 1, "contains_peanut"] = pd.NA              # Dal 1: not known
    out = baseline_recommend(df, calorie_target=500, diets=("jain_friendly",), avoid=("contains_peanut",), top_n=5)
    assert out["recipe_name"].tolist() == ["Dal 2", "Dal 3", "Dal 4", "Dal 5"]


def test_the_table_given_is_not_changed_and_nothing_is_printed(capsys, caplog):
    df = diet_table("jain_friendly")
    before = df.copy()
    with caplog.at_level(logging.INFO, logger="everflavor.recommend"):
        out = baseline_recommend(df, calorie_target=500, diets=("jain_friendly",), top_n=3)
        baseline_recommend(df, calorie_target=500, max_minutes=0.5)                    # nothing matches
        baseline_recommend(diet_table(None), calorie_target=500, diets=("jain_friendly",), top_n=3)
    pd.testing.assert_frame_equal(df, before)
    assert "calorie_distance" in out.columns and "calorie_distance" not in df.columns
    assert capsys.readouterr().out == ""                       # library code logs, it does not print
    messages = [r.getMessage() for r in caplog.records]
    assert "No recipes matched the given filters." in messages
    assert any(m.startswith("safety filter removed 150 of") for m in messages)


def test_the_safety_recheck_stops_at_its_limit_and_says_so(monkeypatch, caplog):
    monkeypatch.setattr(recommend, "MAX_SAFETY_CHECKS", 100)
    df = diet_table(None)                                      # no stored column, 150 recipes that fail first
    with caplog.at_level(logging.WARNING, logger="everflavor.recommend"):
        out = baseline_recommend(df, calorie_target=500, diets=("jain_friendly",), top_n=1, sort_by="protein")
    assert out.empty
    assert any(r.getMessage().startswith("safety filter stopped after 100 of 156") for r in caplog.records)


def test_what_blocks_counts_an_avoided_column_the_way_the_recommender_filters_it():
    df = diet_table("jain_friendly")
    # avoid=("vegan",) keeps the recipes that are not vegan in baseline_recommend and passes_safety_filter;
    # what_blocks used to count the vegan ones instead
    found = baseline_recommend(df, calorie_target=500, avoid=("vegan",), top_n=500)
    assert len(found) == DECOYS
    blocks = what_blocks(df, avoid=("vegan",), max_minutes=30)
    by_kind = {b["kind"]: b["recipes"] for b in blocks}
    assert by_kind == {"avoid": DECOYS, "time": DECOYS}        # without the time limit: the 150 non-vegan ones
    blocks = what_blocks(df, avoid=("contains_peanut",), diets=("jain_friendly",), max_minutes=30)
    assert {b["kind"]: b["recipes"] for b in blocks} == {"avoid": 0, "diet": DECOYS, "time": 6}


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
