"""Can Walter answer his five questions for each dish (0.9.0)? What it is, where it is from, why it matters, similar
dishes and its versions, each from a sourced field only. Audit only: nothing is written into the knowledge.

    python scripts/knowledge/walter_gaps.py   # after graph_assets.py and recipe_dish_links.py

- What is it: the Wikipedia summary sentence.
- Where is it from: a country, and Wikidata's origin or a culinary region.
- Why it matters: a story sentence (History, Origin, Culture), a UNESCO or heritage listing, or a fun-fact candidate.
- Similar dishes: a next dish to try along the Food Graph (discovery_paths.json).
- Its versions: Wikidata variants (walter_context.json).

Writes docs/audits/walter_five_questions.md and data/knowledge/quality/walter_gap_queue.json (dishes missing an
answer, those with the most linked recipes first).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from dish_origins import countries_of
from quality_reports import read, save_md, table
from story_rules import has_story

KNOW = ROOT / "data" / "knowledge"
QUESTIONS = ["what is it", "where is it from", "why it matters", "similar dishes", "its versions"]


def answers(d: dict, walter: dict, paths: dict) -> dict[str, bool]:
    w = walter.get(d["qid"], {})
    return {"what is it": bool(d.get("summary")),
            "where is it from": bool(d.get("country")) and bool(d.get("origin") or d.get("region")),
            "why it matters": bool(has_story(d) or d.get("heritage") or d.get("fun_fact_candidates")),
            "similar dishes": bool(paths.get(d["qid"], {}).get("next")),
            "its versions": bool(w.get("variants") or w.get("variants_not_in_everflavor"))}


def main() -> None:
    walter = read(KNOW / "walter_context.json")["dishes"]
    paths = read(KNOW / "discovery_paths.json")["dishes"]
    recipes = {q: v["recipes"] for q, v in read(KNOW / "dish_recipe_counts.json")["dishes"].items()}
    dishes = [json.loads(line) for line in (KNOW / "dishes.jsonl").open(encoding="utf-8")]
    dishes = [d for d in dishes if d.get("kind") == "dish"]
    got = {d["qid"]: answers(d, walter, paths) for d in dishes}
    per_q = {q: sum(a[q] for a in got.values()) for q in QUESTIONS}
    full = Counter(sum(a.values()) for a in got.values())
    queue = sorted(({"qid": d["qid"], "name": d["name"], "country": d["country"], "recipes": recipes.get(d["qid"], 0),
                     "missing": [q for q in QUESTIONS if not got[d["qid"]][q]]} for d in dishes
                    if not all(got[d["qid"]].values())), key=lambda r: (-r["recipes"], len(r["missing"]), r["name"]))
    (KNOW / "quality" / "walter_gap_queue.json").write_text(json.dumps(
        {"by": "scripts/knowledge/walter_gaps.py", "built_on": date.today().isoformat(), "questions": QUESTIONS,
         "dishes": queue}, ensure_ascii=False, indent=1), encoding="utf-8")
    n = len(dishes)
    lines = [f"# Walter's five questions ({date.today().isoformat()})", "",
             ("For each of our dishes, can Walter answer what it is, where it is from, why it matters, similar dishes "
              "and its versions from a sourced field? From `scripts/knowledge/walter_gaps.py`. A missing answer is "
              "never filled in by a model; it waits for a source. **Audit only.**"), ""]
    lines += table(["Question", "Dishes with an answer", "Share"], [[q, f"{per_q[q]:,}", f"{per_q[q] / n:.0%}"]
                                                                    for q in QUESTIONS])
    lines += ["", "## How many of the five each dish answers", ""]
    lines += table(["Answers", "Dishes"], [[k, f"{full[k]:,}"] for k in range(5, -1, -1)])
    lines += ["", "## The most seen dishes with a gap", "",
              "Dishes the app links the most recipes to, first (the full list: `data/knowledge/quality/walter_gap_queue.json`).", ""]
    lines += table(["Dish", "Country", "Recipes linked", "Missing"],
                   [[r["name"], r["country"], f"{r['recipes']:,}", ", ".join(r["missing"])] for r in queue[:25]])
    per_country: dict[str, list[int]] = {}
    for d in dishes:
        for country in countries_of(d):   # the multi-origin dish policy
            per_country.setdefault(country, []).append(sum(got[d["qid"]].values()))
    scores = sorted(({"country": c, "dishes": len(v), "score": round(sum(v) / len(v), 2),
                      "all_five": sum(x == 5 for x in v)} for c, v in per_country.items() if c),
                    key=lambda r: (r["score"], -r["dishes"], r["country"]))
    lines += ["", "## Walter coverage score per country", "",
              (f"The average number of the five questions a country's dishes answer (0 to 5), weakest first; "
               f"{len(scores)} countries, all in `data/knowledge/quality/walter_country_scores.json`. A low score "
               "points to missing stories, origins, variants or graph links there."), ""]
    lines += table(["Country", "Dishes", "Score (of 5)", "Dishes with all five"],
                   [[r["country"], r["dishes"], f"{r['score']:.2f}", r["all_five"]] for r in scores[:25]])
    (KNOW / "quality" / "walter_country_scores.json").write_text(json.dumps(
        {"by": "scripts/knowledge/walter_gaps.py", "built_on": date.today().isoformat(), "countries": scores},
        ensure_ascii=False, indent=1), encoding="utf-8")
    save_md("walter_five_questions.md", lines)
    print(per_q, dict(full))


if __name__ == "__main__":
    main()
