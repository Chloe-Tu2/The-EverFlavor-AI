"""Write the review sheet for the focus areas' best-documented dishes (Walter's knowledge, 0.6.3).

One row per fact Walter shows first (and the summary), with automatic warnings (`dish_knowledge.fact_warnings`)
and empty `verdict` / `reviewer` / `note` columns for a person: keep, fix (write the fix in the note) or drop.

    python scripts/knowledge/review_sheet.py            # data/knowledge/review/focus_review.csv
    python scripts/knowledge/review_sheet.py --per-area 14
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.dish_knowledge import fact_warnings, load_dishes, tidy_dish

# The focus areas (WAITER_COMPANION plan): USA, Mexico, China, the Middle East and Africa
AREAS = {"United States": ["United States"], "Mexico": ["Mexico"], "China": ["China"],
         "Middle East": ["Lebanon", "Turkey", "Iran", "Iraq", "Saudi Arabia", "Palestine"],
         "Africa": ["Morocco", "Ethiopia", "Egypt", "South Africa"]}
COLUMNS = ["area", "country", "dish", "row", "topic", "source", "text", "warnings", "pre_review", "verdict",
           "reviewer", "note"]


# Wikidata origins that count as the area's own, besides the country names
ORIGIN_ALIASES = {"Mexico": ["Mesoamerica", "Aztec", "New Spain"], "China": ["Qing", "Ming", "Han dynasty", "Tang",
                                                                         "Song dynasty", "Canton", "Sichuan"],
                  "Middle East": ["Near East", "Middle East", "Levant", "Mesopotamia", "Persia", "Ottoman", "Arabia"],
                  "Africa": ["Maghreb", "North Africa", "Horn of Africa", "Africa"], "United States": ["America"]}
# Broad food words, not dishes (a list page names them, but there is no one story to check)
NOT_DISHES = {"confectionery", "chocolate", "tofu", "tortilla", "baguette", "swiss roll", "rabbit stew", "calavera"}


def origin_fit(dish: dict, area: str, countries: list[str]) -> int:
    """0: Wikidata says it comes from the area; 1: no origin recorded; 2: it comes from somewhere else."""
    origin = " ".join(dish.get("origin") or [])
    if not origin:
        return 1
    names = countries + ORIGIN_ALIASES.get(area, [])
    return 0 if any(n.lower() in origin.lower() for n in names) else 2


def pick(dishes: list[dict], area: str, countries: list[str], per_area: int) -> tuple[list[dict], list[dict]]:
    """The area's best-documented dishes (most sourced sentences, own origin first, spread over its countries),
    and the listed ones whose Wikidata origin is elsewhere (a reviewer should check their country)."""
    found = [d for d in dishes if d.get("country") in countries and d.get("kind") == "dish"
             and d["name"].split(" (")[0].lower() not in NOT_DISHES]
    elsewhere = [d for d in found if origin_fit(d, area, countries) == 2]
    found = [d for d in found if origin_fit(d, area, countries) < 2]
    found.sort(key=lambda d: (origin_fit(d, area, countries),
                              -(len(d.get("fun_fact_candidates", [])) + len(d.get("story_candidates", [])))))
    chosen: list[dict] = []
    while len(chosen) < per_area and found:
        for country in countries:   # one from each country in turn
            nxt = next((d for d in found if d.get("country") == country), None)
            if nxt is not None and len(chosen) < per_area:
                chosen.append(nxt)
                found.remove(nxt)
    return chosen, elsewhere


def rows_for(area: str, dish: dict) -> list[dict]:
    tidy = tidy_dish(dish)
    name = tidy["name"].split(" (")[0]
    items = [("summary", "summary", tidy.get("summary", ""), "Wikipedia")]
    items += [(f"fact {i}", f["topic"], f["text"], f["source"]) for i, f in enumerate(tidy["fun_facts"], 1)]
    return [{"area": area, "country": tidy.get("country", ""), "dish": tidy["name"], "row": row, "topic": topic,
             "source": source, "text": text, "warnings": "; ".join(fact_warnings(text, name)), "pre_review": "",
             "verdict": "", "reviewer": "", "note": ""} for row, topic, text, source in items if text]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--per-area", type=int, default=13)
    parser.add_argument("--out", default=str(ROOT / "data/knowledge/review/focus_review.csv"))
    args = parser.parse_args()
    dishes = load_dishes(ROOT / "data/knowledge/dishes.jsonl")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    rows, moved = [], []
    for area, countries in AREAS.items():
        chosen, elsewhere = pick(dishes, area, countries, args.per_area)
        rows += [r for d in chosen for r in rows_for(area, d)]
        moved += [(area, d["name"], d.get("country", ""), ", ".join(d["origin"])) for d in elsewhere]
    with (Path(args.out).parent / "origin_elsewhere.csv").open("w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows([("area", "dish", "listed_under", "wikidata_origin"), *moved])
    out = Path(args.out)
    old = {}
    if out.exists():   # keep what people already wrote
        with out.open(encoding="utf-8", newline="") as f:
            old = {(r["dish"], r["row"]): r for r in csv.DictReader(f)}
    for r in rows:
        kept = old.get((r["dish"], r["row"]))
        if kept and kept["text"] == r["text"]:
            r.update({k: kept.get(k, "") for k in ("pre_review", "verdict", "reviewer", "note")})
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    dishes_n = len({r["dish"] for r in rows})
    print(f"{out}: {dishes_n} dishes, {len(rows)} rows, {sum(bool(r['warnings']) for r in rows)} with warnings")


if __name__ == "__main__":
    main()
