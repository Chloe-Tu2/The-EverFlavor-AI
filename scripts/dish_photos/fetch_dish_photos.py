"""Free-licensed Wikimedia Commons photos of dishes, for recipes that have no photo of their own.

Run from the project folder, stage by stage (each stage caches its result and can be rerun):

    python -I scripts/dish_photos/fetch_dish_photos.py match      # clean names -> Wikidata dishes
    python -I scripts/dish_photos/fetch_dish_photos.py meta       # P18 image, P495 country, Commons license
    python -I scripts/dish_photos/fetch_dish_photos.py download   # 480 px thumbnails (2 at a time, resumable)
    python -I scripts/dish_photos/fetch_dish_photos.py curate     # keep one good photo per dish, delete the rest
    python -I scripts/dish_photos/fetch_dish_photos.py write      # data/processed/dish_photos.parquet + manifest

A further round for the recipes that still have no photo (the same options on every stage):

    python -I scripts/dish_photos/fetch_dish_photos.py <stage> --extend --top 1000 --min-words 2

--extend targets only recipes with no photo at all (no own photo with photo_ok True and clip_score >= -0.03, no
Food.com photo link, no row in dish_photos.parquet), skips dishes already in dish_photos.parquet, keeps its
caches apart (*_ext.parquet), deletes only its own rejected files and appends to dish_photos.parquet and the
manifest instead of replacing them. --top N is how many dishes (by recipes covered) to take; --min-words N is
the shortest dish phrase that may match (default 1: a single word that is not a generic one).

Inputs: data/processed/recipes_*.parquet, data/processed/recipe_photos.parquet (photo_ok True = has a photo),
and the Wikidata dish list (English labels and aliases of every subclass or instance of dish, Q746549; CC0)
cached at data/raw/dish_photos_cache/wikidata_dishes_en.json (the `dishes` stage rebuilds it, paced 65 s).
Outputs: data/raw/dish_photos/<QID>.<ext> and manifest.csv (git-ignored), data/processed/dish_photos.parquet.
Only free licenses are kept (CC0, public domain, CC BY, CC BY-SA, any version); every photo keeps its credit.
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import unicodedata
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, "src")

UA = ("EverFlavorAI-capstone-dish-photos/0.1 (ITAI 2277 student project; https://github.com/med27-coder; "
      "paced, one thumbnail per dish)")
PROC = Path("data/processed")
OUT = Path("data/raw/dish_photos")
CACHE = Path("data/raw/dish_photos_cache")
DISHES = CACHE / "wikidata_dishes_en.json"
TOP = 400
CLIP_CUTOFF = -0.03  # own photos below this clip_score are hidden (docs/plans/RECIPE_PHOTOS.md, photo check)
WIDTH = 480
MIN_BYTES = 8 * 1024

# Single words that name a kind of dish, not one dish: a whole clean name like "Salad" is not matched.
GENERIC = set("""salad soup stew chicken beef pork fish bread cake pie tart cookie biscuit sauce dip dressing
sandwich casserole curry roast steak pasta noodle rice pudding dessert snack appetizer drink beverage cocktail
smoothie juice muffin pancake waffle porridge omelette omelet egg vegetable meat bun roll pastry candy
chocolate jam jelly pizza burger ham carrot caramel onion garlic tomato apple banana corn dumpling taco wrap toast cracker chip fritter patty meatball sausage
marinade glaze frosting icing filling topping stuffing gravy broth stock relish salsa chutney pickle
spread butter cream custard mousse cheesecake brownie bar slice square ball bite cup crumble cobbler crisp
loaf scone bagel flatbread pie skewer kebab kabob grill bbq barbecue fry stir lunch dinner breakfast brunch
side main dish meal treat delight surprise special mix blend medley platter bowl plate salmon shrimp tuna
turkey lamb duck tofu potato bean lentil cheese yogurt milk tea coffee punch lemonade shake fruit nut
seed grain cereal granola oatmeal ice sorbet sherbet popsicle cupcake donut doughnut cheese hash""".split())  # noqa: SIM905

# origin_country (ours) <- Wikidata country labels that mean the same place
COUNTRY_ALIASES = {
    "united states of america": "united states", "usa": "united states",
    "people's republic of china": "china", "republic of china": "taiwan",
    "korea": "south korea", "joseon": "south korea", "korean empire": "south korea", "goryeo": "south korea",
    "north korea": "south korea",
    "kingdom of italy": "italy", "ottoman empire": "turkey", "persia": "iran", "iran": "iran",
    "kingdom of great britain": "united kingdom", "england": "united kingdom", "scotland": "united kingdom",
    "wales": "united kingdom", "northern ireland": "united kingdom", "great britain": "united kingdom",
    "russian empire": "russia", "soviet union": "russia", "kingdom of france": "france",
    "empire of japan": "japan", "mughal empire": "india", "british raj": "india",
    "kingdom of the netherlands": "netherlands", "german empire": "germany", "kingdom of prussia": "germany",
    "austria-hungary": "austria", "kingdom of hungary": "hungary", "kingdom of greece": "greece",
}

WEST = set("""united states|canada|united kingdom|ireland|australia|new zealand|europe|north america|france|germany|
italy|spain|portugal|netherlands|belgium|luxembourg|switzerland|austria|denmark|sweden|norway|finland|iceland|
poland|czech republic|slovakia|hungary|greece|russia|ukraine|romania|bulgaria|croatia|serbia|slovenia|
lithuania|latvia|estonia|belarus|malta|cyprus""".replace("\n", "").split("|"))

IE_WORDS = {"cookie", "brownie", "pie", "smoothie", "pierogie", "veggie", "hoagie", "birdie", "goodie", "sweetie",
            "roti", "calorie", "zombie", "toastie", "frittie", "patisserie", "rotisserie", "boulangerie"}
FREE = re.compile(r"^(cc0|cc[- ]zero|public domain|pd\b.*|cc[- ]by(-sa)?[- ]\d(\.\d)?(\s.*)?|cc[- ]by(-sa)?)$", re.IGNORECASE)
BAD_WORDS = re.compile(r"\b(logos?|flags?|maps?|diagrams?|packag\w*|drawings?|illustrations?|icons?|"
                       r"clip ?art|cartoons?|stamps?|labels?|menus?|signs?|posters?|coats? of arms)\b", re.IGNORECASE)


def load_json(path: Path) -> dict:
    with open(path, encoding="utf8") as f:
        return json.load(f)


def save_json(obj: object, path: Path) -> None:
    with open(path, "w", encoding="utf8") as f:
        json.dump(obj, f, ensure_ascii=False)


def key(s: str) -> str:
    """Compare form of a name: ascii, lower case, no punctuation, simple singular."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", " and ").replace("'s ", "s ").replace("'", "")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    words = []
    for w in s.split():
        if w[:-1] in IE_WORDS:
            w = w[:-1]
        elif len(w) > 3 and w.endswith("ies"):
            w = w[:-3] + "y"
        elif len(w) > 3 and w.endswith("oes"):
            w = w[:-2]
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        words.append(w)
    return " ".join(words)


def session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    return s


def get_json(s: requests.Session, url: str, params: dict, pace: float = 1.0, tries: int = 5) -> dict:
    for i in range(tries):
        try:
            r = s.get(url, params=params, timeout=60)
            if r.status_code == 200:
                time.sleep(pace)
                return r.json()
            print("  http", r.status_code, "retry", i, flush=True)
            time.sleep(float(r.headers.get("Retry-After", 10 * (i + 1))))
        except requests.RequestException as e:
            print("  error", e, "retry", i, flush=True)
            time.sleep(10 * (i + 1))
    raise RuntimeError(f"failed: {url}")


class Opts:
    """Command-line options (see the module docstring); set once in main."""

    top = TOP
    extend = False
    min_words = 1
    apply = False
    dry = False


def cache_name(stem: str) -> Path:
    return CACHE / f"{stem}{'_ext' if Opts.extend else ''}.parquet"


def existing_dish_photos() -> pd.DataFrame:
    p = PROC / "dish_photos.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame(columns=["recipe_id", "dish_qid"])


# ---------------------------------------------------------------- dishes (optional rebuild of the dish list)
def stage_dishes() -> None:
    ep = "https://query.wikidata.org/sparql"
    s = session()

    def run(q: str) -> list:
        for i in range(4):
            r = s.post(ep, data={"query": q, "format": "json"}, timeout=180)
            if r.status_code == 200:
                time.sleep(65)
                return r.json()["results"]["bindings"]
            time.sleep(95)
        raise RuntimeError("query failed")

    def q(x: dict, k: str) -> str:
        return x[k]["value"].rsplit("/", 1)[1]
    cls = {q(x, "c") for x in run("SELECT DISTINCT ?c WHERE { ?c wdt:P279* wd:Q746549 . }")}
    inst = {q(x, "i") for x in run("SELECT DISTINCT ?i WHERE { ?i wdt:P31/wdt:P279* wd:Q746549 . }")}
    items, out = sorted(cls | inst), {}
    for i in range(0, len(items), 5000):
        vals = " ".join("wd:" + c for c in items[i:i + 5000])
        for x in run('SELECT ?i ?l ?a WHERE { VALUES ?i { ' + vals + ' } ?i rdfs:label ?l . FILTER(LANG(?l)="en") '
                     'OPTIONAL { ?i skos:altLabel ?a . FILTER(LANG(?a)="en") } }'):
            d = out.setdefault(q(x, "i"), {"label": x["l"]["value"], "aliases": set(), "is_class": q(x, "i") in cls})
            if "a" in x:
                d["aliases"].add(x["a"]["value"])
    CACHE.mkdir(parents=True, exist_ok=True)
    save_json({k: {**v, "aliases": sorted(v["aliases"])} for k, v in out.items()}, DISHES)


# ---------------------------------------------------------------- match
def photoless_recipes() -> pd.DataFrame:
    cols = ["recipe_id", "recipe_name", "origin_country"]
    df = pd.concat([pd.read_parquet(p, columns=cols) for p in sorted(PROC.glob("recipes_*.parquet"))])
    ph = pd.read_parquet(PROC / "recipe_photos.parquet", columns=["recipe_id", "photo_ok"])
    has = set(ph.loc[ph.photo_ok.astype(bool), "recipe_id"])
    if Opts.extend:
        chk = pd.read_parquet(PROC / "photo_check.parquet", columns=["recipe_id", "clip_score"])
        has -= set(chk.loc[chk.clip_score < CLIP_CUTOFF, "recipe_id"])
        # Food.com photos really downloaded and readable (notebook 11), minus the ones the photo check hides; a
        # link alone is not a photo
        fc = pd.read_parquet(PROC / "foodcom_photos.parquet", columns=["recipe_id", "photo_ok"])
        fc_has = set(fc.loc[fc.photo_ok.astype(bool), "recipe_id"])
        fc_chk = PROC / "photo_check_foodcom.parquet"
        if fc_chk.exists():
            c = pd.read_parquet(fc_chk, columns=["recipe_id", "clip_score"])
            fc_has -= set(c.loc[c.clip_score < CLIP_CUTOFF, "recipe_id"])
        has |= fc_has
        has |= set(existing_dish_photos().recipe_id)
    return df[~df.recipe_id.isin(has)].drop_duplicates("recipe_id").reset_index(drop=True)


def stage_match() -> None:
    from everflavor.dish_names import clean_title
    wd = load_json(DISHES)
    # Labels first (older, lower QIDs win a shared label); an alias only counts when no label has that name
    # and it belongs to one dish ("vegetable salad" is an alias of Olivier salad and of others: skipped).
    names: dict[str, str] = {}
    items = sorted(wd.items(), key=lambda kv: int(kv[0][1:]))
    for qid, v in items:
        k = key(v["label"])
        if k and not re.fullmatch(r"q?\d+", k):
            names.setdefault(k, qid)
    alias_owners: dict[str, set[str]] = {}
    for qid, v in items:
        for n in v["aliases"]:
            k = key(n)
            if k and not re.fullmatch(r"q?\d+", k) and k not in names:
                alias_owners.setdefault(k, set()).add(qid)
    names.update({k: next(iter(o)) for k, o in alias_owners.items() if len(o) == 1})
    maxlen = max(len(k.split()) for k in names)
    df = photoless_recipes()
    print("photo-less recipes", len(df), flush=True)
    cleaned: dict[str, str] = {}
    for t in df.recipe_name.dropna().unique():
        try:
            cleaned[t] = str(clean_title(t)["dish_name"] or t)
        except Exception:  # noqa: BLE001 - keep the raw title if the cleaner trips
            cleaned[t] = t
    df["clean_name"] = df.recipe_name.map(cleaned).fillna("")
    df["k"] = df.clean_name.map(key)

    def find(k: str) -> tuple[str, str]:
        if k in names and len(k.split()) >= Opts.min_words and (len(k.split()) > 1 or k not in GENERIC):
            return k, "whole"
        # The dish is the part before "with/in/on/over/served" ("chicken tikka masala with rice"), and the
        # phrase must end on its last word, the head noun: "easy pork chops" -> pork chop, but
        # "peanut butter cookies" is not "peanut butter".
        head = re.split(r"\b(?:with|in|on|over|served|topped|stuffed|for)\b", k)[0].strip() or k
        for part in [head]:
            w = part.split()
            for n in range(min(maxlen, len(w)), max(1, Opts.min_words - 1), -1):
                p = " ".join(w[len(w) - n:])
                if p in names:
                    return p, "phrase"
        return "", ""
    cache = {k: find(k) for k in df.k.unique()}
    df["match"] = df.k.map(lambda k: cache[k][0])
    df["how"] = df.k.map(lambda k: cache[k][1])
    df = df[df.match != ""].copy()
    df["dish_qid"] = df.match.map(names)
    if Opts.extend:  # dishes that already have a photo row, or whose photo failed the verify stage, are skipped
        df = df[~df.dish_qid.isin(set(existing_dish_photos().dish_qid) | failed_verify())]
    df["dish_label"] = df.dish_qid.map(lambda q: wd[q]["label"])
    CACHE.mkdir(parents=True, exist_ok=True)
    df.drop(columns=["k"]).to_parquet(cache_name("matches"), index=False)
    print("matched", len(df), "dishes", df.dish_qid.nunique(), df.how.value_counts().to_dict())
    print(df.dish_label.value_counts().head(40).to_dict())


# ---------------------------------------------------------------- meta
def wb_entities(s: requests.Session, ids: list[str], props: str) -> dict:
    out = {}
    for i in range(0, len(ids), 50):
        j = get_json(s, "https://www.wikidata.org/w/api.php", {
            "action": "wbgetentities", "ids": "|".join(ids[i:i + 50]), "props": props,
            "languages": "en", "format": "json"})
        out.update(j.get("entities", {}))
    return out


def claim_values(ent: dict, prop: str) -> list:
    vals = []
    for c in ent.get("claims", {}).get(prop, []):
        if c.get("rank") == "deprecated":
            continue
        dv = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if dv is not None:
            vals.append((c.get("rank") == "preferred", dv))
    vals.sort(key=lambda x: not x[0])  # preferred first
    return [v for _, v in vals]


def country_name(label: str) -> str:
    low = label.lower()
    return COUNTRY_ALIASES.get(low, low)


def stage_meta() -> None:
    m = pd.read_parquet(cache_name("matches"))
    s = session()
    pool = m.dish_qid.value_counts().index[: Opts.top * 3].tolist()  # enough candidates to survive the country check
    claims_p = CACHE / "claims.json"
    claims = load_json(claims_p) if claims_p.exists() else {}
    need = [q for q in pool if q not in claims]
    if need:
        for q, e in wb_entities(s, need, "claims").items():
            claims[q] = {"p18": claim_values(e, "P18"), "p495": [v["id"] for v in claim_values(e, "P495")]}
        save_json(claims, claims_p)
    countries = sorted({c for v in claims.values() for c in v["p495"]})
    cl_p = CACHE / "countries.json"
    cl = load_json(cl_p) if cl_p.exists() else {}
    need = [c for c in countries if c not in cl]
    if need:
        for q, e in wb_entities(s, need, "labels").items():
            cl[q] = e.get("labels", {}).get("en", {}).get("value", "")
        save_json(cl, cl_p)

    # Country check, when both are known: the dish's country (P495) must be the recipe's, or both must be in
    # the shared Western home-cooking world (macaroni and cheese is British by Wikidata, cooked everywhere
    # in the US), or US/Mexico (Tex-Mex). This still drops name collisions such as "grilled chicken" -> the
    # Indonesian ayam bakar item on an American recipe.
    def fits(row: pd.Series) -> bool:
        oc = str(row.origin_country or "").strip().lower()
        dc = {country_name(cl.get(c, "")) for c in claims.get(row.dish_qid, {}).get("p495", [])} - {""}
        if not oc or oc in ("unknown", "nan", "none") or not dc or oc in dc:
            return True
        if oc in WEST and dc & WEST:
            return True
        return {oc} | dc >= {"united states", "mexico"}
    m = m[m.dish_qid.isin(pool)].copy()
    m["fits"] = m.apply(fits, axis=1)
    print("country check drops", int((~m.fits).sum()), "recipe matches", flush=True)
    m = m[m.fits]
    top = m.dish_qid.value_counts().index[:Opts.top].tolist()
    m[m.dish_qid.isin(top)].drop(columns=["fits"]).to_parquet(cache_name("matches_top"), index=False)

    # Commons file info for the P18 image (Wikidata's chosen picture) of each top dish
    files = {q: claims[q]["p18"][0] for q in top if claims.get(q, {}).get("p18")}
    print("top dishes", len(top), "with an image (P18)", len(files), flush=True)
    info_p = CACHE / "commons.json"
    info = load_json(info_p) if info_p.exists() else {}
    titles = sorted({f for f in files.values() if f not in info})
    for i in range(0, len(titles), 25):
        j = get_json(s, "https://commons.wikimedia.org/w/api.php", {
            "action": "query", "titles": "|".join("File:" + t for t in titles[i:i + 25]), "prop": "imageinfo",
            "iiprop": "url|extmetadata|size|mime", "iiurlwidth": WIDTH, "format": "json", "formatversion": 2})
        norm = {n["to"]: n["from"] for n in j.get("query", {}).get("normalized", [])}
        for p in j.get("query", {}).get("pages", []):
            name = norm.get(p["title"], p["title"])[5:]
            ii = (p.get("imageinfo") or [{}])[0]
            md = ii.get("extmetadata", {})
            info[name] = {
                "thumb_url": ii.get("thumburl", ""), "file_page": ii.get("descriptionurl", ""),
                "width": ii.get("width"), "height": ii.get("height"), "mime": ii.get("mime", ""),
                "license": md.get("LicenseShortName", {}).get("value", ""),
                "artist": md.get("Artist", {}).get("value", ""),
                "description": md.get("ImageDescription", {}).get("value", ""),
                "object_name": md.get("ObjectName", {}).get("value", ""),
                "categories": md.get("Categories", {}).get("value", "")}
        save_json(info, info_p)
        print(f"  commons {min(i + 25, len(titles))}/{len(titles)}", flush=True)
    wd = load_json(DISHES)
    rows = []
    for q in top:
        f = files.get(q)
        meta = info.get(f, {}) if f else {}
        lic = re.sub(r"\s+", " ", html.unescape(meta.get("license", ""))).strip()
        rows.append({"dish_qid": q, "dish_label": wd[q]["label"], "recipes": int((m.dish_qid == q).sum()),
                     "commons_file": f or "", **meta, "license": lic,
                     "free": bool(f) and bool(FREE.match(lic)), "status": "" if f else "no P18"})
    d = pd.DataFrame(rows)
    d.loc[(d.status == "") & ~d.free, "status"] = "not free"
    d.to_parquet(cache_name("dishes"), index=False)
    print(d.status.replace("", "ok").value_counts().to_dict(), d[d.free].license.value_counts().to_dict())


# ---------------------------------------------------------------- download
def ext_of(url: str, mime: str) -> str:
    e = Path(urllib.parse.urlparse(url).path).suffix.lower().lstrip(".")
    return {"jpeg": "jpg"}.get(e, e) or {"image/png": "png", "image/webp": "webp"}.get(mime, "jpg")


def stage_download() -> None:
    d = pd.read_parquet(cache_name("dishes"))
    d = d[d.free & (d.thumb_url != "") & ~d.dish_qid.isin(HAND_DROP)]  # known bad ones are not fetched again
    OUT.mkdir(parents=True, exist_ok=True)
    s1, s2 = session(), session()

    def fetch(args: tuple[int, pd.Series]) -> str:
        i, r = args
        path = OUT / f"{r.dish_qid}.{ext_of(r.thumb_url, r.mime)}"
        if path.exists() and path.stat().st_size > 0:
            return "have"
        s = s1 if i % 2 else s2
        for t in range(5):
            try:
                resp = s.get(r.thumb_url, timeout=60)
                if resp.status_code == 200:
                    path.write_bytes(resp.content)
                    time.sleep(1.0)
                    return "got"
                time.sleep(float(resp.headers.get("Retry-After", 15 * (t + 1))))
            except requests.RequestException:
                time.sleep(15 * (t + 1))
        return "failed"
    with ThreadPoolExecutor(max_workers=2) as ex:
        res = list(ex.map(fetch, enumerate(r for _, r in d.iterrows())))
    print(pd.Series(res).value_counts().to_dict())


# ---------------------------------------------------------------- curate: one photo per dish, delete the rest
def plain(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


# Pictures dropped after reading the file names and looking at the doubtful ones (Claude, 2026-10-25):
# brand products and packages, diagrams, a logo, and photos of a different dish.
HAND_DROP = {
    "Q2884546": "tuna sandwiches, not tuna salad",
    "Q607754": "a McDonald's product",
    "Q7546879": "Hostess Twinkies, a brand product",
    "Q1243043": "Bahlsen cookies, a brand product",
    "Q16682389": "Voortman cookies, a brand product",
    "Q1038537": "cookies in their package",
    "Q7879663": "Arnott's biscuits, a brand product",
    "Q2005613": "Nuts, a chocolate bar brand, not a dish",
    "Q643995": "beef cut diagram",
    "Q3436828": "beef cut diagram",
    "Q1195276": "cake with the Wikidata logo",
    "Q200527": "pljeskavica, not Salisbury steak",
}


def stage_curate() -> None:
    from PIL import Image
    d = pd.read_parquet(cache_name("dishes"))
    keep, why = {}, {}
    for _, r in d[d.free & (d.thumb_url != "")].iterrows():
        path = OUT / f"{r.dish_qid}.{ext_of(r.thumb_url, r.mime)}"
        reason = ""
        text = " ".join([r.commons_file, plain(r.description), plain(r.object_name)])
        if r.dish_qid in HAND_DROP:
            reason = "checked by eye: " + HAND_DROP[r.dish_qid]
        elif not path.exists():
            reason = "not downloaded"
        elif "svg" in (r.mime or "") or r.commons_file.lower().endswith((".svg", ".gif", ".pdf")):
            reason = "not a photo (file type)"
        elif path.stat().st_size < MIN_BYTES:
            reason = "tiny (<8 KB)"
        elif BAD_WORDS.search(text):
            reason = "name or description: " + BAD_WORDS.search(text).group(0).lower()
        else:
            try:
                with Image.open(path) as im:
                    w, h = im.size
                    im.verify()
                if w / h > 2.5 or h / w > 2.5:
                    reason = f"narrow ({w}x{h})"
            except Exception:  # noqa: BLE001
                reason = "not a readable image"
        if reason:
            why[r.dish_qid] = reason
        else:
            keep[r.dish_qid] = path.name
    removed = []
    mine = set(d.dish_qid)  # --extend: only this round's files may be deleted
    for f in OUT.iterdir():
        if f.name != "manifest.csv" and f.name not in set(keep.values()) and (not Opts.extend or f.stem in mine):
            removed.append(f.name)
            f.unlink()
    d["status"] = [why.get(q, "kept" if q in keep else st) for q, st in zip(d.dish_qid, d.status)]
    d["image_file"] = d.dish_qid.map(lambda q: (OUT / keep[q]).as_posix() if q in keep else "")
    d.to_parquet(cache_name("dishes_curated"), index=False)
    print("kept", len(keep), "deleted files", len(removed), pd.Series(why).value_counts().to_dict())


# ---------------------------------------------------------------- write
def stage_write() -> None:
    total = len(photoless_recipes())  # before appending, so --extend counts this round's targets
    d = pd.read_parquet(cache_name("dishes_curated"))
    d = d[(d.status == "kept") & ~d.dish_qid.isin(failed_verify())].copy()
    d["author"] = d.artist.map(plain).str.slice(0, 200).replace("", "author not stated")
    d["credit"] = [f"Photo of {lab}: {a}, {lic}, via Wikimedia Commons"
                   for lab, a, lic in zip(d.dish_label, d.author, d.license)]
    d["thumb_url"] = d.thumb_url.str.split("?").str[0]  # drop Commons tracking parameters
    cols = ["dish_qid", "dish_label", "image_file", "thumb_url", "file_page", "license", "author", "credit"]
    man = d[cols + ["recipes", "commons_file"]]
    m = pd.read_parquet(cache_name("matches_top"), columns=["recipe_id", "dish_qid"])
    out = m.merge(d[cols], on="dish_qid", how="inner")[["recipe_id"] + cols]
    new = out
    if Opts.extend:  # keep the earlier rows unchanged, add this round's after them
        old = existing_dish_photos()
        new = out[~out.recipe_id.isin(set(old.recipe_id))]
        out = pd.concat([old, new], ignore_index=True)
        man = pd.concat([pd.read_csv(OUT / "manifest.csv"), man], ignore_index=True)
    man.to_csv(OUT / "manifest.csv", index=False, encoding="utf-8")
    out.to_parquet(PROC / "dish_photos.parquet", index=False)
    print("rows added", len(new), "total rows", len(out))
    size = sum(f.stat().st_size for f in OUT.iterdir())
    print(f"dishes {len(d)}  recipes covered {len(new)} of {total} photo-less ({100 * len(new) / total:.1f}%)  "
          f"size {size / 1e6:.1f} MB")
    print(d.license.value_counts().to_dict())


# ---------------------------------------------------------------- CLIP check of general photos (verify, search)
# A photo of a dish in general comes from a match or a search, and a search can return anything, so the cutoff is
# stricter than for a recipe's own photo (-0.03): the photo must look more like this dish than like food in
# general by a clear margin, its name must beat at least 90% of 50 other dish names, and it must look more like
# food than like a package, a bottle, a landscape, a person or a drawing (nonfood < 0). Chosen from hand-checked
# contact sheets (Claude, 2026-10-26): Wikidata's own dish images (verify) were mostly right from clip_score 0.02;
# search results between 0.02 and 0.04 were wrong about half the time (a landscape for "s'mores", foil bricks for
# "meatloaf"), from 0.04 about one in ten or fewer, so a search needs 0.045.
GENERAL_CLIP = 0.02   # verify: the photos matched to Wikidata dishes
SEARCH_CLIP = 0.045   # search: any Commons file
GENERAL_RANK = 0.9
NONFOOD = ["a photo of a product package with a brand label.", "a photo of bottles or jars on a shelf.",
           "a photo of a landscape.", "a photo of a person.", "a drawing or an illustration.",
           "a photo of a building or a shop."]
# File names that point to a package, a shop or something else than a plate of food
SEARCH_BAD = re.compile(r"\b(box|boxes|bottles?|cans?|cartons?|wrappers?|brand|products?|advert\w*|supermarket|"
                        r"grocery|store|shop|panorama|landscape|portrait|ostracon|almanack|dpla|museum|"
                        r"restaurant sign|tv dinner)\b", re.IGNORECASE)
SCORES = CACHE / "clip_scores.parquet"         # (image_file, name) -> clip_score, rank_score
VERIFY = CACHE / "verify.csv"                  # one row per dish_photos dish: its scores and passed True/False
HIDDEN = CACHE / "dish_photos_hidden.parquet"  # rows the verify stage took out of dish_photos.parquet
RESULTS = CACHE / "search_results.json"        # group key -> phrase and free Commons candidates
THUMBS = CACHE / "search_thumbs"               # candidate thumbnails (rejected ones stay here, git-ignored)
CLEAN = CACHE / "clean_names.parquet"          # recipe title -> clean dish name (dish_names.clean_title)
POOL = CACHE / "rank_pool.json"                # the 2000 commonest clean dish names, for rank_score


def failed_verify() -> set[str]:
    """Dishes whose photo failed the general-photo check (verify stage): never written again."""
    if not VERIFY.exists():
        return set()
    v = pd.read_csv(VERIFY)
    return set(v.loc[~v.passed.astype(bool), "dish_qid"])


def passes(clip_score: float, rank_score: float, nonfood: float = -1.0, search: bool = False) -> bool:
    cut = SEARCH_CLIP if search else GENERAL_CLIP
    return bool(clip_score >= cut and rank_score >= GENERAL_RANK and nonfood < 0)


# Words in front of a dish name that say nothing about which dish it is, and people whose dish it is
FLUFF = set("""easy easiest best quick quickie homemade simple healthy healthier light lite skinny my our the a an
ultimate perfect famous classic delicious yummy super really amazing awesome favorite favourite real great speedy
fabulous fantastic wonderful tasty scrumptious fresh basic traditional authentic ultra incredible good lazy
extra""".split())  # noqa: SIM905
FLUFF_PREFIX = re.compile(r"^(?:low[- ]?(?:fat|carb|cal|calorie|sodium)|fat[- ]?free|sugar[- ]?free|gluten[- ]?free|"
                          r"crock[- ]?pot|slow[- ]?cooker|instant[- ]?pot|old[- ]?fashioned|home[- ]?made|"
                          r"\d+[- ]?(?:minute|min|ingredient)s?|one[- ]?pot|no[- ]?fuss|best[- ]?ever|"
                          r"weight[- ]?watchers?|ww)\b\s*")
PEOPLE = set("""grandma grandmas grandmother granny gran nana nanas mom moms mommy mama mamas mother mothers dad dads
daddy papa grandpa aunt aunts auntie uncle uncles mimi mamaw""".split())  # noqa: SIM905
# Single or paired words that never name one dish ("breakfast bowl", "special treat")
VAGUE = set("""treat treats delight delights surprise special mix blend medley platter bowl plate side main dish meal
lunch dinner breakfast brunch snack appetizer dessert bite bites ball balls bar bars cup cups square squares slice
drink beverage thing stuff goodie goodies food recipe""".split())  # noqa: SIM905
# Plain ingredients and cuts: a photo of the raw thing would not show the recipe ("broccoli", "chicken breast")
INGREDIENTS = set("""broccoli spinach asparagu zucchini cauliflower cabbage mushroom pepper eggplant squash kale lettuce
avocado cucumber celery leek beet okra pea artichoke scallop mussel clam oyster crab lobster tilapia cod halibut
haddock trout breast thigh drumstick tenderloin ground loin sirloin fillet filet green bean sweet potato corn sprout
brussel chicken pork beef turkey lamb fresh frozen raw""".split())  # noqa: SIM905
STOP = {"and", "or", "of", "a", "the", "de", "la", "n", "an", "with", "to", "au", "e", "y", "et", "le", "el"}


def core_phrase(name: str) -> str:
    """The part of a clean dish name a photo search can find: no "easy", "grandma's" or "crock pot" in front, no
    "with ..." after. "" when what is left does not name one dish (a single generic word like "chicken", vague
    words only, or more than four words)."""
    s = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)|\".*?\"", " ", s.replace("’", "'"))
    s = re.split(r"\s+-\s+|[:;,/]| a la | from | by | for | served | per | using ", f" {s} ")[0]
    s = re.split(r"\s+with\s+", s)[0]
    for word in ("in", "on", "over"):  # "mussels in sherry" -> mussels, but "pigs in a blanket" stays whole
        left = re.split(rf"\s+{word}\s+", s)[0]
        if len(left.split()) >= 2:
            s = left
    s = re.sub(r"[^a-z0-9' -]+", " ", s)
    s = re.sub(r"^((?:\S+ ){0,2}?[a-z]+) s\b", r"\1's", s.strip())  # Food.com's lost apostrophe: "dan s chili"
    words = s.replace("-", " ").split()
    # people's dishes: "grandma's meatloaf", "aunt sue's chili", "bob's chili" (but not "shepherd's pie")
    for i in reversed(range(min(3, len(words)))):
        w = words[i]
        if w.endswith(("'s", "s'")) or w in PEOPLE:
            rest = words[i + 1:]
            if w.rstrip("'s") in PEOPLE or w in PEOPLE or len(rest) > 1 or (rest and key(rest[0]) not in GENERIC):
                words = rest
            break
    while words:
        joined = " ".join(words)
        m = FLUFF_PREFIX.match(joined)
        if m and m.end() > 0:
            words = joined[m.end():].split()
        elif words[0] in FLUFF or words[0] in PEOPLE or words[0].isdigit():
            words = words[1:]
        else:
            break
    while words and (words[-1] in {"k", "i", "ii", "iii", "iv", "dup", "recipe", "ever", "and", "or"}
                     or words[-1].isdigit()):
        words = words[:-1]
    words = [w.strip("'") for w in words if w.strip("'")]
    if not words or len(words) > 4:
        return ""
    if len(words) == 1 and (key(words[0]) in GENERIC or len(words[0]) < 3):
        return ""
    if all(key(w) in VAGUE or w in STOP for w in words) or all(key(w) in INGREDIENTS for w in words):
        return ""
    return " ".join(words)


def clip_kit():  # type: ignore[no-untyped-def]
    """The photo check's CLIP model (scripts/recipe_photos/check_photos.py), loaded once."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("check_photos", Path("scripts/recipe_photos/check_photos.py"))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    model, preprocess, tokenizer, torch = mod.load_model()
    torch.set_num_threads(4)  # leave the rest of the CPU to the other photo check
    return mod, model, preprocess, tokenizer, torch


def clean_names(titles: list[str]) -> dict[str, str]:
    from everflavor.dish_names import clean_title
    have = pd.read_parquet(CLEAN) if CLEAN.exists() else pd.DataFrame(columns=["title", "clean"])
    out = dict(zip(have.title, have.clean))
    need = sorted({t for t in titles if t not in out})
    for t in need:
        try:
            out[t] = str(clean_title(t)["dish_name"] or t)
        except Exception:  # noqa: BLE001 - keep the raw title if the cleaner trips
            out[t] = t
    if need:
        CACHE.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"title": list(out), "clean": list(out.values())}).to_parquet(CLEAN, index=False)
    return out


def all_recipes() -> pd.DataFrame:
    return pd.concat([pd.read_parquet(p, columns=["recipe_id", "recipe_name"])
                      for p in sorted(PROC.glob("recipes_*.parquet"))]).drop_duplicates("recipe_id")


def rank_pool() -> list[str]:
    """2000 common dish names (all recipes), the 'other dishes' a photo's own name must beat."""
    if POOL.exists():
        return list(load_json(POOL))
    titles = all_recipes().recipe_name.dropna().astype(str)
    cn = clean_names(titles.unique().tolist())
    names = titles.map(cn).str.lower().str.strip()
    names = names[names.map(lambda n: bool(n) and not (len(n.split()) == 1 and key(n) in GENERIC))]
    pool = names.value_counts().index[:2000].tolist()
    save_json(pool, POOL)
    return pool


def score_images(pairs: list[tuple[str, str]]) -> pd.DataFrame:
    """clip_score and rank_score for (image file, dish name) pairs, cached in SCORES."""
    import zlib

    import numpy as np
    from PIL import Image
    have = pd.read_parquet(SCORES) if SCORES.exists() else pd.DataFrame(
        columns=["image_file", "name", "clip_score", "rank_score", "nonfood"])
    if "nonfood" not in have:  # scores from before the non-food check are scored again
        have = have.iloc[0:0].assign(nonfood=pd.Series(dtype=float))
    done = set(zip(have.image_file, have.name))
    todo = sorted({p for p in pairs if p not in done})
    print("CLIP scores cached", len(done), "to score", len(todo), flush=True)
    if todo:
        mod, model, preprocess, tokenizer, torch = clip_kit()

        def text(texts: list[str]) -> np.ndarray:
            out = []
            for b in range(0, len(texts), 256):
                with torch.no_grad():
                    v = model.encode_text(tokenizer(texts[b:b + 256]))
                out.append(torch.nn.functional.normalize(v, dim=-1).numpy())
            return np.concatenate(out)
        pool = rank_pool()
        pool_keys = [set(key(n).split()) for n in pool]
        pool_vec = text([f"a photo of {n}, a type of food." for n in pool])
        gen = text(mod.GENERIC)
        non = text(NONFOOD)
        names = sorted({n for _, n in todo})
        name_vec = dict(zip(names, text([f"a photo of {n}, a type of food." for n in names])))
        rows = []
        for b in range(0, len(todo), 64):
            part = todo[b:b + 64]
            ims, ok = [], []
            for f, _ in part:
                try:
                    with Image.open(f) as im:
                        ims.append(preprocess(im.convert("RGB")))
                        ok.append(True)
                except (OSError, ValueError, SyntaxError, Image.DecompressionBombError):
                    ims.append(torch.zeros(3, 224, 224))
                    ok.append(False)
            with torch.no_grad():
                v = torch.nn.functional.normalize(model.encode_image(torch.stack(ims)), dim=-1).numpy()
            for (f, n), vec, good in zip(part, v, ok):
                if not good:
                    rows.append((f, n, -1.0, 0.0, 1.0))
                    continue
                own = float(vec @ name_vec[n])
                cs = own - float((gen @ vec).mean())
                k = set(key(n).split())
                # other names that are not this dish in other words ("brownie" vs "fudge brownie")
                others = [i for i, pk in enumerate(pool_keys) if not (pk <= k or k <= pk)]
                rng = np.random.default_rng(zlib.crc32(f"{f}|{n}".encode()))
                pick = rng.choice(others, size=50, replace=False)
                rs = float((pool_vec[pick] @ vec < own).mean())
                nf = float((non @ vec).max()) - float((gen @ vec).mean())  # the closest non-food prompt
                rows.append((f, n, round(cs, 4), round(rs, 3), round(nf, 4)))
            print(f"  scored {min(b + 64, len(todo))}/{len(todo)}", flush=True)
        new = pd.DataFrame(rows, columns=["image_file", "name", "clip_score", "rank_score", "nonfood"])
        have = pd.concat([have, new], ignore_index=True) if len(have) else new
        have.to_parquet(SCORES, index=False)
    return have


# ---------------------------------------------------------------- verify: CLIP check of the photos already chosen
def stage_verify() -> None:
    """Score every dish in dish_photos.parquet against its label; write VERIFY. With --apply, take the rows of the
    dishes that fail out of dish_photos.parquet (kept in HIDDEN, so nothing is lost), and the write stages never
    add them again."""
    dp = existing_dish_photos()
    dishes = dp.groupby("dish_qid", as_index=False).agg(dish_label=("dish_label", "first"),
                                                       image_file=("image_file", "first"),
                                                       recipes=("recipe_id", "size"))
    sc = score_images(list(zip(dishes.image_file, dishes.dish_label)))
    v = dishes.merge(sc, left_on=["image_file", "dish_label"], right_on=["image_file", "name"], how="left")
    v["passed"] = [passes(c, r) for c, r in zip(v.clip_score, v.rank_score)]  # nonfood is reported, not used
    v = v.drop(columns=["name"])
    if VERIFY.exists():  # dishes taken out by an earlier --apply stay on the list
        old = pd.read_csv(VERIFY)
        v = pd.concat([v, old[~old.dish_qid.isin(set(v.dish_qid))]], ignore_index=True)
    v.sort_values("clip_score").to_csv(VERIFY, index=False)
    v = v[v.dish_qid.isin(set(dishes.dish_qid))]
    bad = v[~v.passed.astype(bool)]
    print(f"dishes {len(v)}: pass {int(v.passed.sum())}, fail {len(bad)} ({int(bad.recipes.sum())} recipe rows)")
    print(bad.sort_values("recipes", ascending=False).head(15)[["dish_label", "clip_score", "rank_score",
                                                                 "recipes", "image_file"]].to_string())
    if Opts.apply and len(bad):
        drop = dp.dish_qid.isin(set(bad.dish_qid))
        hidden = pd.concat([pd.read_parquet(HIDDEN), dp[drop]]) if HIDDEN.exists() else dp[drop]
        hidden.drop_duplicates("recipe_id").to_parquet(HIDDEN, index=False)
        dp[~drop].to_parquet(PROC / "dish_photos.parquet", index=False)
        print("took out", int(drop.sum()), "rows; dish_photos rows now", int((~drop).sum()))


# ---------------------------------------------------------------- search: Commons search for photo-less dishes
def commons(s: requests.Session, params: dict) -> dict:
    """One Commons API call: 1 request a second, maxlag=5, backing off when the servers are busy."""
    params = {**params, "format": "json", "formatversion": 2, "maxlag": 5}
    for i in range(6):
        j = get_json(s, "https://commons.wikimedia.org/w/api.php", params, pace=1.0)
        if j.get("error", {}).get("code") == "maxlag":
            time.sleep(5 * (i + 1))
            continue
        return j
    raise RuntimeError("commons busy")


def candidates(j: dict, phrase: str) -> tuple[int, list[dict]]:
    """Free, photo-like files from one search answer whose name or categories carry every word of the phrase."""
    need = {w for w in key(phrase).split() if w not in STOP}
    pages = sorted(j.get("query", {}).get("pages", []), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = re.sub(r"\s+", " ", html.unescape(md.get("LicenseShortName", {}).get("value", ""))).strip()
        title = p.get("title", "")[5:]
        w, h = ii.get("width") or 0, ii.get("height") or 0
        words = set(key(" ".join([title.rsplit(".", 1)[0], plain(md.get("ObjectName", {}).get("value", "")),
                                  md.get("Categories", {}).get("value", "").replace("|", " ")])).split())
        if (ii.get("mime") not in ("image/jpeg", "image/png", "image/webp") or min(w, h) < 300
                or max(w, h) / max(1, min(w, h)) > 2.5 or not FREE.match(lic) or BAD_WORDS.search(title)
                or SEARCH_BAD.search(title)
                or not need <= words or not ii.get("thumburl", "").startswith("https://")):
            continue
        out.append({"pageid": p["pageid"], "commons_file": title, "thumb_url": ii["thumburl"].split("?")[0],
                    "file_page": ii.get("descriptionurl", ""), "mime": ii.get("mime"), "license": lic,
                    "artist": md.get("Artist", {}).get("value", "")})
        if len(out) == 5:
            break
    return len(pages), out


def thumb_path(c: dict) -> Path:
    return THUMBS / f"{c['pageid']}.{ext_of(c['thumb_url'], c['mime'])}"


def stage_search() -> None:
    import shutil
    Opts.extend = True
    ph = photoless_recipes()
    cn = clean_names(ph.recipe_name.dropna().astype(str).unique().tolist())
    ph["core"] = ph.recipe_name.astype(str).map(cn).map(core_phrase)
    total = len(ph)
    ph = ph[ph.core != ""].copy()
    ph["gk"] = ph.core.map(key)
    res = load_json(RESULTS) if RESULTS.exists() else {}
    groups = ph.groupby("gk").agg(n=("recipe_id", "size"), phrase=("core", lambda x: x.value_counts().index[0]))
    done = [k for k, v in res.items() if v.get("done")]  # groups a written round has settled (a --dry one has not)
    groups = groups[~groups.index.isin(done)].reset_index().sort_values(["n", "gk"], ascending=[False, True])
    todo = groups.head(Opts.top)
    print(f"photo-less {total}, with a dish phrase {len(ph)} in {len(groups)} unsearched groups; "
          f"this round {len(todo)} names, {int(todo.n.sum())} recipes", flush=True)

    s = session()
    for i, (gk, phrase) in enumerate(zip(todo.gk, todo.phrase)):
        if gk in res:  # searched before (a --dry round or a stopped run)
            continue
        base = {"action": "query", "generator": "search", "gsrnamespace": 6, "gsrlimit": 10, "prop": "imageinfo",
                "iiprop": "url|extmetadata|mime|size", "iiurlwidth": WIDTH}
        hits, cands = candidates(commons(s, {**base, "gsrsearch": f"{phrase} food filetype:bitmap"}), phrase)
        if not cands:
            hits2, cands = candidates(commons(s, {**base, "gsrsearch": f"{phrase} filetype:bitmap"}), phrase)
            hits = max(hits, hits2)
        res[gk] = {"phrase": phrase, "hits": hits, "cands": cands}
        if i % 25 == 24 or i == len(todo) - 1:
            save_json(res, RESULTS)
            print(f"  searched {i + 1}/{len(todo)}", flush=True)
    save_json(res, RESULTS)

    # thumbnails of this round's candidates, 2 at a time, paced
    THUMBS.mkdir(parents=True, exist_ok=True)
    cands = [c for gk in todo.gk for c in res[gk]["cands"] if not thumb_path(c).exists()]
    s1, s2 = session(), session()

    def fetch(args: tuple[int, dict]) -> str:
        i, c = args
        sess = s1 if i % 2 else s2
        for t in range(5):
            try:
                r = sess.get(c["thumb_url"], timeout=60)
                if r.status_code == 200:
                    thumb_path(c).write_bytes(r.content)
                    time.sleep(1.0)
                    return "got"
                time.sleep(float(r.headers.get("Retry-After", 15 * (t + 1))))
            except requests.RequestException:
                time.sleep(15 * (t + 1))
        return "failed"
    print("thumbnails to fetch", len(cands), flush=True)
    with ThreadPoolExecutor(max_workers=2) as ex:
        got = list(ex.map(fetch, enumerate(cands)))
    print(pd.Series(got, dtype=str).value_counts().to_dict(), flush=True)

    pairs = [(thumb_path(c).as_posix(), res[gk]["phrase"]) for gk in todo.gk for c in res[gk]["cands"]
             if thumb_path(c).exists() and thumb_path(c).stat().st_size >= 2048]
    sc = score_images(pairs).set_index(["image_file", "name"])
    best, no_free, rejected = {}, 0, 0
    for gk in todo.gk:
        r = res[gk]
        scored = [(sc.loc[(thumb_path(c).as_posix(), r["phrase"])], c) for c in r["cands"]
                  if (thumb_path(c).as_posix(), r["phrase"]) in sc.index]
        if not scored:
            no_free += 1
            continue
        ok = [(x.clip_score, c) for x, c in scored if passes(x.clip_score, x.rank_score, x.nonfood, search=True)
              and not SEARCH_BAD.search(c["commons_file"])]
        if ok:
            best[gk] = max(ok, key=lambda t: t[0])[1]
        else:
            rejected += 1
    new = ph[ph.gk.isin(list(best))].copy()
    print(f"ROUND names {len(todo)} accepted {len(best)} ({100 * len(best) / max(1, len(todo)):.1f}%) "
          f"recipes {len(new)} rejected_by_clip {rejected} no_free_candidates {no_free}", flush=True)
    if Opts.dry:
        return
    for gk in todo.gk:
        res[gk]["done"] = True
    save_json(res, RESULTS)
    if new.empty:
        return
    rows, man = [], []
    for gk, c in best.items():
        src = thumb_path(c)
        dst = OUT / f"c{c['pageid']}{src.suffix}"
        if not dst.exists():
            shutil.copyfile(src, dst)
        lab = res[gk]["phrase"]
        author = plain(c["artist"])[:200] or "author not stated"
        d = {"dish_qid": f"search:{gk}", "dish_label": lab, "image_file": dst.as_posix(),
             "thumb_url": c["thumb_url"], "file_page": c["file_page"], "license": c["license"], "author": author,
             "credit": f"Photo of {lab}: {author}, {c['license']}, via Wikimedia Commons"}
        rows.append(d)
        man.append({**d, "recipes": int((new.gk == gk).sum()), "commons_file": c["commons_file"]})
    d = pd.DataFrame(rows)
    out = new[["recipe_id", "gk"]].assign(dish_qid=lambda x: "search:" + x.gk).drop(columns="gk")
    out = out.merge(d, on="dish_qid")
    old = existing_dish_photos()
    out = out[~out.recipe_id.isin(set(old.recipe_id))]
    pd.concat([old, out[old.columns].astype(old.dtypes.to_dict())], ignore_index=True).to_parquet(
        PROC / "dish_photos.parquet", index=False)
    pd.concat([pd.read_csv(OUT / "manifest.csv"), pd.DataFrame(man)], ignore_index=True).to_csv(
        OUT / "manifest.csv", index=False, encoding="utf-8")
    print("rows added", len(out), "dish_photos rows", len(old) + len(out))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["dishes", "match", "meta", "download", "curate", "write", "verify", "search"])
    ap.add_argument("--top", type=int, default=TOP, help="dishes to take, by recipes covered (default %(default)s)")
    ap.add_argument("--extend", action="store_true", help="a further round for recipes that still have no photo")
    ap.add_argument("--min-words", type=int, default=1, help="shortest dish phrase that may match")
    ap.add_argument("--apply", action="store_true", help="verify: take failing dishes out of dish_photos.parquet")
    ap.add_argument("--dry", action="store_true", help="search: score but do not write dish_photos.parquet")
    a = ap.parse_args()
    Opts.top, Opts.extend, Opts.min_words, Opts.apply, Opts.dry = a.top, a.extend, a.min_words, a.apply, a.dry
    {"dishes": stage_dishes, "match": stage_match, "meta": stage_meta, "download": stage_download,
     "curate": stage_curate, "write": stage_write, "verify": stage_verify, "search": stage_search}[a.stage]()
