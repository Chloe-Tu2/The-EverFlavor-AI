"""Tests for the shared code in src/everflavor.

Each test pins down one promise a function makes, so a later change that breaks
it is caught at once. Run from the project folder, either with pytest:

    python -m pytest tests

or without installing anything:

    python tests/test_everflavor.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.checks import require_columns
from everflavor.cuisine import map_cuisine, origin_from_labels
from everflavor.diets import DIET_PROFILES, add_diet_profiles, meets_diet
from everflavor.flags import (
    FLAG_COLUMNS,
    add_keyword_flags,
    keyword_flag,
    make_flag,
)
from everflavor.ingredients import (
    normalize_ingredient,
    normalize_ingredient_list,
)
from everflavor.parsing import parse_label_list, parse_list_string
from everflavor.pipeline import (
    MAX_KCAL_PER_SERVING,
    clean_huggingface,
    run_pipeline,
    split_by_ingredient_group,
    split_tables,
)
from everflavor.recommend import passes_safety_filter


def expect_error(error, function, *args, **kwargs):
    """Return the error message if `function` raises `error`; fail otherwise."""
    try:
        function(*args, **kwargs)
    except error as e:
        return str(e)
    raise AssertionError(f"{function.__name__} did not raise {error.__name__}")


# ------------------------------------------------------------------ parsing and ingredients
def test_parse_lists_in_both_text_formats():
    assert parse_list_string('["salt", "sugar"]') == ["salt", "sugar"]
    assert parse_list_string("['salt', 'sugar']") == ["salt", "sugar"]
    assert parse_list_string("not a list") == []
    assert parse_label_list("Middle East") == ["middle east"]


def test_normalize_ingredient_removes_quantities_and_plurals():
    assert normalize_ingredient("2 Large Eggs") == ["egg"]
    assert normalize_ingredient("1/2 cup grated parmesan cheese") == ["parmesan cheese"]
    assert normalize_ingredient("canola oil or vegetable oil") == ["canola oil"]
    assert normalize_ingredient("salt and pepper") == ["salt", "pepper"]
    assert normalize_ingredient_list(["egg", "2 eggs", "Chopped Onions"]) == ["egg", "onion"]


# ------------------------------------------------------------------ flags
def test_make_flag_matches_whole_words_only():
    pork = ["ham", "bacon"]
    assert make_flag("smoked ham", pork)
    assert not make_flag("graham cracker", pork)              # 'ham' inside 'graham'
    assert make_flag("ham hocks", pork)                       # plural still matches
    assert not make_flag("turkey bacon", pork, ["turkey bacon"])   # exception phrase
    assert not make_flag(None, pork)                          # not text


def test_keyword_flags_read_hidden_ingredients():
    assert keyword_flag("soy sauce | rice", "contains_gluten")    # soy sauce has wheat
    assert keyword_flag("za'atar | olive oil", "contains_sesame")
    assert not keyword_flag("butter lettuce | tomato", "contains_dairy")
    assert not keyword_flag("tofu | rice | soy sauce", "contains_meat")
    assert not keyword_flag("grilled lamb chops", "vegetarian")


def test_add_keyword_flags_uses_the_name_and_does_not_change_its_input():
    df = pd.DataFrame({"ingredients": [["yogurt", "garlic"]], "name": ["Grilled Lamb Chops with Tzatziki"]})
    before = df.copy()
    flagged = add_keyword_flags(df, "ingredients", name_col="name")
    assert not flagged.loc[0, "vegetarian"]                   # lamb is only in the name
    assert flagged.loc[0, "contains_dairy"]
    assert set(FLAG_COLUMNS) <= set(flagged.columns)
    pd.testing.assert_frame_equal(df, before)                 # the caller's table is unchanged


def test_gluten_free_name_does_not_count_as_wheat():
    df = pd.DataFrame({"ingredients": [["rice flour", "egg"]], "name": ["Gluten-Free Bread"]})
    assert not add_keyword_flags(df, "ingredients", name_col="name").loc[0, "contains_gluten"]


def test_missing_column_gives_a_clear_error():
    message = expect_error(ValueError, add_keyword_flags, pd.DataFrame({"x": [1]}), "ingredients")
    assert "ingredients" in message and "add_keyword_flags" in message
    expect_error(ValueError, require_columns, pd.DataFrame(), ["a"], "here")


# ------------------------------------------------------------------ diets
def flags_frame(**values):
    """One recipe with every flag False except the ones given."""
    row = dict.fromkeys(FLAG_COLUMNS, False)
    row.update(values)
    return pd.DataFrame([row])


def test_diet_rules():
    assert meets_diet(flags_frame(), "halal_friendly").all()
    assert not meets_diet(flags_frame(contains_pork=True), "halal_friendly").all()
    assert meets_diet(flags_frame(contains_meat=True), "kosher_friendly").all()
    assert not meets_diet(flags_frame(contains_meat=True, contains_dairy=True), "kosher_friendly").all()
    assert meets_diet(flags_frame(vegetarian=True), "jain_friendly").all()
    assert not meets_diet(flags_frame(vegetarian=True, contains_allium=True), "jain_friendly").all()
    assert "Unknown diet" in expect_error(ValueError, meets_diet, flags_frame(), "paleo")


def test_add_diet_profiles_returns_a_copy_and_needs_listed_nutrition():
    df = flags_frame(vegetarian=True).assign(nutrition_plausible=[False], sodium_mg=[100.0], carbs_g=[5.0])
    before = df.copy()
    out = add_diet_profiles(df)
    assert set(DIET_PROFILES) <= set(out.columns)
    assert not out.loc[0, "lower_sodium"]                     # nutrition not listed/plausible
    pd.testing.assert_frame_equal(df, before)


# ------------------------------------------------------------------ cuisine and origin
def test_cuisine_family_and_origin():
    assert map_cuisine("['african', 'middle-eastern']", substring_match=False) == "African"  # priority
    assert map_cuisine("Italy") == "European"
    assert origin_from_labels("['mexican', 'tex-mex']") == ("United States", "Texas")
    assert origin_from_labels("['iranian-persian']") == ("Iran", None)
    assert origin_from_labels("['american', 'italian']") == ("Unknown", None)


# ------------------------------------------------------------------ pipeline
def test_clean_huggingface_converts_calories_and_drops_bad_servings():
    raw = pd.DataFrame({
        "recipe_name": ["a", "b", "c", "d"],
        "calories": [800.0, 500.0, 900.0, 100_000.0],
        "cuisine_type": ["['italian']"] * 4,
        "servings": [4, 0, 60, 2],
    })
    clean = clean_huggingface(raw)
    assert clean["recipe_name"].tolist() == ["a"]             # b: 0 servings, c: > 50, d: too many kcal
    assert clean.loc[clean.index[0], "calories_per_serving"] == 200.0
    assert (clean["calories_per_serving"] <= MAX_KCAL_PER_SERVING).all()


def test_run_pipeline_rejects_unknown_sources_and_missing_columns():
    assert "Unknown source" in expect_error(ValueError, run_pipeline, pd.DataFrame(), source="recipedb")
    assert "recipe_name" in expect_error(ValueError, run_pipeline, pd.DataFrame({"x": [1]}), source="culinarydb")


def test_split_keeps_ingredient_groups_together_and_does_not_change_its_input():
    df = pd.DataFrame({
        "ingredient_group": [f"g{i // 2}" for i in range(400)],   # 200 groups of 2 recipes
        "cuisine_family": ["European", "Asian"] * 200,
    })
    before = df.copy()
    split = split_by_ingredient_group(df, verbose=False)
    assert "split" not in df.columns
    pd.testing.assert_frame_equal(df, before)
    assert (split.groupby("ingredient_group")["split"].nunique() == 1).all()
    train, val, test = split_tables(split)
    assert len(train) + len(val) + len(test) == len(df)
    assert 0.6 < len(train) / len(df) < 0.8


# ------------------------------------------------------------------ safety filter
def test_safety_filter_rechecks_ingredients_and_name():
    row = pd.Series({"ingredient_list": ["rice", "egg"], "recipe_name": "Fried Rice with Bacon"})
    assert not passes_safety_filter(row, avoid=("contains_pork",))       # bacon only in the name
    assert not passes_safety_filter(row, diets=("halal_friendly",))
    assert passes_safety_filter(row, avoid=("contains_peanut",))
    assert not passes_safety_filter(row, vegan=True)



# ------------------------------------------------------------------ bugs found by the type checker (mypy)
def test_score_flags_accepts_a_tuple_of_flags(tmp_path=None):
    import tempfile

    from everflavor.review import score_flags
    folder = Path(tmp_path or tempfile.mkdtemp())
    labeled = folder / "labeled.csv"
    pd.DataFrame({"recipe_id": ["r1", "r2"], "recipe_name": ["a", "b"], "ingredients": ["ham", "rice"],
                  "contains_pork": ["1", "0"]}).to_csv(labeled, index=False)
    df_all = pd.DataFrame({"recipe_id": ["r1", "r2"], "contains_pork": [True, False]})
    scores, disagreements = score_flags(labeled, df_all, ("contains_pork",))   # a tuple, not a list
    assert scores.loc["contains_pork", "recall"] == 1.0
    assert disagreements.empty


def test_retry_helpers_refuse_zero_retries():
    from everflavor.sources import (
        _get_json,  # private, but its promise is worth testing
    )
    assert "retries" in expect_error(ValueError, _get_json, "https://example.invalid", retries=0)

if __name__ == "__main__":
    tests = [(name, test) for name, test in sorted(globals().items()) if name.startswith("test_")]
    failed = 0
    for name, test in tests:
        try:
            test()
            print(f"  pass  {name}")
        except Exception as e:  # noqa: BLE001 - report every failing test, then exit with an error
            failed += 1
            print(f"  FAIL  {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed} of {len(tests)} tests passed")
    sys.exit(1 if failed else 0)
