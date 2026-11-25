"""Culinary regions from Wikidata (review item 33, approved by med27-coder, 2026-11-25). Provisional: kept in their
own file, not in the place tree, until a person reviews them.

    python scripts/knowledge/wikidata_regions.py   # before atlas_health.py

The rules: a region is a Wikidata cuisine item (Q1778821 or a subclass) with a country (P17) that
  1. is inside the country: it names a place (P131 located in, P276 location or P361 part of),
  2. has its own cuisine item, and is not the national cuisine,
  3. is named explicitly ("cuisine of Chiloé", "Viennese cuisine"), never an ethnic or diaspora cuisine,
  4. is not a disputed place (those go to a person: status "needs a person"),
  5. stays provisional until one of our dishes is linked to it (a dish with "cuisine" P2012 = the region);
     only a "linked" region counts as regional data in the atlas debt.
Writes data/knowledge/atlas/wikidata_culinary_regions.json and docs/audits/wikidata_culinary_regions.md.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "src"))

from dish_origins import countries_of, tree_countries
from quality_reports import save_md, table
from regional_sources import LABELS, regional

KNOW = ROOT / "data" / "knowledge"
OUT = KNOW / "atlas" / "wikidata_culinary_regions.json"
QUERY = """SELECT ?c ?cLabel ?countryLabel (SAMPLE(?place) AS ?p) (GROUP_CONCAT(DISTINCT ?dish; separator=" ") AS ?dishes)
WHERE { ?c wdt:P31/wdt:P279* wd:Q1778821 ; wdt:P17 ?country .
  OPTIONAL { ?c wdt:P131|wdt:P276|wdt:P361 ?place . }
  OPTIONAL { ?dish wdt:P2012 ?c . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } } GROUP BY ?c ?cLabel ?countryLabel"""
# ethnic, diaspora or court cuisines: not places (rule 3)
NOT_A_PLACE = {"Muhajir cuisine", "Nikkei cuisine", "Indian Singaporean cuisine", "Chifa", "Khmer royal cuisine",
               "Novena Peranakan", "Indonesian-Dutch cuisine", "Chinese Islamic cuisine", "Korean royal court cuisine"}
# disputed places: a person decides (rule 4)
DISPUTED = {"cuisine of Northern Cyprus", "Abkhazian cuisine", "cuisine of Jerusalem", "Kosovan cuisine",
            "South Ossetian cuisine", "Transnistrian cuisine", "Crimean cuisine"}


def main() -> None:
    from everflavor.knowledge import _sparql
    rows = _sparql(QUERY, ROOT / "data" / "raw" / "knowledge_cache" / "wikidata")
    dishes = {d["qid"]: d for d in (json.loads(line) for line in (KNOW / "dishes.jsonl").open(encoding="utf-8"))
              if d.get("kind") == "dish"}
    regions = []
    for r in rows:
        country = LABELS.get(r["countryLabel"], r["countryLabel"])
        label = r["cLabel"]
        if country not in tree_countries() or not regional(label, country) or label in NOT_A_PLACE:
            continue
        if not r.get("p"):
            continue   # rule 1: no place named
        linked = sorted(q.rsplit("/", 1)[-1] for q in (r.get("dishes") or "").split())
        ours = [q for q in linked if q in dishes and country in countries_of(dishes[q])]
        status = "needs a person" if label in DISPUTED else "linked" if ours else "provisional"
        regions.append({"qid": r["c"].rsplit("/", 1)[-1], "name": label, "country": country,
                        "place": r["p"].rsplit("/", 1)[-1], "dishes_in_wikidata": len(linked),
                        "our_dishes": [{"qid": q, "name": dishes[q]["name"]} for q in ours], "status": status})
    regions = list({r["qid"]: r for r in regions}.values())
    regions.sort(key=lambda r: (r["country"], r["name"]))
    OUT.write_text(json.dumps({"by": "scripts/knowledge/wikidata_regions.py", "built_on": date.today().isoformat(),
                               "rule": "review item 33 (med27-coder, 2026-11-25); provisional until reviewed",
                               "regions": regions}, ensure_ascii=False, indent=1), encoding="utf-8")
    status = Counter(r["status"] for r in regions)
    linked_countries = sorted({r["country"] for r in regions if r["status"] == "linked"})
    lines = [f"# Culinary regions from Wikidata ({date.today().isoformat()})", "",
             (f"{len(regions)} regions in {len({r['country'] for r in regions})} countries pass the rules of review item "
              f"33 (approved by med27-coder): {status['linked']} linked to one of our dishes, {status['provisional']} "
              f"provisional (no dish of ours yet), {status['needs a person']} disputed places for a person. Only a "
              f"linked region counts as regional data in the atlas debt ({len(linked_countries)} countries: "
              f"{', '.join(linked_countries) or 'none'}). From `scripts/knowledge/wikidata_regions.py`; the regions "
              "are not in the place tree yet."), ""]
    lines += table(["Country", "Region", "Status", "Our dishes"],
                   [[r["country"], r["name"], r["status"], ", ".join(d["name"] for d in r["our_dishes"]) or "none"]
                    for r in regions])
    save_md("wikidata_culinary_regions.md", lines)
    print(dict(status), "linked countries:", linked_countries)


if __name__ == "__main__":
    main()
