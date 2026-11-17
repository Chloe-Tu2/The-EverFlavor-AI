"""Free Commons photos for photo-less recipes of ONE region, found through Wikidata (native dish names).

English recipe titles miss Commons files that carry the dish's own name. This script asks Wikidata for the food items
of a region's countries (with English aliases, native labels, the P18 image and the P373 Commons category), matches
photo-less recipes of that region to them by name, and looks for a free photo of each matched item.

Run from the project folder, one region at a time:

    python -I scripts/dish_photos/fetch_regional.py search --region india --dry --report FILE.json
    python -I scripts/dish_photos/fetch_regional.py search --region india --limit 400 --dry --report FILE.json
    python -I scripts/dish_photos/fetch_regional.py search --region india          # write (appends rows only)

--limit N takes the N matched items that cover the most recipes. --dry writes nothing but caches and the report.

Sources (official APIs only, one request a second, maxlag=5, backing off on 429):
  query.wikidata.org SPARQL, one query per region, cached in data/raw/dish_photos_cache/regional/wd_<region>.json
  Commons API: the item's P18 file, the files of its P373 category (20), a search haswbstatement:P180=<QID> (10)
  and a search for each native label (10). Every answer is cached in regional/commons_<region>.json, thumbnails in
  regional/thumbs/, CLIP scores in regional/clip_scores.parquet (the shared score cache is never written here).
Only free licences (CC0, public domain, CC BY, CC BY-SA, never NC or ND) and files not already in
dish_photos.parquet. Photos are scored with the English item label and accepted with fdp.passes(search=True).
Write mode appends rows (dish_qid "regional:<QID>") and never overwrites a recipe that already has a row.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import sys
import time
import urllib.parse
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "src")
import fetch_dish_photos as fdp

SPARQL = "https://query.wikidata.org/sparql"
RCACHE = fdp.CACHE / "regional"
THUMBS = RCACHE / "thumbs"
SCORES = RCACHE / "clip_scores.parquet"
CLEAN = RCACHE / "clean_names.parquet"
CAT_LIMIT, P180_LIMIT, LABEL_LIMIT = 20, 10, 10
PAGE = 3000        # SPARQL rows per page
MAX_PER_ITEM = 30   # candidates scored per item

# region -> (origin_country values as in the recipes table, Wikidata label languages)
REGIONS: dict[str, tuple[list[str], list[str]]] = {
    "india": (["India", "Pakistan", "Bangladesh", "Sri Lanka", "Nepal"],
              ["hi", "ta", "te", "bn", "mr", "gu", "ur", "pa", "ml", "kn", "en"]),
    "japan": (["Japan"], ["ja"]),
    "spain": (["Spain", "Andorra"], ["es", "ca", "eu", "gl"]),
    "mexico": (["Mexico"], ["es"]),
    "east_asia": (["China", "South Korea", "Taiwan", "Japan"], ["zh", "ko", "ja"]),
    "southeast_asia": (["Thailand", "Vietnam", "Philippines", "Indonesia", "Malaysia", "Cambodia", "Laos"],
                       ["th", "vi", "tl", "id", "ms", "km", "lo"]),
    "middle_east": (["Lebanon", "Turkey", "Iran", "Iraq", "Egypt", "Saudi Arabia", "Palestine", "Syria", "Armenia",
                     "Azerbaijan"], ["ar", "tr", "fa", "he", "hy", "az"]),
    "africa": (["Morocco", "South Africa", "Ethiopia", "Nigeria", "Algeria", "Tunisia", "Libya", "Sudan", "Somalia",
                "Kenya", "Angola", "Congo", "Botswana", "Namibia"], ["ar", "am", "af", "fr", "sw", "yo", "ha"]),
    "latin_america": (["Brazil", "Argentina", "Peru", "Chile", "Colombia", "Cuba", "Venezuela", "Ecuador",
                       "Guatemala", "Costa Rica", "Honduras", "Uruguay", "Puerto Rico"], ["es", "pt"]),
    "europe": (["France", "Italy", "Germany", "Greece", "Portugal", "Poland", "Hungary", "Sweden", "Norway",
                "Denmark", "Finland", "Netherlands", "Belgium", "Austria", "Switzerland", "Czech Republic",
                "Russia", "Ukraine", "Croatia", "Bulgaria", "Albania", "Slovakia", "Estonia", "Iceland"],
               ["fr", "it", "de", "el", "pt", "pl", "hu", "sv", "nb", "da", "fi", "nl", "cs", "ru", "uk", "hr",
                "bg", "sq", "sk", "et", "is"]),
}

# Sub-regions for the fallback levels: name -> (continent, cuisine items, origin_country values). The groups follow
# the UN geoscheme; the country lists are ours (the origin_country values of the recipes table). Cuisine items are
# Wikidata "regional cuisine" items found with wbsearchentities (2026-10-27); dishes link to them by P2012
# (cuisine) up the P279 chain. Eastern Europe has no cuisine item, so it is matched by country (P495) only.
SUBREGIONS: dict[str, tuple[str, list[str], list[str]]] = {
    "south_asia": ("asia", ["Q7566053"], ["India", "Pakistan", "Bangladesh", "Sri Lanka", "Nepal", "Afghanistan"]),
    "southeast_asia": ("asia", ["Q5876122"], ["Thailand", "Vietnam", "Philippines", "Indonesia", "Malaysia",
                                               "Cambodia", "Laos", "Myanmar", "Singapore"]),
    "east_asia": ("asia", ["Q19368756"], ["China", "Japan", "South Korea", "Taiwan", "Mongolia"]),
    "central_asia": ("asia", ["Q5060372"], ["Kazakhstan", "Uzbekistan", "Kyrgyzstan", "Tajikistan", "Turkmenistan"]),
    "west_asia": ("asia", ["Q1547037", "Q765174"], ["Lebanon", "Turkey", "Iran", "Iraq", "Saudi Arabia", "Palestine",
                                                     "Syria", "Armenia", "Azerbaijan", "Israel", "Jordan", "Yemen"]),
    "north_africa": ("africa", ["Q108884549"], ["Morocco", "Algeria", "Tunisia", "Libya", "Egypt", "Sudan"]),
    "west_africa": ("africa", ["Q11880026"], ["Nigeria", "Ghana", "Senegal", "Mali", "Ivory Coast"]),
    "east_africa": ("africa", ["Q3203205"], ["Ethiopia", "Kenya", "Somalia", "Tanzania", "Uganda"]),
    "central_africa": ("africa", ["Q8963583"], ["Congo", "Angola", "Cameroon"]),
    "southern_africa": ("africa", ["Q5876111"], ["South Africa", "Botswana", "Namibia", "Zimbabwe"]),
    "northern_europe": ("europe", ["Q20892186"], ["Sweden", "Norway", "Denmark", "Finland", "Iceland", "Estonia",
                                                   "Ireland", "United Kingdom"]),
    "western_europe": ("europe", ["Q108884451"], ["France", "Germany", "Belgium", "Netherlands", "Austria",
                                                   "Switzerland"]),
    "southern_europe": ("europe", ["Q108884332", "Q934309"], ["Italy", "Spain", "Portugal", "Greece", "Croatia",
                                                               "Albania", "Andorra"]),
    "eastern_europe": ("europe", [], ["Russia", "Poland", "Hungary", "Czech Republic", "Slovakia", "Ukraine",
                                      "Bulgaria"]),
    "caribbean": ("americas", ["Q1729345"], ["Cuba", "Jamaica", "Puerto Rico", "Dominica", "Barbados", "Aruba",
                                              "Antigua and Barbuda", "Cayman Islands"]),
    "central_america": ("americas", ["Q26821206"], ["Mexico", "Guatemala", "Costa Rica", "Honduras"]),
    "south_america": ("americas", ["Q10686720"], ["Brazil", "Argentina", "Peru", "Chile", "Colombia", "Venezuela",
                                                   "Ecuador", "Uruguay"]),
    "north_america": ("americas", ["Q4120078"], ["United States", "Canada"]),
}
# continent -> (Wikidata continent items for P495/P30, cuisine items); the last resort, reported on its own
CONTINENTS: dict[str, tuple[list[str], list[str]]] = {
    "asia": (["Q48"], ["Q728206"]), "africa": (["Q15"], ["Q386284"]), "europe": (["Q46"], ["Q579316"]),
    "americas": (["Q49", "Q18"], ["Q2707196"]),
}
# region -> its sub-regions (the fallback level between country and continent)
REGION_SUBS: dict[str, list[str]] = {
    "india": ["south_asia"], "japan": ["east_asia"], "spain": ["southern_europe"], "mexico": ["central_america"],
    "east_asia": ["east_asia"], "southeast_asia": ["southeast_asia"], "middle_east": ["west_asia"],
    "africa": ["north_africa", "west_africa", "east_africa", "central_africa", "southern_africa"],
    "latin_america": ["central_america", "south_america", "caribbean"],
    "europe": ["northern_europe", "western_europe", "southern_europe", "eastern_europe"],
}
LEVELS = ("country", "subregion", "continent")   # matching order: an earlier level wins


# ---------------------------------------------------------------- pure rules (tested without network)
def region_subregions(region: str) -> list[str]:
    region_countries(region)
    return REGION_SUBS[region]


def region_continent(region: str) -> str:
    return SUBREGIONS[region_subregions(region)[0]][0]


def region_countries(region: str) -> list[str]:
    if region not in REGIONS:
        raise ValueError(f"unknown region {region!r}; choose from {sorted(REGIONS)}")
    return REGIONS[region][0]


def region_languages(region: str) -> list[str]:
    region_countries(region)
    return REGIONS[region][1]


def _by_country(countries: list[str]) -> str:
    names = " ".join(f'"{c}"@en' for c in countries)
    return f"VALUES ?cl {{ {names} }} ?c rdfs:label ?cl . ?item wdt:P495 ?c ."


def _by_cuisine(cuisines: list[str]) -> str:
    return "VALUES ?cu { " + " ".join(f"wd:{c}" for c in cuisines) + " } ?item wdt:P2012/wdt:P279* ?cu ."


def sparql_query(region: str, level: str = "country", offset: int = 0, page: int = 3000) -> str:
    """The Wikidata query for one region and level: food items with aliases, native labels, P18 and P373.
    country: P495 in the region's countries. subregion: P495 in the countries of the region's sub-regions, or a
    cuisine (P2012, up the P279 chain) of those sub-regions. continent_p30 / continent_cuisine: P495 on the continent (P30), or its cuisine.
    Paged with LIMIT/OFFSET to stay under the 60 s limit."""
    if level == "country":
        where = _by_country(region_countries(region))
    elif level == "subregion":
        subs = [SUBREGIONS[n] for n in region_subregions(region)]
        cuisines = sorted({c for _, cs, _ in subs for c in cs})
        where = _by_country(sorted({c for _, _, cl in subs for c in cl}))
        if cuisines:
            where = "{ " + where + " } UNION { " + _by_cuisine(cuisines) + " }"
    elif level == "continent_p30":   # the continent level is two queries: together they time out
        where = ("VALUES ?cont { " + " ".join(f"wd:{c}" for c in CONTINENTS[region_continent(region)][0])
                 + " } ?c wdt:P30 ?cont . ?item wdt:P495 ?c .")   # countries first: the other way times out
    elif level == "continent_cuisine":
        where = _by_cuisine(CONTINENTS[region_continent(region)][1])
    else:
        raise ValueError(f"unknown level {level!r}")
    # a whole continent times out with the subclass chain, so continent_p30 takes direct dish/food instances only
    cls_path = "wdt:P31" if level == "continent_p30" else "wdt:P31/wdt:P279*"
    langs = ", ".join(f'"{lg}"' for lg in region_languages(region) if lg != "en")
    native = (f'OPTIONAL {{ ?item rdfs:label ?nl . FILTER(LANG(?nl) IN ({langs})) }}' if langs else "")
    return f"""SELECT ?item ?label ?img ?cat
  (GROUP_CONCAT(DISTINCT ?al; separator="|") AS ?aliases)
  (GROUP_CONCAT(DISTINCT ?nl; separator="|") AS ?native) WHERE {{
  {where}
  VALUES ?cls {{ wd:Q746549 wd:Q2095 }}
  ?item {cls_path} ?cls .
  ?item rdfs:label ?label . FILTER(LANG(?label) = "en")
  OPTIONAL {{ ?item skos:altLabel ?al . FILTER(LANG(?al) = "en") }}
  {native}
  OPTIONAL {{ ?item wdt:P18 ?img }}
  OPTIONAL {{ ?item wdt:P373 ?cat }}
}} GROUP BY ?item ?label ?img ?cat ORDER BY ?item LIMIT {page} OFFSET {offset}"""



def parse_sparql(j: dict) -> list[dict]:
    """SPARQL JSON -> one dict per item (rows of the same item merged)."""
    items: dict[str, dict] = {}
    for b in j.get("results", {}).get("bindings", []):
        qid = b["item"]["value"].rsplit("/", 1)[-1]
        it = items.setdefault(qid, {"qid": qid, "label": b["label"]["value"], "aliases": [], "native": [],
                                    "images": [], "cats": []})
        for field, col in (("aliases", "aliases"), ("native", "native")):
            for v in b.get(col, {}).get("value", "").split("|"):
                if v and v not in it[field]:
                    it[field].append(v)
        if "img" in b:
            name = urllib.parse.unquote(b["img"]["value"].rsplit("/", 1)[-1]).replace("_", " ")
            if name not in it["images"]:
                it["images"].append(name)
        if "cat" in b and b["cat"]["value"] not in it["cats"]:
            it["cats"].append(b["cat"]["value"])
    return list(items.values())


def match_recipes(recipes: pd.DataFrame, items: list[dict]) -> dict[str, list[str]]:
    """Item QID -> recipe ids. `recipes` needs recipe_id and gk (key of the core phrase). An item matches by the
    key of its English label or of any English alias; a recipe matching several items goes to each of them."""
    by_key: dict[str, set[str]] = {}
    for it in items:
        for name in [it["label"], *it["aliases"]]:
            k = fdp.key(name)
            if k:
                by_key.setdefault(k, set()).add(it["qid"])
    out: dict[str, list[str]] = {}
    for rid, gk in zip(recipes.recipe_id, recipes.gk):
        for qid in sorted(by_key.get(gk, ())):
            out.setdefault(qid, []).append(rid)
    return out


def is_free(license_name: str) -> bool:
    """The same licence rule as the Commons search (fdp.FREE): CC0, public domain, CC BY, CC BY-SA."""
    return bool(fdp.FREE.match(re.sub(r"\s+", " ", license_name or "").strip()))


def free_candidates(j: dict, used: set[str], limit: int = MAX_PER_ITEM) -> list[dict]:
    """Free, photo-like files of one Commons answer that are not used yet (file titles in `used`)."""
    pages = sorted(j.get("query", {}).get("pages", []), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = re.sub(r"\s+", " ", html.unescape(md.get("LicenseShortName", {}).get("value", ""))).strip()
        title = p.get("title", "")[5:]
        w, h = ii.get("width") or 0, ii.get("height") or 0
        if (ii.get("mime") not in ("image/jpeg", "image/png", "image/webp") or min(w, h) < 300
                or max(w, h) / max(1, min(w, h)) > 2.5 or not is_free(lic) or fdp.BAD_WORDS.search(title)
                or fdp.SEARCH_BAD.search(title) or title.replace("_", " ") in used
                or not ii.get("thumburl", "").startswith("https://")):
            continue
        out.append({"pageid": p["pageid"], "commons_file": title, "thumb_url": ii["thumburl"].split("?")[0],
                    "file_page": ii.get("descriptionurl", ""), "mime": ii.get("mime"), "license": lic,
                    "artist": md.get("Artist", {}).get("value", "")})
        if len(out) == limit:
            break
    return out


def used_titles(file_pages: list[str]) -> set[str]:
    """Commons file titles (spaces, no File: prefix) of the photos dish_photos.parquet already uses."""
    out = set()
    for u in file_pages:
        if "/wiki/File:" in str(u):
            out.add(urllib.parse.unquote(str(u).split("/wiki/File:", 1)[1]).replace("_", " "))
    return out


def merge_candidates(lists: list[list[dict]], limit: int = MAX_PER_ITEM) -> list[dict]:
    """Candidates of several sources, each file once, in source order."""
    seen, out = set(), []
    for lst in lists:
        for c in lst:
            if c["pageid"] not in seen:
                seen.add(c["pageid"])
                out.append(c)
    return out[:limit]


def match_levels(pools: dict[str, pd.DataFrame], items_by_level: dict[str, list[dict]]
                 ) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Match level by level (country, then subregion, then continent). A recipe matched at an earlier level is not
    matched again, and an item found at an earlier level keeps that level. `pools` gives each level its recipes
    (the fallback levels may also take recipes of unknown origin). Returns item QID -> recipe ids, item QID -> level."""
    matched: dict[str, list[str]] = {}
    source: dict[str, str] = {}
    taken: set[str] = set()
    for lv in LEVELS:
        if lv not in items_by_level:
            continue
        pool = pools[lv][~pools[lv].recipe_id.isin(taken)]
        items = [it for it in items_by_level[lv] if it["qid"] not in source]
        for q, ids in match_recipes(pool, items).items():
            matched[q] = ids
            source[q] = lv
            taken.update(ids)
    return matched, source


def report_totals(photoless: int, matched_items: dict[str, list[str]], chosen: dict[str, dict],
                  source: dict[str, str] | None = None, unknown: set[str] | None = None) -> dict:
    """Totals of a run: photoless recipes in the region, matched ones, items with a photo, recipes gained.
    A recipe that several accepted items match is counted once. Recipes of unknown origin (`unknown`, ids) are
    counted apart. With `source` (item -> level) items and recipes are also counted per level."""
    unk = unknown or set()
    matched_recipes = {r for ids in matched_items.values() for r in ids}
    gained = {r for q in chosen for r in matched_items.get(q, [])}
    known = matched_recipes - unk
    out: dict = {"photoless_recipes_in_region": photoless, "matched_items": len(matched_items),
                 "matched_recipes": len(known), "unmatched_recipes": photoless - len(known),
                 "items_with_accepted_photo": len(chosen), "recipes_that_would_get_a_photo": len(gained - unk)}
    if source is not None:
        by_level = {}
        for lv in LEVELS:
            rec = {r for q, ids in matched_items.items() if source.get(q) == lv for r in ids} - unk
            gain = {r for q in chosen if source.get(q) == lv for r in matched_items[q]} - unk
            by_level[lv] = {"items": sum(1 for q in matched_items if source.get(q) == lv),
                            "recipes": len(rec), "recipes_gained": len(gain)}
        out["by_level"] = by_level
        out["unknown_origin_recipes_matched"] = len(matched_recipes & unk)
        out["unknown_origin_recipes_that_would_get_a_photo"] = len(gained & unk)
    return out



# ---------------------------------------------------------------- network
def sparql(s: requests.Session, query: str) -> dict:
    """One SPARQL call (60 s server limit), backing off on 429/5xx."""
    for i in range(5):
        try:
            r = s.get(SPARQL, params={"query": query, "format": "json"}, timeout=90,
                      headers={"Accept": "application/sparql-results+json"})
            if r.status_code == 200:
                return r.json()
            print("  sparql http", r.status_code, "retry", i, flush=True)
            time.sleep(float(r.headers.get("Retry-After", 30 * (i + 1))))
        except (requests.RequestException, ValueError) as e:
            print("  sparql error", e, "retry", i, flush=True)
            time.sleep(30 * (i + 1))
    raise RuntimeError("wikidata query failed")


def wikidata_items(region: str, level: str = "country") -> list[dict]:
    """The Wikidata food items of one region and level, cached (the country level keeps its first file name)."""
    path = RCACHE / (f"wd_{region}.json" if level == "country" else f"wd_{region}_{level}.json")
    if path.exists():
        return list(fdp.load_json(path))  # type: ignore[arg-type]
    s = fdp.session()
    bindings: list[dict] = []
    for part in (["continent_p30", "continent_cuisine"] if level == "continent" else [level]):
        for page in range(10):
            j = sparql(s, sparql_query(region, part, offset=page * PAGE, page=PAGE))
            got = j.get("results", {}).get("bindings", [])
            bindings += got
            if len(got) < PAGE:
                break
            time.sleep(5)
    items = parse_sparql({"results": {"bindings": bindings}})
    RCACHE.mkdir(parents=True, exist_ok=True)
    fdp.save_json(items, path)
    return items


IMG = {"prop": "imageinfo", "iiprop": "url|extmetadata|mime|size", "iiurlwidth": fdp.WIDTH}


def item_candidates(s: requests.Session, it: dict, used: set[str]) -> list[dict]:
    """Free candidate files of one item from its image, category, P180 statements and native labels."""
    lists = []
    if it["images"]:
        j = fdp.commons(s, {"action": "query", "titles": "|".join(f"File:{n}" for n in it["images"][:10]), **IMG})
        for p in j.get("query", {}).get("pages", []):
            p["index"] = 0
        lists.append(free_candidates(j, used))
    for cat in it["cats"][:2]:
        lists.append(free_candidates(fdp.commons(s, {
            "action": "query", "generator": "categorymembers", "gcmtitle": f"Category:{cat}", "gcmtype": "file",
            "gcmnamespace": 6, "gcmlimit": CAT_LIMIT, **IMG}), used))
    base = {"action": "query", "generator": "search", "gsrnamespace": 6, **IMG}
    lists.append(free_candidates(fdp.commons(s, {
        **base, "gsrsearch": f"haswbstatement:P180={it['qid']}", "gsrlimit": P180_LIMIT}), used))
    for name in it["native"][:6]:
        lists.append(free_candidates(fdp.commons(s, {
            **base, "gsrsearch": f"{name} filetype:bitmap", "gsrlimit": LABEL_LIMIT}), used))
    return merge_candidates(lists)


def thumb_path(c: dict) -> Path:
    return THUMBS / f"{c['pageid']}.{fdp.ext_of(c['thumb_url'], c['mime'])}"


def download_thumbs(cands: list[dict]) -> None:
    THUMBS.mkdir(parents=True, exist_ok=True)
    s = fdp.session()
    todo = [c for c in cands if not thumb_path(c).exists()]
    print("thumbnails to fetch", len(todo), flush=True)
    for c in todo:
        for t in range(5):
            try:
                r = s.get(c["thumb_url"], timeout=60)
                if r.status_code == 200:
                    thumb_path(c).write_bytes(r.content)
                    time.sleep(1.0)
                    break
                time.sleep(float(r.headers.get("Retry-After", 15 * (t + 1))))
            except requests.RequestException:
                time.sleep(15 * (t + 1))


def use_regional_caches() -> None:
    """Keep the shared CLIP-score and clean-name caches untouched: score into regional/ (seeded with a copy)."""
    RCACHE.mkdir(parents=True, exist_ok=True)
    for src, dst in ((fdp.SCORES, SCORES), (fdp.CLEAN, CLEAN)):
        if not dst.exists() and src.exists():
            shutil.copyfile(src, dst)
    fdp.SCORES, fdp.CLEAN = SCORES, CLEAN


def stage_search(region: str, limit: int | None, dry: bool, report: Path | None, fallback: bool = True) -> None:
    use_regional_caches()
    fdp.Opts.extend = True
    countries = region_countries(region)
    allph = fdp.photoless_recipes()
    allph = allph[allph.origin_country.isin([*countries, "Unknown"])].copy()
    cn = fdp.clean_names(allph.recipe_name.dropna().astype(str).unique().tolist())
    allph["gk"] = allph.recipe_name.astype(str).map(cn).map(fdp.core_phrase).map(fdp.key)
    allph = allph[allph.gk != ""]
    inreg = allph.origin_country.isin(countries)
    photoless = int(fdp.photoless_recipes().origin_country.isin(countries).sum())
    unknown = set(allph.loc[~inreg, "recipe_id"])
    # the country level sees the region's recipes; sub-region and continent also see recipes of unknown origin
    pools = {"country": allph[inreg], "subregion": allph, "continent": allph}
    levels = LEVELS if fallback else LEVELS[:1]
    items_by_level = {lv: wikidata_items(region, lv) for lv in levels}
    items = [it for lv in levels for it in items_by_level[lv]]
    by_qid = {it["qid"]: it for it in items}
    matched, source = match_levels(pools, items_by_level)
    order = sorted(matched, key=lambda q: (-len(matched[q]), q))
    if limit:
        order = order[:limit]
        matched = {q: matched[q] for q in order}
    print(f"{region}: photoless {photoless}, wikidata items {len(items)}, matched items {len(matched)} "
          f"({', '.join(f'{lv} {sum(1 for q in matched if source[q] == lv)}' for lv in levels)})", flush=True)

    old = fdp.existing_dish_photos()
    used = used_titles(old["file_page"].dropna().tolist()) if "file_page" in old else set()
    cpath = RCACHE / f"commons_{region}.json"
    cache = fdp.load_json(cpath) if cpath.exists() else {}
    s = fdp.session()
    for i, q in enumerate(order):
        if q not in cache:
            cache[q] = item_candidates(s, by_qid[q], used)
        if i % 20 == 19 or i == len(order) - 1:
            fdp.save_json(cache, cpath)
            print(f"  searched {i + 1}/{len(order)}", flush=True)
    fdp.save_json(cache, cpath)
    cache = {q: [c for c in v if c["commons_file"].replace("_", " ") not in used] for q, v in cache.items()}

    download_thumbs([c for q in order for c in cache[q]])
    pairs = [(thumb_path(c).as_posix(), by_qid[q]["label"]) for q in order for c in cache[q]
             if thumb_path(c).exists() and thumb_path(c).stat().st_size >= 2048]
    sc = fdp.score_images(pairs).drop_duplicates(["image_file", "name"]).set_index(["image_file", "name"])
    chosen: dict[str, dict] = {}
    for q in order:
        lab = by_qid[q]["label"]
        ok = []
        for c in cache[q]:
            k = (thumb_path(c).as_posix(), lab)
            if k in sc.index:
                x = sc.loc[k]
                if fdp.passes(x.clip_score, x.rank_score, x.nonfood, search=True):
                    ok.append({**c, "clip_score": float(x.clip_score), "thumb": thumb_path(c).as_posix()})
        if ok:
            chosen[q] = max(ok, key=lambda c: c["clip_score"])
    totals = report_totals(photoless, matched, chosen, source, unknown)
    print("TOTALS", totals, flush=True)
    if report:
        rows = [{"qid": q, "label": by_qid[q]["label"], "commons_file": c["commons_file"], "thumb": c["thumb"],
                 "clip_score": c["clip_score"], "license": c["license"], "recipes": len(matched[q]),
                 "source": source[q]}
                for q, c in chosen.items()]
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps({"region": region, "totals": totals, "items": rows}, ensure_ascii=False,
                                     indent=1), encoding="utf8")
    if not dry:
        write_rows(chosen, matched, by_qid)


def write_rows(chosen: dict[str, dict], matched: dict[str, list[str]], by_qid: dict[str, dict]) -> None:
    """Append rows for recipes without one; a recipe already in dish_photos.parquet is never touched."""
    old = fdp.existing_dish_photos()
    have = set(old.recipe_id)
    rows, man = [], []
    for q, c in chosen.items():
        ids = [r for r in matched[q] if r not in have]
        if not ids:
            continue
        dst = fdp.OUT / f"c{c['pageid']}{Path(c['thumb']).suffix}"
        if not dst.exists():
            shutil.copyfile(c["thumb"], dst)
        lab = by_qid[q]["label"]
        author = fdp.plain(c["artist"])[:200] or "author not stated"
        d = {"dish_qid": f"regional:{q}", "dish_label": lab, "image_file": dst.as_posix(),
             "thumb_url": c["thumb_url"], "file_page": c["file_page"], "license": c["license"], "author": author,
             "credit": f"Photo of {lab}: {author}, {c['license']}, via Wikimedia Commons"}
        for r in ids:
            rows.append({"recipe_id": r, **d})
            have.add(r)
        man.append({**d, "recipes": len(ids), "commons_file": c["commons_file"]})
    if not rows:
        print("nothing to add")
        return
    new = pd.DataFrame(rows)[list(old.columns)].astype(old.dtypes.to_dict())
    pd.concat([old, new], ignore_index=True).to_parquet(fdp.PROC / "dish_photos.parquet", index=False)
    pd.concat([pd.read_csv(fdp.OUT / "manifest.csv"), pd.DataFrame(man)], ignore_index=True).to_csv(
        fdp.OUT / "manifest.csv", index=False, encoding="utf-8")
    print("rows added", len(new), "dish_photos rows", len(old) + len(new))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["search"])
    ap.add_argument("--region", required=True, choices=sorted(REGIONS))
    ap.add_argument("--limit", type=int, default=0, help="only the N matched items covering the most recipes")
    ap.add_argument("--dry", action="store_true", help="score and report, write no dish_photos rows")
    ap.add_argument("--no-fallback", action="store_true", help="country level only (no sub-region or continent)")
    ap.add_argument("--report", type=Path, help="save what was found as JSON")
    a = ap.parse_args()
    stage_search(a.region, a.limit or None, a.dry, a.report, not a.no_fallback)
