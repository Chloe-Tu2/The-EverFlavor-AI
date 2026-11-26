"""Q2b phase 0, new story sources: do other-language Wikipedias give the story-less countries' dishes a history
section the English article lacks? Audit only: no story is written, nothing is translated.

    python scripts/knowledge/story_sources.py   # after story_recovery.py

For every dish in the story recovery queue (the countries with no dish story): its French, Spanish, Portuguese and
German articles (Wikidata sitelinks, CC0), and whether each has a section named like History, Origin or Etymology
in that language (the section list only; no text is read or kept). Licence of those articles: CC BY-SA 4.0, with
credit. A person decides whether a non-English source may be used and who translates it (a review item); machine
translation of a story would be AI output, which the evidence tiers never use.
Writes docs/audits/story_source_research.md and data/knowledge/quality/story_source_candidates.json.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from collections import defaultdict
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))   # the shared fetch helpers

import fetch_tools as ft
from quality_reports import read, save_md, table

from everflavor.knowledge import WIKIDATA_USER_AGENT, _sparql

KNOW = ROOT / "data" / "knowledge"
CACHE = ROOT / "data" / "raw" / "knowledge_cache"
LANGS = ["fr", "es", "pt", "de"]
HISTORY = re.compile(r"histo|origin|origem|étymolog|etymolog|etimolog|geschichte|herkunft|tradition|tradici|"
                     r"culture|cultura|kultur", re.IGNORECASE)


def sitelinks(qids: list[str]) -> dict[str, dict[str, str]]:
    """qid -> {language: article title} for the four languages."""
    values = " ".join(f"wd:{q}" for q in qids)
    sites = " ".join(f"<https://{lang}.wikipedia.org/>" for lang in LANGS)
    rows = _sparql(f"""SELECT ?item ?site ?title WHERE {{ VALUES ?item {{ {values} }} VALUES ?site {{ {sites} }}
      ?a schema:about ?item ; schema:isPartOf ?site ; schema:name ?title . }}""", CACHE / "wikidata")
    out: dict[str, dict[str, str]] = defaultdict(dict)
    for r in rows:
        lang = r["site"].split("//")[1].split(".")[0]
        out[r["item"].rsplit("/", 1)[-1]][lang] = r["title"]
    return out


def sections(lang: str, title: str) -> list[str]:
    """The article's section headings, cached."""
    folder = CACHE / f"wikipedia_{lang}"
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / (hashlib.sha1(f"sections:{title}".encode(), usedforsecurity=False).hexdigest()[:16] + ".json")
    data = ft.load_json(file, {}) if file.exists() else {}
    if not data:
        session = requests.Session()
        session.headers["User-Agent"] = WIKIDATA_USER_AGENT
        data = ft.request(session, f"https://{lang}.wikipedia.org/w/api.php", parse=lambda r: r.json(), tries=4,
                          wait=10.0, params={"action": "parse", "page": title, "prop": "sections", "redirects": 1,
                                             "format": "json", "formatversion": 2})
        ft.save_json(data, file)
        time.sleep(1)   # fair use
    return [re.sub(r"<[^>]+>", "", s["line"]) for s in data.get("parse", {}).get("sections", [])]


def main() -> None:
    queue = read(KNOW / "quality" / "story_recovery_queue.json")["dishes"]
    links = sitelinks(sorted({d["qid"] for d in queue}))
    rows, per_country = [], defaultdict(set)
    for d in queue:
        found = {lang: [s for s in sections(lang, t) if HISTORY.search(s)] for lang, t in links.get(d["qid"], {}).items()}
        found = {lang: secs for lang, secs in found.items() if secs}
        if found:
            per_country[d["country"]].add(d["dish"])
        rows.append({"country": d["country"], "dish": d["dish"], "qid": d["qid"],
                     "articles": links.get(d["qid"], {}), "history_sections": found})
    (KNOW / "quality" / "story_source_candidates.json").write_text(json.dumps(
        {"by": "scripts/knowledge/story_sources.py", "built_on": date.today().isoformat(),
         "source": "French, Spanish, Portuguese and German Wikipedia (CC BY-SA 4.0); section headings only",
         "dishes": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    countries = sorted({d["country"] for d in queue})
    with_article = sum(1 for r in rows if r["articles"])
    lines = [f"# Story source research (Q2b phase 0, {date.today().isoformat()})", "",
             (f"{len(countries)} countries have no dish story; their {len(rows)} dishes were checked in four other "
              "Wikipedias. From `scripts/knowledge/story_sources.py`. **Audit only:** only section headings are "
              "read; no text is kept or translated. Using a non-English source, and who translates it, is a "
              "person's choice (a review item)."), "",
             (f"{with_article} of the {len(rows)} dishes have an article in at least one of the four languages; "
              f"{sum(1 for r in rows if r['history_sections'])} have a history, origin, etymology or culture section "
              f"there. That reaches {len(per_country)} of the {len(countries)} countries."), "",
             "## Dishes with a history section in another language", ""]
    lines += table(["Country", "Dish", "Languages and sections"],
                   [[r["country"], r["dish"], "; ".join(f"{lang}: {', '.join(s)}"
                                                       for lang, s in r["history_sections"].items())]
                    for r in rows if r["history_sections"]])
    lines += ["", "## Countries this source does not reach", "",
              ", ".join(c for c in countries if c not in per_country) or "none"]
    save_md("story_source_research.md", lines)
    print(f"{len(rows)} dishes over {len(countries)} countries; history sections elsewhere for "
          f"{sum(1 for r in rows if r['history_sections'])} dishes, {len(per_country)} countries")


if __name__ == "__main__":
    main()
