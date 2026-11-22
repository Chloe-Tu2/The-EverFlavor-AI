"""What Wikidata says each backlog candidate is (CC0): its "instance of" (P31) and whether it has a manufacturer
(P176), a brand (P1716) or an owner (P127). The coverage audit uses it to keep commercial products and events (a
candy bar brand, a food scare) out of the dishes to add.

    python scripts/knowledge/fetch_backlog_types.py   # data/knowledge/coverage/wikidata_types.json
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FAMILIES = ROOT / "data" / "knowledge" / "dish_families.json"
OUT = ROOT / "data" / "knowledge" / "coverage" / "wikidata_types.json"
UA = {"User-Agent": "EverFlavorCoverageAudit/0.1 (student project; https://github.com/Chloe-Tu2/The-EverFlavor-AI)"}
QUERY = """SELECT ?item (GROUP_CONCAT(DISTINCT ?typeL; separator="|") AS ?types)
 (COUNT(DISTINCT ?maker) AS ?makers) (COUNT(DISTINCT ?brand) AS ?brands) (COUNT(DISTINCT ?owner) AS ?owners) WHERE {
 VALUES ?item { %s }
 OPTIONAL { ?item wdt:P31 ?type. ?type rdfs:label ?typeL FILTER(LANG(?typeL)="en") }
 OPTIONAL { ?item wdt:P176 ?maker } OPTIONAL { ?item wdt:P1716 ?brand } OPTIONAL { ?item wdt:P127 ?owner }
} GROUP BY ?item"""


def main() -> None:
    fam = json.loads(FAMILIES.read_text(encoding="utf-8"))
    qids = sorted({m["qid"] for f in fam["families"] for m in f["members"] if not m["in_everflavor"]})
    out: dict[str, dict] = {}
    for i in range(0, len(qids), 250):
        values = " ".join(f"wd:{q}" for q in qids[i:i + 250])
        url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": QUERY % values, "format": "json"})
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
            for row in json.load(r)["results"]["bindings"]:
                q = row["item"]["value"].rsplit("/", 1)[1]
                out[q] = {"instance_of": sorted(x for x in row.get("types", {}).get("value", "").split("|") if x),
                          "manufacturer": int(row["makers"]["value"]) > 0, "brand": int(row["brands"]["value"]) > 0,
                          "owner": int(row["owners"]["value"]) > 0}
        time.sleep(1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": {"name": "Wikidata", "licence": "CC0 1.0", "retrieved": date.today().isoformat()},
                               "items": out}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(len(out), "items")


if __name__ == "__main__":
    main()
