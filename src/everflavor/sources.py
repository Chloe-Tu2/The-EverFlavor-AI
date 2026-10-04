"""Download helpers for every data source (Week 4 and 5.8): skip-if-present,
paced and retried requests, and never a key in an error message."""
from __future__ import annotations

import io
import json
import re
import string
import time
import zipfile
from collections.abc import Iterable, Mapping
from pathlib import Path

import pandas as pd
import requests

from .progress import progress_bar

# ------------------------------------------------------------------ files

__all__ = [
    "ENERGY_NAMES",
    "OFF_BASE_URL",
    "OFF_HEADERS",
    "OFF_MIN_INTERVAL",
    "OFF_RETRY_STATUS",
    "RETRY_STATUS",
    "USDA_BASE_URL",
    "USDA_DOWNLOADS",
    "USDA_NUTRIENTS",
    "cached_off_search",
    "download_and_unzip",
    "download_file",
    "download_themealdb",
    "download_usda",
    "extract_off_record",
    "find_file",
    "get_energy_kcal",
    "off_get_by_barcode",
    "off_search",
    "usda_search",
    "usda_table",
]


def download_file(url: str, target: str | Path, timeout: int = 300) -> Path:
    """Download a file, writing it under a temporary name first.

    An interrupted download is therefore never mistaken for a finished one.
    Only for URLs without a key in them: an error message shows the URL.

    Returns:
        The downloaded file.
    """
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()   # only for URLs without a key in them
    partial = target.with_suffix(".part")
    partial.write_bytes(response.content)
    partial.replace(target)
    return target


def find_file(folder: str | Path, name: str) -> Path | None:
    """Return the first file called `name` anywhere under `folder`, or None."""
    return next(Path(folder).rglob(name), None)


def download_and_unzip(url: str, folder: str | Path, timeout: int = 120) -> None:
    """Download a zip file and extract it into `folder`."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    zipfile.ZipFile(io.BytesIO(response.content)).extractall(folder)


# ------------------------------------------------------------------ USDA API (2.4.1)
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"


def usda_search(query: str, api_key: str, page_size: int = 5, data_type: str = "Foundation,SR Legacy") -> dict:
    """Search the USDA FoodData Central API for an ingredient.

    Args:
        query: The ingredient name to search for.
        api_key: The USDA API key (never printed, not even in errors).
        page_size: Number of results to return.
        data_type: Comma-separated USDA data types. "Foundation,SR Legacy"
            returns generic raw ingredients instead of branded products.

    Returns:
        The API's JSON answer.

    Raises:
        RuntimeError: If the API answers with an error status (for example 403
            for an invalid key) or cannot be reached.
    """
    params: dict[str, str | int] = {
        "api_key": api_key,  # passed in, never written in the code
        "query": query,
        "pageSize": page_size,
        "dataType": data_type,
    }
    try:
        response = requests.get(USDA_BASE_URL, params=params, timeout=15)
    except requests.RequestException as e:
        # A connection error's message contains the full request URL, key included:
        # report only its type, and `from None` keeps the original out of the traceback
        raise RuntimeError(f"USDA API could not be reached ({type(e).__name__})") from None
    if not response.ok:
        # Do not use raise_for_status() here: its message contains the
        # full request URL, which would print the API key in the output.
        raise RuntimeError(f"USDA API request failed with HTTP {response.status_code}")
    return response.json()


# USDA reports energy under several names, and some entries are in kJ.
# We only accept kcal values, in this order of preference.
ENERGY_NAMES = ["Energy", "Energy (Atwater General Factors)", "Energy (Atwater Specific Factors)"]

def get_energy_kcal(food_nutrients: Iterable[dict]) -> float | None:
    """Return a USDA food's energy in kcal (ENERGY_NAMES order), or None if only kJ is listed."""
    kcal_values = {
        n.get("nutrientName"): n.get("value")
        for n in food_nutrients
        if str(n.get("unitName", "")).upper() == "KCAL"
    }
    for name in ENERGY_NAMES:
        if name in kcal_values:
            return kcal_values[name]
    return None


# ------------------------------------------------------------------ USDA bulk downloads (5.8.1)
USDA_DOWNLOADS = {
    # name      : (download URL, top-level key in the JSON file)
    "fndds"     : ("https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_survey_food_json_2024-10-31.zip", "SurveyFoods"),
    "sr_legacy" : ("https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_json_2018-04.zip", "SRLegacyFoods"),
}
# USDA nutrient name -> our column (values are per 100 g)
USDA_NUTRIENTS = {"Energy": "kcal_100g", "Protein": "protein_100g", "Total lipid (fat)": "fat_100g",
                  "Carbohydrate, by difference": "carbs_100g", "Sodium, Na": "sodium_mg_100g"}


def download_usda(name: str, folder: str | Path, refresh: bool = False) -> Path:
    """Return the local zip of one USDA bulk download ("fndds" or "sr_legacy"), downloading it if needed."""
    if name not in USDA_DOWNLOADS:
        raise ValueError(f"Unknown USDA download '{name}'. Use one of: {', '.join(USDA_DOWNLOADS)}.")
    url, _ = USDA_DOWNLOADS[name]
    target = Path(folder) / url.rsplit("/", 1)[-1]
    if target.exists() and not refresh:
        return target
    print(f"Downloading {target.name} from USDA ...")
    return download_file(url, target)


def usda_table(name: str, folder: str | Path, refresh: bool = False,
               nutrients: Mapping[str, str] | None = None) -> pd.DataFrame:
    """Read one USDA bulk download into a table.

    Args:
        name: "fndds" (prepared dishes) or "sr_legacy" (single ingredients).
        folder: Where the zip files are kept.
        refresh: Download again even if the zip exists.
        nutrients: Extra {USDA nutrient name: column} to read besides
            USDA_NUTRIENTS, for example the fatty acids in cooking.FAT_NUTRIENTS.

    Returns:
        One row per food: 'fdc_id', 'description', the USDA_NUTRIENTS (and any
        extra `nutrients`) per 100 g and 'serving_g' (FNDDS's typical portion,
        else missing).
    """
    wanted = {**USDA_NUTRIENTS, **(nutrients or {})}
    _, key = USDA_DOWNLOADS[name]
    with zipfile.ZipFile(download_usda(name, folder, refresh)) as archive:
        json_name = next(n for n in archive.namelist() if n.endswith(".json"))
        foods = json.loads(archive.read(json_name))[key]
    rows = []
    for food in foods:
        row = {"fdc_id": food["fdcId"], "description": food["description"]}
        for item in food.get("foodNutrients", []):
            nutrient = item.get("nutrient", {})
            column = wanted.get(nutrient.get("name"))
            # Energy is listed in both kcal and kJ: keep kcal only
            if column and (column != "kcal_100g" or str(nutrient.get("unitName", "")).lower() == "kcal"):
                row[column] = item.get("amount")
        # FNDDS gives a typical portion for when the amount eaten is unknown
        row["serving_g"] = next((p.get("gramWeight") for p in food.get("foodPortions", [])
                                 if p.get("portionDescription") == "Quantity not specified"), None)
        rows.append(row)
    return pd.DataFrame(rows).dropna(subset=["kcal_100g"]).reset_index(drop=True)


# ------------------------------------------------------------------ Open Food Facts (2.4.4)
OFF_BASE_URL = "https://world.openfoodfacts.org"

# Open Food Facts asks every client to send a descriptive User-Agent.
# Requests without one can be blocked with 403 Forbidden.
OFF_HEADERS = {
    "User-Agent": "EverFlavorAI - Colab Academic Project - Version 1.0 (contact: team@everglow.com)"
}

# Status codes that mean "try again later" (rate limit or server busy)
OFF_RETRY_STATUS = {429, 500, 502, 503, 504}

# Open Food Facts allows 10 search requests and 15 product requests per
# minute per user, and answers 503 when it is over its limits or busy.
# We keep at least this many seconds between requests of each kind.
OFF_MIN_INTERVAL = {"search": 6.5, "product": 4.5}
_off_last_request = {"search": 0.0, "product": 0.0}


def _off_wait_turn(kind):
    """Sleep just long enough to stay under the rate limit for this kind of request."""
    wait = OFF_MIN_INTERVAL[kind] - (time.monotonic() - _off_last_request[kind])
    if wait > 0:
        time.sleep(wait)
    _off_last_request[kind] = time.monotonic()


def _off_get(url: str, params: dict | None = None, kind: str = "product", retries: int = 3,
            backoff: float = 10.0) -> dict:
    """GET a URL from Open Food Facts and return the JSON body.

    Requests are paced to respect the API's rate limits. Temporary failures
    (rate limits, busy servers, timeouts) are retried after the wait the
    server asks for (Retry-After), or 10 s, then 20 s.

    Args:
        url: Full endpoint URL.
        params: Query parameters.
        kind: "search" or "product" (they have different limits).
        retries: Maximum number of attempts.
        backoff: Seconds to wait after the first failure; doubles each time.

    Returns:
        The parsed JSON answer.

    Raises:
        requests.HTTPError: For an error that is not temporary, or after the last attempt.
    """
    for attempt in range(1, retries + 1):
        _off_wait_turn(kind)
        try:
            response = requests.get(url, params=params, headers=OFF_HEADERS, timeout=20)
        except (requests.ConnectionError, requests.Timeout):
            if attempt == retries:
                raise
            time.sleep(backoff * 2 ** (attempt - 1))
            continue
        if response.status_code in OFF_RETRY_STATUS and attempt < retries:
            retry_after = response.headers.get("Retry-After", "")
            wait = float(retry_after) if retry_after.isdigit() else backoff * 2 ** (attempt - 1)
            time.sleep(min(wait, 120))
            continue
        if not response.ok:
            # Short message (the full one repeats the long request URL)
            raise requests.HTTPError(f"Open Food Facts answered HTTP {response.status_code}",
                                     response=response)
        return response.json()
    raise ValueError(f"retries must be at least 1, got {retries}")


def off_search(query: str, page_size: int = 5) -> list[dict]:
    """Search Open Food Facts for products with completed nutrition facts.

    Args:
        query: Ingredient or product name.
        page_size: Maximum number of results.

    Returns:
        Raw product records (every one has at least a calorie value).
    """
    url = f"{OFF_BASE_URL}/cgi/search.pl"
    params: dict[str, str | int] = {
        "search_terms"   : query,
        "search_simple"  : 1,
        "action"         : "process",
        "json"           : 1,
        "page_size"      : page_size,
        # Only return products with completed nutrition facts
        "tagtype_0"      : "states",
        "tag_contains_0" : "contains",
        "tag_0"          : "en:nutrition-facts-completed",
    }
    return _off_get(url, params=params, kind="search").get("products", [])


def off_get_by_barcode(barcode: str) -> dict | None:
    """Fetch one Open Food Facts product by barcode (EAN-13 or UPC), or None if unknown.

    Raises:
        ValueError: If `barcode` is not 8 to 14 digits. The barcode becomes part of
            the request URL, so text such as "../search" must never get through
            (agents may pass a user's input here).
    """
    barcode = str(barcode).strip()
    if not re.fullmatch(r"\d{8,14}", barcode):
        raise ValueError(f"A barcode must be 8 to 14 digits, got {barcode!r}.")
    url = f"{OFF_BASE_URL}/api/v2/product/{barcode}.json"
    try:
        data = _off_get(url)
    except requests.HTTPError as e:
        # The API answers 404 for barcodes it does not know
        if e.response is not None and e.response.status_code == 404:
            return None
        raise
    if data.get("status") == 1:
        return data.get("product")
    return None


def extract_off_record(product: dict) -> dict:
    """Pull the fields we use from a raw Open Food Facts product.

    Nutrition values are per 100 g. Missing text fields become "" so they count
    as missing; Nutri-Score is kept only when it is A to E.

    Returns:
        A flat record: product_name, brands, countries, ingredients_text,
        energy_kcal_100g, proteins_100g, fat_100g, carbs_100g, fiber_100g,
        sodium_100g, nutriscore_grade, nova_group, allergens, image_url.
    """
    nut = product.get("nutriments") or {}
    # OFF uses "unknown" or "not-applicable" when there is no score.
    # We store those as "" so they are counted as missing.
    grade = (product.get("nutriscore_grade") or "").upper()
    return {
        "product_name"     : (product.get("product_name") or "").strip(),
        "brands"           : product.get("brands") or "",
        "countries"        : product.get("countries") or "",
        "ingredients_text" : product.get("ingredients_text") or "",
        # All nutrition values are per 100 g of product
        "energy_kcal_100g" : nut.get("energy-kcal_100g"),
        "proteins_100g"    : nut.get("proteins_100g"),
        "fat_100g"         : nut.get("fat_100g"),
        "carbs_100g"       : nut.get("carbohydrates_100g"),
        "fiber_100g"       : nut.get("fiber_100g"),
        "sodium_100g"      : nut.get("sodium_100g"),
        # Nutri-Score: A (best) to E (worst)
        "nutriscore_grade" : grade if grade in {"A", "B", "C", "D", "E"} else "",
        # NOVA group: 1 (unprocessed) to 4 (ultra-processed)
        "nova_group"       : product.get("nova_group"),
        "allergens"        : product.get("allergens") or "",
        "image_url"        : product.get("image_url") or "",
    }


def cached_off_search(query: str, cache_dir: str | Path, refresh: bool = False,
                      page_size: int = 3) -> tuple[list[dict], bool]:
    """Search Open Food Facts, reusing a saved copy of the same search if there is one.

    Returns:
        (products, came_from_cache).
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / (re.sub(r"[^a-z0-9]+", "_", query.lower()) + ".json")
    if cache_file.exists() and not refresh:
        return json.loads(cache_file.read_text(encoding="utf-8")), True
    products = off_search(query, page_size=page_size)
    cache_file.write_text(json.dumps(products), encoding="utf-8")
    return products, False


# ------------------------------------------------------------------ TheMealDB (2.4.6)
# Status codes that mean "try again later" (rate limit or server busy)
RETRY_STATUS = {429, 500, 502, 503, 504}


def _get_json(url: str, params: dict | None = None, retries: int = 3, backoff: float = 2.0) -> dict:
    """GET a URL and return its JSON, retrying temporary errors with a growing wait.

    Raises:
        RuntimeError: For an error status or a failed connection, without showing
            the URL (it may contain a key).
    """
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=20)
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt == retries:
                # The original message contains the URL: report only the error type
                raise RuntimeError(f"TheMealDB could not be reached ({type(e).__name__})") from None
            time.sleep(backoff * attempt)
            continue
        if response.status_code in RETRY_STATUS and attempt < retries:
            time.sleep(backoff * attempt)
            continue
        if not response.ok:
            # Do not print the URL: it contains the API key
            raise RuntimeError(f"TheMealDB request failed with HTTP {response.status_code}")
        return response.json()
    raise ValueError(f"retries must be at least 1, got {retries}")


def _meal_to_row(meal: dict) -> dict:
    """Flatten one TheMealDB record (its ingredients are in 20 numbered fields)."""
    ingredients, measures = [], []
    for i in range(1, 21):
        name = (meal.get(f"strIngredient{i}") or "").strip()
        if name:
            ingredients.append(name)
            measures.append((meal.get(f"strMeasure{i}") or "").strip())
    return {
        "recipe_id"   : meal["idMeal"],
        "recipe_name" : meal.get("strMeal"),
        # Newer records use strCountry instead of strArea
        "area"        : meal.get("strArea") or meal.get("strCountry"),
        "category"    : meal.get("strCategory"),
        "instructions": meal.get("strInstructions"),
        "ingredients" : ingredients,
        "measures"    : measures,
        "tags"        : meal.get("strTags"),
        "source_url"  : meal.get("strSource"),
    }


def download_themealdb(search_url: str) -> pd.DataFrame:
    """Collect TheMealDB by searching every first letter and digit, with a short pause between requests.

    Args:
        search_url: The search endpoint, including the API key.

    Returns:
        One row per recipe (repeats removed); failed searches are reported and skipped.
    """
    meals = {}
    for first_char in progress_bar(string.ascii_lowercase + string.digits, "Searching TheMealDB"):
        try:
            data = _get_json(search_url, params={"f": first_char})
        except (requests.RequestException, RuntimeError, ValueError) as e:
            # Only the error type: the full message can contain the URL with the key
            print(f"  Warning: search for '{first_char}' failed ({type(e).__name__})")
            continue
        for meal in data.get("meals") or []:
            meals[meal["idMeal"]] = meal
        time.sleep(0.3)   # be polite to the free API
    return pd.DataFrame([_meal_to_row(m) for m in meals.values()])
