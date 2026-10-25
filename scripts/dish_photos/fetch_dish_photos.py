"""Free-licensed Wikimedia Commons photos of dishes, for recipes that have no photo of their own.

Run from the project folder, stage by stage (each stage caches its result and can be rerun):

    python -I scripts/dish_photos/fetch_dish_photos.py match      # clean names -> Wikidata dishes
    python -I scripts/dish_photos/fetch_dish_photos.py meta       # P18 image, P495 country, Commons license
    python -I scripts/dish_photos/fetch_dish_photos.py download   # 480 px thumbnails (2 at a time, resumable)
    python -I scripts/dish_photos/fetch_dish_photos.py curate     # keep one good photo per dish, delete the rest
    python -I scripts/dish_photos/fetch_dish_photos.py write      # data/processed/dish_photos.parquet + manifest

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
        if k in names and (len(k.split()) > 1 or k not in GENERIC):
            return k, "whole"
        # The dish is the part before "with/in/on/over/served" ("chicken tikka masala with rice"), and the
        # phrase must end on its last word, the head noun: "easy pork chops" -> pork chop, but
        # "peanut butter cookies" is not "peanut butter".
        head = re.split(r"\b(?:with|in|on|over|served|topped|stuffed|for)\b", k)[0].strip() or k
        for part in [head]:
            w = part.split()
            for n in range(min(maxlen, len(w)), 1, -1):
                p = " ".join(w[len(w) - n:])
                if p in names:
                    return p, "phrase"
        return "", ""
    cache = {k: find(k) for k in df.k.unique()}
    df["match"] = df.k.map(lambda k: cache[k][0])
    df["how"] = df.k.map(lambda k: cache[k][1])
    df = df[df.match != ""].copy()
    df["dish_qid"] = df.match.map(names)
    df["dish_label"] = df.dish_qid.map(lambda q: wd[q]["label"])
    CACHE.mkdir(parents=True, exist_ok=True)
    df.drop(columns=["k"]).to_parquet(CACHE / "matches.parquet", index=False)
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
    m = pd.read_parquet(CACHE / "matches.parquet")
    s = session()
    pool = m.dish_qid.value_counts().index[: TOP * 3].tolist()  # enough candidates to survive the country check
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
    top = m.dish_qid.value_counts().index[:TOP].tolist()
    m[m.dish_qid.isin(top)].drop(columns=["fits"]).to_parquet(CACHE / "matches_top.parquet", index=False)

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
    d.to_parquet(CACHE / "dishes.parquet", index=False)
    print(d.status.replace("", "ok").value_counts().to_dict(), d[d.free].license.value_counts().to_dict())


# ---------------------------------------------------------------- download
def ext_of(url: str, mime: str) -> str:
    e = Path(urllib.parse.urlparse(url).path).suffix.lower().lstrip(".")
    return {"jpeg": "jpg"}.get(e, e) or {"image/png": "png", "image/webp": "webp"}.get(mime, "jpg")


def stage_download() -> None:
    d = pd.read_parquet(CACHE / "dishes.parquet")
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
    d = pd.read_parquet(CACHE / "dishes.parquet")
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
    for f in OUT.iterdir():
        if f.name != "manifest.csv" and f.name not in set(keep.values()):
            removed.append(f.name)
            f.unlink()
    d["status"] = [why.get(q, "kept" if q in keep else st) for q, st in zip(d.dish_qid, d.status)]
    d["image_file"] = d.dish_qid.map(lambda q: (OUT / keep[q]).as_posix() if q in keep else "")
    d.to_parquet(CACHE / "dishes_curated.parquet", index=False)
    print("kept", len(keep), "deleted files", len(removed), pd.Series(why).value_counts().to_dict())


# ---------------------------------------------------------------- write
def stage_write() -> None:
    d = pd.read_parquet(CACHE / "dishes_curated.parquet")
    d = d[d.status == "kept"].copy()
    d["author"] = d.artist.map(plain).str.slice(0, 200).replace("", "author not stated")
    d["credit"] = [f"Photo of {lab}: {a}, {lic}, via Wikimedia Commons"
                   for lab, a, lic in zip(d.dish_label, d.author, d.license)]
    d["thumb_url"] = d.thumb_url.str.split("?").str[0]  # drop Commons tracking parameters
    cols = ["dish_qid", "dish_label", "image_file", "thumb_url", "file_page", "license", "author", "credit"]
    d[cols + ["recipes", "commons_file"]].to_csv(OUT / "manifest.csv", index=False, encoding="utf-8")
    m = pd.read_parquet(CACHE / "matches_top.parquet", columns=["recipe_id", "dish_qid"])
    out = m.merge(d[cols], on="dish_qid", how="inner")[["recipe_id"] + cols]
    out.to_parquet(PROC / "dish_photos.parquet", index=False)
    total = len(photoless_recipes())
    size = sum(f.stat().st_size for f in OUT.iterdir())
    print(f"dishes {len(d)}  recipes covered {len(out)} of {total} photo-less ({100 * len(out) / total:.1f}%)  "
          f"size {size / 1e6:.1f} MB")
    print(d.license.value_counts().to_dict())


if __name__ == "__main__":
    {"dishes": stage_dishes, "match": stage_match, "meta": stage_meta, "download": stage_download,
     "curate": stage_curate, "write": stage_write}[sys.argv[1]]()
