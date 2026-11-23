"""Region knowledge pages: one JSON per food region of the place tree (West Africa, Polynesia, the Levant ...): its
countries, coverage, representative dishes, common dish families, Indigenous traditions and related regions.
Built only from what we hold (dishes.jsonl, dish_families.json, the coverage and quality audits); never written by
hand or by an AI model. Audit only, for a later Atlas page.

    python scripts/knowledge/region_pages.py

Needs culinary_coverage.py and quality_reports.py first. Writes data/knowledge/atlas/regions/<slug>.json and
docs/audits/region_knowledge.md.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from quality_reports import read, save_md, table

from everflavor.taxonomy import load_taxonomy

KNOW = ROOT / "data" / "knowledge"
OUT = KNOW / "atlas" / "regions"
REQUIRED = ("id", "name", "continent", "countries", "coverage_score", "representative_dishes", "dish_families",
            "sources", "human_reviewed")
SOURCES = [{"name": "Wikipedia", "licence": "CC BY-SA 4.0"}, {"name": "Wikidata", "licence": "CC0"},
           {"name": "Unicode CLDR (regions)", "licence": "Unicode License"}]


def validate(page: dict, countries: set[str]) -> list[str]:
    """What is wrong with a region page (empty when it is fine)."""
    bad = [f"missing {k}" for k in REQUIRED if k not in page]
    bad += [f"unknown country {c}" for c in page.get("countries", []) if c not in countries]
    score = page.get("coverage_score")
    if score is not None and not 0 <= score <= 100:
        bad.append("coverage out of range")
    if not page.get("countries"):
        bad.append("no countries")
    if not page.get("sources"):
        bad.append("no sources")
    if any(t.get("reviewed") is not False for t in page.get("indigenous_traditions", [])):
        bad.append("an Indigenous tag marked reviewed without a person")
    return bad


def main() -> None:
    tax = load_taxonomy()
    dishes = [json.loads(line) for line in (KNOW / "dishes.jsonl").open(encoding="utf-8") if line.strip()]
    fam = read(KNOW / "dish_families.json")
    fam_name = {f["qid"]: f["name"] for f in fam["families"]}
    score = {d["qid"]: d["score"] for d in read(KNOW / "quality" / "dish_quality.json")["dishes"]}
    cover = {c["country"]: c["score"] for c in read(KNOW / "atlas" / "culinary_coverage.json")["countries"]}
    regions = [n for n in tax.nodes.values() if n.level == "region"]
    OUT.mkdir(parents=True, exist_ok=True)
    rows, all_countries = [], {n.name for n in tax.nodes.values() if n.level == "country"}
    for node in sorted(regions, key=lambda n: n.slug):
        countries = sorted(tax.countries_in(node.slug))
        mine = [d for d in dishes if d["country"] in countries]
        real = sorted((d for d in mine if d["kind"] == "dish"), key=lambda d: -score.get(d["qid"], 0))
        families = Counter(fam_name[f] for d in mine for f in fam["dish_families"].get(d["qid"], []) if f in fam_name)
        shared = [n for n, k in Counter(d["name"] for d in real).items() if k > 1]
        scored = [cover[c] for c in countries if c in cover]
        page = {
            "id": node.slug, "name": node.name,
            "continent": tax.nodes[node.parent].name if node.parent in tax.nodes else node.parent,
            "countries": countries,
            "countries_with_a_dish": sorted({d["country"] for d in real}),
            "coverage_score": round(sum(scored) / len(scored), 1) if scored else 0.0,
            "dish_count": len(real), "food_and_drink_count": len(mine) - len(real),
            "story_count": sum(bool(d.get("story_candidates")) for d in mine),
            "representative_dishes": [d["name"] for d in real[:8]],
            "dish_families": [n for n, _ in families.most_common(8)],
            "indigenous_traditions": [{"tradition": t, "foods": k, "reviewed": False} for t, k in sorted(
                Counter(t for d in mine for t in d.get("traditions", [])).items())],
            "related_regions": sorted(n.name for n in regions if n.parent == node.parent and n.slug != node.slug),
            "shared_names": shared, "sources": SOURCES, "human_reviewed": False,
            "built_on": date.today().isoformat(), "by": "scripts/knowledge/region_pages.py",
        }
        problems = validate(page, all_countries)
        if problems:
            raise SystemExit(f"{node.slug}: {problems}")
        (OUT / f"{node.slug}.json").write_text(json.dumps(page, ensure_ascii=False, indent=1), encoding="utf-8")
        rows.append([node.name, page["continent"], len(countries), len(page["countries_with_a_dish"]),
                     page["dish_count"], page["coverage_score"], ", ".join(page["representative_dishes"][:3])])
    lines = [f"# Region knowledge ({date.today().isoformat()})", "",
             ("One page per food region of the place tree, in `data/knowledge/atlas/regions/`, built by "
              "`scripts/knowledge/region_pages.py` from the dishes, families and coverage we hold. Representative "
              "dishes are our best-scored dishes there (`dish_quality.json`), not a judgment of what matters most: "
              "a person reviews each page (`human_reviewed: false`). **Audit only.**"), ""]
    lines += table(["Region", "Continent", "Countries", "With a dish", "Dishes", "Coverage", "Representative"],
                   sorted(rows, key=lambda r: r[5]))
    save_md("region_knowledge.md", lines)
    print("regions:", len(rows))


if __name__ == "__main__":
    main()
