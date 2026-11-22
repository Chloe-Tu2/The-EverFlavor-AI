"""The world's countries and territories from Wikidata (CC0), for the coverage audit: every item with an ISO
3166-1 code (P297) that still exists, with its English name, continent (P30), "part of" groupings (P361) and
population (P1082).

    python scripts/knowledge/fetch_countries.py     # data/knowledge/countries.json
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "knowledge" / "countries.json"
UA = {"User-Agent": "EverFlavorCoverageAudit/0.1 (student project; https://github.com/Chloe-Tu2/The-EverFlavor-AI)"}
QUERY = """SELECT ?c ?cLabel (SAMPLE(?iso) AS ?code) (GROUP_CONCAT(DISTINCT ?contL; separator="|") AS ?continents)
 (GROUP_CONCAT(DISTINCT ?partL; separator="|") AS ?parts) (MAX(?pop) AS ?population) WHERE {
 ?c wdt:P297 ?iso. FILTER NOT EXISTS { ?c wdt:P576 ?end }
 OPTIONAL { ?c wdt:P30 ?cont. ?cont rdfs:label ?contL FILTER(LANG(?contL)="en") }
 OPTIONAL { ?c wdt:P361 ?part. ?part rdfs:label ?partL FILTER(LANG(?partL)="en") }
 OPTIONAL { ?c wdt:P1082 ?pop }
 SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } } GROUP BY ?c ?cLabel"""


def main() -> None:
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": QUERY, "format": "json"})
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
        rows = json.load(r)["results"]["bindings"]
    by_iso: dict[str, dict] = {}
    for r in rows:
        item = {"qid": r["c"]["value"].rsplit("/", 1)[1], "name": r["cLabel"]["value"], "iso": r["code"]["value"],
                "continents": sorted(x for x in r.get("continents", {}).get("value", "").split("|") if x),
                "part_of": sorted(x for x in r.get("parts", {}).get("value", "").split("|") if x),
                "population": int(float(r["population"]["value"])) if "population" in r else None}
        old = by_iso.get(item["iso"])
        if old is None or (item["population"] or 0) > (old["population"] or 0):   # Netherlands, not the Kingdom
            by_iso[item["iso"]] = item
    out = {"source": {"name": "Wikidata", "url": "https://www.wikidata.org", "licence": "CC0 1.0",
                      "retrieved": date.today().isoformat()},
           "countries": sorted(by_iso.values(), key=lambda c: c["name"])}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    print(len(by_iso), "countries and territories")


if __name__ == "__main__":
    main()
