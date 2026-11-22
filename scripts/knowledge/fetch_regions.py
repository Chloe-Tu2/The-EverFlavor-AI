"""The UN's world regions (M49) for every country, as Unicode CLDR publishes them, for the atlas audit.

CLDR's territory containment (World > continent > subregion > country) and its English names, from the official
JSON (github.com/unicode-org/cldr-json, Unicode License V3, free to use with this notice: "Copyright (c) 2015-2024
Unicode, Inc."). Only the main tree is read, not CLDR's extra groupings (the EU, the Eurozone, the UN itself).

    python scripts/knowledge/fetch_regions.py    # data/knowledge/atlas/regions.json
"""
from __future__ import annotations

import json
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "knowledge" / "atlas" / "regions.json"
UA = {"User-Agent": "EverFlavorAtlas/0.1 (student project; https://github.com/Chloe-Tu2/The-EverFlavor-AI)"}
CONTINENTS = ("002", "019", "142", "150", "009")   # Africa, the Americas, Asia, Europe, Oceania


def get(path: str) -> dict:
    url = f"https://raw.githubusercontent.com/unicode-org/cldr-json/main/cldr-json/{path}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def regions(tree: dict[str, list[str]], names: dict[str, str]) -> dict[str, dict[str, str]]:
    """ISO code -> its continent and the smallest region holding it ("Western Europe", "Caribbean")."""
    out: dict[str, dict[str, str]] = {}

    def walk(code: str, continent: str, parent: str) -> None:
        for child in tree.get(code, []):
            if child.isalpha():                                  # a country or territory (two letters)
                out[child] = {"continent": names[continent], "subregion": names[parent]}
            else:                                                # a region (three digits)
                walk(child, continent, child)

    for c in CONTINENTS:
        walk(c, c, c)
    return out


def main() -> None:
    data = get("cldr-core/supplemental/territoryContainment.json")["supplemental"]
    tree = {k: v["_contains"] for k, v in data["territoryContainment"].items() if "-status-" not in k}
    names = get("cldr-localenames-full/main/en/territories.json")["main"]["en"]["localeDisplayNames"]["territories"]
    found = regions(tree, names)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "source": {"name": "Unicode CLDR territory containment (UN M49 regions)",
                   "version": data["version"]["_cldrVersion"], "url": "https://github.com/unicode-org/cldr-json",
                   "licence": "Unicode License V3; Copyright (c) 2015-2024 Unicode, Inc.",
                   "retrieved": date.today().isoformat()},
        "countries": dict(sorted(found.items()))}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
        newline="\n")
    subs = {v["subregion"] for v in found.values()}
    print(f"{len(found)} countries and territories in {len(subs)} regions")


if __name__ == "__main__":
    main()
