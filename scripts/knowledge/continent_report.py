"""One page per continent from the Global Culinary Atlas files: its score, its subregions, the countries with no
dish, the versions we lack and the backlog by status. Audit only: no dish is added or published.

    python scripts/knowledge/continent_report.py

Needs atlas_audit.py first. Writes docs/audits/continent_coverage_report.md.
"""
from __future__ import annotations

import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from quality_reports import read, save_md, table

ATLAS = ROOT / "data" / "knowledge" / "atlas"


def main() -> None:
    scores = read(ATLAS / "coverage_scores.json")
    variants = read(ATLAS / "missing_variants.json")["subregions"]
    backlog = read(ATLAS / "regional_expansion_backlog.json")["subregions"]
    lines = [f"# Coverage by continent ({date.today().isoformat()})", "",
             ("Read from the Global Culinary Atlas files (`data/knowledge/atlas/`, regions from Unicode CLDR) by "
              "`scripts/knowledge/continent_report.py`. How the score works: "
              "[global_culinary_atlas.md](global_culinary_atlas.md). **Audit only:** nothing is added or published."),
             "", "| Continent | Countries | With dishes | Dishes | Recipes | Score | Band |",
             "|---|---:|---:|---:|---:|---:|---|"]
    lines += [f"| {c['continent']} | {c['countries']} | {c['with_dishes']} | {c['dishes']:,} | {c['recipes']:,} | "
              f"{c['score']} | {c['band']} |" for c in scores["continents"]]
    for c in scores["continents"]:
        name = c["continent"]
        subs = [s for s in scores["subregions"] if s["continent"] == name]
        countries = [k for k in scores["countries"] if k["continent"] == name]
        only_recipes = sorted(k["country"] for k in countries if k["coverage"] == "recipes only")
        status = Counter(r["status"] for s in subs for r in backlog.get(s["subregion"], []))
        lacking = sum(len(variants.get(s["subregion"], [])) for s in subs)
        lines += ["", f"## {name}", "",
                  (f"{c['with_dishes']} of {c['countries']} countries and territories have a dish; "
                   f"{len(only_recipes)} have recipes but no dish page; {lacking} versions of dishes we have are "
                   "missing; the backlog holds " + ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in
                                                            sorted(status.items())) + "."), ""]
        lines += table(["Subregion", "Countries", "With dishes", "Dishes", "Score", "Band"],
                       [[s["subregion"], s["countries"], s["with_dishes"], s["dishes"], s["score"], s["band"]]
                        for s in sorted(subs, key=lambda s: s["score"])])
        if only_recipes:
            lines += ["", "Recipes but no dish page: " + ", ".join(only_recipes) + "."]
    save_md("continent_coverage_report.md", lines)
    print("continents:", len(scores["continents"]))


if __name__ == "__main__":
    main()
