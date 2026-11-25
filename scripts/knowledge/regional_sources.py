"""Q1 phase 0, regional source research: is there a free, reusable source for food regions within countries, and
how far does it reach? Audit only: no region is added to the place tree.

    python scripts/knowledge/regional_sources.py   # after atlas_health.py

Measures the one candidate the project can already read with its licence in order: Wikidata (CC0), the items that
are a cuisine (Q1778821 or a subclass) with a country (P17). A cuisine item that is not the country's national
cuisine is a candidate food region. For each country with no regional data in the atlas debt: how many such
items exist, and examples. Other sources are listed with their licence for a person to choose from.
Writes docs/audits/regional_source_research.md and data/knowledge/atlas/regional_source_candidates.json.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "src"))

import fetch_knowledge as fk
from dish_origins import ALIASES, tree_countries
from quality_reports import read, save_md, table

KNOW = ROOT / "data" / "knowledge"
QUERY = """SELECT ?c ?cLabel ?countryLabel WHERE {
  ?c wdt:P31/wdt:P279* wd:Q1778821 ; wdt:P17 ?country .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }"""
# Wikidata country labels that differ from the place tree's names (labels only)
LABELS = {**ALIASES, "Kingdom of the Netherlands": "Netherlands", "Kingdom of Denmark": "Denmark",
          "realm of the United Kingdom": "United Kingdom", "United States of America": "United States",
          "Czech Republic": "Czechia", "Ivory Coast": "Ivory Coast", "The Gambia": "The Gambia"}
OTHER_SOURCES = [
    ["Wikidata cuisine items (measured here)", "CC0", "already used; items carry a country and often a region",
     "best first candidate"],
    ["Wikipedia 'Category:Cuisine by region' and regional cuisine articles", "CC BY-SA 4.0 (credit)",
     "already used for dishes; region pages need reading, not a structured list", "second, by hand per country"],
    ["GeoNames or OpenStreetMap administrative regions", "CC BY 4.0 / ODbL",
     "places only, no food: could name regions, never say a region has a cuisine", "only to place a sourced region"],
    ["UNESCO Intangible Cultural Heritage lists", "facts reusable, texts copyrighted",
     "a few regional food traditions per country, with the country", "for preservation, not full coverage"],
    ["Commercial food atlases (for example TasteAtlas)", "proprietary", "broad but not reusable", "not allowed"],
]


def regional(label: str, country: str) -> bool:
    """Whether a cuisine item may be a food region of the country: a named "cuisine of X" or "X cuisine" that is
    not the national cuisine ("Kenyan cuisine", "Cuisine of Kenya", "Kenya cuisine") and has an English label."""
    low = label.lower()
    adj = (fk.APP_COUNTRIES.get(country) or "").lower()
    national = {f"cuisine of {country.lower()}", f"cuisine of the {country.lower()}", f"{country.lower()} cuisine",
                f"{adj} cuisine"}
    return (low.startswith("cuisine of ") or low.endswith(" cuisine")) and low not in national \
        and not re.fullmatch(r"q\d+", low)


def main() -> None:
    from everflavor.knowledge import _sparql
    rows = _sparql(QUERY, ROOT / "data" / "raw" / "knowledge_cache" / "wikidata")
    items: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        country = LABELS.get(r["countryLabel"], r["countryLabel"])
        if country in tree_countries() and regional(r["cLabel"], country):
            items[country].add(r["cLabel"])
    debt = read(KNOW / "atlas" / "atlas_debt.json")["countries"]
    targets = sorted(r["country"] for r in debt if "no culinary region" in r["gaps"])
    reach = {c: sorted(items.get(c, set())) for c in targets}
    covered = [c for c in targets if reach[c]]
    (KNOW / "atlas" / "regional_source_candidates.json").write_text(json.dumps(
        {"by": "scripts/knowledge/regional_sources.py", "built_on": date.today().isoformat(),
         "source": "Wikidata (CC0): cuisine items with a country, not the national cuisine", "countries": reach},
        ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [f"# Regional source research (Q1 phase 0, {date.today().isoformat()})", "",
             (f"{len(targets)} countries with a dish have no regional data. The goal of phase 0 is a trustworthy "
              "source, not data. From `scripts/knowledge/regional_sources.py`. **Audit only:** no region is added; "
              "a person chooses the source and the mapping rule (a review item)."), "",
             "## Candidate sources", ""]
    lines += table(["Source", "Licence", "What it gives", "Use"], OTHER_SOURCES)
    lines += ["", "## How far Wikidata reaches", "",
              (f"Wikidata has at least one non-national cuisine item for {len(covered)} of the {len(targets)} "
               f"countries ({len(covered) / len(targets):.0%}); the other {len(targets) - len(covered)} have none, "
               "so no single free source covers them all. Items are often ethnic or diaspora cuisines (Chinese "
               "Islamic, Indonesian-Dutch), not regions, so each needs a check: is it a place within the country?"),
              "", "## Proposed mapping (for a person to accept)", "",
              ("1. A Wikidata cuisine item becomes a culinary region only if it names a place within the country "
               "(its own P131 or P276, or its label is a region's name), never an ethnic group or diaspora."),
              ("2. Its dishes come from Wikidata (P2012 cuisine, or the dish's origin being that region), not from "
               "proximity on a page."),
              "3. Countries Wikidata does not reach keep the gap; the debt counts it honestly.", "",
              "## Countries Wikidata reaches", ""]
    lines += table(["Country", "Items", "Examples"], [[c, len(reach[c]), ", ".join(reach[c][:4])] for c in covered])
    lines += ["", "## Countries with no candidate", "", ", ".join(c for c in targets if not reach[c]) or "none"]
    save_md("regional_source_research.md", lines)
    print(f"{len(targets)} countries without regional data; Wikidata reaches {len(covered)}")


if __name__ == "__main__":
    main()
