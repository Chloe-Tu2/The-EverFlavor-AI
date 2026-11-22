"""Which of our dishes and their families have an image on Wikidata (P18, a Wikimedia Commons file), for the
media audit. Only the file names are read: no image is downloaded, and nothing is shown before the photo pipeline
(scripts/dish_photos/) checks its licence and the image itself.

    python scripts/knowledge/fetch_image_candidates.py   # data/knowledge/media/wikidata_images.json
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KNOW = ROOT / "data" / "knowledge"
OUT = KNOW / "media" / "wikidata_images.json"
UA = {"User-Agent": "EverFlavorMediaAudit/0.1 (student project; https://github.com/Chloe-Tu2/The-EverFlavor-AI)"}
QUERY = "SELECT ?item (SAMPLE(?img) AS ?image) WHERE { VALUES ?item { %s } ?item wdt:P18 ?img } GROUP BY ?item"


def main() -> None:
    dishes = [json.loads(line) for line in (KNOW / "dishes.jsonl").open(encoding="utf-8")]
    fam = json.loads((KNOW / "dish_families.json").read_text(encoding="utf-8"))
    qids = sorted({d["qid"] for d in dishes if d.get("kind") == "dish"} | {f["qid"] for f in fam["families"]})
    found: dict[str, str] = {}
    for i in range(0, len(qids), 300):
        values = " ".join(f"wd:{q}" for q in qids[i:i + 300])
        url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": QUERY % values, "format": "json"})
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
            for row in json.load(r)["results"]["bindings"]:
                file = urllib.parse.unquote(row["image"]["value"].rsplit("/", 1)[1])
                found[row["item"]["value"].rsplit("/", 1)[1]] = file
        time.sleep(1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": {"name": "Wikidata P18", "licence": "CC0 1.0 (the statement; each file has "
                                          "its own Commons licence)", "retrieved": date.today().isoformat()},
                               "asked": len(qids), "images": found}, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{len(found)} of {len(qids)} items have a Wikidata image")


if __name__ == "__main__":
    main()
