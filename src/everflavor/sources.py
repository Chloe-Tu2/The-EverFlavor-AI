"""Download helpers for every data source (Week 4 and 5.8): skip-if-present,
paced and retried requests, and never a key in an error message."""
import io
import json
import re
import string
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

# ------------------------------------------------------------------ files

def download_file(url, target, timeout=300):
    """Download `url` to `target`. Writes under a temporary name first, so an
    interrupted download is never mistaken for a finished one."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()   # only for URLs without a key in them
    partial = target.with_suffix(".part")
    partial.write_bytes(response.content)
    partial.replace(target)
    return target


def find_file(folder, name):
    """Return the first file called `name` anywhere under `folder`, or None."""
    return next(Path(folder).rglob(name), None)


def download_and_unzip(url, folder, timeout=120):
    """Download a zip file and extract it into `folder`."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    zipfile.ZipFile(io.BytesIO(response.content)).extractall(folder)


# ------------------------------------------------------------------ USDA API (2.4.1)
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"


def usda_search(query, api_key, page_size=5, data_type="Foundation,SR Legacy"):
    """Search the USDA FoodData Central API for a given ingredient.

    Args:
        query (str): The ingredient name to search for.
        api_key (str): The USDA API key (never printed).
        page_size (int): Number of results to return.
        data_type (str): Comma-separated USDA data types to search.
            "Foundation,SR Legacy" returns generic raw ingredients
            instead of branded products (plantain, not plantain chips).

    Returns:
        dict: The raw JSON response from the API.

    Raises:
        RuntimeError: If the API returns an error status
            (for example 403 for an invalid key).
    """
    params = {
        "api_key": api_key,  # passed in, never written in the code
        "query": query,
        "pageSize": page_size,
        "dataType": data_type,
    }
    response = requests.get(USDA_BASE_URL, params=params, timeout=15)
    if not response.ok:
        # Do not use raise_for_status() here: its message contains the
        # full request URL, which would print the API key in the output.
        raise RuntimeError(f"USDA API request failed with HTTP {response.status_code}")
    return response.json()


# USDA reports energy under several names, and some entries are in kJ.
# We only accept kcal values, in this order of preference.
ENERGY_NAMES = ["Energy", "Energy (Atwater General Factors)", "Energy (Atwater Specific Factors)"]

def get_energy_kcal(food_nutrients):
    """Return the energy value in kcal, or None if no kcal value is listed."""
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


def download_usda(name, folder, refresh=False):
    """Return the local zip for one USDA download, downloading it if needed."""
    url, _ = USDA_DOWNLOADS[name]
    target = Path(folder) / url.rsplit("/", 1)[-1]
    if target.exists() and not refresh:
        return target
    print(f"Downloading {target.name} from USDA ...")
    return download_file(url, target)


def usda_table(name, folder, refresh=False):
    """Read one USDA download into a table: one row per food, nutrients per 100 g."""
    _, key = USDA_DOWNLOADS[name]
    with zipfile.ZipFile(download_usda(name, folder, refresh)) as archive:
        json_name = next(n for n in archive.namelist() if n.endswith(".json"))
        foods = json.loads(archive.read(json_name))[key]
    rows = []
    for food in foods:
        row = {"fdc_id": food["fdcId"], "description": food["description"]}
        for item in food.get("foodNutrients", []):
            nutrient = item.get("nutrient", {})
            column = USDA_NUTRIENTS.get(nutrient.get("name"))
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


def off_get(url, params=None, kind="product", retries=3, backoff=10.0):
    """GET a URL from Open Food Facts and return the JSON body.

    Requests are paced to respect the API's rate limits. Temporary
    failures (rate limits, busy servers, timeouts) are retried after
    the wait the server asks for (Retry-After), or 10 s, then 20 s.
    Any other error is raised.

    Args:
        url (str): Full endpoint URL.
        params (dict | None): Query parameters.
        kind (str): "search" or "product" (they have different limits).
        retries (int): Maximum number of attempts.
        backoff (float): Seconds to wait after the first failure;
            the wait doubles with each attempt.

    Returns:
        dict: The parsed JSON response.
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


def off_search(query, page_size=5):
    """Search Open Food Facts for products matching a query string.

    Only returns products that already have completed nutrition facts,
    so every result will have at least a calorie value.

    Args:
        query (str): Ingredient or product name to search for.
        page_size (int): Maximum number of results to return.

    Returns:
        list[dict]: List of raw product dictionaries from the API.
    """
    url = f"{OFF_BASE_URL}/cgi/search.pl"
    params = {
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
    return off_get(url, params=params, kind="search").get("products", [])


def off_get_by_barcode(barcode):
    """Fetch a single product record from Open Food Facts by barcode.

    Args:
        barcode (str): The product barcode (EAN-13 or UPC).

    Returns:
        dict | None: The product dictionary, or None if not found.
    """
    url = f"{OFF_BASE_URL}/api/v2/product/{barcode}.json"
    try:
        data = off_get(url)
    except requests.HTTPError as e:
        # The API answers 404 for barcodes it does not know
        if e.response is not None and e.response.status_code == 404:
            return None
        raise
    if data.get("status") == 1:
        return data.get("product")
    return None


def extract_off_record(product):
    """Pull the fields we need from a raw Open Food Facts product dict.

    Fields: product_name, brands, countries, ingredients_text,
    energy_kcal_100g, proteins_100g, fat_100g, carbs_100g,
    fiber_100g, sodium_100g, nutriscore_grade, nova_group,
    allergens, image_url.

    Text fields that are missing come back as an empty string.

    Args:
        product (dict): A raw product dictionary from the OFF API.

    Returns:
        dict: A flat dictionary of cleaned fields.
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


def cached_off_search(query, cache_dir, refresh=False, page_size=3):
    """Return (products, came_from_cache) for a search, using the saved copy if there is one."""
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


def get_json(url, params=None, retries=3, backoff=2.0):
    """GET a URL and return its JSON, retrying temporary errors with a growing wait."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=20)
        except (requests.ConnectionError, requests.Timeout):
            if attempt == retries:
                raise
            time.sleep(backoff * attempt)
            continue
        if response.status_code in RETRY_STATUS and attempt < retries:
            time.sleep(backoff * attempt)
            continue
        if not response.ok:
            # Do not print the URL: it contains the API key
            raise RuntimeError(f"TheMealDB request failed with HTTP {response.status_code}")
        return response.json()


def meal_to_row(meal):
    """Flatten one TheMealDB record (ingredients are in 20 numbered fields)."""
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


def download_themealdb(search_url):
    """Search TheMealDB by every first letter and digit; return one row per recipe."""
    meals = {}
    for first_char in string.ascii_lowercase + string.digits:
        try:
            data = get_json(search_url, params={"f": first_char})
        except (requests.RequestException, RuntimeError, ValueError) as e:
            # Only the error type: the full message can contain the URL with the key
            print(f"  Warning: search for '{first_char}' failed ({type(e).__name__})")
            continue
        for meal in data.get("meals") or []:
            meals[meal["idMeal"]] = meal
        time.sleep(0.3)   # be polite to the free API
    return pd.DataFrame([meal_to_row(m) for m in meals.values()])
