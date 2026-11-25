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
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))   # the shared fetch helpers
import fetch_tools as ft

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
# The atlas sprints (2026-11-22, med27-coder): Africa, the Pacific Islands, the Caribbean, Central America and
# Central Asia; a missing page is skipped. Their cuisine pages also link dishes of other countries (the Belizean
# page links Burrito), so such a page sets a dish's country only when Wikidata's origin or the dish's own intro
# names that country (`claims_country`); otherwise the dish keeps the country another list gives it.
ATLAS_SPRINT_COUNTRIES = {
    "Nigeria": "Nigerian",
    "Ghana": "Ghanaian",
    "Senegal": "Senegalese",
    "Ivory Coast": "Ivorian",
    "Mali": "Malian",
    "Benin": "Beninese",
    "Burkina Faso": "Burkinabé",
    "Guinea": "Guinean",
    "Guinea-Bissau": "Bissau-Guinean",
    "Liberia": "Liberian",
    "Sierra Leone": "Sierra Leonean",
    "The Gambia": "Gambian",
    "Togo": "Togolese",
    "Niger": "Nigerien",
    "Mauritania": "Mauritanian",
    "Cape Verde": "Cape Verdean",
    "Cameroon": "Cameroonian",
    "Gabon": "Gabonese",
    "Chad": "Chadian",
    "Central African Republic": "Central African",
    "Equatorial Guinea": "Equatoguinean",
    "Angola": "Angolan",
    "Congo": "Republic of the Congo",
    "Democratic Republic of the Congo": "Democratic Republic of the Congo",
    "São Tomé and Príncipe": "São Toméan",
    "Kenya": "Kenyan",
    "Tanzania": "Tanzanian",
    "Uganda": "Ugandan",
    "Rwanda": "Rwandan",
    "Burundi": "Burundian",
    "Somalia": "Somali",
    "Eritrea": "Eritrean",
    "Djibouti": "Djiboutian",
    "South Sudan": "South Sudanese",
    "Madagascar": "Malagasy",
    "Mauritius": "Mauritian",
    "Seychelles": "Seychellois",
    "Comoros": "Comorian",
    "Mozambique": "Mozambican",
    "Zambia": "Zambian",
    "Zimbabwe": "Zimbabwean",
    "Malawi": "Malawian",
    "Botswana": "Botswana",
    "Namibia": "Namibian",
    "Lesotho": "Basotho",
    "Eswatini": "Swazi",
    "Algeria": "Algerian",
    "Tunisia": "Tunisian",
    "Libya": "Libyan",
    "Sudan": "Sudanese",
    "Fiji": "Fijian",
    "Papua New Guinea": "Papua New Guinean",
    "Solomon Islands": "Solomon Islands",
    "Vanuatu": "Vanuatuan",
    "Samoa": "Samoan",
    "Tonga": "Tongan",
    "Kiribati": "I-Kiribati",
    "Trinidad and Tobago": "Trinidad and Tobago",
    "Haiti": "Haitian",
    "Dominican Republic": "Dominican Republic",
    "The Bahamas": "Bahamian",
    "Barbados": "Barbadian",
    "Guatemala": "Guatemalan",
    "Honduras": "Honduran",
    "El Salvador": "Salvadoran",
    "Nicaragua": "Nicaraguan",
    "Costa Rica": "Costa Rican",
    "Panama": "Panamanian",
    "Belize": "Belizean",
    "Uzbekistan": "Uzbek",
    "Kazakhstan": "Kazakh",
    "Kyrgyzstan": "Kyrgyz",
    "Tajikistan": "Tajik",
    "Turkmenistan": "Turkmen",
    # Sprint 2 (2026-11-23): the rest of Oceania
    "Tuvalu": "Tuvaluan",
    "Nauru": "Nauruan",
    "Marshall Islands": "Marshallese",
    "Palau": "Palauan",
    "Federated States of Micronesia": "Micronesian",
    "Cook Islands": "Cook Islands",
    "Niue": "Niuean",
    "New Caledonia": "New Caledonian",
    "French Polynesia": "French Polynesian",
    "Guam": "Guamanian",
    "Northern Mariana Islands": "Northern Mariana Islands",
    "American Samoa": "American Samoan",
    # Sprint 3, coverage recovery (2026-11-23): countries with no dish yet. South America
    "Venezuela": "Venezuelan", "Ecuador": "Ecuadorian", "Uruguay": "Uruguayan", "Bolivia": "Bolivian",
    "Paraguay": "Paraguayan", "Guyana": "Guyanese", "Suriname": "Surinamese",
    # Northern and Eastern Europe, the Balkans and the Mediterranean
    "Iceland": "Icelandic", "Estonia": "Estonian", "Latvia": "Latvian", "Lithuania": "Lithuanian",
    "Ukraine": "Ukrainian", "Romania": "Romanian", "Moldova": "Moldovan", "Belarus": "Belarusian",
    "Bulgaria": "Bulgarian", "Slovakia": "Slovak", "Serbia": "Serbian", "Croatia": "Croatian",
    "Bosnia and Herzegovina": "Bosnia and Herzegovina", "Slovenia": "Slovenian", "North Macedonia": "Macedonian",
    "Montenegro": "Montenegrin", "Albania": "Albanian", "Andorra": "Andorran", "Malta": "Maltese",
    "Cyprus": "Cypriot", "Luxembourg": "Luxembourg",
    # Southern Asia
    "Nepal": "Nepalese", "Bangladesh": "Bangladeshi", "Afghanistan": "Afghan", "Sri Lanka": "Sri Lankan",
    "Bhutan": "Bhutanese", "Maldives": "Maldivian",
    # Western Asia and the Caucasus
    "Israel": "Israeli", "Jordan": "Jordanian", "Syria": "Syrian", "Yemen": "Yemeni", "Oman": "Omani",
    "United Arab Emirates": "Emirati", "Qatar": "Qatari", "Kuwait": "Kuwaiti", "Bahrain": "Bahraini",
    "Georgia": "Georgian", "Armenia": "Armenian", "Azerbaijan": "Azerbaijani",
    # East and Southeast Asia
    "Taiwan": "Taiwanese", "Mongolia": "Mongolian", "North Korea": "North Korean", "Laos": "Lao",
    "Myanmar": "Burmese", "Singapore": "Singaporean", "Brunei": "Bruneian", "Timor-Leste": "East Timorese",
    # The Caribbean
    "Dominica": "Dominica", "Cayman Islands": "Caymanian", "Aruba": "Aruban",
    "Antigua and Barbuda": "Antigua and Barbuda", "Grenada": "Grenadian", "Saint Lucia": "Saint Lucian",
    "Saint Vincent and the Grenadines": "Vincentian", "Saint Kitts and Nevis": "Kittitian and Nevisian",
    "Curaçao": "Curaçaoan", "Guadeloupe": "Guadeloupean", "Martinique": "Martinican",
}
APP_COUNTRIES.update(ATLAS_SPRINT_COUNTRIES)
# Indigenous food traditions (sprint 2, 2026-11-23): page -> (its country, or None when Wikidata's origin decides;
# the tradition's name; the words a dish's own intro must use). A dish is tagged with the tradition only when its
# intro names the people, and one found only on such a page is kept only then: never guessed.
INDIGENOUS_PAGES: dict[str, tuple[str | None, str, tuple[str, ...]]] = {
    "Māori cuisine": ("New Zealand", "Māori", ("maori",)),
    "Bush tucker": ("Australia", "Aboriginal Australian", ("aboriginal", "indigenous australian", "bush tucker",
                                                           "bushfood", "bush food")),
    "Native American cuisine": (None, "Native American", ("native american", "indigenous peoples of the americas",
                                                           "first nations", "indigenous")),
    "Indigenous cuisine of the Americas": (None, "Native American", ("native american", "indigenous peoples of the americas",
                                                                     "first nations", "indigenous")),
    "Inuit cuisine": ("Canada", "Inuit", ("inuit", "inuk", "yupik")),
    "Sámi cuisine": (None, "Sámi", ("sami",)),
    "Ainu cuisine": ("Japan", "Ainu", ("ainu",)),
    "Mapuche cuisine": ("Chile", "Mapuche", ("mapuche",)),
    "Native Hawaiian cuisine": ("United States", "Native Hawaiian", ("native hawaiian", "hawaiian")),
    "Chamorro cuisine": ("Guam", "Chamorro", ("chamorro",)),
}


def traditions(lists: list[str], intro: str) -> list[str]:
    """The Indigenous traditions whose page lists the dish and whose people its intro names. A name only inside
    brackets does not count: "Louise cake (keke ruihi in Māori)" gives the name in Māori, not a Māori dish."""
    text = f" {_plain_words(re.sub(r'[(][^()]*[)]', ' ', intro))} "
    return sorted({name for page, (_, name, words) in INDIGENOUS_PAGES.items()
                   if page in lists and any(re.search(rf"\b{re.escape(w)}\b", text) for w in words)})


def _first_mention(country: str, text: str) -> int:
    """Where the plain-words `text` first names `country` or its adjective; -1 when it does not."""
    found = [m.start() for n in {country, APP_COUNTRIES.get(country, country)}
             if (m := re.search(rf"\b{re.escape(_plain_words(n))}\b", text))]
    return min(found) if found else -1


def claims_country(country: str, intro: str, origin: list[str]) -> bool:
    """Whether the sources say a dish is from `country`: Wikidata's origin when it gives one (only then), else the
    dish's intro naming the country or its adjective."""
    if origin:
        return country in origin
    return _first_mention(country, f" {_plain_words(intro)} ") >= 0


def sprint_country(countries: list[str], intro: str, origin: list[str]) -> str | None:
    """Of the sprint countries whose pages list a dish, the one the sources claim: Wikidata's origin first, else
    the one its intro names earliest ("Salvadoran ... also eaten in Guatemala" is El Salvador)."""
    claimed = [c for c in countries if claims_country(c, intro, origin)]
    if origin or not claimed:
        return claimed[0] if claimed else None
    text = f" {_plain_words(intro)} "
    return min(claimed, key=lambda c: _first_mention(c, text))
# Countries whose cuisine page has another title ("Cuisine of Botswana")
COUNTRY_PAGES = {
    'Congo': ['Cuisine of the Republic of the Congo'],
    'Democratic Republic of the Congo': ['Cuisine of the Democratic Republic of the Congo'],
    'São Tomé and Príncipe': ['Cuisine of São Tomé and Príncipe'],
    'Botswana': ['Cuisine of Botswana'],
    'Lesotho': ['Cuisine of Lesotho'],
    'Vanuatu': ['Cuisine of Vanuatu'],
    'Kiribati': ['Cuisine of Kiribati'],
    'Cayman Islands': ['Cuisine of the Cayman Islands'],
}
# The app's regions (country, region as the app names it) -> their Wikipedia pages; a missing page is skipped
APP_REGIONS = {
    ("Mexico", "Baja California"): ["Baja California cuisine", "Cuisine of Baja California"],
    ("Mexico", "Oaxaca"): ["Oaxacan cuisine"],
    ("China", "Beijing"): ["Beijing cuisine"], ("China", "Guangdong"): ["Cantonese cuisine"],
    ("China", "Hunan"): ["Hunan cuisine"], ("China", "Sichuan"): ["Sichuan cuisine"],
    # China by region and province (the focus plan): the rest of the Eight Great Traditions and well-known others
    ("China", "Shandong"): ["Shandong cuisine"], ("China", "Jiangsu"): ["Jiangsu cuisine", "Huaiyang cuisine"],
    ("China", "Zhejiang"): ["Zhejiang cuisine"], ("China", "Fujian"): ["Fujian cuisine"],
    ("China", "Anhui"): ["Anhui cuisine"], ("China", "Shanghai"): ["Shanghai cuisine"],
    ("China", "Yunnan"): ["Yunnan cuisine"], ("China", "Xinjiang"): ["Xinjiang cuisine"],
    ("China", "Hong Kong"): ["Hong Kong cuisine"], ("China", "Northeast China"): ["Northeastern Chinese cuisine"],
    ("China", "Hakka"): ["Hakka cuisine"], ("China", "Teochew"): ["Teochew cuisine"],
    # Mexico by culinary region (the focus plan)
    ("Mexico", "Yucatán"): ["Yucatán cuisine", "Cuisine of Yucatán"], ("Mexico", "Puebla"): ["Cuisine of Puebla"],
    ("Mexico", "Jalisco"): ["Cuisine of Jalisco"], ("Mexico", "Veracruz"): ["Cuisine of Veracruz"],
    ("Mexico", "Michoacán"): ["Cuisine of Michoacán"], ("Mexico", "Mexico City"): ["Cuisine of Mexico City"],
    ("Mexico", "Northern Mexico"): ["Northern Mexican cuisine"],
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
# Mexico's region pages are prose: their links include places, crafts and other states' dishes (the Baja California
# page once made Torta ahogada, a Jalisco dish, "Baja California"). There a region page sets the region only when
# the dish's own intro or Wikidata origin names it (review, 2026-11-11).
PROSE_REGION_COUNTRIES = {"Mexico"}
# When no region page fits, the state the dish's intro or origin names (Mexico by state: the focus plan's divisions)
COUNTRY_DIVISIONS = {"Mexico": [
    "Aguascalientes", "Baja California Sur", "Baja California", "Campeche", "Chiapas", "Chihuahua", "Coahuila",
    "Colima", "Durango", "Guanajuato", "Guerrero", "Hidalgo", "Jalisco", "Mexico City", "Michoacán", "Morelos",
    "Nayarit", "Nuevo León", "Oaxaca", "Puebla", "Querétaro", "Quintana Roo", "San Luis Potosí", "Sinaloa", "Sonora",
    "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatán", "Zacatecas", "State of Mexico"]}


def _plain_words(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def named_region(options: list[str], intro: str, origin: list[str]) -> str | None:
    """The region the dish's intro names first (then its Wikidata origin), among `options`, else None.
    The earliest mention wins: "originated in the town of Motul (Yucatán) ... also in Oaxaca" is Yucatán; a longer
    name wins a tie ("Baja California Sur" over "Baja California")."""
    text = _plain_words(intro + " " + " ".join(origin))
    found = [(text.find(_plain_words(r)), -len(r), r) for r in options if _plain_words(r) in text]
    return min(found)[2] if found else None


# Lists that cover several countries: the dish's country comes from Wikidata's origin when it is an app country
GROUP_LISTS = ["List of Middle Eastern dishes",
               "List of African dishes"]


def sources() -> list[tuple[str | None, str | None, str]]:
    """(country, region, page) for every page to read; group lists have no fixed country."""
    out: list[tuple[str | None, str | None, str]] = []
    for country, adj in APP_COUNTRIES.items():
        out += [(country, None, f"List of {adj} dishes"), (country, None, f"{adj} cuisine")]
        out += [(country, None, page) for page in COUNTRY_PAGES.get(country, [])]
        if country in ATLAS_SPRINT_COUNTRIES and country not in COUNTRY_PAGES:
            out += [(country, None, f"Cuisine of {country}")]   # Kenya's page is "Cuisine of Kenya"
    out += [(country, region, page) for (country, region), pages in APP_REGIONS.items() for page in pages]
    out += [("United States", None, "List of American foods"),
            ("United States", None, "List of regional dishes of the United States")]
    out += [(None, None, page) for page in GROUP_LISTS]
    out += [(country, None, page) for page, (country, _, _) in INDIGENOUS_PAGES.items()]
    out += [(country, None, f"Category:{APP_COUNTRIES[country]} cuisine") for country in ORIGIN_TARGETS
            if country in APP_COUNTRIES]   # sprint 4
    return out


def reads_prose(country: str | None, page: str) -> bool:
    """Whether a page's paragraph links count too: a sprint country's cuisine page (Fiji's is prose, not a list) or
    an Indigenous tradition's page. Dishes found only there need a source's claim (see main)."""
    return page in INDIGENOUS_PAGES or (country in ATLAS_SPRINT_COUNTRIES and not page.startswith("List of"))
STOP_SECTIONS = {"see also", "references", "external links", "further reading", "notes", "gallery", "bibliography"}
# Tags with no closing tag: they must not count in the nesting depth
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
NAME_COLUMNS = re.compile(r"name|dish|food|english", re.IGNORECASE)
REGION_COLUMNS = re.compile(r"region|origin|country|state|province|area|location", re.IGNORECASE)
NOT_DISH_TITLE = re.compile(r"^(List of|Category:|File:|Help:|Wikipedia:|Template|Portal:|Special:)|cuisine$")


class ListPage(HTMLParser):
    """Reads a Wikipedia list page: each row/bullet's first article link, its section and its region cells."""

    def __init__(self, prose: bool = False) -> None:
        super().__init__(convert_charrefs=True)
        self.prose = prose           # also take the article links in paragraphs (marked "prose")
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
                if self.prose and self.cell is None and self.li is None and "p" in self.stack[:-1]:
                    self.rows.append({"title": title, "section": self.section(), "regions": [], "prose": True})

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
    data = ft.load_json(file, {}) if file.exists() else {}   # an unreadable cache file is asked again
    if data:
        return data
    try:
        session = requests.Session()
        session.headers["User-Agent"] = WIKIDATA_USER_AGENT
        data = ft.request(session, WIKIPEDIA_API, parse=lambda r: r.json(), tries=4, wait=10.0,
                          params={**params, "format": "json", "formatversion": 2})
    except ft.FetchError as e:
        raise RuntimeError(f"Wikipedia did not answer ({e}); rerun later (answers so far are cached)") from e
    ft.save_json(data, file)
    time.sleep(1)   # fair use
    return data


def list_rows(page: str, prose: bool = False) -> list[dict]:
    html = _get({"action": "parse", "page": page, "prop": "text", "redirects": 1}, f"parse:{page}")
    if "parse" not in html:
        return []   # no such page
    parser = ListPage(prose)
    parser.feed(html["parse"]["text"])
    return [r for r in parser.rows if not NOT_DISH_TITLE.search(r["title"])]


def category_rows(category: str) -> list[dict]:
    """The articles in a Wikipedia category and in its subcategories of dishes, breads, soups, stews or desserts, one level down (sprint 4).
    Read like a paragraph: a dish found only here is kept only when Wikidata's origin or its intro names the
    country (see main)."""
    def members(title: str, kinds: str) -> list[dict]:
        data = _get({"action": "query", "list": "categorymembers", "cmtitle": title, "cmnamespace": kinds,
                     "cmlimit": 500}, f"category:{title}:{kinds}")
        return data.get("query", {}).get("categorymembers", [])
    found = members(category, "0|14")
    subs = [m["title"] for m in found if m["ns"] == 14 and re.search(r"dishes|breads|soups|stews|desserts",
                                                                      m["title"], re.IGNORECASE)]
    titles = [m["title"] for m in found if m["ns"] == 0] + [m["title"] for c in subs for m in members(c, "0")]
    return [{"title": t, "section": "", "regions": [], "prose": True} for t in dict.fromkeys(titles)
            if not NOT_DISH_TITLE.search(t)]


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
              "P138": "named_after", "P1435": "heritage",
              # who made it first and where (the "what inspired it" facts), and what it was based on
              "P61": "inventor", "P1071": "created_in", "P144": "based_on", "P1889": "not_to_confuse"}


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


# Sprint 4 (2026-11-23, coverage recovery): the countries still weak or not covered after sprint 3
# (docs/audits/country_representation.md). Their cuisine pages are read already, so Wikidata adds the dishes whose
# country of origin (P495) is one of them and that have an English Wikipedia article: dishes only (no foods or
# drinks, which bring brands), and never over a country a cuisine page gives.
ORIGIN_TARGETS = (
    "Algeria", "Antigua and Barbuda", "Aruba", "Bahrain", "Barbados", "Belarus", "Belize", "Benin", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brunei", "Burkina Faso", "Burundi", "Cambodia", "Cameroon",
    "Cape Verde", "Central African Republic", "Chad", "Comoros", "Congo", "Costa Rica", "Curaçao", "Cyprus",
    "Democratic Republic of the Congo", "Djibouti", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Fiji",
    "French Polynesia", "Gabon", "Grenada", "Guadeloupe", "Guinea", "Guinea-Bissau", "Guyana", "Honduras",
    "Ivory Coast", "Jordan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Latvia", "Lesotho", "Liberia", "Libya",
    "Malawi", "Mali", "Martinique", "Mauritania", "Mauritius", "Moldova", "Montenegro", "Mozambique", "Namibia",
    "New Caledonia", "New Zealand", "Niger", "Oman", "Panama", "Papua New Guinea", "Puerto Rico", "Qatar", "Rwanda",
    "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "Saudi Arabia", "Sierra Leone", "Solomon Islands",
    "South Sudan", "Sudan", "Suriname", "Syria", "São Tomé and Príncipe", "Tajikistan", "Tanzania", "The Bahamas",
    "The Gambia", "Timor-Leste", "Togo", "Tonga", "Turkmenistan", "United Arab Emirates", "Vanuatu", "Zambia",
    "Zimbabwe",
    # sprint 5 (2026-11-25, weak regions): the empty UN members and weak countries sprint 4 did not target
    "Andorra", "Dominica", "Federated States of Micronesia", "Marshall Islands", "Nauru", "Northern Mariana Islands",
    "Palau", "Saint Kitts and Nevis", "Tuvalu",
)
WIKIDATA_NAMES ={"Congo": "Republic of the Congo"}   # our name -> the name in data/knowledge/countries.json
ORIGIN_QUERY = """SELECT ?item ?country ?type ?article WHERE {{
  VALUES ?country {{ {countries} }}
  ?item wdt:P495 ?country ; wdt:P31|wdt:P279 ?type .
  ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> .
}}"""


def origin_titles(dish_classes: set[str]) -> dict[str, str]:
    """English article title -> target country, for the dishes whose Wikidata country of origin is a target."""
    known = {c["name"]: c["qid"] for c in json.loads(
        (ROOT / "data" / "knowledge" / "countries.json").read_text(encoding="utf-8"))["countries"]}
    by_qid = {known[WIKIDATA_NAMES.get(n, n)]: n for n in ORIGIN_TARGETS if WIKIDATA_NAMES.get(n, n) in known}
    keys = sorted(by_qid)
    out: dict[str, str] = {}
    for start in range(0, len(keys), 10):
        batch = " ".join(f"wd:{q}" for q in keys[start:start + 10])
        for r in _sparql(ORIGIN_QUERY.format(countries=batch), CACHE / "wikidata"):
            if r["type"].rsplit("/", 1)[-1] in dish_classes:
                title = unquote(r["article"].rsplit("/wiki/", 1)[-1]).replace("_", " ")
                out.setdefault(title, by_qid[r["country"].rsplit("/", 1)[-1]])
    return out


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
# A sentence ends at . ! ? before a capital, but not after an initial or abbreviation ("the U.S. Senate",
# "General J. B. M. Hertzog", "St. Louis", "c. 1850"), which once cut facts in half (review, 2026-11-11)
SENTENCE = re.compile(r"(?<=[.!?])(?<!\b[A-Z]\.)(?<!\bSt\.)(?<!\bDr\.)(?<!\bMr\.)(?<!\bMrs\.)(?<!\bMs\.)"
                      r"(?<!\bGen\.)(?<!\bJr\.)(?<!\bSr\.)(?<!\bNo\.)(?<!\bca\.)(?<!\bc\.)(?<!\bvs\.)\s+(?=[A-Z])")


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
    for country, region, list_page in sources():
        rows = (category_rows(list_page) if list_page.startswith("Category:")
                else list_rows(list_page, reads_prose(country, list_page)))
        if not rows:
            missing.append(list_page)
            continue
        print(f"{country or 'group'} / {region or '-'}: {list_page}: {len(rows)} rows")
        for r in rows:
            if list_page.startswith("Category:"):
                # Sprint 4: a category only adds articles no page gives; it never changes a dish's country
                if r["title"] not in listed:
                    listed[r["title"]] = {"country": country, "region": None, "lists": [list_page], "sections": [],
                                          "regions": [], "countries": [country], "listed": True,
                                          "category_only": True}
                continue
            entry = listed.setdefault(r["title"], {"country": country, "region": region, "lists": [],
                                                   "sections": [], "regions": []})
            if region and region not in entry.setdefault("region_options", []):
                entry["region_options"].append(region)
            if region and not entry["region"]:
                # A region page is the most precise: it sets the region and the country, and its page comes
                # first in "learn more"
                entry["country"], entry["region"] = country, region
                entry["lists"].insert(0, list_page)
            entry["country"] = entry["country"] or country
            if country and country not in entry.setdefault("countries", []):
                entry["countries"].append(country)
            if list_page not in entry["lists"]:
                entry["lists"].append(list_page)
            if not r.get("prose"):
                entry["listed"] = True   # in a list or table, not only named in a paragraph
            if r["section"] and r["section"] not in entry["sections"]:
                entry["sections"].append(r["section"])
            entry["regions"] += [x for x in r["regions"] if x not in entry["regions"]]
    dishes_set = food_classes(("Q746549",))
    added = 0
    for title, country in origin_titles(dishes_set).items():
        if title not in listed:   # a cuisine page's country comes first
            listed[title] = {"country": country, "region": None, "lists": [], "sections": [], "regions": [],
                             "countries": [country], "listed": True, "wikidata_origin": True}
            added += 1
    print(f"Wikidata country of origin (sprint 4): {added} more articles")
    print(f"{len(listed)} different linked articles; no page or no list rows: {len(missing)}")
    if args.dry:
        print("missing:", "; ".join(missing))
        return

    pages = page_items(list(listed))
    facts = wikidata_facts(sorted({p["qid"] for p in pages.values()}))
    foods = food_classes()
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
        region = entry["region"]
        if entry.get("category_only") and not (dishes_set.intersection(f.get("types", []))
                                               and claims_country(country, intro, f.get("origin", []))):
            continue   # only in a category: a dish its Wikidata origin or its own intro gives to the country
        tags = traditions(entry["lists"], intro)
        only_indigenous = all(p in INDIGENOUS_PAGES for p in entry["lists"])
        if only_indigenous and not tags:
            continue   # an Indigenous page links it, but its intro does not name the people
        if not entry.get("listed") and not tags and not (
                country in ATLAS_SPRINT_COUNTRIES
                and sprint_country([c for c in entry.get("countries", []) if c in ATLAS_SPRINT_COUNTRIES],
                                   intro, f.get("origin", []))):
            continue   # only named in a paragraph, and no source claims it for the page's country
        if country in ATLAS_SPRINT_COUNTRIES:
            # A sprint country's page linked it: keep a country the sources claim; else another listing's
            # country, else its Wikidata origin, else it waits
            listing = entry.get("countries", [])
            picked = sprint_country([c for c in listing if c in ATLAS_SPRINT_COUNTRIES], intro, f.get("origin", []))
            others = [c for c in listing if c not in ATLAS_SPRINT_COUNTRIES]
            origin = [o for o in f.get("origin", []) if o in APP_COUNTRIES]
            new_country = next(iter([picked] if picked else others + origin), None)
            if new_country is None:
                continue
            if new_country != country:
                country, region = new_country, None
        url = "https://en.wikipedia.org/wiki/" + page["title"].replace(" ", "_")
        if country in PROSE_REGION_COUNTRIES:
            region = named_region(entry.get("region_options", []) + COUNTRY_DIVISIONS.get(country, []), intro,
                                  f.get("origin", []))
        dishes[page["qid"]] = {
            "qid": page["qid"], "name": page["title"], "country": country, "region": region,
            "kind": "dish" if dishes_set.intersection(f.get("types", [])) else "food or drink",
            "sections": [" > ".join(s) for s in entry["sections"]], "regions": entry["regions"][:6],
            **({"traditions": tags} if tags else {}),
            **({"found_by": "Wikidata country of origin"} if entry.get("wikidata_origin") else {}),
            "summary": (sentences(intro) or [""])[0],
            "fun_fact_candidates": fact_candidates(intro),
            "story_candidates": [x for x in stories.get(page["title"], []) if x not in fact_candidates(intro)],
            **{k: v for k, v in f.items() if k != "types"},
            "sources": [{"name": "Wikidata", "url": f"https://www.wikidata.org/wiki/{page['qid']}", "licence": "CC0"},
                        {"name": f"Wikipedia: {page['title']}", "url": url, "licence": "CC BY-SA 4.0",
                         "credit": "Wikipedia contributors"},
                        *({"name": f"Wikipedia: {name}", "licence": "CC BY-SA 4.0"} for name in entry["lists"])],
            "learn_more": learn_more(page["title"], page["title"], page["qid"], [p for p in entry["lists"] if not p.startswith("Category:")],
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
