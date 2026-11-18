"""Build the review sheet for the ingredient-name merge (roadmap phase 1, step 2).

Phase 1 gives each food one id that every table points to (the allergy rules, may-contain, specialty ingredients,
USDA). Merging names changes which allergy flags fire, so a person signs off every merge first (a recorded policy).

The candidates are names that notebook 04 matched *exactly* to the same Wikidata item (its label or an alias):
"icing sugar" and "powdered sugar", "soy sauce" and "soya sauce". Looser matches are left out: Wikidata groups
"thyme sprig" with "mint sprig", and 44 cheeses under "cheese", which are different foods for an allergy.

For each name the sheet shows the flags the safety engine sets on it today, the flags its whole group sets, and
what it would gain if the group shared one set of flags. The reviewer fills `same_food` (yes / no / unsure),
`reviewed_by` and `notes`: docs/flag_review/HOW_TO_REVIEW_INGREDIENT_MERGES.md.

Needs notebook 01's recipe splits and notebook 04's `ingredient_names.parquet` in data/processed/ (local only).
Run from the project folder: `python scripts/ingredient_merge_review.py`. Writes
docs/flag_review/ingredient_merge_review.csv and prints the summary, including the names in other languages that
miss a flag their English name has (a separate finding, not part of this sheet).
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.flags import flags_for_term

PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "docs" / "flag_review" / "ingredient_merge_review.csv"
COLUMNS = ["group_id", "name", "recipes", "flags_now", "flags_in_group", "would_gain", "same_food", "reviewed_by",
           "notes"]


def recipe_counts() -> Counter:
    """How many recipes list each ingredient name (notebook 01's normalized ingredient lists)."""
    counts: Counter = Counter()
    for split in ("train", "val", "test"):
        lists = pd.read_parquet(PROCESSED / f"recipes_{split}.parquet", columns=["ingredient_list"])["ingredient_list"]
        for items in lists:
            counts.update(set(items) if items is not None else ())
    return counts


def review_rows(names: pd.DataFrame, counts: Counter) -> pd.DataFrame:
    """One row per English name in a group of two or more exact matches; names that would gain a flag first."""
    exact = names[(names["match"] == "exact")][["ingredient", "wikidata_id"]].drop_duplicates().dropna()
    groups = exact.groupby("wikidata_id")["ingredient"].apply(lambda s: sorted(set(s)))
    rows = []
    for qid, members in groups.items():
        if len(members) < 2:
            continue
        flags = {m: set(flags_for_term(m)) for m in members}
        union = set().union(*flags.values())
        for member in members:
            rows.append({"group_id": qid, "name": member, "recipes": counts.get(member, 0),
                         "flags_now": "; ".join(sorted(flags[member])), "flags_in_group": "; ".join(sorted(union)),
                         "would_gain": "; ".join(sorted(union - flags[member])), "same_food": "", "reviewed_by": "",
                         "notes": ""})
    out = pd.DataFrame(rows, columns=COLUMNS)
    gains = out.groupby("group_id")["would_gain"].transform(lambda s: (s != "").any())
    out["_gain"], out["_size"] = gains, out.groupby("group_id")["recipes"].transform("sum")
    return out.sort_values(["_gain", "_size", "group_id", "recipes"], ascending=[False, False, True, False]) \
              .drop(columns=["_gain", "_size"])


def language_gaps(names: pd.DataFrame) -> pd.DataFrame:
    """Names in other languages (exact matches) missing a flag their English name has."""
    exact = names[(names["match"] == "exact") & (names["language"] != "en")].dropna(subset=["name"])
    english = {i: set(flags_for_term(i)) for i in exact["ingredient"].unique()}
    rows = []
    for row in exact.itertuples():
        missing = english[row.ingredient] - set(flags_for_term(str(row.name).lower()))
        if missing:
            rows.append({"ingredient": row.ingredient, "language": row.language, "name": row.name,
                         "missing": "; ".join(sorted(missing))})
    return pd.DataFrame(rows)


def main() -> None:
    names = pd.read_parquet(PROCESSED / "ingredient_names.parquet")
    sheet = review_rows(names, recipe_counts())
    sheet.to_csv(OUT, index=False, encoding="utf-8")
    gaining = sheet[sheet["would_gain"] != ""]
    print(f"{OUT.name}: {sheet['group_id'].nunique()} groups, {len(sheet)} names; "
          f"{len(gaining)} names would gain a flag:")
    print(gaining[["group_id", "name", "flags_now", "would_gain"]].to_string(index=False))
    gaps = language_gaps(names)
    print(f"\nOther languages: {len(gaps)} names miss a flag their English name has; by language:")
    print(gaps["language"].value_counts().head(12).to_string())


if __name__ == "__main__":
    main()
