"""Three scores per country (sprint 3, coverage recovery): is it covered, is it represented, is it enriched?
A country with one dish is covered; one with ten dishes, families, stories and regions is represented.
Audit only: nothing is changed or shown in the app.

    python scripts/knowledge/country_scores.py

Reads dishes.jsonl, dish_families.json, walter_context.json, discovery_paths.json and
atlas/culinary_coverage.json (run after graph_assets.py and culinary_coverage.py). Writes
data/knowledge/atlas/country_scores.json and docs/audits/country_representation.md.

Scores (proposed by Claude on med27-coder's KPIs, 2026-11-23; needs_human_review item 28):
- coverage: the country has at least one dish (yes or no).
- representation (0-100): the average of depth (dishes / 3, at most 1), the share of dishes in a family, the share
  with a story, and the share with a culinary region (only where the place tree has its culinary regions).
- enrichment (0-100): the average of the shares of dishes with a Wikidata origin, a known variant, a related dish
  (a next dish to try) and two or more of Walter's lines.
- weak representation: covered, but fewer than three dishes or a representation score under 50.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from dish_origins import countries_of
from quality_reports import read, save_md, table
from story_rules import has_story

KNOW = ROOT / "data" / "knowledge"
OUT = KNOW / "atlas" / "country_scores.json"
WEAK_BELOW = 50.0


def share(items: list[dict], test) -> float:
    return sum(bool(test(d)) for d in items) / len(items) if items else 0.0


def scores(dishes: list[dict], families: set[str], walter: dict, paths: dict, has_regions: bool) -> dict:
    """The representation and enrichment scores (0-100) of one country's dishes, with their parts."""
    rep = {"depth": min(len(dishes) / 3, 1.0), "families": share(dishes, lambda d: d["qid"] in families),
           "stories": share(dishes, has_story)}   # the story rule (item 34)
    if has_regions:
        rep["regions"] = share(dishes, lambda d: d.get("region"))
    enr = {"origins": share(dishes, lambda d: d.get("origin")),
           "variants": share(dishes, lambda d: (w := walter.get(d["qid"], {})).get("variants")
                             or w.get("variants_not_in_everflavor")),
           "related": share(dishes, lambda d: paths.get(d["qid"], {}).get("next")
                            or walter.get(d["qid"], {}).get("related")),
           "walter": share(dishes, lambda d: len(walter.get(d["qid"], {}).get("lines", [])) >= 2)}
    return {"representation": round(100 * sum(rep.values()) / len(rep), 1) if dishes else 0.0,
            "enrichment": round(100 * sum(enr.values()) / len(enr), 1) if dishes else 0.0,
            "representation_parts": {k: round(v, 3) for k, v in rep.items()},
            "enrichment_parts": {k: round(v, 3) for k, v in enr.items()}}


def main() -> None:
    by_country: dict[str, list[dict]] = defaultdict(list)
    for line in (KNOW / "dishes.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        if d.get("kind") == "dish":
            for country in countries_of(d):   # the multi-origin dish policy
                by_country[country].append(d)
    families = set(read(KNOW / "dish_families.json").get("dish_families", {}))
    walter = read(KNOW / "walter_context.json")["dishes"]
    paths = read(KNOW / "discovery_paths.json")["dishes"]
    rows = []
    for c in read(KNOW / "atlas" / "culinary_coverage.json")["countries"]:
        dishes = by_country.get(c["country"], [])
        s = scores(dishes, families, walter, paths, bool(c.get("culinary_regions")))
        covered = bool(dishes)
        rows.append({"country": c["country"], "continent": c["continent"], "subregion": c["subregion"],
                     "counted": c["counted"], "dishes": len(dishes), "covered": covered, **s,
                     "weak": covered and (len(dishes) < 3 or s["representation"] < WEAK_BELOW)})
    counted = [r for r in rows if r["counted"]]
    covered = [r for r in counted if r["covered"]]

    def avg(group: list[dict], key: str) -> float:
        return round(sum(r[key] for r in group) / len(group), 1) if group else 0.0

    summary = {"countries": len(counted), "covered": len(covered),
               "with three dishes or more": sum(r["dishes"] >= 3 for r in counted),
               "weak representation": sum(r["weak"] for r in counted),
               "representation (average of covered countries)": avg(covered, "representation"),
               "enrichment (average of covered countries)": avg(covered, "enrichment")}
    continents = {}
    for name in sorted({r["continent"] for r in counted}):
        group = [r for r in counted if r["continent"] == name]
        cov = [r for r in group if r["covered"]]
        continents[name] = {"countries": len(group), "covered": len(cov), "weak": sum(r["weak"] for r in group),
                            "representation": avg(cov, "representation"), "enrichment": avg(cov, "enrichment")}
    targets = {"not covered": sorted(r["country"] for r in counted if not r["covered"]),
               "weak representation": sorted(r["country"] for r in counted if r["weak"])}
    OUT.write_text(json.dumps({"by": "scripts/knowledge/country_scores.py", "built_on": date.today().isoformat(),
                               "rule": __doc__.split("Scores", 1)[1].strip() if __doc__ else "",
                               "summary": summary, "continents": continents, "targets": targets,
                               "countries": rows}, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = [f"# Country representation ({date.today().isoformat()})", "",
             ("Three scores per country from `scripts/knowledge/country_scores.py`: **coverage** (at least one dish), "
              "**representation** (depth, families, stories, culinary regions) and **enrichment** (origins, variants, "
              "related dishes, Walter's lines). Countries of 100,000 people or more. The score rules are a proposal "
              "for review (needs_human_review item 28). **Audit only.**"), ""]
    lines += table(["Measure", "Value"], [[k[0].upper() + k[1:], f"{v:,g}"] for k, v in summary.items()])
    lines += ["", "## By continent", ""]
    lines += table(["Continent", "Countries", "Covered", "Weak", "Representation", "Enrichment"],
                   [[k, v["countries"], v["covered"], v["weak"], v["representation"], v["enrichment"]]
                    for k, v in continents.items()])
    lines += ["", "## Weak representation (the next sprint's targets)", ""]
    lines += table(["Country", "Continent", "Dishes", "Representation", "Enrichment"],
                   [[r["country"], r["continent"], r["dishes"], r["representation"], r["enrichment"]]
                    for r in sorted(counted, key=lambda r: (r["representation"], r["country"])) if r["weak"]])
    lines += ["", "## Not covered yet", "", ", ".join(targets["not covered"]) or "None."]
    save_md("country_representation.md", lines)
    print(summary)


if __name__ == "__main__":
    main()
