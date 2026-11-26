"""The multi-origin dish policy (docs/governance/multi_origin_dish_policy.md, med27-coder, 2026-11-24): which
countries a dish counts for. Shared by the counting scripts, so coverage, representation and the country counts
all follow one rule.

A dish counts for its listing country (the `country` field, set by the keep rule) and for every other country
Wikidata gives as its country of origin (P495), when that country is a country node in the place tree. A
historical state, a region or a sub-national name (Ottoman Empire, Levant, Scotland, Korea) is never mapped to a
country: that would be inference. A person can drop an added country in
data/knowledge/review/shared_dish_origins.csv (verdict `drop`); it then stops counting.

    python scripts/knowledge/dish_origins.py   # writes the review sheet and docs/audits/multi_origin_dishes.md
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import date
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

KNOW = ROOT / "data" / "knowledge"
SHEET = KNOW / "review" / "shared_dish_origins.csv"
FIELDS = ["dish", "qid", "listed_under", "added_country", "evidence", "first_dish_for_country", "verdict",
          "reviewer", "note"]
# Wikidata labels that name a place-tree country under another name (labels only; no political judgement)
ALIASES = {"People's Republic of China": "China", "Republic of the Congo": "Congo"}


@cache
def tree_countries() -> frozenset[str]:
    with (ROOT / "data" / "reference" / "food_taxonomy.csv").open(encoding="utf-8") as f:
        return frozenset(r["name"] for r in csv.DictReader(f) if r["level"] == "country")


@cache
def dropped() -> frozenset[tuple[str, str]]:
    """(qid, country) pairs a person dropped in the review sheet."""
    if not SHEET.exists():
        return frozenset()
    with SHEET.open(encoding="utf-8", newline="") as f:
        return frozenset((r["qid"], r["added_country"]) for r in csv.DictReader(f)
                         if r.get("verdict", "").strip().lower() == "drop")


DECISIONS = ROOT / "data" / "reference" / "dish_decisions.csv"


@cache
def decisions(kind: str) -> frozenset[tuple[str, str]]:
    """(qid, country) pairs a person decided in data/reference/dish_decisions.csv: `drop` takes the dish out of that
    country (the fetch leaves it out), `add` makes it count there too (the multi-origin dish policy)."""
    if not DECISIONS.exists():
        return frozenset()
    with DECISIONS.open(encoding="utf-8", newline="") as f:
        return frozenset((r["qid"], r["country"]) for r in csv.DictReader(f) if r["decision"].strip().lower() == kind)


def added_countries(d: dict) -> list[str]:
    """The countries a dish counts for beyond its listing country: Wikidata's origin, then a person's additions."""
    out: list[str] = []
    for o in d.get("origin") or []:
        c = ALIASES.get(o, o)
        if c in tree_countries() and c != d.get("country") and c not in out and (d["qid"], c) not in dropped():
            out.append(c)
    out += [c for q, c in sorted(decisions("add")) if q == d.get("qid") and c != d.get("country") and c not in out]
    return out


def countries_of(d: dict) -> list[str]:
    """Every country a dish counts for: its listing country first, then the added ones."""
    first = [d["country"]] if d.get("country") else []
    return first + added_countries(d)


def main() -> None:
    dishes = [d for d in (json.loads(line) for line in (KNOW / "dishes.jsonl").open(encoding="utf-8"))
              if d.get("kind") == "dish"]
    listed = {d["country"] for d in dishes if d.get("country")}
    old: dict[tuple[str, str], dict] = {}
    if SHEET.exists():
        with SHEET.open(encoding="utf-8", newline="") as f:
            old = {(r["qid"], r["added_country"]): r for r in csv.DictReader(f)}
    rows = []
    for d in dishes:
        for o in d.get("origin") or []:
            c = ALIASES.get(o, o)
            if c not in tree_countries() or c == d.get("country"):
                continue
            prev = old.get((d["qid"], c), {})
            rows.append({"dish": d["name"], "qid": d["qid"], "listed_under": d.get("country") or "", "added_country": c,
                         "evidence": "Wikidata country of origin (P495)",
                         "first_dish_for_country": "yes" if c not in listed else "no",
                         "verdict": prev.get("verdict", ""), "reviewer": prev.get("reviewer", ""),
                         "note": prev.get("note", "")})
    rows = list({(r["qid"], r["added_country"]): r for r in rows}.values())
    rows.sort(key=lambda r: (r["first_dish_for_country"] != "yes", r["added_country"], r["dish"]))
    with SHEET.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    counted = [r for r in rows if r["verdict"].strip().lower() != "drop"]
    gained = sorted({r["added_country"] for r in counted if r["first_dish_for_country"] == "yes"})
    per = Counter(r["added_country"] for r in counted)
    multi = sum(1 for d in dishes if added_countries(d))
    from quality_reports import save_md, table
    lines = [f"# Multi-origin dishes ({date.today().isoformat()})", "",
             (f"Under the [multi-origin dish policy](../governance/multi_origin_dish_policy.md), {multi:,} dishes count "
              f"for more than one country: {len(counted):,} added attributions by Wikidata's country of origin. "
              f"{len(gained)} countries get their first dish this way: {', '.join(gained) or 'none'}. From "
              "`scripts/knowledge/dish_origins.py`. A person can drop any added country in "
              "`data/knowledge/review/shared_dish_origins.csv` (verdict `drop`; first-dish rows are listed first). "
              "Disputed cultural ownership and political disputes stay a person's call (policy rule 5)."), "",
             "## Countries with the most added dishes", ""]
    lines += table(["Country", "Added dishes", "First dish this way"],
                   [[c, n, "yes" if c in gained else "no"] for c, n in per.most_common(25)])
    lines += ["", "## Countries that get their first dish", ""]
    lines += table(["Country", "Dishes", "Listed under"],
                   [[c, ", ".join(r["dish"] for r in counted if r["added_country"] == c),
                     ", ".join(sorted({r["listed_under"] for r in counted if r["added_country"] == c}))]
                    for c in gained])
    save_md("multi_origin_dishes.md", lines)
    print(f"{multi} multi-origin dishes; {len(counted)} added attributions; first dish for {len(gained)}: {gained}")


if __name__ == "__main__":
    main()
