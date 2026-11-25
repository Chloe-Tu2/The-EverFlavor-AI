"""World culinary coverage: how well each country's food tradition is represented, not how many dishes we hold.

Level 1, five checks per country: at least three representative dishes, a dish family, a cuisine description
(one of its dishes links its cuisine's Wikipedia article), a food history (one of its dishes has story sentences)
and its regional styles (where the place tree has culinary regions, at least one holds a dish; elsewhere the
check does not apply).
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
sys.path.insert(0, str(ROOT / "src"))

from dish_origins import countries_of
from quality_reports import read, save_md, table
from story_rules import has_story

KNOW = ROOT / "data" / "knowledge"
OUT = KNOW / "atlas" / "culinary_coverage.json"
MIN_PEOPLE = 100_000
CHECKS = {"dishes": "three representative dishes", "family": "a dish family",
          "cuisine": "a cuisine description", "history": "a food history",
          "regions": "regional styles (where it has culinary regions)"}


def country_score(checks: dict[str, bool], region_share: float | None, family_share: float) -> float:
    """60 x level-1 checks met / 5 + 20 x level 2 + 20 x level 3; a country with no culinary regions in the place
    tree has no level 2, so the other two levels share its weight (out of 80, scaled to 100)."""
    score = 60 * sum(checks.values()) / len(checks) + 20 * family_share
    return round(score + 20 * region_share if region_share is not None else score * 100 / 80, 1)


SHEET = KNOW / "review" / "indigenous_tags.csv"
SHEET_FIELDS = ["tradition", "food", "qid", "country", "wikipedia", "summary", "verdict", "reviewer", "note"]


def review_sheet(foods: list[dict]) -> dict[tuple[str, str], dict]:
    """Rewrites data/knowledge/review/indigenous_tags.csv with every tag, keeping what people wrote (verdict,
    reviewer, note); returns (tradition, qid) -> its row. A tag is reviewed only with `keep` and a reviewer's name."""
    import csv
    old: dict[tuple[str, str], dict] = {}
    if SHEET.exists():
        with SHEET.open(encoding="utf-8", newline="") as f:
            old = {(r["tradition"], r["qid"]): r for r in csv.DictReader(f)}
    rows = []
    for f in sorted(foods, key=lambda f: (f["tradition"], f["name"])):
        kept = old.get((f["tradition"], f["qid"]), {})
        rows.append({"tradition": f["tradition"], "food": f["name"], "qid": f["qid"], "country": f["country"],
                     "wikipedia": f.get("wikipedia", ""), "summary": f.get("summary", "")[:200],
                     **{k: kept.get(k, "") for k in ("verdict", "reviewer", "note")}})
    with SHEET.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=SHEET_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    gone = [k for k in old if old[k].get("verdict") and k not in {(r["tradition"], r["qid"]) for r in rows}]
    if gone:
        print(f"{len(gone)} reviewed tags are no longer found by the fetch (kept out of the sheet): {gone}")
    return {(r["tradition"], r["qid"]): r for r in rows}


def is_reviewed(row: dict) -> bool:
    return row.get("verdict", "").strip().lower() == "keep" and bool(row.get("reviewer", "").strip())


# Wikidata's names for some UN members -> ours (the Kingdom of the Netherlands is the Netherlands here)
UN_NAMES = {"Kingdom of the Netherlands": "Netherlands", "People's Republic of China": "China",
            "Kingdom of Denmark": "Denmark", "Republic of the Congo": "Congo"}
UN_OBSERVERS = {"Palestine": "Q219060", "Vatican City": "Q237"}
UN_QUERY = """SELECT DISTINCT ?c ?cLabel WHERE {
  ?c p:P463 ?st . ?st ps:P463 wd:Q1065 . FILTER NOT EXISTS { ?st pq:P582 ?end }
  ?c wdt:P31 wd:Q3624078 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}"""


def un_states() -> dict:
    """The usual count beside ours: the 193 UN member states (Wikidata: member of the United Nations, a sovereign
    state) and the 2 observer states (Palestine, Vatican City), and how many have a dish. Our coverage counts CLDR
    countries and territories of 100,000 people or more instead (review item 21)."""
    from everflavor.knowledge import _sparql
    rows = _sparql(UN_QUERY, ROOT / "data" / "raw" / "knowledge_cache" / "wikidata")
    members = sorted({UN_NAMES.get(r["cLabel"], r["cLabel"]) for r in rows})
    have = {c for line in (KNOW / "dishes.jsonl").open(encoding="utf-8")
            for d in [json.loads(line)] if d["kind"] == "dish" for c in countries_of(d)}
    return {"members": len(members), "members_with_a_dish": sum(m in have for m in members),
            "observers": len(UN_OBSERVERS), "observers_with_a_dish": sum(o in have for o in UN_OBSERVERS),
            "members_without_a_dish": [m for m in members if m not in have], "member_states": members}


def write_traditions(foods: list[dict]) -> None:
    """data/knowledge/atlas/indigenous_traditions.json: one object per tradition, for review
    (docs/governance/indigenous_review.md); people's verdicts come from the review sheet."""
    from fetch_knowledge import INDIGENOUS_PAGES
    sheet = review_sheet(foods)
    for f in foods:
        row = sheet[(f["tradition"], f["qid"])]
        f.update({"reviewed": is_reviewed(row), "verdict": row["verdict"] or None, "reviewer": row["reviewer"] or None})
        f.pop("wikipedia", None)
        f.pop("summary", None)
    out = []
    for page, (country, name, _) in INDIGENOUS_PAGES.items():
        if any(t["name"] == name for t in out):
            next(t for t in out if t["name"] == name)["sources"].append(wiki(page))
            continue
        out.append({"name": name, "people": name, "country": country or "several (Wikidata origin decides)",
                    "sources": [wiki(page)],
                    "foods": [{k: v for k, v in f.items() if k != "tradition"} for f in foods if f["tradition"] == name]})
    (OUT.parent / "indigenous_traditions.json").write_text(json.dumps(
        {"by": "scripts/knowledge/culinary_coverage.py", "rubric": "docs/governance/indigenous_review.md",
         "licence": "Wikipedia CC BY-SA 4.0, Wikidata CC0", "traditions": out}, ensure_ascii=False, indent=1),
        encoding="utf-8")


def wiki(page: str) -> dict:
    return {"name": f"Wikipedia: {page}", "url": "https://en.wikipedia.org/wiki/" + page.replace(" ", "_"),
            "licence": "CC BY-SA 4.0"}


def main() -> None:
    atlas = read(KNOW / "atlas" / "coverage_scores.json")["countries"]
    cov = {c["iso"]: c for c in read(KNOW / "coverage" / "country_coverage.json")["countries"] if c["iso"]}
    regions = defaultdict(list)
    for r in read(KNOW / "coverage" / "culinary_region_coverage.json")["regions"]:
        if r.get("in_taxonomy"):
            regions[r["country"]].append(r)
    cuisine, history = set(), set()
    indigenous: dict[str, list[str]] = defaultdict(list)   # tradition -> its dishes and foods (sprint 2)
    foods: list[dict] = []
    for line in (KNOW / "dishes.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        for t in d.get("traditions", []):
            indigenous[t].append(d["name"])
            url = next((x["url"] for x in d["sources"] if x["name"].startswith("Wikipedia: ") and x.get("url")), "")
            foods.append({"tradition": t, "name": d["name"], "qid": d["qid"], "country": d["country"],
                          "kind": d["kind"], "reviewed": False, "wikipedia": url, "summary": d.get("summary", "")})
        if d["kind"] != "dish":
            continue
        if any(lm["level"] == "more" and "cuisine" in lm["url"].lower() for lm in d.get("learn_more", [])):
            cuisine.add(d["country"])
        if has_story(d):   # the story rule (item 34)
            history.update(countries_of(d))   # a dish's story tells of every country it comes from

    rows = []
    for a in atlas:
        c = cov.get(a["iso"], {})
        name = c.get("country", a["country"])
        regs = regions.get(name, [])
        region_share = sum(r["dishes"] > 0 for r in regs) / len(regs) if regs else None
        checks = {"dishes": a["dishes"] >= 3, "family": a["families"] > 0, "cuisine": name in cuisine,
                  "history": name in history, "regions": any(r["dishes"] for r in regs)}
        if not regs:
            checks.pop("regions")   # no culinary regions in the place tree: the check does not apply
        family_share = float(c.get("share_known") or 0.0)
        people = c.get("population") or 0
        rows.append({"country": a["country"], "iso": a["iso"], "continent": a["continent"],
                     "subregion": a["subregion"], "population": people, "counted": people >= MIN_PEOPLE,
                     "dishes": a["dishes"], "recipes": a["recipes"], "level_1": checks,
                     "level_1_met": all(checks.values()), "culinary_regions": len(regs),
                     "level_2": round(region_share, 3) if region_share is not None else None, "level_3": round(family_share, 3),
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
        "rule": {"checks": CHECKS, "score": "60 x level-1 checks met / 5 + 20 x level 2 + 20 x level 3 (no culinary regions: out of 80, scaled to 100)",
                 "counted": f"population >= {MIN_PEOPLE:,} (proposed)"},
        "world": world, "un_states": un_states(), "continents": conts, "subregions": subs, "countries": rows,
        "indigenous_traditions": {k: sorted(v) for k, v in sorted(indigenous.items())}},
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    lines = [f"# World culinary coverage ({date.today().isoformat()})", "",
             ("How well each food tradition is represented, the headline metric from 2026-11-22 (decided by "
              "med27-coder): dish and recipe counts are secondary. Built by `scripts/knowledge/culinary_coverage.py`; "
              "per country: `data/knowledge/atlas/culinary_coverage.json`. **Audit only.**"), "",
             ("**Level 1**, five checks: " + "; ".join(CHECKS.values()) + ". **Level 2:** the share of its "
              "culinary regions that hold a dish. **Level 3:** the share of its dish families' known members we "
              "have. **Coverage** = 60 x level-1 checks met / 5 + 20 x level 2 + 20 x level 3 (a country with no culinary "
              "regions in the place tree: the other levels out of 80, scaled to 100), averaged over the "
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
    write_traditions(foods)
    lines += ["", "## Indigenous food traditions (sprint 2)", "",
              ("A dish or food is tagged with a tradition only when that tradition's Wikipedia page lists it and its "
               "own intro names the people (`fetch_knowledge.INDIGENOUS_PAGES`); never guessed. A person reviews the "
               "tags (`docs/governance/needs_human_review.md`)."), ""]
    lines += table(["Tradition", "Dishes and foods", "Examples"],
                   [[k, len(v), ", ".join(sorted(v)[:6])] for k, v in sorted(indigenous.items())]
                   or [["none yet", 0, ""]])
    save_md("world_culinary_coverage.md", lines)
    print("world", world, {k: v["coverage"] for k, v in conts.items()})


if __name__ == "__main__":
    main()
