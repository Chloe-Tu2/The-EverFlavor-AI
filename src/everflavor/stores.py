"""Stores, restaurants and products by country for the Sourcing Agent (notebook 03).

OpenStreetMap and Open Food Facts need no key. Google Places needs
GOOGLE_PLACES_API_KEY and is skipped until a key is set. Anything about a
specific store (what it stocks, whether a dish is halal) stays "unverified:
check with the store" unless the place itself publishes it."""
from __future__ import annotations

import json
import re
import time
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from .ingredients import normalize_ingredient
from .progress import progress_bar

__all__ = [
    "COUNTRY_ALIASES",
    "COUNTRY_CUISINES",
    "COUNTRY_REGIONS",
    "GOOGLE_PLACES_DETAILS_URL",
    "GOOGLE_PLACES_SEARCH_URL",
    "NAME_HINTS",
    "OFF_EXPORT_URL",
    "OFF_FIELDS",
    "OSM_TAGS",
    "OSM_USER_AGENT",
    "OVERPASS_URLS",
    "PLACE_QUERIES",
    "UNVERIFIED_NOTE",
    "link_ingredients_to_products",
    "off_products_by_country",
    "osm_places",
    "place_details_live",
    "place_queries",
    "region_coverage",
    "search_places",
    "suggest_where_to_buy",
]

UNVERIFIED_NOTE = "Unverified: check with the store before you go."
OSM_USER_AGENT = "EverFlavorAI/0.1 (student project; https://github.com/Chloe-Tu2/The-EverFlavor-AI)"
RETRY_STATUS = {429, 500, 502, 503, 504}

# Our origin country -> the word OpenStreetMap and store names use for its cuisine
COUNTRY_CUISINES = {
    "China": "chinese", "Mexico": "mexican", "India": "indian", "Italy": "italian", "France": "french",
    "Japan": "japanese", "Thailand": "thai", "Vietnam": "vietnamese", "South Korea": "korean", "Greece": "greek",
    "Spain": "spanish", "Morocco": "moroccan", "Ethiopia": "ethiopian", "Lebanon": "lebanese", "Turkey": "turkish",
    "Iran": "persian", "Nigeria": "nigerian", "Brazil": "brazilian", "Peru": "peruvian", "Cuba": "cuban",
    "Philippines": "filipino", "Indonesia": "indonesian", "Germany": "german", "United Kingdom": "british",
    "Pakistan": "pakistani", "Jamaica": "jamaican", "Colombia": "colombian", "Egypt": "egyptian",
    "United States": "american",
}
# Origin country -> the broader kind of grocery that often carries its products (a name hint in NAME_HINTS)
COUNTRY_REGIONS = {
    **dict.fromkeys(["China", "Japan", "South Korea", "Thailand", "Vietnam", "Philippines", "Indonesia", "Taiwan",
                     "Malaysia", "Singapore"], "asian"),
    **dict.fromkeys(["Mexico", "Brazil", "Peru", "Cuba", "Colombia", "Argentina", "El Salvador", "Guatemala",
                     "Puerto Rico", "Venezuela"], "latin american"),
    **dict.fromkeys(["India", "Pakistan", "Bangladesh", "Sri Lanka", "Nepal"], "indian"),
    **dict.fromkeys(["Lebanon", "Turkey", "Iran", "Syria", "Israel", "Egypt", "Morocco", "Iraq"], "middle eastern"),
    **dict.fromkeys(["Greece", "Italy", "Spain", "Cyprus"], "mediterranean"),
    **dict.fromkeys(["Ethiopia", "Nigeria", "Ghana", "Kenya", "Senegal", "Somalia"], "african"),
    **dict.fromkeys(["Jamaica", "Trinidad And Tobago", "Haiti", "Barbados"], "caribbean"),
    **dict.fromkeys(["Poland", "Russia", "Ukraine"], "eastern european"),
}
# Words in a shop's name that hint at what it sells; a guess, never a fact
NAME_HINTS = {
    "asian": "asian", "oriental": "asian", "h mart": "korean", "hmart": "korean", "99 ranch": "chinese",
    "hong kong": "chinese", "mercado": "latin american", "carniceria": "latin american", "fiesta": "latin american",
    "supermercado": "latin american", "tienda": "latin american", "halal": "halal", "kosher": "kosher",
    "india": "indian", "patel": "indian", "desi": "indian", "african": "african", "caribbean": "caribbean",
    "mediterranean": "mediterranean", "middle east": "middle eastern", "persian": "persian", "korean": "korean",
    "vietnam": "vietnamese", "viet": "vietnamese", "japan": "japanese", "thai": "thai", "filipino": "filipino",
    "seafood": "seafood", "ethiopian": "ethiopian", "russian": "eastern european", "polish": "eastern european",
}


# ------------------------------------------------------------------ OpenStreetMap (section 3)
# Public Overpass servers; the next one is tried when one is busy (fair use: few, cached queries)
OVERPASS_URLS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
                 "https://overpass.private.coffee/api/interpreter"]
OSM_TAGS = {
    "restaurant": '["amenity"="restaurant"]',
    "grocery": '["shop"~"^(supermarket|convenience|greengrocer|deli)$"]',
    "butcher": '["shop"="butcher"]',
}


def _overpass(query: str, retries: int = 2, timeout: int = 120) -> dict:
    """Run an Overpass query on the first server that answers; busy servers are skipped."""
    for attempt in range(1, retries + 1):
        for url in OVERPASS_URLS:
            try:
                response = requests.post(url, data={"data": query}, timeout=timeout,
                                         headers={"User-Agent": OSM_USER_AGENT})
            except (requests.ConnectionError, requests.Timeout):
                continue
            if response.ok:
                return response.json()
            if response.status_code not in RETRY_STATUS:
                response.raise_for_status()
        time.sleep(10 * attempt)
    raise RuntimeError("No Overpass server answered; try again later")


def _yes(tags: Mapping[str, str], key: str) -> bool | None:
    """Read an OpenStreetMap yes/only/no tag as True / False, or None when it is not set."""
    value = tags.get(key)
    return None if value is None else value in ("yes", "only")


def _name_hint(name: str) -> str:
    """Guess what a shop sells from its name ("Viet Hoa Supermarket" -> "vietnamese"), or ""."""
    lower = name.lower()
    return next((hint for word, hint in NAME_HINTS.items() if re.search(rf"\b{re.escape(word)}\b", lower)), "")


def osm_places(area: Mapping[str, object], category: str, cache_dir: str | Path, refresh: bool = False) -> pd.DataFrame:
    """Download OpenStreetMap places of one category around `area`, cached (ODbL: credit OpenStreetMap).

    Args:
        area: {"name", "lat", "lng", "radius_m"}.
        category: A key of OSM_TAGS ("restaurant", "grocery", "butcher").
        cache_dir: Where the answer is saved.
        refresh: True asks Overpass again instead of using the saved answer.

    Returns:
        One row per place: osm_id, name, lat, lng, category, cuisine (list, split on ";"),
        name_hint (a guess from the name), diet_halal, diet_kosher, diet_vegan,
        diet_vegetarian (True / False / None when not tagged), opening_hours, website, brand, source="osm".
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", str(area["name"]).lower()).strip("_")
    cache_file = cache_dir / f"{slug}_{category}_{area['radius_m']}.json"
    if cache_file.exists() and not refresh:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
    else:
        query = (f"[out:json][timeout:90];nwr{OSM_TAGS[category]}"
                 f"(around:{area['radius_m']},{area['lat']},{area['lng']});out center tags;")
        data = _overpass(query)
        cache_file.write_text(json.dumps(data), encoding="utf-8")
    rows = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        center = element.get("center", element)
        name = tags.get("name", "")
        rows.append({
            "osm_id": f"{element['type']}/{element['id']}", "name": name,
            "lat": center.get("lat"), "lng": center.get("lon"), "category": category,
            "cuisine": [c.strip() for c in tags.get("cuisine", "").split(";") if c.strip()],
            "name_hint": _name_hint(name),
            "diet_halal": _yes(tags, "diet:halal"), "diet_kosher": _yes(tags, "diet:kosher"),
            "diet_vegan": _yes(tags, "diet:vegan"), "diet_vegetarian": _yes(tags, "diet:vegetarian"),
            "opening_hours": tags.get("opening_hours", ""), "website": tags.get("website", ""),
            "brand": tags.get("brand", ""), "source": "osm",
        })
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ Google Places (section 2)
GOOGLE_PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_PLACES_DETAILS_URL = "https://places.googleapis.com/v1/places/"
PLACE_QUERIES = {
    # category -> query templates; {cuisine} is filled from the pilot cuisines
    "grocery": ["{cuisine} grocery store", "{cuisine} market"],
    "restaurant": ["{cuisine} restaurant"],
    "butcher": ["halal butcher", "kosher butcher"],
}


def place_queries(cuisines: Iterable[str]) -> list[tuple[str, str, str]]:
    """Return (category, cuisine hint, query) for every PLACE_QUERIES template and pilot cuisine."""
    out = []
    for category, templates in PLACE_QUERIES.items():
        for template in templates:
            if "{cuisine}" in template:
                out += [(category, c, template.format(cuisine=c)) for c in cuisines]
            else:
                out.append((category, template.split()[0], template))
    return out


def _google_post(url: str, body: dict, api_key: str, field_mask: str) -> dict:
    """POST to Google Places with the key in a header (never in the URL), without showing it in errors."""
    try:
        response = requests.post(url, json=body, timeout=30,
                                 headers={"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": field_mask})
    except (requests.ConnectionError, requests.Timeout) as e:
        raise RuntimeError(f"Google Places could not be reached ({type(e).__name__})") from None
    if not response.ok:
        raise RuntimeError(f"Google Places request failed with HTTP {response.status_code}")
    return response.json()


def search_places(query: str, area: Mapping[str, object], api_key: str, cache_dir: str | Path,
                  refresh: bool = False) -> list[dict]:
    """Search Google Places (Text Search, New API) near `area` and cache only the place IDs.

    Google allows storing place IDs, not names, ratings or hours, so only the ID,
    the query and the date are kept; place_details_live fetches the rest when the
    agent shows a place. The field mask asks only for IDs and types (cheapest).

    Returns:
        [{"place_id", "query", "types", "retrieved"}].
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", f"{area['name']} {query}".lower()).strip("_")
    cache_file = cache_dir / f"{slug}.json"
    if cache_file.exists() and not refresh:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    body = {"textQuery": query, "locationBias": {"circle": {
        "center": {"latitude": area["lat"], "longitude": area["lng"]}, "radius": float(str(area["radius_m"]))}}}
    data = _google_post(GOOGLE_PLACES_SEARCH_URL, body, api_key, "places.id,places.types")
    today = datetime.now(timezone.utc).date().isoformat()
    places = [{"place_id": p["id"], "query": query, "types": p.get("types", []), "retrieved": today}
              for p in data.get("places", [])]
    cache_file.write_text(json.dumps(places), encoding="utf-8")
    return places


def place_details_live(place_id: str, api_key: str) -> dict:
    """Fetch name, address, hours and website for one place when the agent shows it (never stored).

    Raises:
        RuntimeError: For a failed request, without showing the key.
    """
    if not re.fullmatch(r"[A-Za-z0-9_-]+", place_id):
        raise ValueError(f"not a Google place ID: {place_id!r}")
    try:
        response = requests.get(GOOGLE_PLACES_DETAILS_URL + place_id, timeout=30, headers={
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "displayName,formattedAddress,regularOpeningHours.weekdayDescriptions,websiteUri"})
    except (requests.ConnectionError, requests.Timeout) as e:
        raise RuntimeError(f"Google Places could not be reached ({type(e).__name__})") from None
    if not response.ok:
        raise RuntimeError(f"Google Places request failed with HTTP {response.status_code}")
    data = response.json()
    return {"name": data.get("displayName", {}).get("text", ""), "address": data.get("formattedAddress", ""),
            "hours": data.get("regularOpeningHours", {}).get("weekdayDescriptions", []),
            "website": data.get("websiteUri", ""), "note": UNVERIFIED_NOTE}


# ------------------------------------------------------------------ Open Food Facts export (section 4)
OFF_EXPORT_URL = "https://huggingface.co/datasets/openfoodfacts/product-database/resolve/main/food.parquet"
OFF_FIELDS = ["code", "product_name", "brands", "categories_tags", "origins_tags", "manufacturing_places_tags",
              "countries_tags", "stores_tags", "allergens_tags", "traces_tags", "ingredients_analysis_tags"]


# Spellings volunteers use for one country, and values that name no country
COUNTRY_ALIASES = {"Usa": "United States", "Us": "United States", "U S A": "United States", "America": "United States",
                   "Uk": "United Kingdom", "England": "United Kingdom", "Unknown": "", "Other": ""}


def _tag_name(tag: str) -> str:
    """Turn an Open Food Facts tag into words: "en:united-states" -> "United States", "en:usa" -> "United States"."""
    name = tag.split(":", 1)[-1].replace("-", " ").strip().title()
    return COUNTRY_ALIASES.get(name, name)


def _add_home_country(products: pd.DataFrame) -> pd.DataFrame:
    """Add home_country (origin, else where it is made) and sold_in_us from the tag columns.

    Only real country names count: the countries products are sold in give the list,
    so a city in the free-text "made in" field ("Plano") is not taken for a country.
    """
    countries = {_tag_name(t) for tags in products["countries_tags"] for t in tags} - {""}

    def first_country(tags: Sequence[str]) -> str:
        return next((name for name in (_tag_name(t) for t in tags) if name in countries), "")

    origins = products["origins_tags"].map(first_country)
    made_in = products["manufacturing_places_tags"].map(first_country)
    products["home_country"] = origins.where(origins != "", made_in)
    products["sold_in_us"] = products["countries_tags"].map(lambda t: "en:united-states" in list(t))
    return products


def _main_name(names: object) -> str:
    """The product name in its main language (the export stores one name per language)."""
    if names is None or isinstance(names, str):
        return names or ""
    entries = list(names)  # type: ignore[call-overload]
    for wanted in ("main", "en"):
        for entry in entries:
            if entry.get("lang") == wanted and entry.get("text"):
                return str(entry["text"])
    return str(entries[0].get("text", "")) if entries else ""


def _compact_products(table: pd.DataFrame) -> pd.DataFrame:
    """Keep the fields notebook 03 uses, with tags as plain lists and home_country / sold_in_us added."""
    def tags(column: str) -> pd.Series:
        return table[column].map(lambda v: [str(t) for t in v] if v is not None else [])
    out = pd.DataFrame({"code": table["code"].astype(str), "product_name": table["product_name"].map(_main_name),
                        "brands": table["brands"].fillna("").astype(str)})
    for column in OFF_FIELDS[3:]:
        out[column] = tags(column)
    return _add_home_country(out)


def off_products_by_country(source: str | Path, cache_file: str | Path, n_row_groups: int | None = 200,
                            refresh: bool = False, chunk: int = 20) -> pd.DataFrame:
    """Read the Open Food Facts export (only OFF_FIELDS) and add home_country and sold_in_us, cached.

    The export (ODbL) is one Parquet file of about 7.9 GB and 4.8 million products
    in about 4,700 row groups. Only the needed columns are read, in chunks, so it
    fits in Colab's memory. With a URL as `source` the columns are read over the
    network (about 2 seconds per 1,000 products), so by default an evenly spread
    sample of row groups is read; with the downloaded file every row group can be.

    Args:
        source: OFF_EXPORT_URL, or the downloaded `food.parquet`.
        cache_file: Where the compact table is saved (read back on later runs).
        n_row_groups: How many evenly spread row groups to read; None reads all of them.
        refresh: True reads the export again instead of the saved table.
        chunk: Row groups read at a time.

    Returns:
        code, product_name, brands, the tag columns of OFF_FIELDS (lists), home_country
        (origin, or where it is made when origin is empty; "" when neither), sold_in_us.
    """
    import pyarrow.parquet as pq

    cache_file = Path(cache_file)
    if cache_file.exists() and not refresh:
        saved = pd.read_parquet(cache_file)
        for column in OFF_FIELDS[3:]:   # Parquet gives arrays back; the tables use plain lists
            saved[column] = saved[column].map(list)
        return _add_home_country(saved)   # recomputed, so a newer country rule applies to saved tables
    if str(source).startswith("http"):
        import fsspec
        handle = fsspec.open(str(source), block_size=2**16, cache_type="readahead").open()
    else:
        handle = open(source, "rb")   # noqa: SIM115 - closed below, after every chunk is read
    try:
        parquet = pq.ParquetFile(handle)
        total = parquet.metadata.num_row_groups
        groups = list(range(total)) if n_row_groups is None or n_row_groups >= total else \
            sorted({round(i * (total - 1) / max(n_row_groups - 1, 1)) for i in range(n_row_groups)})
        parts = [_compact_products(parquet.read_row_groups(groups[i:i + chunk], columns=OFF_FIELDS).to_pandas())
                 for i in progress_bar(range(0, len(groups), chunk), "Open Food Facts export")]
    finally:
        handle.close()
    products = pd.concat(parts, ignore_index=True)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    products.to_parquet(cache_file, index=False)
    return products


# ------------------------------------------------------------------ linking (section 5)
def _category_words(tag: str) -> str:
    """One normalized ingredient name for a category tag: "en:soy-sauces" -> "soy sauce"."""
    names = normalize_ingredient(tag.split(":", 1)[-1].replace("-", " "))
    return names[0] if names else ""


def link_ingredients_to_products(ingredients: Sequence[str], products: pd.DataFrame,
                                 max_per_ingredient: int = 50) -> pd.DataFrame:
    """Match normalized ingredient names to Open Food Facts products.

    "category": an English category of the product is the ingredient ("en:soy-sauces"
    for "soy sauce"); "name": the ingredient appears as whole words in the product
    name, tried only when no category matches. Products sold in the US come first.

    Returns:
        ingredient, code, product_name, brands, home_country, sold_in_us, match
        ("category" / "name"), confidence ("high" / "medium").
    """
    wanted = set(ingredients)
    category_hits: dict[str, list[int]] = {}
    for position, tags in enumerate(products["categories_tags"]):
        for tag in tags:
            if tag.startswith("en:"):
                name = _category_words(tag)
                if name in wanted:
                    category_hits.setdefault(name, []).append(position)
    names = products["product_name"].fillna("").str.lower()
    order = (~products["sold_in_us"]).to_numpy().argsort(kind="stable")   # sold in the US first
    rank = pd.Series(range(len(order)), index=order).sort_index().to_numpy()
    rows = []
    for ingredient in dict.fromkeys(ingredients):
        positions, match = category_hits.get(ingredient, []), "category"
        if not positions:
            hits = names.str.contains(rf"\b{re.escape(ingredient)}s?\b", regex=True)
            positions, match = list(hits[hits].index), "name"
        positions = sorted(set(positions), key=lambda p: rank[p])[:max_per_ingredient]
        for p in positions:
            product = products.iloc[p]
            rows.append((ingredient, product["code"], product["product_name"], product["brands"],
                         product["home_country"], bool(product["sold_in_us"]), match,
                         "high" if match == "category" else "medium"))
    return pd.DataFrame(rows, columns=["ingredient", "code", "product_name", "brands", "home_country",
                                       "sold_in_us", "match", "confidence"])


def _cuisine_places(places: pd.DataFrame, cuisine: str) -> pd.DataFrame:
    """Places whose cuisine tag or name hint is `cuisine`."""
    if places.empty or not cuisine:
        return places.iloc[0:0]
    tagged = places["cuisine"].map(lambda c: cuisine in list(c))
    return places[tagged | (places["name_hint"] == cuisine)]


def suggest_where_to_buy(ingredient: str, origin_country: str, links: pd.DataFrame, places: pd.DataFrame,
                         n: int = 5) -> dict:
    """Brands from `origin_country`, and nearby groceries that may carry them (unverified).

    Never "store X has it": stores come only as places to try, each with UNVERIFIED_NOTE.
    Stores are groceries of that country's cuisine, else of its broader kind
    (COUNTRY_REGIONS: an Asian market for Chinese soy sauce); when none is known the
    list stays empty rather than suggesting an unrelated store.

    Returns:
        {"ingredient", "origin_country", "home_brands" (from that country, sold in the US),
        "home_brands_elsewhere" (from that country, not marked as sold in the US),
        "other_brands_sold_in_us", "stores_to_try" (up to n names), "store_match"
        ("cuisine", "region" or "none"), "note"}.
    """
    rows = links[(links["ingredient"] == ingredient) & (links["brands"] != "")]
    from_home = rows["home_country"].str.lower() == origin_country.lower()
    groceries = places[places["category"] == "grocery"] if len(places) else places
    stores, store_match = _cuisine_places(groceries, COUNTRY_CUISINES.get(origin_country, "")), "cuisine"
    if stores.empty:
        stores, store_match = _cuisine_places(groceries, COUNTRY_REGIONS.get(origin_country, "")), "region"
    if stores.empty:
        store_match = "none"
    return {"ingredient": ingredient, "origin_country": origin_country,
            "home_brands": list(dict.fromkeys(rows[from_home & rows["sold_in_us"]]["brands"]))[:n],
            "home_brands_elsewhere": list(dict.fromkeys(rows[from_home & ~rows["sold_in_us"]]["brands"]))[:n],
            "other_brands_sold_in_us": list(dict.fromkeys(rows[rows["sold_in_us"]]["brands"]))[:n],
            "stores_to_try": [s for s in dict.fromkeys(stores["name"]) if s][:n] if len(stores) else [],
            "store_match": store_match, "note": UNVERIFIED_NOTE}


# ------------------------------------------------------------------ coverage (section 6)
def region_coverage(recipes: pd.DataFrame, links: pd.DataFrame, products: pd.DataFrame,
                    places: pd.DataFrame, top_ingredients: int = 20) -> pd.DataFrame:
    """One row per origin country: how ready the Sourcing Agent is for its recipes.

    Returns:
        origin_country, recipes, ingredients_linked_pct (of its `top_ingredients` most
        used ingredients, the share with at least one product), home_products_sold_in_us,
        nearby_places (restaurants or groceries of its cuisine), sorted by recipes.
    """
    linked = set(links["ingredient"])
    home_us = products[products["sold_in_us"]]["home_country"].str.lower().value_counts()
    rows = []
    for country, group in recipes[recipes["origin_country"] != "Unknown"].groupby("origin_country"):
        top = pd.Series([i for items in group["ingredient_list"] for i in items]).value_counts().head(top_ingredients)
        pct = round(100 * sum(i in linked for i in top.index) / len(top), 1) if len(top) else 0.0
        rows.append((country, len(group), pct, int(home_us.get(str(country).lower(), 0)),
                     len(_cuisine_places(places, COUNTRY_CUISINES.get(str(country), "")))))
    return (pd.DataFrame(rows, columns=["origin_country", "recipes", "ingredients_linked_pct",
                                        "home_products_sold_in_us", "nearby_places"])
            .sort_values("recipes", ascending=False, ignore_index=True))
