"""Which facts to review first: the rows of the fact review sheet ranked by how much the app shows them, so a
person's first hour covers the most seen facts. A suggested order only; verdicts still go in focus_review.csv.

    python scripts/knowledge/review_priority.py   # after review_sheet.py and recipe_dish_links.py

Score per row: the recipes the app links to the dish (dish_recipe_counts.json), counted as log(1 + recipes), plus
a bonus for what Walter shows first (the summary, then the first fact), minus a little when the automatic warnings
already flag the row (it may be a drop, quick to decide). Writes data/knowledge/review/focus_review_priority.csv.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "data" / "knowledge" / "review"
SHEET = REVIEW / "focus_review.csv"
OUT = REVIEW / "focus_review_priority.csv"
SHOWN_FIRST = {"summary": 2.0, "fact 1": 1.0}


def score(recipes: int, row: str, warnings: str) -> float:
    return round(math.log1p(recipes) + SHOWN_FIRST.get(row, 0.0) - (0.5 if warnings.strip() else 0.0), 3)


def main() -> None:
    counts = json.loads((ROOT / "data" / "knowledge" / "dish_recipe_counts.json").read_text(encoding="utf-8"))
    recipes = {d["name"]: d["recipes"] for d in counts["dishes"].values()}
    with SHEET.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    ranked = []
    for i, r in enumerate(rows, start=2):   # the sheet's line number, header on line 1
        n = recipes.get(r["dish"], 0)
        ranked.append({"rank": 0, "sheet_line": i, "dish": r["dish"], "country": r["country"], "row": r["row"],
                       "recipes_linked": n, "score": score(n, r["row"], r.get("warnings", "")),
                       "reviewed": "yes" if r.get("verdict", "").strip() else "no", "text": r["text"][:160]})
    ranked.sort(key=lambda r: (r["reviewed"] == "yes", -r["score"], r["sheet_line"]))
    for i, r in enumerate(ranked, start=1):
        r["rank"] = i
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(ranked[0]))
        writer.writeheader()
        writer.writerows(ranked)
    top = ranked[:100]
    print(f"{len(ranked)} rows; the first 100 cover {len({r['dish'] for r in top})} dishes and "
          f"{sum(r['recipes_linked'] for r in {r['dish']: r for r in top}.values()):,} linked recipes")


if __name__ == "__main__":
    main()
