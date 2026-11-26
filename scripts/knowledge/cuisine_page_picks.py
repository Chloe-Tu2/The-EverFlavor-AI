"""Pick sheets for the empty countries whose cuisine page links many articles but none passes the claim rule
(campaign G, manual country research; campaign F, Southern Africa). Audit only: no dish is added and no country is
assigned; a person writes a verdict for each article.

    python scripts/knowledge/cuisine_page_picks.py   # after empty_country_backlog.py

For each UN member without a dish that has a cuisine page: every dish or food article the page links, its first
sentence, Wikidata's origin, whether its intro names the country or its adjective, a wider region ("southern
Africa", "West Africa") or neither, and where the atlas has it now. The claim rule (fetch_knowledge.claims_country)
lets Wikidata's origin decide when it gives one, so an article whose intro names the country but whose origin is
elsewhere is an attribution choice for a person. Writes docs/audits/cuisine_page_picks.md and
data/knowledge/review/cuisine_page_picks.csv (verdicts already given are kept on rerun).
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

import fetch_knowledge as fk
from quality_reports import read, save_md, table

KNOW = ROOT / "data" / "knowledge"
SHEET = KNOW / "review" / "cuisine_page_picks.csv"
FIELDS = ["country", "article", "qid", "kind", "wikidata_origin", "intro_names", "in_atlas_under", "first_sentence",
          "verdict", "note"]
WIDER = re.compile(r"\b(southern|west|western|east|eastern|central|north|northern) africa|\bsahel|\bpolynesia|"
                   r"\bmelanesia|\bmicronesia|\bpacific|\bcaribbean|\bwest indies|\bbalkans|\bcaucasus|\blevant|"
                   r"\barabian|\bgulf\b|\bhorn of africa|\bmaghreb|\bcentral asia", re.IGNORECASE)


def kept_verdicts() -> dict[tuple[str, str], tuple[str, str]]:
    if not SHEET.exists():
        return {}
    with SHEET.open(encoding="utf-8", newline="") as f:
        return {(r["country"], r["qid"]): (r["verdict"], r["note"]) for r in csv.DictReader(f)}


def main() -> None:
    backlog = [c for c in read(KNOW / "atlas" / "empty_country_backlog.json")["countries"] if c.get("cuisine_page")]
    atlas = {d["qid"]: d["country"] for d in (json.loads(line) for line in (KNOW / "dishes.jsonl").open(encoding="utf-8"))}
    foods, dishes_set = fk.food_classes(), fk.food_classes(("Q746549",))
    kept = kept_verdicts()
    rows: list[dict] = []
    for c in backlog:
        country, page = c["country"], c["cuisine_page"]
        titles = list(dict.fromkeys(r["title"] for r in fk.list_rows(page, prose=True)))
        pages = fk.page_items(titles)
        facts = fk.wikidata_facts(sorted({p["qid"] for p in pages.values()}))
        seen: set[str] = set()
        for p in pages.values():
            f = facts.get(p["qid"], {})
            if p["qid"] in seen or not foods.intersection(f.get("types", [])):
                continue   # a place, person or ingredient group, not a dish or food
            seen.add(p["qid"])
            plain = f" {fk._plain_words(p['intro'])} "
            names = ("the country" if fk._first_mention(country, plain) >= 0
                     else (m.group(0).lower() if (m := WIDER.search(p["intro"])) else "neither"))
            verdict, note = kept.get((country, p["qid"]), ("", ""))
            rows.append({"country": country, "article": p["title"], "qid": p["qid"],
                         "kind": "dish" if dishes_set.intersection(f.get("types", [])) else "food or drink",
                         "wikidata_origin": "; ".join(f.get("origin", [])), "intro_names": names,
                         "in_atlas_under": atlas.get(p["qid"], ""),
                         "first_sentence": (fk.sentences(p["intro"]) or [""])[0][:300],
                         "verdict": verdict, "note": note})
    order = {"the country": 0, "neither": 2}
    rows.sort(key=lambda r: (r["country"], order.get(r["intro_names"], 1), r["kind"] != "dish", r["article"]))
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    with SHEET.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    per = Counter(r["country"] for r in rows)
    named = Counter(r["country"] for r in rows if r["intro_names"] == "the country")
    wider = Counter(r["country"] for r in rows if r["intro_names"] not in ("the country", "neither"))
    lines = [f"# Cuisine page pick sheets ({date.today().isoformat()})", "",
             (f"For the {len(backlog)} UN members without a dish that have a cuisine page: {len(rows)} dish or food "
              "articles the page links, none kept by the fetch. From `scripts/knowledge/cuisine_page_picks.py`. "
              "**Audit only:** a person writes a verdict (add, skip) in `data/knowledge/review/cuisine_page_picks.csv`; "
              "nothing is added until then (campaign G, and F for Southern Africa)."), "",
             ("How to read it: \"intro names\" says whether the article's own intro names the country or its "
              "adjective (the strongest lead; the claim rule set it aside because Wikidata gives another origin), a "
              "wider region, or neither. \"In atlas under\" is where the atlas has the article now, if anywhere."), ""]
    lines += table(["Country", "Articles", "Intro names the country", "Intro names a wider region"],
                   [[k, per[k], named[k], wider[k]] for k in sorted(per, key=lambda k: (-named[k], -wider[k], k))])
    lead = [r for r in rows if r["intro_names"] != "neither"]
    lines += ["", "## The strongest leads", "",
              "Articles whose intro names the country or a wider region it belongs to (the full sheet has every article).", ""]
    lines += table(["Country", "Article", "Kind", "Wikidata origin", "Intro names", "In atlas under"],
                   [[r["country"], r["article"], r["kind"], r["wikidata_origin"] or "none", r["intro_names"],
                     r["in_atlas_under"] or "no"] for r in lead[:80]])
    save_md("cuisine_page_picks.md", lines)
    print(f"{len(rows)} articles over {len(per)} countries; intro names the country: {sum(named.values())}; "
          f"a wider region: {sum(wider.values())}")


if __name__ == "__main__":
    main()
