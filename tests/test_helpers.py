"""Tests for the helper modules: environment, reporting, charts, text features,
nutrition, source helpers, the recommender and the diet descriptions.

Like tests/test_everflavor.py, they need no downloads and no API key. Run from the
project folder with `python -m pytest tests`, or without pytest:

    python tests/test_helpers.py
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import types
import warnings
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")   # draw charts without a screen (GitHub, terminals)

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import progress, sources
from everflavor.charts import SAVE_DPI, label_bars, show_figure
from everflavor.diets import DIET_COLUMNS, describe_diet_rules
from everflavor.environment import (
    folder_has,
    get_secret,
    load_env_file,
    print_download_checks,
    short_path,
)
from everflavor.features import TextFeatures
from everflavor.flags import FLAG_COLUMNS
from everflavor.nutrition import (
    add_foodcom_macros,
    add_hf_macros,
    ingredient_energy_features,
    nutrition_checks,
)
from everflavor.progress import PROGRESS_ENV, progress_bar
from everflavor.recommend import baseline_recommend
from everflavor.reporting import (
    by_source,
    hf_revision,
    package_version,
    print_checklist,
    saved_rows,
    to_json,
)
from everflavor.sources import (
    cached_off_search,
    extract_off_record,
    find_file,
    get_energy_kcal,
)


# ------------------------------------------------------------------ environment
def test_short_path_hides_the_home_folder_in_any_letter_case():
    home = str(Path.home())
    assert short_path(Path(home) / "project") == "~" + os.sep + "project"
    assert short_path(home) == "~"
    if os.name == "nt":                                   # Windows paths ignore case
        assert short_path(home.lower() + "\\project") == "~\\project"
    assert short_path(home + "x" + os.sep + "y") == home + "x" + os.sep + "y"   # another user's folder
    assert short_path(os.sep + "data") == os.sep + "data"


def test_load_env_file_reads_keys_without_replacing_existing_ones():
    names = ["EVERFLAVOR_TEST_A", "EVERFLAVOR_TEST_B", "EVERFLAVOR_TEST_C", "EVERFLAVOR_TEST_SET"]
    saved = {n: os.environ.pop(n, None) for n in names}
    try:
        os.environ["EVERFLAVOR_TEST_SET"] = "keep me"
        with tempfile.TemporaryDirectory() as folder:
            env = Path(folder) / ".env"
            # A byte order mark, as Windows Notepad saves it
            env.write_text("﻿# comment\nEVERFLAVOR_TEST_A=plain\nexport EVERFLAVOR_TEST_B=\"quoted\"\n"
                           "EVERFLAVOR_TEST_C=\nnot a setting\nEVERFLAVOR_TEST_SET=new\n", encoding="utf-8")
            assert load_env_file(env)
            assert not load_env_file(Path(folder) / "missing.env")
        assert os.environ["EVERFLAVOR_TEST_A"] == "plain"
        assert os.environ["EVERFLAVOR_TEST_B"] == "quoted"
        assert "EVERFLAVOR_TEST_C" not in os.environ          # empty values are not set
        assert os.environ["EVERFLAVOR_TEST_SET"] == "keep me"
    finally:
        for name, value in saved.items():
            os.environ.pop(name, None)
            if value is not None:
                os.environ[name] = value


def test_download_checks_report_missing_steps_once():
    with tempfile.TemporaryDirectory() as folder:
        (Path(folder) / "a.parquet").write_bytes(b"x")
        (Path(folder) / "empty").mkdir()
        assert folder_has(folder, "*.parquet") == Path(folder) / "a.parquet"
        assert folder_has(Path(folder) / "nowhere", "*") is None
        checks = [("2.4", "file", Path(folder) / "a.parquet"), ("2.5", "empty folder", Path(folder) / "empty"),
                  ("2.5", "missing", Path(folder) / "missing.csv"), ("2.6", "not built", None)]
        assert print_download_checks(checks) == ["2.5", "2.6"]
        pd.DataFrame({"a": [1, 2, 3]}).to_parquet(Path(folder) / "rows.parquet")
        (Path(folder) / "empty" / "x.txt").write_text("x")
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            assert print_download_checks([("2.4", "table", Path(folder) / "rows.parquet"),
                                          ("2.5", "folder", Path(folder) / "empty")], refresh=True) == []
        text = printed.getvalue()
        assert "3 rows" in text and "1 files" in text and "Everything is downloaded" in text
        assert "REFRESH_DOWNLOADS is True" in text


class _FakeColab:
    """Put a fake google.colab (with Colab Secrets) in sys.modules for one test, then remove it."""

    def __init__(self, secrets: dict[str, str]):
        def get(name: str) -> str:
            if name not in secrets:
                raise RuntimeError("SecretNotFoundError")   # Colab raises its own error types
            return secrets[name]
        self.modules = {"google": types.ModuleType("google"), "google.colab": types.ModuleType("google.colab"),
                        "google.colab.userdata": types.ModuleType("google.colab.userdata")}
        self.modules["google.colab.userdata"].get = get          # type: ignore[attr-defined]
        self.modules["google.colab"].userdata = self.modules["google.colab.userdata"]   # type: ignore[attr-defined]
        self.modules["google"].colab = self.modules["google.colab"]   # type: ignore[attr-defined]
        self.saved: dict[str, types.ModuleType | None] = {}

    def __enter__(self):
        self.saved = {name: sys.modules.get(name) for name in self.modules}
        sys.modules.update(self.modules)

    def __exit__(self, *exc):
        for name, module in self.saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def test_get_secret_reads_colab_secrets_first_then_the_environment():
    names = ["EVERFLAVOR_TEST_A", "EVERFLAVOR_TEST_B", "EVERFLAVOR_TEST_C"]
    old = {name: os.environ.pop(name, None) for name in names}
    try:
        os.environ["EVERFLAVOR_TEST_A"] = "from-env"
        os.environ["EVERFLAVOR_TEST_B"] = "from-env"
        assert get_secret("EVERFLAVOR_TEST_A") == "from-env"          # VS Code / Antigravity
        assert get_secret("EVERFLAVOR_TEST_C") is None
        with _FakeColab({"EVERFLAVOR_TEST_A": "from-colab", "EVERFLAVOR_TEST_C": ""}):
            assert get_secret("EVERFLAVOR_TEST_A") == "from-colab"    # Colab Secrets win
            assert get_secret("EVERFLAVOR_TEST_B") == "from-env"      # not in Secrets: the environment
            assert get_secret("EVERFLAVOR_TEST_C") is None            # empty secret counts as missing
        assert get_secret("EVERFLAVOR_TEST_A") == "from-env"          # the fake Colab is gone again
    finally:
        for name, value in old.items():
            os.environ.pop(name, None)
            if value is not None:
                os.environ[name] = value



def test_progress_bar_shows_progress_without_changing_the_loop():
    old = os.environ.pop(PROGRESS_ENV, None)
    try:
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            assert [x * 2 for x in progress_bar(range(5), "Demo")] == [0, 2, 4, 6, 8]
        assert "Demo" in printed.getvalue() and "5/5" in printed.getvalue()   # stdout, not red stderr
        os.environ[PROGRESS_ENV] = "0"
        items = ["a", "b"]
        assert progress_bar(items, "off") is items                          # turned off: nothing printed
        # In a notebook (Colab, VS Code, Antigravity), "text" forces the text bar instead of a widget
        os.environ[PROGRESS_ENV] = "text"
        real_in_notebook = progress._in_notebook
        progress._in_notebook = lambda: True
        try:
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                assert list(progress_bar(items, "Forced text")) == items
            assert "Forced text" in printed.getvalue() and "2/2" in printed.getvalue()
        finally:
            progress._in_notebook = real_in_notebook
    finally:
        os.environ.pop(PROGRESS_ENV, None)
        if old is not None:
            os.environ[PROGRESS_ENV] = old

# ------------------------------------------------------------------ reporting
def test_reporting_helpers():
    assert json.dumps({"n": np.int64(3), "ok": np.bool_(True)}, default=to_json) == '{"n": 3, "ok": true}'
    assert saved_rows("no/such/file.csv").empty
    with tempfile.TemporaryDirectory() as folder:
        proof = Path(folder) / "done.txt"
        proof.write_text("x")
        done, total = print_checklist([("WEEK 4", "by hand", None), ("WEEK 4", "made", str(proof)),
                                       ("WEEK 5", "not made", str(Path(folder) / "missing.txt"))])
    assert (done, total) == (2, 3)
    table = by_source(pd.DataFrame({"source": ["foodcom", "foodcom", "huggingface"], "vegan": [True, False, True]}),
                      "vegan")
    assert table.loc["total", "total"] == 3 and table.loc["total", True] == 2
    assert package_version("pandas") == pd.__version__ and package_version("no-such-package-xyz") is None
    saved = sys.modules.get("huggingface_hub")
    sys.modules["huggingface_hub"] = None   # type: ignore[assignment]   # import fails, as when it is not installed
    try:
        assert hf_revision("datahiveai/recipes-with-nutrition") is None
    finally:
        if saved is None:
            sys.modules.pop("huggingface_hub", None)
        else:
            sys.modules["huggingface_hub"] = saved


# ------------------------------------------------------------------ charts
def test_show_figure_saves_a_sharp_png():
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.bar(["a", "b"], [1200, 30])
    label_bars(ax)
    assert [t.get_text() for t in ax.texts] == ["1,200", "30"]
    with tempfile.TemporaryDirectory() as folder, warnings.catch_warnings():
        warnings.simplefilter("ignore")          # "non-interactive backend" when there is no screen
        show_figure(fig, "test_chart", folder=Path(folder) / "figures")
        png = Path(folder) / "figures" / "test_chart.png"
        assert png.is_file()
        from matplotlib.image import imread
        width = imread(png).shape[1]
    plt.close(fig)
    assert width > 6.4 * SAVE_DPI * 0.8          # a default 6.4-inch figure at SAVE_DPI (minus trimmed margins)


# ------------------------------------------------------------------ text features
def test_text_features_learn_the_vocabulary_from_training_rows_only():
    train = pd.DataFrame({"ingredient_list": [["rice", "egg"], ["rice", "soy sauce"], ["egg", "flour"]],
                          "recipe_name": ["Egg Fried Rice", "Soy Rice Bowl", "Egg Noodles"]})
    other = pd.DataFrame({"ingredient_list": [["saffron", "rice"]], "recipe_name": ["Saffron Rice Pilaf"]})
    features = TextFeatures(title_min_df=1, ingredient_min_df=1)
    fitted = features.fit_transform(train)
    transformed = features.transform(other)
    assert fitted.shape[0] == 3 and transformed.shape == (1, fitted.shape[1])
    assert "saffron" not in features.ingredients.vocabulary_      # never learned from other rows
    assert transformed.nnz > 0                                    # "rice" is known


# ------------------------------------------------------------------ nutrition
def test_foodcom_and_hugging_face_macros():
    foodcom = pd.DataFrame({"nutrition": ["[400.0, 10.0, 5.0, 25.0, 40.0, 3.0, 10.0]", "not a list"]})
    out = add_foodcom_macros(foodcom)
    assert out.loc[0, "calories_per_serving"] == 400
    assert out[["fat_g", "sodium_mg", "protein_g", "carbs_g"]].iloc[0].tolist() == [6.5, 600.0, 20.0, 30.0]
    assert out[["calories_per_serving", "fat_g"]].iloc[1].isna().tolist() == [True, True]   # unreadable text
    assert "calories_per_serving" not in foodcom

    hf = pd.DataFrame({"total_nutrients": [json.dumps({"PROCNT": {"quantity": 40}, "NA": {"quantity": 800}}), "bad"],
                       "servings": [4, 2]})
    out = add_hf_macros(hf)
    assert out[["protein_g", "sodium_mg"]].iloc[0].tolist() == [10.0, 200.0]
    assert out[["fat_g"]].iloc[0].isna().tolist() == [True]                       # not listed
    assert out[["protein_g", "fat_g"]].iloc[1].isna().tolist() == [True, True]    # unreadable JSON


def test_nutrition_checks_flag_impossible_values():
    df = pd.DataFrame({"calories_per_serving": [500, 5, 500, 500],
                       "protein_g": [25, 1, 200, 25], "fat_g": [20, 0, 10, 20], "carbs_g": [55, 0, 10, 5],
                       "sodium_mg": [700, 10, 700, np.nan]})
    checks = nutrition_checks(df)
    assert checks.all(axis=1).tolist() == [True, False, False, False]
    assert not checks.iloc[3]["macros match calories"]      # 4*25 + 4*5 + 9*20 = 300 kcal, not 500


def test_ingredient_energy_features_use_only_matched_ingredients():
    lists = pd.Series([["butter", "sugar", "water"], ["unknown"]], index=[10, 20])
    out = ingredient_energy_features(lists, {"butter": 717, "sugar": 387, "water": 0})
    first = out[["ing_kcal_max", "ing_share_over_500"]].iloc[0].round(3).tolist()
    assert first == [717.0, 0.333]
    assert out.loc[20].isna().all()


# ------------------------------------------------------------------ source helpers (no network)
def test_usda_energy_prefers_kcal_and_open_food_facts_record():
    nutrients = [{"nutrientName": "Energy", "unitName": "kJ", "value": 1000},
                 {"nutrientName": "Energy (Atwater General Factors)", "unitName": "KCAL", "value": 240}]
    assert get_energy_kcal(nutrients) == 240
    assert get_energy_kcal([{"nutrientName": "Energy", "unitName": "kJ", "value": 1000}]) is None
    record = extract_off_record({"product_name": " Tahini ", "nutriscore_grade": "unknown",
                                 "nutriments": {"energy-kcal_100g": 595}})
    assert record["product_name"] == "Tahini" and record["nutriscore_grade"] == ""
    assert record["energy_kcal_100g"] == 595 and record["brands"] == ""


def test_cached_off_search_searches_once_then_reuses_the_saved_copy():
    calls = []
    real_search = sources.off_search

    def fake_search(query, page_size=5):
        calls.append(query)
        return [{"product_name": query}]

    sources.off_search = fake_search
    try:
        with tempfile.TemporaryDirectory() as folder:
            first = cached_off_search("Ranch Dressing", folder)
            second = cached_off_search("ranch dressing", folder)
            third = cached_off_search("ranch dressing", folder, refresh=True)
            assert find_file(folder, "ranch_dressing.json") is not None
    finally:
        sources.off_search = real_search
    assert first == ([{"product_name": "Ranch Dressing"}], False)
    assert second == ([{"product_name": "Ranch Dressing"}], True)
    assert third[1] is False and calls == ["Ranch Dressing", "ranch dressing"]


# ------------------------------------------------------------------ recommender
def test_baseline_recommend_filters_ranks_and_rechecks():
    rows = []
    for name, ingredients, kcal, flags in [
        ("Lentil Soup", ["lentil", "onion"], 480, {}),
        ("Bacon Pasta", ["bacon", "pasta"], 500, {"contains_pork": True, "vegetarian": False}),
        ("Rice Bowl", ["rice", "tofu"], 300, {}),
        # A wrong stored flag: the safety filter must still catch the ham
        ("Ham Salad", ["ham", "lettuce"], 505, {}),
    ]:
        row = {**dict.fromkeys(FLAG_COLUMNS, False), "vegetarian": True, "vegan": True, **flags}
        rows.append({**row, "recipe_name": name, "ingredient_list": ingredients, "cuisine_family": "European",
                     "calories_per_serving": kcal, "nutrition_plausible": True})
    df = pd.DataFrame(rows)
    out = baseline_recommend(df, calorie_target=500, avoid=("contains_pork",), top_n=3)
    assert out["recipe_name"].tolist() == ["Lentil Soup", "Rice Bowl"]
    none = baseline_recommend(df, cuisine_family="european", avoid=("vegan",))   # case ignored; nothing left
    assert none.empty and {"recipe_name", "calorie_distance"} <= set(none.columns)  # same columns, no crash
    with pytest.raises(ValueError):
        baseline_recommend(df, cuisine_family="Klingon")                       # a typo is an error, not "none"
    with pytest.raises(ValueError):
        baseline_recommend(df, calorie_target=-50)


def test_every_diet_rule_is_described():
    lines = describe_diet_rules()
    assert len(lines) == len(DIET_COLUMNS)
    assert all(line.split(":")[0].strip() in DIET_COLUMNS for line in lines)


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
