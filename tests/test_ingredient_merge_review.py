"""The ingredient-merge review sheet (scripts/ingredient_merge_review.py), on a tiny made-up name table."""
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from ingredient_merge_review import language_gaps, review_rows


def _names() -> pd.DataFrame:
    rows = [("soy sauce", "Q1", "exact", "en", "soy sauce"), ("soya sauce", "Q1", "exact", "en", "soya sauce"),
            ("thyme sprig", "Q2", "head", "en", "sprig"), ("mint sprig", "Q2", "head", "en", "sprig"),
            ("walnut", "Q3", "exact", "en", "walnut"), ("walnut", "Q3", "exact", "xx", "zzqq")]
    return pd.DataFrame(rows, columns=["ingredient", "wikidata_id", "match", "language", "name"])


def test_only_exact_matches_are_merge_candidates_and_gains_come_first() -> None:
    sheet = review_rows(_names(), Counter({"soy sauce": 10, "soya sauce": 2}))
    assert set(sheet["group_id"]) == {"Q1"}                  # "head" matches (sprigs) are never offered
    assert list(sheet.columns[-3:]) == ["same_food", "reviewed_by", "notes"]
    assert (sheet[["same_food", "reviewed_by", "notes"]] == "").all().all()   # left for the reviewer
    soy = sheet.set_index("name")
    assert soy.loc["soy sauce", "recipes"] == 10
    assert set(soy.loc["soya sauce", "would_gain"].split("; ")) <= set(soy.loc["soy sauce", "flags_now"].split("; "))


def test_other_language_names_missing_a_flag_are_reported() -> None:
    gaps = language_gaps(_names())
    assert list(gaps["name"]) == ["zzqq"] and "contains_tree_nut" in gaps.iloc[0]["missing"]
