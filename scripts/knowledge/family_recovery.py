"""Q4 family recovery: the countries with no dish in a dish family, and the families their dishes may belong to.
Audit only: no dish is added to a family; a person confirms each candidate.

    python scripts/knowledge/family_recovery.py   # after atlas_health.py

A candidate comes from sourced text only: a known family (dish_families.json, from Wikidata) whose name the dish's
own Wikipedia intro uses ("X is a type of flatbread"), or a family the dish is "based on" in Wikidata (P144).
Writes docs/audits/family_recovery_backlog.md and data/knowledge/quality/family_recovery_queue.json.
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
# family names that are also plain ingredients: an intro naming them says what a dish is made of, not its family
INGREDIENT_WORDS = {"bean", "beef", "pork", "rice", "cheese", "milk", "butter", "flour", "vegetable oil", "cereal",
                    "chili pepper", "salad", "tortilla", "chicken", "fish", "egg", "potato", "maize", "meat"}


def main() -> None:
    debt = read(KNOW / "atlas" / "atlas_debt.json")["countries"]
    targets = {r["country"] for r in debt if "no family" in r["gaps"]}
    families = [f for f in read(KNOW / "dish_families.json")["families"] if f.get("kind") == "family"]
    names = {f["name"].lower(): f for f in families if len(f["name"]) > 3}
    pattern = re.compile(r"\b(" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r")s?\b")
    queue = []
    for line in (KNOW / "dishes.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        if d.get("kind") != "dish":
            continue
        for country in (c for c in countries_of(d) if c in targets):
            summary = (d.get("summary") or "").lower()
            ingredients = {i.lower() for i in d.get("made_from") or []} | INGREDIENT_WORDS
            found = {m.group(1) for m in pattern.finditer(summary)
                     if m.group(1) != d["name"].lower() and m.group(1) not in ingredients}
            based = [b for b in d.get("based_on") or [] if b.lower() in names]
            queue.append({"country": country, "dish": d["name"], "qid": d["qid"],
                          "families_named_in_intro": sorted(names[n]["name"] for n in found),
                          "based_on_family": based})
    queue.sort(key=lambda r: (r["country"], not (r["families_named_in_intro"] or r["based_on_family"]), r["dish"]))
    (KNOW / "quality" / "family_recovery_queue.json").write_text(json.dumps(
        {"by": "scripts/knowledge/family_recovery.py", "built_on": date.today().isoformat(), "dishes": queue},
        ensure_ascii=False, indent=1), encoding="utf-8")
    with_candidate = {r["country"] for r in queue if r["families_named_in_intro"] or r["based_on_family"]}
    lines = [f"# Family recovery backlog (Q4, {date.today().isoformat()})", "",
             (f"{len(targets)} countries have no dish in a dish family. For {len(with_candidate)} of them a dish's own "
              "intro names a known family, or Wikidata says it is based on one. From "
              "`scripts/knowledge/family_recovery.py`. **Audit only:** a person confirms each candidate before a dish "
              "joins a family; the queue is `data/knowledge/quality/family_recovery_queue.json`."), ""]
    lines += table(["Country", "Dish", "Families its intro names", "Based on (Wikidata)"],
                   [[r["country"], r["dish"], ", ".join(r["families_named_in_intro"]) or "none",
                     ", ".join(r["based_on_family"]) or "none"] for r in queue])
    save_md("family_recovery_backlog.md", lines)
    print(f"{len(targets)} countries without a family; candidates for {len(with_candidate)}")


if __name__ == "__main__":
    main()
