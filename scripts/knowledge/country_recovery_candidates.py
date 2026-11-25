"""Campaign A, the UN members still without a dish: candidate dishes from each country's own cuisine page, with the
evidence a person needs. Audit only: nothing is counted or moved; a person decides each row.

    python scripts/knowledge/country_recovery_candidates.py   # after empty_country_backlog.py

For every empty member with a cuisine page: the articles that page links (read from the fetch's cache) that the
atlas already holds as dishes under another country, and whether the dish's own intro names the empty country
(evidence the multi-origin dish policy allows, rule 3; a mention can still be "also eaten in", so a person checks).
Writes docs/audits/country_recovery_candidates.md and data/knowledge/review/country_recovery_candidates.csv
(verdict `add` makes it a source-backed origin for a later run; verdicts are kept on rerun).
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

import fetch_knowledge as fk
from empty_country_packets import wiki_title
from quality_reports import read, save_md, table

KNOW = ROOT / "data" / "knowledge"
SHEET = KNOW / "review" / "country_recovery_candidates.csv"
FIELDS = ["country", "dish", "qid", "in_atlas_under", "wikidata_origin", "intro_names_country", "intro",
          "verdict", "reviewer", "note"]


def main() -> None:
    backlog = [r for r in read(KNOW / "atlas" / "empty_country_backlog.json")["countries"] if r["cuisine_page"]]
    dishes = [json.loads(line) for line in (KNOW / "dishes.jsonl").open(encoding="utf-8")]
    by_title = {wiki_title(d): d for d in dishes if d.get("kind") == "dish"}
    old: dict[tuple[str, str], dict] = {}
    if SHEET.exists():
        with SHEET.open(encoding="utf-8", newline="") as f:
            old = {(r["country"], r["qid"]): r for r in csv.DictReader(f)}
    rows, summary = [], []
    for b in backlog:
        country = b["country"]
        linked = {r["title"] for r in fk.list_rows(b["cuisine_page"], True)}
        found = [by_title[t] for t in sorted(linked) if t in by_title]
        named = 0
        for d in found:
            says = fk.claims_country(country, d.get("summary", ""), [])
            named += says
            prev = old.get((country, d["qid"]), {})
            rows.append({"country": country, "dish": d["name"], "qid": d["qid"], "in_atlas_under": d["country"],
                         "wikidata_origin": "; ".join(d.get("origin") or []) or "none",
                         "intro_names_country": "yes" if says else "no", "intro": d.get("summary", "")[:200],
                         "verdict": prev.get("verdict", ""), "reviewer": prev.get("reviewer", ""),
                         "note": prev.get("note", "")})
        summary.append([country, b["cuisine_page"], len(linked), len(found), named])
    rows.sort(key=lambda r: (r["intro_names_country"] != "yes", r["country"], r["dish"]))
    with SHEET.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    summary.sort(key=lambda s: (-s[4], -s[3], s[0]))
    strong = [r for r in rows if r["intro_names_country"] == "yes"]
    lines = [f"# Country recovery candidates ({date.today().isoformat()})", "",
             (f"Campaign A: the {len(backlog)} UN members still without a dish that have a cuisine page. Their pages "
              f"link {len(rows)} dishes the atlas already holds under another country; for {len(strong)} the dish's "
              "own intro names the empty country (evidence the multi-origin dish policy allows). From "
              "`scripts/knowledge/country_recovery_candidates.py`. **Audit only:** a person writes `add` or `no` in "
              "`data/knowledge/review/country_recovery_candidates.csv` (intro rows first); nothing counts until then."),
             "", "## Per country", ""]
    lines += table(["Country", "Cuisine page", "Articles linked", "Dishes in the atlas", "Intro names the country"],
                   summary)
    lines += ["", "## Strongest candidates (the intro names the country)", ""]
    lines += table(["Country", "Dish", "In the atlas under", "Wikidata origin"],
                   [[r["country"], r["dish"], r["in_atlas_under"], r["wikidata_origin"]] for r in strong[:60]])
    if len(strong) > 60:
        lines += ["", f"And {len(strong) - 60} more in the sheet."]
    save_md("country_recovery_candidates.md", lines)
    print(f"{len(rows)} candidates for {len(backlog)} countries; intro names the country for {len(strong)}; "
          f"countries with one: {len({r['country'] for r in strong})}")


if __name__ == "__main__":
    main()
