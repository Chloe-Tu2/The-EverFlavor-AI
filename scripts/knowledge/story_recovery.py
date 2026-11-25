"""Q2 story recovery: the countries with no dish story, and the sourced material that could give them one.
Audit only: no story is written; a person or a later fetch decides.

    python scripts/knowledge/story_recovery.py   # after atlas_health.py

A country has "no story" when none of its dishes has a story sentence (story_candidates: History, Origin, Culture and similar sections). For each
such country, per dish: a history sentence in the dish's own Wikipedia intro (a sentence with a dating or origin
word), and Wikidata facts that tell a story (inception, inventor, named after, based on, created in, heritage).
Writes docs/audits/story_recovery_report.md and data/knowledge/quality/story_recovery_queue.json.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from dish_origins import countries_of
from quality_reports import read, save_md, table

KNOW = ROOT / "data" / "knowledge"
HISTORY_WORDS = re.compile(r"\b(originat\w*|dates? (back|from)|centur(y|ies)|introduc\w*|invent\w*|"
                           r"named (after|for)|first (made|recorded|mentioned)|ancient|colonial|\d{3,4}s?)\b", re.IGNORECASE)
FACTS = ["inception", "inventor", "named_after", "based_on", "created_in", "heritage"]


def intro_history(summary: str) -> str:
    for sentence in re.split(r"(?<=[.!?])\s+", summary or ""):
        if HISTORY_WORDS.search(sentence):
            return sentence.strip()
    return ""


def main() -> None:
    debt = read(KNOW / "atlas" / "atlas_debt.json")["countries"]
    targets = {r["country"]: r for r in debt if "no story" in r["gaps"]}
    dishes = [json.loads(line) for line in (KNOW / "dishes.jsonl").open(encoding="utf-8")]
    queue = []
    for d in dishes:
        if d.get("kind") != "dish":
            continue
        for country in countries_of(d):
            if country not in targets:
                continue
            facts = {k: d[k] for k in FACTS if d.get(k)}
            sentence = intro_history(d.get("summary", ""))
            queue.append({"country": country, "dish": d["name"], "qid": d["qid"], "intro_history": sentence,
                          "wikidata_facts": facts, "has_material": bool(sentence or facts)})
    queue.sort(key=lambda r: (r["country"], not r["has_material"], r["dish"]))
    (KNOW / "quality" / "story_recovery_queue.json").write_text(json.dumps(
        {"by": "scripts/knowledge/story_recovery.py", "built_on": date.today().isoformat(), "dishes": queue},
        ensure_ascii=False, indent=1), encoding="utf-8")
    per = []
    for country in sorted(targets):
        mine = [r for r in queue if r["country"] == country]
        best = next((r for r in mine if r["has_material"]), None)
        per.append([country, len(mine), sum(r["has_material"] for r in mine),
                    f"{best['dish']}: {(best['intro_history'] or json.dumps(best['wikidata_facts']))[:140]}"
                    if best else "none: needs a new source"])
    ready = sum(1 for p in per if p[2])
    lines = [f"# Story recovery (Q2, {date.today().isoformat()})", "",
             (f"{len(targets)} countries have no dish story (no sentence from a History, Origin, Culture or similar section). For {ready} of them a "
              "dish already carries sourced material that could become one: a history sentence in its own "
              "Wikipedia intro, or Wikidata facts (inception, inventor, named after, heritage). From "
              "`scripts/knowledge/story_recovery.py`. **Audit only:** nothing is written as a story; the full queue "
              "is `data/knowledge/quality/story_recovery_queue.json`."), "",
             ("How the material can be used: an intro sentence is already shown as the dish summary, so turning it "
              "into a story needs a person's yes (or a rule change that counts intro history as a story, a "
              "review item). Countries with no material need their dishes' articles read again or a new source."),
             "", "## Per country", ""]
    lines += table(["Country", "Dishes", "With material", "Best material"], per)
    save_md("story_recovery_report.md", lines)
    print(f"{len(targets)} countries without a story; material for {ready}")


if __name__ == "__main__":
    main()
