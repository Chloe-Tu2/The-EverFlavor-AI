"""Evidence packets for the empty countries whose dishes Wikidata already knows (campaign A, empty country recovery).
Audit only: nothing in the atlas is changed and no country is assigned; a person decides each dish.

    python scripts/knowledge/empty_country_packets.py   # after empty_country_backlog.py

For each "low" country in the backlog: every dish Wikidata gives it as country of origin, whether the atlas has the
dish and under which country, which pages listed it there, and the evidence on each side. Writes
docs/audits/empty_country_packets.md and data/knowledge/review/empty_country_packets.csv (a verdict column a
person fills in; verdicts already given are kept on rerun).
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
from quality_reports import read, save_md, table

KNOW = ROOT / "data" / "knowledge"
SHEET = KNOW / "review" / "empty_country_packets.csv"
FIELDS = ["country", "dish", "qid", "in_atlas_under", "wikidata_origin", "listed_by", "intro_names_country",
          "verdict", "note"]


def wiki_title(d: dict) -> str:
    for s in d.get("sources", []):
        if s.get("url", "").startswith("https://en.wikipedia.org/wiki/"):
            return s["url"].rsplit("/wiki/", 1)[-1].replace("_", " ")
    return d["name"]


def kept_verdicts() -> dict[tuple[str, str], tuple[str, str]]:
    if not SHEET.exists():
        return {}
    with SHEET.open(encoding="utf-8", newline="") as f:
        return {(r["country"], r["dish"]): (r["verdict"], r["note"]) for r in csv.DictReader(f)}


def main() -> None:
    low = [r["country"] for r in read(KNOW / "atlas" / "empty_country_backlog.json")["countries"]
           if r["difficulty"] == "low"]
    dishes = [json.loads(line) for line in (KNOW / "dishes.jsonl").open(encoding="utf-8")]
    by_title = {wiki_title(d): d for d in dishes}
    origins = fk.origin_titles(fk.food_classes(("Q746549",)))
    old = kept_verdicts()
    rows = []
    for country in low:
        for title in sorted(t for t, c in origins.items() if c == country):
            d = by_title.get(title)
            listed = [s["name"].removeprefix("Wikipedia: ") for s in (d or {}).get("sources", [])
                      if s["name"].startswith("Wikipedia: ") and "url" not in s]
            intro = (d or {}).get("summary", "")
            names = fk.APP_COUNTRIES.get(country, country)
            verdict, note = old.get((country, title), ("", ""))
            rows.append({"country": country, "dish": title, "qid": (d or {}).get("qid", ""),
                         "in_atlas_under": d["country"] if d else "not in the atlas",
                         "wikidata_origin": "; ".join((d or {}).get("origin") or [country]),
                         "listed_by": "; ".join(listed), "intro_names_country":
                         "yes" if country in intro or names in intro else "no", "verdict": verdict, "note": note})
    with SHEET.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    absent = sum(r["in_atlas_under"] == "not in the atlas" for r in rows)
    lines = [f"# Empty country evidence packets ({date.today().isoformat()})", "",
             (f"The {len(low)} UN member states with no dish whose dishes Wikidata already knows: {len(rows)} dishes, "
              f"{len(rows) - absent} already in the atlas under another country and {absent} not in the atlas. From "
              "`scripts/knowledge/empty_country_packets.py`. **Audit only:** no dish is moved; a person writes a "
              "verdict (move, keep, both) in `data/knowledge/review/empty_country_packets.csv`."), "",
             ("How to read it: `in_atlas_under` is where the atlas has the dish now and `listed_by` the pages that put "
              "it there (often a region page, review item 25). Wikidata's origin is a stronger signal than a cuisine "
              "page listing, but an attribution dispute stays a person's call."), ""]
    for country in low:
        mine = [r for r in rows if r["country"] == country]
        lines += [f"## {country} ({len(mine)})", ""]
        lines += table(["Dish", "In the atlas under", "Wikidata origin", "Listed by", "Intro names it"],
                       [[r["dish"], r["in_atlas_under"], r["wikidata_origin"], r["listed_by"] or "none",
                         r["intro_names_country"]] for r in mine])
        lines.append("")
    save_md("empty_country_packets.md", lines[:-1])
    print(f"{len(rows)} dishes for {len(low)} countries; {absent} not in the atlas")


if __name__ == "__main__":
    main()
