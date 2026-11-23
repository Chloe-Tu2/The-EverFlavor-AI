"""Two work queues from the quality files: which dishes gain the most from the least work (the rich-dish upgrade
queue), and what the waiter cannot yet tell about each dish (the Walter enrichment queue). Nothing is filled or
published: each row names the gap, the source or script that can fill it, and how much work that is.

    python scripts/knowledge/enrichment_queues.py

Needs quality_reports.py first (data/knowledge/quality/dish_quality.json). Writes
data/knowledge/quality/rich_dish_upgrade_queue.json, data/knowledge/quality/walter_enrichment_queue.json and
docs/audits/dish_enrichment_queues.md.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from quality_reports import WEIGHTS, read, save_json, save_md, table

KNOW = ROOT / "data" / "knowledge"
TODAY = date.today().isoformat()
STAGED = ROOT / "data" / "raw" / "dish_photos_approved" / "staging.parquet"
RICH = 70
# A gap in the score -> (score part, work: 1 low, 2 medium, 3 high, how it is filled)
FILL = {
    "photo": ("image", 1, "a checked Commons photo is staged: a person signs off its contact sheet"),
    "photo_queue": ("image", 2, "a free Commons photo is approved but failed the photo check: rescue it by eye"),
    "photo_none": ("image", 3, "no free photo found yet: scripts/dish_photos/ on Commons or Openverse"),
    "story": ("history", 2, "fetch_knowledge.py --stories (if its article has a history section)"),
    "fun_facts": ("facts", 2, "fetch_knowledge.py (fun-fact sentences from its intro)"),
    "family": ("family", 2, "notebook 15, when Wikidata files it under a family"),
    "variants": ("variants", 2, "Wikidata: versions of it (P144, subclass of)"),
    "related": ("related", 2, "the Food Graph: comes with a family or versions"),
    "recipe": ("recipe", 3, "a licensed recipe source; never written"),
    "origin": ("country", 3, "Wikidata P495 only: nothing to fill on our side"),
}
WORK = {1: "low", 2: "medium", 3: "high"}


def staged_photos() -> tuple[set[str], set[str]]:
    """(dishes whose fetched photo passed the check, dishes with a fetched photo that failed it)."""
    if not STAGED.exists():
        return set(), set()
    import pandas as pd
    s = pd.read_parquet(STAGED, columns=["dish_qid", "clip_pass"])
    passed = set(s.loc[s.clip_pass.astype(bool), "dish_qid"])
    return passed, set(s.dish_qid) - passed


def upgrade_queue(dishes: list[dict], approved: set[str], passed: set[str], failed: set[str]) -> list[dict]:
    """Every dish that is not rich, with its gaps by work and the score it reaches with the low and medium ones."""
    rows = []
    for d in dishes:
        if d["tier"] == "rich":
            continue
        gaps = []
        for m in d["missing"]:
            key = m
            if m == "photo":
                key = "photo" if d["qid"] in passed else "photo_queue" if d["qid"] in failed | approved else "photo_none"
            if key not in FILL:
                continue
            part, work, how = FILL[key]
            gaps.append({"gap": m, "points": WEIGHTS[part], "work": WORK[work], "how": how})
        if not d["region"]:
            gaps.append({"gap": "region", "points": WEIGHTS["region"], "work": "medium",
                         "how": "a region on Wikidata or the place tree; never guessed"})
        reach = d["score"] + sum(g["points"] for g in gaps if g["work"] != "high")
        low = d["score"] + sum(g["points"] for g in gaps if g["work"] == "low")
        rows.append({"qid": d["qid"], "name": d["name"], "country": d["country"], "score": d["score"],
                     "tier": d["tier"], "score_with_low_work": min(low, 100),
                     "score_with_low_and_medium_work": min(reach, 100),
                     "rich_with_low_work": low >= RICH, "rich_within_reach": reach >= RICH,
                     "gaps": sorted(gaps, key=lambda g: (list(WORK.values()).index(g["work"]), -g["points"]))})
    # Lowest effort first: rich with low work, then rich within reach, then the most points per medium step
    return sorted(rows, key=lambda r: (not r["rich_with_low_work"], not r["rich_within_reach"],
                                       -(r["score_with_low_and_medium_work"] - r["score"]), r["name"]))


def walter_queue(raw: dict[str, dict], walter: dict[str, dict]) -> list[dict]:
    """What the waiter is missing for each dish, from the fields the knowledge notebook keeps."""
    rows = []
    for q, d in raw.items():
        w = walter.get(q, {})
        miss = {
            "history": not d.get("story_candidates"),
            "origin": not d.get("origin"),
            "ingredient_explanation": not d.get("made_from"),
            "interesting_fact": not (d.get("fun_fact_candidates") or d.get("fun_facts_candidates")),
            "related_dishes": not (w.get("related") or w.get("variants")),
        }
        gaps = [k for k, v in miss.items() if v]
        if gaps:
            rows.append({"qid": q, "name": d["name"], "country": d.get("country") or "", "missing": gaps,
                         "lines_now": len(w.get("lines", []))})
    return sorted(rows, key=lambda r: (len(r["missing"]), -r["lines_now"], r["name"]))


def main() -> None:
    quality = read(KNOW / "quality" / "dish_quality.json")["dishes"]
    raw = {d["qid"]: d for d in (json.loads(line) for line in (KNOW / "dishes.jsonl").open(encoding="utf-8"))
           if d["kind"] == "dish"}
    walter = read(KNOW / "walter_context.json")["dishes"]
    approved = {r["dish_id"] for r in read(KNOW / "media" / "approved_image_queue.json")["dishes"]}
    passed, failed = staged_photos()

    up = upgrade_queue(quality, approved, passed, failed)
    low = sum(r["rich_with_low_work"] for r in up)
    reach = sum(r["rich_within_reach"] for r in up)
    work = Counter(g["work"] for r in up for g in r["gaps"])
    save_json("rich_dish_upgrade_queue.json", {
        "by": "scripts/knowledge/enrichment_queues.py",
        "about": ("Dishes that are not rich yet (score under 70), lowest effort first. Each gap names its points in "
                  "the completeness score, the work (low: waiting for a person's check; medium: a script and a "
                  "source we already use; high: a new licensed source or nothing on our side) and how it is "
                  "filled. Nothing here is filled or published."),
        "sources": ["data/knowledge/quality/dish_quality.json", "data/knowledge/media/approved_image_queue.json",
                    "the git-ignored photo staging table (scripts/dish_photos/fetch_approved.py), when present"],
        "photos_staged": bool(passed or failed), "weights": WEIGHTS, "rich_from": RICH, "dishes": up})

    wq = walter_queue(raw, walter)
    gaps = Counter(m for r in wq for m in r["missing"])
    save_json("walter_enrichment_queue.json", {
        "by": "scripts/knowledge/enrichment_queues.py",
        "about": ("What the waiter cannot yet tell about each dish, from the knowledge notebook's fields "
                  "(Wikipedia CC BY-SA sentences, Wikidata CC0 facts). Fewest gaps first: those dishes are one step "
                  "from complete. Technique is not listed: no source we use states it, so it stays unknown."),
        "sources": ["data/knowledge/dishes.jsonl", "data/knowledge/walter_context.json"],
        "fills": {"history": "fetch_knowledge.py --stories", "origin": "Wikidata P495 (nothing on our side)",
                  "ingredient_explanation": "Wikidata P186 (made from)",
                  "interesting_fact": "fetch_knowledge.py (intro sentences)",
                  "related_dishes": "the Food Graph (family, versions)"},
        "dishes": wq})

    n = len(quality)
    lines = [f"# Dish enrichment queues ({TODAY})", "",
             ("Two queues for people, built from the quality files by `scripts/knowledge/enrichment_queues.py`. "
              "Nothing in them is filled or published; each gap names the source or script that can fill it."), "",
             "## Rich-dish upgrade queue", "",
             (f"`data/knowledge/quality/rich_dish_upgrade_queue.json`: the {len(up):,} of {n:,} dishes that are not "
              "rich, lowest effort first."), ""]
    lines += table(["What", "Dishes"], [
        ["become rich with low work only (a staged photo signed off)", f"{low:,}"],
        ["could become rich with low and medium work, at most (if the sources we already use have the facts)", f"{reach:,}"],
        ["stay below rich even then (they need a recipe source, a Wikidata fact or a new photo)", f"{len(up) - reach:,}"]])
    lines += ["", "Gaps by work:", ""]
    lines += table(["Work", "Gaps"], [[k, f"{work[k]:,}"] for k in WORK.values()])
    lines += ["", "The first ten:", ""]
    lines += table(["Dish", "Country", "Score", "With low work", "With low and medium"],
                   [[r["name"], r["country"], r["score"], r["score_with_low_work"],
                     r["score_with_low_and_medium_work"]] for r in up[:10]])
    lines += ["", "## Walter enrichment queue", "",
              (f"`data/knowledge/quality/walter_enrichment_queue.json`: {len(wq):,} of {len(raw):,} dishes miss at "
               "least one thing the waiter tells. Technique is not counted: no source we use states it."), ""]
    lines += table(["Missing", "Dishes", "Filled by"],
                   [[k.replace("_", " "), f"{gaps[k]:,}", v] for k, v in
                    read(KNOW / "quality" / "walter_enrichment_queue.json")["fills"].items()])
    lines += ["", f"Dishes missing only one thing: {sum(len(r['missing']) == 1 for r in wq):,}."]
    save_md("dish_enrichment_queues.md", lines)
    print(f"upgrade queue {len(up)} (rich with low work {low}, within reach {reach}); walter queue {len(wq)}")


if __name__ == "__main__":
    main()
