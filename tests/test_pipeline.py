"""End-to-end tests for the preprocessing pipeline (src/everflavor/pipeline.py).

Tiny raw tables in the shape of each source go through run_pipeline,
combine_sources, remove_excluded_recipes, the split and the validation rules,
so the whole chain is checked without downloads or an API key. Run from the
project folder with `python -m pytest tests`, or this file alone (needs pytest):

    python tests/test_pipeline.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.diets import DIET_COLUMNS, add_diet_profiles
from everflavor.flags import FLAG_COLUMNS
from everflavor.pipeline import (
    COMMON_COLUMNS,
    MAX_KCAL_PER_SERVING,
    MAX_MINUTES,
    MAX_SERVINGS,
    clean_foodcom,
    clean_huggingface,
    combine_sources,
    remove_excluded_recipes,
    run_pipeline,
    split_by_ingredient_group,
    split_tables,
    validate_recipes,
)


# ------------------------------------------------------------------ raw tables, one per source
def _foodcom_nutrition(kcal: float, fat_g: float, carbs_g: float, protein_g: float, sodium_mg: float) -> str:
    """Food.com's nutrition text: kcal, then % daily value of fat, sugar, sodium, protein, sat fat, carbs."""
    return str([kcal, fat_g / 65 * 100, 0.0, sodium_mg / 2400 * 100, protein_g / 50 * 100, 0.0, carbs_g / 300 * 100])


def raw_foodcom() -> pd.DataFrame:
    good = _foodcom_nutrition(415, 15, 50, 20, 600)
    rows = [
        (1, "Bacon  Pasta ", "['pasta', 'bacon', 'parmesan cheese']", good, 30, "['italian', 'main-dish']", "['boil', 'fry']"),
        (2, "Shared Title Stew", "['beef', 'carrots', 'onion']", good, 120, "['mexican']", "['simmer']"),
        (3, "Dog Biscuits", "['flour', 'peanut butter', 'egg']", good, 40, "['dietary']", "['bake']"),
        (4, "Salt Water", "['salt']", good, 5, "['easy']", "['mix']"),
        (5, "Bacon  Pasta ", "['pasta', 'bacon']", good, 30, "['italian']", "['boil']"),          # repeated name
        (6, "Slow Ferment", "['flour', 'water', 'yeast']", good, MAX_MINUTES + 1, "[]", "['wait']"),
        (7, None, "['rice', 'beans']", good, 20, "[]", "['cook']"),                                  # no name
    ]
    return pd.DataFrame(rows, columns=["id", "name", "ingredients", "nutrition", "minutes", "tags", "steps"])


def _hf_row(name: str, foods: list[str], kcal_total: float, servings: object, labels: list[str],
            cuisine: str = "['italian']") -> dict:
    per = servings if isinstance(servings, (int, float)) and servings > 0 else 1
    nutrients = {"PROCNT": {"quantity": 20 * per}, "FAT": {"quantity": 15 * per},
                 "CHOCDF": {"quantity": 50 * per}, "NA": {"quantity": 600 * per}}
    return {"recipe_name": name, "calories": kcal_total, "cuisine_type": cuisine, "servings": servings,
            "total_nutrients": json.dumps(nutrients),
            "ingredients": json.dumps([{"food": f, "text": "1 cup " + f} for f in foods]),
            "ingredient_lines": json.dumps(["1 cup " + f for f in foods]),
            "health_labels": json.dumps(labels)}


ALL_FREE = ["gluten-free", "dairy-free", "egg-free", "peanut-free", "tree-nut-free", "fish-free",
            "shellfish-free", "soy-free"]


def raw_huggingface() -> pd.DataFrame:
    return pd.DataFrame([
        _hf_row("Tomato Rice", ["rice", "tomato", "basil"], 1660, 4, ALL_FREE + ["vegetarian", "vegan"]),
        _hf_row("Shared title stew!", ["beef", "potato", "carrot"], 1660, 4, ALL_FREE, cuisine="['french']"),
        _hf_row("Party Platter", ["rice", "tomato"], 1660, MAX_SERVINGS + 1, ALL_FREE),
        _hf_row("Heavy Cake", ["flour", "sugar", "butter"], (MAX_KCAL_PER_SERVING + 1) * 2, 2, []),
        _hf_row("No Servings", ["rice", "tomato"], 1660, "n/a", ALL_FREE),
    ])


def raw_culinarydb() -> pd.DataFrame:
    return pd.DataFrame({
        "recipe_id": [10, 11],
        "recipe_name": ["Miso Soup", "Pork Dumplings"],
        "ingredients": ["['miso', 'tofu', 'seaweed']", "['pork', 'flour', 'cabbage']"],
        "cuisine": ["Japanese", "Chinese"],
    })


def raw_themealdb() -> pd.DataFrame:
    return pd.DataFrame({
        "recipe_id": [52771],
        "recipe_name": ["Chicken Tagine"],
        "ingredients": ['["chicken", "apricots", "cinnamon"]'],
        "area": ["Moroccan"],
        "source_url": ["https://example.com/tagine"],
    })


def all_sources() -> list[pd.DataFrame]:
    return [run_pipeline(raw_foodcom(), "foodcom"), run_pipeline(raw_huggingface(), "huggingface"),
            run_pipeline(raw_culinarydb(), "culinarydb"), run_pipeline(raw_themealdb(), "themealdb")]


# ------------------------------------------------------------------ cleaning (5.3)
def test_clean_foodcom_drops_missing_repeated_and_too_long_recipes():
    raw = raw_foodcom()
    out = clean_foodcom(raw)
    assert out["id"].tolist() == [1, 2, 3, 4]
    assert len(raw) == 7                                       # the input is not changed


def test_clean_huggingface_converts_calories_to_per_serving():
    out = clean_huggingface(raw_huggingface())
    assert out["recipe_name"].tolist() == ["Tomato Rice", "Shared title stew!"]
    assert out["calories_per_serving"].tolist() == [415, 415]


def test_cleaning_reports_what_it_dropped(capsys):
    clean_foodcom(raw_foodcom(), verbose=True)
    printed = capsys.readouterr().out
    assert "Dropped 1 rows with missing" in printed
    assert "Dropped 1 duplicate recipe names" in printed
    assert "Dropped 1 recipes with cook time > 24 hours" in printed


# ------------------------------------------------------------------ one call per source (5.5)
def test_run_pipeline_gives_the_same_columns_for_every_source():
    for df in all_sources():
        assert list(df.columns) == COMMON_COLUMNS
        assert df.index.tolist() == list(range(len(df)))
    foodcom, hf, culinarydb, themealdb = all_sources()
    bacon = foodcom.iloc[0]
    assert bacon["recipe_id"] == "foodcom_1" and bacon["recipe_name"] == "Bacon Pasta"
    assert bacon["contains_pork"] and bacon["contains_dairy"] and not bacon["vegetarian"]
    assert bacon["instructions"] == "boil\nfry"
    assert bacon["protein_g"] == pytest.approx(20) and bacon["sodium_mg"] == pytest.approx(600)
    assert hf["recipe_id"].tolist() == ["hf_0", "hf_1"]
    assert hf.iloc[0]["vegan"] and not hf.iloc[0]["contains_gluten"]
    assert hf.iloc[0]["protein_g"] == pytest.approx(20)
    assert culinarydb.loc[1, "contains_pork"] and culinarydb.loc[1, "cuisine_family"] == "Asian"
    assert themealdb.loc[0, "url"] == "https://example.com/tagine"
    assert themealdb.loc[0, "origin_country"] == "Morocco"


def test_run_pipeline_rejects_unknown_sources_and_missing_columns():
    with pytest.raises(ValueError, match="Unknown source"):
        run_pipeline(raw_foodcom(), "allrecipes")
    with pytest.raises(ValueError):
        run_pipeline(raw_foodcom().drop(columns=["steps"]), "foodcom")


# ------------------------------------------------------------------ combining (5.6)
def test_combine_sources_keeps_the_preferred_copy_and_drops_one_ingredient_recipes():
    df_all, counts_before, dropped_small = combine_sources(all_sources())
    assert counts_before.to_dict() == {"foodcom": 4, "huggingface": 2, "culinarydb": 2, "themealdb": 1}
    # "Shared Title Stew" and "Shared title stew!" are one title: Hugging Face comes first in SOURCE_PRIORITY
    stews = df_all[df_all["recipe_name"].str.lower().str.startswith("shared title stew")]
    assert stews["source"].tolist() == ["huggingface"]
    assert dropped_small == 1 and "Salt Water" not in set(df_all["recipe_name"])
    assert (~df_all["vegan"] | df_all["vegetarian"]).all()
    assert df_all["recipe_id"].is_unique
    small = df_all["complexity"] < 3
    assert (df_all.loc[small, "ingredient_group"] == df_all.loc[small, "recipe_id"]).all()


def test_pet_food_is_removed_after_combining():
    df_all, _, _ = combine_sources(all_sources())
    kept, removed = remove_excluded_recipes(df_all)
    assert removed == {"meat from household pets": 0, "made for pets, not people": 1}
    assert "Dog Biscuits" not in set(kept["recipe_name"])
    assert len(kept) == len(df_all) - 1


# ------------------------------------------------------------------ splitting (5.7)
def _many_recipes(n_groups: int = 60, per_group: int = 3) -> pd.DataFrame:
    families = ["Asian", "European", "Latin American"]
    rows = [{"recipe_id": f"r{g}_{i}", "ingredient_group": f"g{g}", "cuisine_family": families[g % 3]}
            for g in range(n_groups) for i in range(per_group)]
    return pd.DataFrame(rows)


def test_split_keeps_each_ingredient_group_in_one_split():
    df = _many_recipes()
    out = split_by_ingredient_group(df, seed=42, verbose=False)
    assert "split" not in df.columns                          # the input is not changed
    assert (out.groupby("ingredient_group")["split"].nunique() == 1).all()
    shares = out.drop_duplicates("ingredient_group")["split"].value_counts(normalize=True)
    assert shares["train"] == pytest.approx(0.70, abs=0.02)
    assert shares["val"] == pytest.approx(0.15, abs=0.02) and shares["test"] == pytest.approx(0.15, abs=0.02)
    again = split_by_ingredient_group(df, seed=42, verbose=False)
    assert out["split"].equals(again["split"])                # the same seed gives the same split
    train, val, test = split_tables(out)
    assert len(train) + len(val) + len(test) == len(df)


def test_split_groups_small_families_with_other(capsys):
    df = pd.concat([_many_recipes(), pd.DataFrame([{"recipe_id": "x", "ingredient_group": "gx",
                                                   "cuisine_family": "African"}])], ignore_index=True)
    out = split_by_ingredient_group(df, verbose=True)
    assert "['African']" in capsys.readouterr().out
    assert out["split"].notna().all()


# ------------------------------------------------------------------ validation (5.10)
def final_table() -> pd.DataFrame:
    """The combined test sources with the columns later steps of notebook 01 add."""
    df_all, _, _ = combine_sources(all_sources())
    df, _ = remove_excluded_recipes(df_all)
    df = split_by_ingredient_group(df, verbose=False)
    df = add_diet_profiles(df)
    estimated = ~df["nutrition_plausible"]
    df["nutrition_source"] = np.where(estimated, "estimated", "listed")
    df["calories_est_min"] = np.where(estimated, 300.0, np.nan)
    df["calories_est_max"] = np.where(estimated, 500.0, np.nan)
    df.loc[estimated, "calories_per_serving"] = 400.0
    df["usda_dish"], df["usda_dish_kcal"] = None, np.nan
    known = df["origin_country"] != "Unknown"
    df["origin_source"] = np.where(known, "labeled", "unknown")
    df["origin_confidence"] = np.where(known, 1.0, np.nan)
    return df


def test_a_clean_table_passes_every_validation_rule():
    results = validate_recipes(final_table(), origin_min_confidence=0.7)
    assert len(results) == 26
    assert [rule for rule, passed in results.items() if not passed] == []


@pytest.mark.parametrize(("rule", "breaks"), [
    ("recipe_id is unique", lambda df: df.assign(recipe_id="same")),
    ("vegan recipes are also vegetarian", lambda df: df.assign(vegan=True, vegetarian=False)),
    ("no pet meat and no recipes made for pets", lambda df: df.assign(recipe_name="Peanut Dog Treats")),
    ("no pet meat and no recipes made for pets", lambda df: df.assign(contains_pet_meat=True)),
    ("flags are true/false only", lambda df: df.assign(contains_egg=df["contains_egg"].astype(object))),
    ("every recipe is in exactly one split", lambda df: df.assign(split="holdout")),
    ("unclean meat also counts as meat", lambda df: df.assign(contains_unclean_meat=True, contains_meat=False)),
    ("every diet column follows its rule (5.4.7)", lambda df: df.assign(halal_friendly=~df["halal_friendly"])),
])
def test_each_validation_rule_catches_its_own_problem(rule, breaks):
    results = validate_recipes(breaks(final_table()), origin_min_confidence=0.7)
    assert results[rule] is False


def test_validation_reports_missing_columns():
    results = validate_recipes(final_table().drop(columns=["split"]), origin_min_confidence=0.7)
    assert list(results.values()) == [False]
    assert "split" in next(iter(results))


def test_every_flag_and_diet_column_is_true_or_false_after_the_pipeline():
    df = final_table()
    assert all(df[c].dtype == bool for c in FLAG_COLUMNS + DIET_COLUMNS)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
