"""Taxonomy and culinary region validation: the Food Taxonomy (`data/reference/food_taxonomy.csv`) checked against
the UN's regions (Unicode CLDR, `data/knowledge/atlas/regions.json`) and against what the graph hangs on it.

    python scripts/knowledge/taxonomy_validation.py   # docs/audits/taxonomy_validation_report.md, quality/taxonomy_validation.json

A food region can differ from the UN's statistical one on purpose (the Persian Region holds Iran, which the UN
puts in Southern Asia), so a difference is listed for a person to look at, never changed here. Run after
`atlas_audit.py` and `recipe_graph.py`.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.domain import KnowledgeGraph
from everflavor.taxonomy import load_taxonomy

KNOW = ROOT / "data" / "knowledge"
DOC = ROOT / "docs" / "audits" / "taxonomy_validation_report.md"
OUT = KNOW / "quality" / "taxonomy_validation.json"

# The UN continent or subregions each of our zones and regions is compared with (the closest UN groups; a food
# zone may join or split them, as MENA joins Western Asia and Northern Africa)
ZONE_UN = {"asia": {"Asia"}, "europe": {"Europe"}, "mena": {"Asia", "Africa"}, "africa": {"Africa"},
           "north_america": {"Americas"}, "latin_america": {"Americas"}, "caribbean": {"Americas"},
           "oceania": {"Oceania"}}
REGION_UN = {
    "east_asia": {"Eastern Asia"}, "southeast_asia": {"Southeast Asia"}, "south_asia": {"Southern Asia"},
    "british_isles": {"Northern Europe"}, "western_europe": {"Western Europe"}, "nordic": {"Northern Europe"},
    "central_europe": {"Eastern Europe", "Western Europe"}, "eastern_europe": {"Eastern Europe"},
    "mediterranean_europe": {"Southern Europe"}, "baltic": {"Northern Europe"},
    "levant": {"Western Asia"}, "anatolia": {"Western Asia"}, "persian_region": {"Southern Asia", "Central Asia"},
    "mesopotamia": {"Western Asia"}, "arabian_peninsula": {"Western Asia"}, "caucasus": {"Western Asia"},
    "north_africa": {"Northern Africa"}, "east_africa": {"Eastern Africa"}, "southern_africa": {"Southern Africa"},
    "west_africa": {"Western Africa"}, "central_africa": {"Middle Africa"}, "usa_canada": {"Northern America"},
    "mexico_central_america": {"Central America"}, "south_america": {"South America"},
    "caribbean_islands": {"Caribbean"}, "australasia": {"Australasia"}}
BELOW_COUNTRY = {"state", "division", "culinary_region"}


def main() -> None:
    tax = load_taxonomy()
    regions = json.loads((KNOW / "atlas" / "regions.json").read_text(encoding="utf-8"))["countries"]
    coverage = json.loads((KNOW / "coverage" / "country_coverage.json").read_text(encoding="utf-8"))["countries"]
    iso = {c["country"]: c["iso"] for c in coverage if c["iso"]}
    recipe_from = json.loads((KNOW / "recipe_graph_counts.json").read_text(encoding="utf-8"))["recipe_from_by_place"]
    graph = KnowledgeGraph.load(ROOT).food_graph(tax)
    dishes_at = Counter(e.target for e in graph.edges if e.relation in ("origin", "eaten_in"))

    countries = [n for n in tax.nodes.values() if n.level == "country"]
    no_iso = sorted(n.name for n in countries if n.name not in iso)
    zone_diff, region_diff = [], []
    for n in countries:
        un = regions.get(iso.get(n.name, ""))
        if not un:
            continue
        zone = tax.ancestor(n.slug, "zone")
        region = tax.ancestor(n.slug, "region")
        if zone and un["continent"] not in ZONE_UN.get(zone.slug, set()):
            zone_diff.append({"country": n.name, "zone": zone.name, "un_continent": un["continent"]})
        if region and region.slug in REGION_UN and un["subregion"] not in REGION_UN[region.slug]:
            region_diff.append({"country": n.name, "region": region.name, "un_subregion": un["subregion"]})
    missing = sorted(({"country": c["country"], "dishes": c["dishes"], "recipes": c["recipes"],
                       "un_subregion": regions.get(c["iso"], {}).get("subregion", "")}
                      for c in coverage if not c["in_taxonomy"] and (c["dishes"] or c["recipes"])),
                     key=lambda r: (-r["dishes"], -r["recipes"]))
    below = []
    for n in sorted((n for n in tax.nodes.values() if n.level in BELOW_COUNTRY), key=lambda n: n.slug):
        below.append({"place": n.name, "level": n.level, "country": (tax.ancestor(n.slug, "country") or n).name,
                      "dishes": dishes_at[f"place:{n.slug}"], "recipes_by_label": recipe_from.get(n.name, 0)})
    empty_below = [b for b in below if not b["dishes"] and not b["recipes_by_label"]]
    empty_countries = sorted(n.name for n in countries if not dishes_at[f"place:{n.slug}"]
                             and not recipe_from.get(n.name, 0))
    out = {"about": "The Food Taxonomy against the UN regions (CLDR) and the graph; differences are for review.",
           "built_on": date.today().isoformat(), "by": "scripts/knowledge/taxonomy_validation.py",
           "nodes": dict(Counter(n.level for n in tax.nodes.values())), "structure": "valid (load_taxonomy checks "
           "parents, levels and loops)", "countries_without_iso": no_iso, "zone_differences": zone_diff,
           "region_differences": region_diff, "countries_missing_from_taxonomy": missing,
           "below_country": below, "empty_countries": empty_countries}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    write_doc(out, empty_below)
    print(f"zone diffs {len(zone_diff)}, region diffs {len(region_diff)}, missing countries {len(missing)}, "
          f"empty below-country {len(empty_below)} of {len(below)}, empty countries {len(empty_countries)}")


def write_doc(out: dict, empty_below: list[dict]) -> None:
    by_level = defaultdict(list)
    for b in out["below_country"]:
        by_level[b["level"]].append(b)
    lines = [f"# Taxonomy validation ({out['built_on']})", "",
             ("The Food Taxonomy (`data/reference/food_taxonomy.csv`) checked against the UN's regions (Unicode CLDR, "
             "see the atlas) and against what the Food Graph attaches to it. A food region may differ from the UN's "
             "on purpose, so differences are listed for a person to look at; nothing is changed here. Data: "
             "`data/knowledge/quality/taxonomy_validation.json` (`scripts/knowledge/taxonomy_validation.py`)."), "",
             "## Structure", "",
             (f"Valid: {sum(out['nodes'].values())} places ({', '.join(f'{v} {k}' for k, v in out['nodes'].items())}),"
             " every parent known, every level under an allowed one, no loops (`load_taxonomy` refuses a table "
             "that breaks these)."),
             f"Countries whose name has no ISO code in our country list: {', '.join(out['countries_without_iso']) or 'none'}.",
             "", "## Zones against the UN continents", ""]
    lines += ([f"- {d['country']}: our {d['zone']}, the UN's {d['un_continent']}" for d in out["zone_differences"]]
              or ["Every country's zone matches its UN continent (MENA counts as Asia and Africa)."])
    lines += ["", "## Regions against the UN subregions", "",
              ("Each of our regions is compared with the closest UN subregions (Central Europe with Western and "
              "Eastern Europe, the Persian Region with Southern and Central Asia). A difference is often a food "
              "choice, not an error."), ""]
    lines += ([f"- {d['country']}: our {d['region']}, the UN's {d['un_subregion']}" for d in out["region_differences"]]
              or [(f"None: all {out['nodes'].get('country', 0)} "
                  "countries sit in a region that matches their UN subregion.")])
    lines += ["", "## Countries with dishes or recipes that the taxonomy lacks", "",
              "These cannot be placed on the map or in discovery until a node is added (from a published source):", ""]
    lines += [f"- {m['country']} ({m['un_subregion'] or 'no UN region'}): {m['dishes']} dishes, {m['recipes']} recipes"
              for m in out["countries_missing_from_taxonomy"]] or [("None: every country with a dish or a recipe "
                                                                  "has a node.")]
    lines += ["", "## Culinary regions below a country", "",
              ("States, divisions and culinary regions, with the dishes placed there (Wikidata origin or the "
              "Wikipedia cuisine list) and the recipes whose source labels name them:"), "",
              "| Place | Level | Country | Dishes | Recipes |", "|---|---|---|---:|---:|"]
    lines += [f"| {b['place']} | {b['level']} | {b['country']} | {b['dishes']} | {b['recipes_by_label']} |"
              for lvl in sorted(by_level) for b in by_level[lvl]]
    lines += ["", (f"{len(empty_below)} of {len(out['below_country'])} hold nothing directly (a division may still hold its states and culinary regions): "
              f"{', '.join(b['place'] for b in empty_below) or 'none'}."), "",
              (f"Countries with no dish and no recipe yet ({len(out['empty_countries'])}): "
              f"{', '.join(out['empty_countries']) or 'none'}.")]
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
