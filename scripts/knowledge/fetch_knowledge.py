"""Collect sourced dish knowledge for the waiter (the waiter plan, phase 1; kept local until it is done).

Nobody writes the facts by hand: they come from open sources that already hold them.
- Wikipedia's curated dish lists for the focus areas (USA, Mexico, China, the Middle East, Africa) give the
  best-known dishes and, from their section headings and table columns, the region (division) of each.
- Wikidata (CC0) keeps only real foods and dishes (by type) and adds origin, start year, ingredients, namesake and
  heritage listings.
- Each dish's English Wikipedia intro (CC BY-SA 4.0, credit per article) gives a summary and fact-like sentences,
  kept as fun-fact *candidates*. Claude tidies them in the knowledge notebook; nothing is invented.

Output: data/knowledge/dishes.jsonl (one dish per line, with its sources and licences). Raw answers are cached in
data/raw/knowledge_cache/ (git-ignored), so a rerun only asks for what is missing.

    python scripts/knowledge/fetch_knowledge.py            # all focus areas
    python scripts/knowledge/fetch_knowledge.py --dry      # list counts only, writes nothing in data/knowledge
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from everflavor.knowledge import WIKIDATA_USER_AGENT, _sparql

CACHE = ROOT / "data" / "raw" / "knowledge_cache"
OUT = ROOT / "data" / "knowledge" / "dishes.jsonl"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

# Start with what the app shows now: every country in its Country list (50+ recipes, 2026-11-10) and every region
# in its region list. Other countries come later (add them here). Country -> its adjective in page titles.
APP_COUNTRIES = {
    "United States": "American", "Italy": "Italian", "Mexico": "Mexican", "France": "French", "India": "Indian",
    "China": "Chinese", "Canada": "Canadian", "United Kingdom": "British", "Greece": "Greek",
    "Australia": "Australian", "Thailand": "Thai", "Japan": "Japanese", "Spain": "Spanish", "Morocco": "Moroccan",
    "Germany": "German", "Ireland": "Irish", "South Korea": "Korean", "South Africa": "South African",
    "Lebanon": "Lebanese", "Vietnam": "Vietnamese", "Turkey": "Turkish", "Sweden": "Swedish", "Russia": "Russian",
    "Portugal": "Portuguese", "Iran": "Iranian", "Poland": "Polish", "Jamaica": "Jamaican", "Cuba": "Cuban",
    "New Zealand": "New Zealand", "Hungary": "Hungarian", "Switzerland": "Swiss", "Brazil": "Brazilian",
    "Denmark": "Danish", "Philippines": "Filipino", "Netherlands": "Dutch", "Indonesia": "Indonesian",
    "Egypt": "Egyptian", "Norway": "Norwegian", "Finland": "Finnish", "Belgium": "Belgian",
    "Argentina": "Argentine", "Austria": "Austrian", "Peru": "Peruvian", "Czech Republic": "Czech",
    "Pakistan": "Pakistani", "Malaysia": "Malaysian", "Ethiopia": "Ethiopian", "Saudi Arabia": "Saudi Arabian",
    "Puerto Rico": "Puerto Rican", "Chile": "Chilean", "Colombia": "Colombian", "Iraq": "Iraqi",
    "Cambodia": "Cambodian", "Palestine": "Palestinian",
}
# The app's regions (country, region as the app names it) -> their Wikipedia pages; a missing page is skipped
APP_REGIONS = {
    ("Mexico", "Baja California"): ["Baja California cuisine", "Cuisine of Baja California"],
    ("Mexico", "Oaxaca"): ["Oaxacan cuisine"],
    ("China", "Beijing"): ["Beijing cuisine"], ("China", "Guangdong"): ["Cantonese cuisine"],
    ("China", "Hunan"): ["Hunan cuisine"], ("China", "Sichuan"): ["Sichuan cuisine"],
    ("Canada", "British Columbia"): ["Cuisine of British Columbia"], ("Canada", "Ontario"): ["Cuisine of Ontario"],
    ("Canada", "Quebec"): ["Quebec cuisine"],
    ("United Kingdom", "England"): ["English cuisine"], ("United Kingdom", "Scotland"): ["Scottish cuisine"],
    ("United Kingdom", "Wales"): ["Welsh cuisine"],
    ("United States", "California"): ["California cuisine"],
    ("United States", "Hawaii"): ["Cuisine of Hawaii"],
    ("United States", "Louisiana"): ["Louisiana Creole cuisine", "Cajun cuisine"],
    ("United States", "Midwestern US"): ["Midwestern cuisine", "Cuisine of the Midwestern United States"],
    ("United States", "Northeastern US"): ["Cuisine of New England", "Cuisine of the Mid-Atlantic United States"],
    ("United States", "Pacific Northwest"): ["Cuisine of the Pacific Northwest"],
    ("United States", "Pennsylvania"): ["Pennsylvania Dutch cuisine", "Cuisine of Philadelphia"],
    ("United States", "Southern US"): ["Cuisine of the Southern United States", "Soul food"],
    ("United States", "Southwestern US"): ["Cuisine of the Southwestern United States", "New Mexican cuisine"],
    ("United States", "Texas"): ["Texan cuisine", "Tex-Mex"],
}
# Lists that cover several countries: the dish's country comes from Wikidata's origin when it is an app country
GROUP_LISTS = ["List of Middle Eastern dishes",
               "List of African dishes"]


def sources() -> list[tuple[str | None, str | None, str]]:
    """(country, region, page) for every page to read; group lists have no fixed country."""
    out: list[tuple[str | None, str | None, str]] = []
    for country, adj in APP_COUNTRIES.items():
        out += [(country, None, f"List of {adj} dishes"), (country, None, f"{adj} cuisine")]
    out += [(country, region, page) for (country, region), pages in APP_REGIONS.items() for page in pages]
    out += [("United States", None, "List of American foods"),
            ("United States", None, "List of regional dishes of the United States")]
    out += [(None, None, page) for page in GROUP_LISTS]
    return out
STOP_SECTIONS = {"see also", "references", "external links", "further reading", "notes", "gallery", "bibliography"}
# Tags with no closing tag: they must not count in the nesting depth
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
NAME_COLUMNS = re.compile(r"name|dish|food|english", re.IGNORECASE)
REGION_COLUMNS = re.compile(r"region|origin|country|state|province|area|location", re.IGNORECASE)
NOT_DISH_TITLE = re.compile(r"^(List of|Category:|File:|Help:|Wikipedia:|Template|Portal:|Special:)|cuisine$")


class ListPage(HTMLParser):
    """Reads a Wikipedia list page: each row/bullet's first article link, its section and its region cells."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.headings: dict[int, str] = {}
        self.level = 0
        self.in_heading = False
        self.heading_text = ""
        self.stopped = False
        self.skip_depth = 0          # inside a navbox, reference list or infobox
        self.stack: list[str] = []
        self.rows: list[dict] = []
        # table state
        self.headers: list[str] = []
        self.cells: list[dict] = []
        self.cell: dict | None = None
        self.li: dict | None = None

    def section(self) -> list[str]:
        return [self.headings[k] for k in sorted(self.headings) if k <= self.level]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in VOID_TAGS:
            return
        a = dict(attrs)
        cls = a.get("class") or ""
        self.stack.append(tag)
        if self.skip_depth:
            self.skip_depth += 1
            return
        if any(c in cls for c in ("navbox", "reflist", "references", "infobox", "sidebar", "mw-editsection",
                                  "hatnote", "toc")):
            self.skip_depth = 1
            return
        if tag in ("h2", "h3", "h4"):
            self.in_heading, self.heading_text = True, ""
            self.level = int(tag[1])
        elif self.stopped:
            return
        elif tag == "tr":
            self.cells = []
        elif tag in ("td", "th"):
            self.cell = {"tag": tag, "text": "", "link": None}
        elif tag == "li":
            self.li = {"text": "", "link": None}
        elif tag == "a":
            href = a.get("href") or ""
            if href.startswith("/wiki/") and ":" not in href[6:]:
                title = unquote(href[6:].split("#")[0]).replace("_", " ")
                for holder in (self.cell, self.li):
                    if holder is not None and holder["link"] is None:
                        holder["link"] = title

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_TAGS:
            return
        if self.stack:
            self.stack.pop()
        if self.skip_depth:
            self.skip_depth -= 1
            return
        if tag in ("h2", "h3", "h4") and self.in_heading:
            self.in_heading = False
            text = self.heading_text.strip()
            self.headings = {k: v for k, v in self.headings.items() if k < self.level}
            self.headings[self.level] = text
            self.stopped = self.level == 2 and text.lower() in STOP_SECTIONS
        elif self.stopped:
            return
        elif tag in ("td", "th") and self.cell is not None:
            self.cells.append(self.cell)
            self.cell = None
        elif tag == "tr":
            if self.cells and all(c["tag"] == "th" for c in self.cells):
                self.headers = [c["text"].strip() for c in self.cells]
            elif self.cells:
                # The dish is in the "Name"/"Dish" column (the first column is often an image), else the first
                # cell with an article link
                named = [i for i, h in enumerate(self.headers) if NAME_COLUMNS.search(h)]
                order = named + [i for i in range(len(self.cells)) if i not in named]
                link = next((self.cells[i]["link"] for i in order if i < len(self.cells) and self.cells[i]["link"]),
                            None)
                regions = [c["text"].strip() for h, c in zip(self.headers, self.cells, strict=False)
                           if REGION_COLUMNS.search(h) and c["text"].strip()]
                if link:
                    self.rows.append({"title": link, "section": self.section(), "regions": regions})
        elif tag == "li" and self.li is not None:
            if self.li["link"] and "td" not in self.stack:
                self.rows.append({"title": self.li["link"], "section": self.section(), "regions": []})
            self.li = None
        elif tag == "table":
            self.headers = []

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.in_heading:
            self.heading_text += data
        for holder in (self.cell, self.li):
            if holder is not None:
                holder["text"] += data


def _get(params: dict, cache_name: str) -> dict:
    """One Wikipedia API call, cached; waits and retries when the API is busy."""
    folder = CACHE / "wikipedia"
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / (hashlib.sha1(cache_name.encode(), usedforsecurity=False).hexdigest()[:16] + ".json")
    if file.exists():
        return json.loads(file.read_text(encoding="utf-8"))
    for attempt in range(4):
        try:
            response = requests.get(WIKIPEDIA_API, timeout=60, headers={"User-Agent": WIKIDATA_USER_AGENT},
                                    params={**params, "format": "json", "formatversion": 2})
        except (requests.ConnectionError, requests.Timeout):
            time.sleep(10 * (attempt + 1))   # a dropped connection: wait and try again
            continue
        if response.status_code in (429, 500, 502, 503, 504):
            time.sleep(10 * (attempt + 1))
            continue
        response.raise_for_status()
        data = response.json()
        file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        time.sleep(1)   # fair use
        return data
    raise RuntimeError("Wikipedia kept answering 'busy'; rerun later (answers so far are cached)")


def list_rows(page: str) -> list[dict]:
    html = _get({"action": "parse", "page": page, "prop": "text", "redirects": 1}, f"parse:{page}")
    if "parse" not in html:
        return []   # no such page
    parser = ListPage()
    parser.feed(html["parse"]["text"])
    return [r for r in parser.rows if not NOT_DISH_TITLE.search(r["title"])]


def page_items(titles: list[str]) -> dict[str, dict]:
    """Title -> {"qid", "title", "intro"} for existing articles (redirects followed), 20 per request."""
    out: dict[str, dict] = {}
    for start in range(0, len(titles), 20):
        batch = titles[start:start + 20]
        data = _get({"action": "query", "prop": "extracts|pageprops", "ppprop": "wikibase_item", "exintro": 1,
                     "explaintext": 1, "exlimit": 20, "redirects": 1, "titles": "|".join(batch)},
                    "intro:" + "|".join(batch)).get("query", {})
        back: dict[str, str] = {}
        for step in data.get("normalized", []) + data.get("redirects", []):
            back[step["to"]] = back.get(step["from"], step["from"])
        for page in data.get("pages", []):
            qid = page.get("pageprops", {}).get("wikibase_item")
            if qid:
                out[back.get(page["title"], page["title"])] = {"qid": qid, "title": page["title"],
                                                              "intro": page.get("extract", "")}
    return out


FACTS_QUERY = """
SELECT ?dish ?value ?valueLabel WHERE {{
  VALUES ?dish {{ {dishes} }}
  ?dish wdt:{prop} ?value .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}"""
FACT_PROPS = {"P31": "types", "P279": "types", "P495": "origin", "P571": "inception", "P527": "parts", "P186": "made_from",
              "P138": "named_after", "P1435": "heritage"}


def wikidata_facts(qids: list[str]) -> dict[str, dict[str, list[str]]]:
    facts: dict[str, dict[str, list[str]]] = {q: {} for q in qids}
    for prop, field in FACT_PROPS.items():
        for start in range(0, len(qids), 200):
            batch = " ".join(f"wd:{q}" for q in qids[start:start + 200])
            for r in _sparql(FACTS_QUERY.format(dishes=batch, prop=prop), CACHE / "wikidata"):
                if field == "types":
                    value = r["value"].rsplit("/", 1)[-1]
                elif field == "inception":
                    value = r["value"][:5].lstrip("+")   # "+1890-01-01T00:00:00Z" -> "1890"
                else:
                    value = r.get("valueLabel", "")
                    if re.fullmatch(r"Q[0-9]+", value):
                        continue   # no English label
                values = facts[r["dish"].rsplit("/", 1)[-1]].setdefault(field, [])
                if value and value not in values:
                    values.append(value)
    return facts


def food_classes(roots: tuple[str, ...] = ("Q746549", "Q2095", "Q40050")) -> set[str]:
    """Wikidata classes under 'dish' (Q746549), 'food' (Q2095) and 'drink' (Q40050)."""
    classes: set[str] = set()
    for root in roots:
        rows = _sparql(f"SELECT ?c WHERE {{ ?c wdt:P279* wd:{root} }}", CACHE / "wikidata")
        classes |= {r["c"].rsplit("/", 1)[-1] for r in rows}
    return classes


# A sentence worth keeping as a fun-fact candidate has one of these signals (dates, names, stories, records)
FACT_SIGNALS = re.compile(
    r"\b(1[0-9]{3}|20[0-2][0-9]|[0-9]{1,2}(st|nd|rd|th) century|named|invent|originat|legend|believed|"
    r"tradition|popular|famous|known as|UNESCO|festival|introduced|first|record|emperor|dynasty|king|queen|"
    r"street food|celebrat|ritual|symbol|national dish|inspired|created by|based on|adapted|in hono[u]?r of)",
    re.IGNORECASE)
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def sentences(intro: str) -> list[str]:
    return [s.strip() for s in SENTENCE.split(re.sub(r"\s+", " ", intro)) if s.strip()]


def fact_candidates(intro: str) -> list[str]:
    return [s for s in sentences(intro)[1:] if 40 <= len(s) <= 320 and FACT_SIGNALS.search(s)][:8]


# Article sections that hold a dish's story ("== History ==" in the plain-text extract)
STORY_SECTIONS = re.compile(r"histor|origin|etymolog|name|legend|culture|tradition|myth|invent|background|"
                            r"significance|symbolism", re.IGNORECASE)
SECTION_HEADING = re.compile(r"^(={2,4})\s*(.+?)\s*\1\s*$", re.MULTILINE)


def story_sentences(full_text: str, limit: int = 10) -> list[str]:
    """Fact-like sentences from the story sections of a whole article (History, Origin, Etymology, Culture...)."""
    parts = SECTION_HEADING.split(full_text)   # [intro, "==", heading, text, "==", heading, text, ...]
    out: list[str] = []
    for i in range(1, len(parts) - 2, 3):
        if STORY_SECTIONS.search(parts[i + 1]):
            out += [s for s in sentences(parts[i + 2]) if 40 <= len(s) <= 320 and FACT_SIGNALS.search(s)]
    return list(dict.fromkeys(out))[:limit]


def article_stories(titles: list[str]) -> dict[str, list[str]]:
    """Title -> story sentences; one whole article per request (the API's limit), cached, 1 s apart."""
    out: dict[str, list[str]] = {}
    for n, title in enumerate(titles, 1):
        data = _get({"action": "query", "prop": "extracts", "explaintext": 1, "exsectionformat": "wiki",
                     "redirects": 1, "titles": title}, f"full:{title}").get("query", {})
        text = next((p.get("extract", "") for p in data.get("pages", [])), "")
        out[title] = story_sentences(text)
        if n % 250 == 0:
            print(f"  stories: {n}/{len(titles)} articles", flush=True)
    return out


def wiki_url(title: str) -> str:
    return "https://en.wikipedia.org/wiki/" + quote(title.replace(" ", "_"))


def learn_more(name: str, title: str, qid: str, lists: list[str], heritage: list[str]) -> list[dict]:
    """Where to read more, by how deep the user wants to go (the waiter offers the level that fits their
    settings): "quick" = the dish's article; "more" = its cuisine or region page (history and neighbours);
    "deep" = books (Open Library), UNESCO when the dish is listed there, and the raw facts on Wikidata."""
    links = [{"level": "quick", "title": f"{title} (Wikipedia)", "url": wiki_url(title)}]
    links += [{"level": "more", "title": f"{page} (Wikipedia)", "url": wiki_url(page)}
              for page in lists if not page.startswith("List of regional")][:2]
    if any("UNESCO" in h or "Intangible" in h for h in heritage):
        links.append({"level": "deep", "title": "UNESCO Intangible Cultural Heritage",
                      "url": "https://ich.unesco.org/en/lists?text=" + quote(name)})
    links += [{"level": "deep", "title": f"Books about {name} (Open Library)",
               "url": "https://openlibrary.org/search?q=" + quote(name)},
              {"level": "deep", "title": "All recorded facts (Wikidata)", "url": f"https://www.wikidata.org/wiki/{qid}"}]
    return links


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--dry", action="store_true", help="print list counts only")
    parser.add_argument("--stories", action="store_true",
                        help="also read each article's History/Origin/Culture sections (about 1.5 hours the first time)")
    args = parser.parse_args()

    listed: dict[str, dict] = {}   # title -> where it was listed (country, region, lists, sections, regions)
    missing = []
    for country, region, page in sources():
        rows = list_rows(page)
        if not rows:
            missing.append(page)
            continue
        print(f"{country or 'group'} / {region or '-'}: {page}: {len(rows)} rows")
        for r in rows:
            entry = listed.setdefault(r["title"], {"country": country, "region": region, "lists": [],
                                                   "sections": [], "regions": []})
            if region and not entry["region"]:
                # A region page is the most precise: it sets the region and the country, and its page comes
                # first in "learn more"
                entry["country"], entry["region"] = country, region
                entry["lists"].insert(0, page)
            entry["country"] = entry["country"] or country
            if page not in entry["lists"]:
                entry["lists"].append(page)
            if r["section"] and r["section"] not in entry["sections"]:
                entry["sections"].append(r["section"])
            entry["regions"] += [x for x in r["regions"] if x not in entry["regions"]]
    print(f"{len(listed)} different linked articles; no page or no list rows: {len(missing)}")
    if args.dry:
        print("missing:", "; ".join(missing))
        return

    pages = page_items(list(listed))
    facts = wikidata_facts(sorted({p["qid"] for p in pages.values()}))
    foods = food_classes()
    dishes_set = food_classes(("Q746549",))
    dishes: dict[str, dict] = {}
    stories: dict[str, list[str]] = {}
    if args.stories:
        kept = [p["title"] for t, p in pages.items()
                if foods.intersection(facts.get(p["qid"], {}).get("types", []))]
        stories = article_stories(sorted(set(kept)))
    for title, entry in listed.items():
        page = pages.get(title)
        if not page or page["qid"] in dishes:
            continue
        f = facts.get(page["qid"], {})
        if not foods.intersection(f.get("types", [])):
            continue   # a place, person or ingredient group linked from the list, not a dish or food
        # Group lists name no country: take Wikidata's origin when it is a country the app shows
        country = entry["country"] or next((o for o in f.get("origin", []) if o in APP_COUNTRIES), None)
        if country is None:
            continue   # not from a country the app shows (picked up later)
        intro = page["intro"]
        url = "https://en.wikipedia.org/wiki/" + page["title"].replace(" ", "_")
        dishes[page["qid"]] = {
            "qid": page["qid"], "name": page["title"], "country": country, "region": entry["region"],
            "kind": "dish" if dishes_set.intersection(f.get("types", [])) else "food or drink",
            "sections": [" > ".join(s) for s in entry["sections"]], "regions": entry["regions"][:6],
            "summary": (sentences(intro) or [""])[0],
            "fun_fact_candidates": fact_candidates(intro),
            "story_candidates": [x for x in stories.get(page["title"], []) if x not in fact_candidates(intro)],
            **{k: v for k, v in f.items() if k != "types"},
            "sources": [{"name": "Wikidata", "url": f"https://www.wikidata.org/wiki/{page['qid']}", "licence": "CC0"},
                        {"name": f"Wikipedia: {page['title']}", "url": url, "licence": "CC BY-SA 4.0",
                         "credit": "Wikipedia contributors"},
                        *({"name": f"Wikipedia: {name}", "licence": "CC BY-SA 4.0"} for name in entry["lists"])],
            "learn_more": learn_more(page["title"], page["title"], page["qid"], entry["lists"],
                                     f.get("heritage", [])),
            "reviewed": False,
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as out:
        for d in sorted(dishes.values(), key=lambda x: (x["country"], x["name"].lower())):
            out.write(json.dumps(d, ensure_ascii=False) + "\n")
    by_country: dict[str, int] = {}
    for d in dishes.values():
        by_country[d["country"]] = by_country.get(d["country"], 0) + 1
    print(f"kept {len(dishes)} dishes and foods; by country: {by_country}; "
          f"{sum(bool(d['fun_fact_candidates']) for d in dishes.values())} with fun-fact candidates "
          f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
