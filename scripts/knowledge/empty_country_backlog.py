"""The UN member states with no dish yet: what each one's sources hold, why nothing was kept, and what to try
next (sprint 5's starting list). Audit only: nothing is fetched into the atlas or changed.

    python scripts/knowledge/empty_country_backlog.py   # after culinary_coverage.py

For each country: its cuisine page (as the fetch names it) and how many links it has, its Wikipedia category's
articles, the dishes Wikidata gives it as country of origin, its food region in the place tree and how many
dishes that region has. Pages already read come from the fetch's cache; a page never read is asked once.
Writes docs/audits/empty_country_backlog.md and data/knowledge/atlas/empty_country_backlog.json.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

import fetch_knowledge as fk
from quality_reports import read, save_md, table

KNOW = ROOT / "data" / "knowledge"


def plan(page_links: int, category: int, wikidata: int) -> tuple[str, str]:
    """(difficulty, what to try), from what the sources hold."""
    if wikidata:
        return "low", "Wikidata gives dishes: check why the fetch did not keep them (page title, type)"
    if page_links >= 20:
        return "medium", "the cuisine page links many articles, none kept by the claim rule: a person picks from them"
    if category:
        return "medium", "the category holds articles, none a dish naming the country: a person checks them"
    if page_links:
        return "high", "a short cuisine page: read it by hand for dishes with their own articles"
    return "high", "no cuisine page or category: a free source beyond Wikipedia (a book, a ministry page) or none yet"


def main() -> None:
    un = read(KNOW / "atlas" / "culinary_coverage.json")["un_states"]
    empty = un["members_without_a_dish"]
    with (ROOT / "data" / "reference" / "food_taxonomy.csv").open(encoding="utf-8") as f:
        tree = {r["name"]: r["parent"] for r in csv.DictReader(f)}
    region_dishes = Counter()
    for line in (KNOW / "dishes.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        if d["kind"] == "dish":
            region_dishes[tree.get(d["country"], "")] += 1
    wikidata = Counter(fk.origin_titles(fk.food_classes(("Q746549",))).values())
    rows = []
    for country in empty:
        adj = fk.APP_COUNTRIES.get(country)
        pages = ([f"{adj} cuisine", f"Cuisine of {country}", *fk.COUNTRY_PAGES.get(country, [])] if adj
                 else [f"Cuisine of {country}"])
        found = [(p, len(fk.list_rows(p, True))) for p in pages]
        page, links = max(found, key=lambda x: x[1])
        category = len(fk.category_rows(f"Category:{adj} cuisine")) if adj else 0
        region = tree.get(country, "")
        level, todo = plan(links, category, wikidata.get(country, 0))
        rows.append({"country": country, "cuisine_page": page if links else "", "page_links": links,
                     "category_articles": category, "wikidata_dishes": wikidata.get(country, 0),
                     "in_the_fetch": country in fk.APP_COUNTRIES, "food_region": region,
                     "region_dishes": region_dishes.get(region, 0) if region else 0, "difficulty": level,
                     "try_next": todo if country in fk.APP_COUNTRIES else "not read by the fetch yet: add it to "
                     "ATLAS_SPRINT_COUNTRIES and the place tree, then " + todo})
    order = {"low": 0, "medium": 1, "high": 2}
    rows.sort(key=lambda r: (order[r["difficulty"]], -r["page_links"], r["country"]))
    (KNOW / "atlas" / "empty_country_backlog.json").write_text(json.dumps(
        {"by": "scripts/knowledge/empty_country_backlog.py", "built_on": date.today().isoformat(),
         "countries": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [f"# UN member states with no dish yet ({date.today().isoformat()})", "",
             (f"{len(rows)} of the {un['members']} UN member states have no dish in the atlas. What their sources "
              "hold and what to try next, easiest first (sprint 5's starting list). From "
              "`scripts/knowledge/empty_country_backlog.py`. **Audit only.**"), ""]
    lines += table(["Country", "Cuisine page (links)", "Category articles", "Wikidata dishes", "Food region (its dishes)",
                    "Difficulty", "Try next"],
                   [[r["country"], f"{r['cuisine_page']} ({r['page_links']})" if r["cuisine_page"] else "none",
                     r["category_articles"], r["wikidata_dishes"],
                     f"{r['food_region']} ({r['region_dishes']})" if r["food_region"] else "not in the tree",
                     r["difficulty"], r["try_next"]] for r in rows])
    lines += ["", ("The claim rule (a dish is kept only when Wikidata's origin or its own intro names the country) is "
                   "why a page with many links can still give nothing: its links are often shared dishes of the "
                   "region. Loosening it is a person's call (review item 30).")]
    save_md("empty_country_backlog.md", lines)
    print(Counter(r["difficulty"] for r in rows))


if __name__ == "__main__":
    main()
