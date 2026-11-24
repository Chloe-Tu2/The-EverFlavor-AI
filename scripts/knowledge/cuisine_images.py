"""Cuisine image fallbacks (0.8.0): for a dish with no photo of its own, a photo of its country's cuisine, labelled
as such ("a photo of Kenyan cuisine, not this dish"). The image is the one Wikidata names (P18) for the cuisine
article our fetch read; its Commons file must pass the dish photo pipeline's rules (free licence, an author to
credit, a photo, 400 px or more, not a map or logo). Only file information is read; nothing is downloaded, and the
app shows none until a person says `keep` in the review sheet.

    python scripts/knowledge/cuisine_images.py

Writes data/knowledge/media/cuisine_image_queue.json and data/knowledge/review/cuisine_images.csv (people's
verdicts are kept on every run). Run after fetch_knowledge.py.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from image_queue import META, check, fetch_meta

from everflavor.knowledge import _sparql

KNOW = ROOT / "data" / "knowledge"
OUT = KNOW / "media" / "cuisine_image_queue.json"
SHEET = KNOW / "review" / "cuisine_images.csv"
FIELDS = ["risk", "risk_reason", "country", "cuisine_page", "file", "file_page", "licence", "author", "passes",
          "why_not", "verdict",
          "reviewer", "note"]
QUERY = """SELECT ?title ?image WHERE {{
  VALUES ?title {{ {titles} }}
  ?article schema:name ?title ; schema:isPartOf <https://en.wikipedia.org/> ; schema:about ?item .
  ?item wdt:P18 ?image .
}}"""


def cuisine_pages() -> dict[str, list[str]]:
    """Country -> its own cuisine articles, as the fetch names them ("Kenyan cuisine", "Cuisine of Kenya", a page
    in COUNTRY_PAGES), for the countries we have entries for. A neighbour's page never stands in for it."""
    from fetch_knowledge import APP_COUNTRIES, COUNTRY_PAGES
    have = {json.loads(line)["country"] for line in (KNOW / "dishes.jsonl").open(encoding="utf-8")}
    return {c: [f"{APP_COUNTRIES[c]} cuisine", f"Cuisine of {c}", *COUNTRY_PAGES.get(c, [])]
            for c in sorted(have) if c in APP_COUNTRIES}


def _words(text: str) -> str:
    import re
    import unicodedata
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return " " + re.sub(r"[^a-z0-9]+", " ", plain) + " "


def risk(country: str, file: str, description: str, passes: bool, names: dict[str, list[str]],
         dishes: dict[str, set[str]]) -> tuple[str, str]:
    """A first sort for the person who reviews (never a decision): "likely wrong" when the file fails the photo
    rules or its name or description names another country and not this one; "probably right" when it names this
    country or one of its dishes; else "needs a look"."""
    text = _words(f"{file} {description}")
    if not passes:
        return "likely wrong", "fails the photo rules"
    own = any(f" {w} " in text for w in names[country])
    dish = next((d for d in sorted(dishes.get(country, set())) if len(d) > 4 and f" {d} " in text), "")
    other = next((c for c, ws in names.items() if c != country and any(f" {w} " in text for w in ws)), "")
    if other and not own and not dish:
        return "likely wrong", f"names {other}, not {country}"
    if own or dish:
        return "probably right", f"names {country if own else 'its dish ' + dish}"
    return "needs a look", "names neither the country nor one of its dishes"


def is_kept(row: dict) -> bool:
    return row.get("verdict", "").strip().lower() == "keep" and bool(row.get("reviewer", "").strip())


def main() -> None:
    pages = cuisine_pages()
    titles = sorted({t for ts in pages.values() for t in ts})
    images: dict[str, str] = {}
    for i in range(0, len(titles), 50):
        batch = " ".join(json.dumps(t, ensure_ascii=False) + "@en" for t in titles[i:i + 50])
        for r in _sparql(QUERY.format(titles=batch), KNOW.parent / "raw" / "knowledge_cache" / "wikidata"):
            images.setdefault(r["title"], unquote(r["image"].rsplit("/", 1)[-1]).replace("_", " "))
    picked = {c: next(((t, images[t]) for t in ts if t in images), None) for c, ts in pages.items()}
    known = json.loads(META.read_text(encoding="utf-8")) if META.exists() else {}
    known = fetch_meta([p[1] for p in picked.values() if p], known)
    META.write_text(json.dumps(known, ensure_ascii=False, indent=1), encoding="utf-8")

    old = {}
    if SHEET.exists():
        with SHEET.open(encoding="utf-8", newline="") as f:
            old = {r["country"]: r for r in csv.DictReader(f)}
    from fetch_knowledge import APP_COUNTRIES
    names = {c: sorted({_words(c).strip(), _words(a).strip()} - {""}) for c, a in APP_COUNTRIES.items()}
    dishes: dict[str, set[str]] = {}
    for line in (KNOW / "dishes.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        dishes.setdefault(d["country"], set()).add(_words(d["name"].split(" (")[0]).strip())
    rows = []
    for country in sorted(picked):
        if not picked[country]:
            continue
        page, file = picked[country]
        m = known.get(file, {})
        why = check(file, m)
        kept = old.get(country, {}) if old.get(country, {}).get("file") == file else {}
        level, reason = risk(country, file, m.get("description", ""), not why, names, dishes)
        rows.append({"risk": level, "risk_reason": reason, "country": country, "cuisine_page": page, "file": file, "file_page": m.get("file_page", ""),
                     "licence": m.get("license", ""), "author": m.get("author", ""), "passes": "yes" if not why else "no",
                     "why_not": "; ".join(why), **{k: kept.get(k, "") for k in ("verdict", "reviewer", "note")}})
    order = {"likely wrong": 0, "needs a look": 1, "probably right": 2}
    rows.sort(key=lambda r: (order[r["risk"]], r["country"]))
    with SHEET.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    OUT.write_text(json.dumps({
        "by": "scripts/knowledge/cuisine_images.py", "built_on": date.today().isoformat(),
        "rule": "Wikidata P18 of the country's cuisine article; the dish photo pipeline's Commons rules; shown only "
                "after a person's keep, labelled as a photo of the cuisine, not of the dish",
        "countries_with_dishes": len(pages), "with_an_image": len(rows),
        "passing": sum(r["passes"] == "yes" for r in rows), "approved_by_a_person": sum(is_kept(r) for r in rows),
        "images": [{**r, "approved": is_kept(r) and r["passes"] == "yes"} for r in rows]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(pages)} countries; {len(rows)} with a cuisine image; {sum(r['passes'] == 'yes' for r in rows)} pass the "
          f"rules; {sum(is_kept(r) for r in rows)} approved by a person")


if __name__ == "__main__":
    main()
