"""World culinary coverage: how well each country's food tradition is represented, not how many dishes we hold.

Level 1, five checks per country: at least three representative dishes, a dish family, a cuisine description
(one of its dishes links its cuisine's Wikipedia article), a food history (one of its dishes has story sentences)
and its regional styles (where the place tree has culinary regions, at least one holds a dish).
Level 2: the share of its culinary regions that hold a dish. Level 3: the share of its dish families' known
members we have (`share_known`). Country score = 60 x level-1 checks met / 5 + 20 x level 2 + 20 x level 3.

Counted countries (proposed policy, for the team): every CLDR country or territory with 100,000 people or more
(Wikidata population); smaller ones are listed but not counted, so an uninhabited territory does not pull a
continent down. Audit only: nothing is added or published.

    python scripts/knowledge/culinary_coverage.py

Needs coverage_audit.py and atlas_audit.py first. Writes data/knowledge/atlas/culinary_coverage.json and
docs/audits/world_culinary_coverage.md.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from quality_reports import read, save_md, table

KNOW = ROOT / "data" / "knowledge"
OUT = KNOW / "atlas" / "culinary_coverage.json"
MIN_PEOPLE = 100_000
CHECKS = {"dishes": "three representative dishes", "family": "a dish family",
          "cuisine": "a cuisine description", "history": "a food history",
          "regions": "regional styles (where it has culinary regions)"}


def country_score(checks: dict[str, bool], region_share: float, family_share: float) -> float:
    return round(60 * sum(checks.values()) / len(checks) + 20 * region_share + 20 * family_share, 1)


def main() -> None:
    atlas = read(KNOW / "atlas" / "coverage_scores.json")["countries"]
    cov = {c["iso"]: c for c in read(KNOW / "coverage" / "country_coverage.json")["countries"] if c["iso"]}
    regions = defaultdict(list)
    for r in read(KNOW / "coverage" / "culinary_region_coverage.json")["regions"]:
        if r.get("in_taxonomy"):
            regions[r["country"]].append(r)
    cuisine, history = set(), set()
    for line in (KNOW / "dishes.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        if d["kind"] != "dish":
            continue
        if any(lm["level"] == "more" and "cuisine" in lm["url"].lower() for lm in d.get("learn_more", [])):
            cuisine.add(d["country"])
        if d.get("story_candidates"):
            history.add(d["country"])

    rows = []
    for a in atlas:
        c = cov.get(a["iso"], {})
        name = c.get("country", a["country"])
        regs = regions.get(name, [])
        region_share = sum(r["dishes"] > 0 for r in regs) / len(regs) if regs else 1.0 if a["dishes"] else 0.0
        checks = {"dishes": a["dishes"] >= 3, "family": a["families"] > 0, "cuisine": name in cuisine,
                  "history": name in history, "regions": (not regs and a["dishes"] > 0) or any(r["dishes"] for r in regs)}
        family_share = float(c.get("share_known") or 0.0)
        people = c.get("population") or 0
        rows.append({"country": a["country"], "iso": a["iso"], "continent": a["continent"],
                     "subregion": a["subregion"], "population": people, "counted": people >= MIN_PEOPLE,
                     "dishes": a["dishes"], "recipes": a["recipes"], "level_1": checks,
                     "level_1_met": all(checks.values()), "culinary_regions": len(regs),
                     "level_2": round(region_share, 3), "level_3": round(family_share, 3),
                     "score": country_score(checks, region_share, family_share),
                     "missing": [CHECKS[k] for k, v in checks.items() if not v]})

    def summary(group: list[dict]) -> dict:
        n = [r for r in group if r["counted"]]
        return {"countries": len(n), "level_1": sum(r["level_1_met"] for r in n),
                "with_a_dish": sum(r["dishes"] > 0 for r in n),
                "coverage": round(sum(r["score"] for r in n) / len(n), 1) if n else 0.0}

    by = {"continent": defaultdict(list), "subregion": defaultdict(list)}
    for r in rows:
        by["continent"][r["continent"]].append(r)
        by["subregion"][(r["continent"], r["subregion"])].append(r)
    world = summary(rows)
    conts = {k: summary(v) for k, v in sorted(by["continent"].items())}
    subs = {f"{k[0]} / {k[1]}": summary(v) for k, v in sorted(by["subregion"].items())}
    OUT.write_text(json.dumps({
        "by": "scripts/knowledge/culinary_coverage.py", "built_on": date.today().isoformat(),
        "sources": ("data/knowledge/atlas/coverage_scores.json (Unicode CLDR regions), "
                    "data/knowledge/coverage/ (Wikidata CC0 countries and populations), dishes.jsonl "
                    "(Wikipedia CC BY-SA, Wikidata CC0)"),
        "rule": {"checks": CHECKS, "score": "60 x level-1 checks met / 5 + 20 x level 2 + 20 x level 3",
                 "counted": f"population >= {MIN_PEOPLE:,} (proposed)"},
        "world": world, "continents": conts, "subregions": subs, "countries": rows},
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    lines = [f"# World culinary coverage ({date.today().isoformat()})", "",
             ("How well each food tradition is represented, the headline metric from 2026-11-22 (decided by "
              "med27-coder): dish and recipe counts are secondary. Built by `scripts/knowledge/culinary_coverage.py`; "
              "per country: `data/knowledge/atlas/culinary_coverage.json`. **Audit only.**"), "",
             ("**Level 1**, five checks: " + "; ".join(CHECKS.values()) + ". **Level 2:** the share of its "
              "culinary regions that hold a dish. **Level 3:** the share of its dish families' known members we "
              "have. **Coverage** = 60 x level-1 checks met / 5 + 20 x level 2 + 20 x level 3, averaged over the "
              f"counted countries (CLDR, {MIN_PEOPLE:,} people or more: a proposed rule)."), "",
             (f"**World culinary coverage: {world['coverage']}%.** {world['level_1']} of {world['countries']} "
              f"counted countries meet level 1; {world['with_a_dish']} have at least one dish."), "",
             "## By continent", ""]
    lines += table(["Continent", "Counted countries", "With a dish", "Level 1 met", "Coverage"],
                   [[k, v["countries"], v["with_a_dish"], v["level_1"], f"{v['coverage']}%"] for k, v in conts.items()])
    lines += ["", "## By subregion", ""]
    lines += table(["Continent / subregion", "Counted countries", "With a dish", "Level 1 met", "Coverage"],
                   [[k, v["countries"], v["with_a_dish"], v["level_1"], f"{v['coverage']}%"]
                    for k, v in sorted(subs.items(), key=lambda kv: kv[1]["coverage"])])
    miss = defaultdict(int)
    for r in rows:
        if r["counted"] and r["dishes"]:
            for m in r["missing"]:
                miss[m] += 1
    lines += ["", "## What keeps countries with dishes below level 1", ""]
    lines += table(["Missing", "Countries"], [[k, v] for k, v in sorted(miss.items(), key=lambda kv: -kv[1])])
    africa = sorted((r for r in rows if r["continent"] == "Africa" and r["counted"]), key=lambda r: -r["score"])
    lines += ["", "## Africa, country by country (the first sprint)", ""]
    lines += table(["Country", "Subregion", "Dishes", "Recipes", "Score", "Missing"],
                   [[r["country"], r["subregion"], r["dishes"], f"{r['recipes']:,}", r["score"],
                     ("no dish page yet" if not r["dishes"] else "; ".join(r["missing"]) or "none")] for r in africa if r["dishes"] or r["recipes"]])
    none = [r["country"] for r in africa if not r["dishes"] and not r["recipes"]]
    lines += ["", f"No dish and no recipe yet ({len(none)}): " + ", ".join(none) + "."]
    save_md("world_culinary_coverage.md", lines)
    print("world", world, {k: v["coverage"] for k, v in conts.items()})


if __name__ == "__main__":
    main()
