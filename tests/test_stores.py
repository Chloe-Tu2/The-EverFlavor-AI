"""Tests for stores, restaurants and products (src/everflavor/stores.py), notebook 03.

No request leaves the computer: requests.get / requests.post and time.sleep are
replaced. The key checks: a Google key never shows up in an error, and store
claims always stay "unverified". Run with `python -m pytest tests`, or alone:

    python tests/test_stores.py
"""
import sys
from pathlib import Path

import pandas as pd
import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import stores
from everflavor.stores import (
    UNVERIFIED_NOTE,
    link_ingredients_to_products,
    off_products_by_country,
    osm_places,
    place_details_live,
    place_queries,
    region_coverage,
    search_places,
    suggest_where_to_buy,
)

FAKE_KEY = "FAKE_PLACES_KEY_DO_NOT_PRINT"
AREA = {"name": "Test City", "lat": 29.76, "lng": -95.37, "radius_m": 5000}


class FakeResponse:
    """The parts of requests.Response the helpers use."""

    def __init__(self, status: int = 200, body: object = None):
        self.status_code = status
        self.ok = status < 400
        self._body = body if body is not None else {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if not self.ok:
            raise requests.HTTPError(f"HTTP {self.status_code}")


@pytest.fixture
def fake_net(monkeypatch):
    """Replace requests.get and requests.post with a queue of answers; record every call; never sleep."""
    calls: list[dict] = []
    answers: list[object] = []

    def fake(method):
        def call(url, **kwargs):
            calls.append({"method": method, "url": url, **kwargs})
            answer = answers.pop(0)
            if isinstance(answer, Exception):
                raise answer
            return answer
        return call

    monkeypatch.setattr(stores.requests, "get", fake("get"))
    monkeypatch.setattr(stores.requests, "post", fake("post"))
    monkeypatch.setattr(stores.time, "sleep", lambda *_: None)
    return calls, answers


# ------------------------------------------------------------------ OpenStreetMap
def test_osm_places_try_the_next_server_and_read_tags(fake_net, tmp_path):
    calls, answers = fake_net
    answers.extend([FakeResponse(504), FakeResponse(200, {"elements": [
        {"type": "node", "id": 1, "lat": 29.7, "lon": -95.3,
         "tags": {"name": "Viet Hoa International Foods", "shop": "supermarket", "diet:halal": "no"}},
        {"type": "way", "id": 2, "center": {"lat": 29.8, "lon": -95.4},
         "tags": {"name": "Blue Nile", "amenity": "restaurant", "cuisine": "ethiopian;vegan", "diet:vegan": "only"}},
    ]})])
    out = osm_places(AREA, "grocery", tmp_path).set_index("osm_id")
    assert [c["url"] for c in calls] == stores.OVERPASS_URLS[:2]                # the busy server is skipped
    assert "EverFlavorAI" in calls[0]["headers"]["User-Agent"]
    assert [out.loc["node/1", "name_hint"], out.loc["node/1", "diet_halal"]] == ["vietnamese", False]
    assert out.loc["way/2", "cuisine"] == ["ethiopian", "vegan"] and out.loc["way/2", "lat"] == 29.8
    assert [out.loc["way/2", "diet_vegan"], out.loc["way/2", "diet_kosher"]] == [True, None]
    osm_places(AREA, "grocery", tmp_path)                                       # from the cache
    assert len(calls) == 2


# ------------------------------------------------------------------ Google Places
def test_google_places_keep_only_ids_and_never_show_the_key(fake_net, tmp_path):
    calls, answers = fake_net
    answers.append(FakeResponse(200, {"places": [{"id": "ChIJabc", "types": ["grocery_store"],
                                                  "displayName": {"text": "Not stored"}}]}))
    places = search_places("Ethiopian grocery store", AREA, FAKE_KEY, tmp_path)
    assert places[0]["place_id"] == "ChIJabc" and "displayName" not in places[0]
    assert calls[0]["headers"]["X-Goog-Api-Key"] == FAKE_KEY and FAKE_KEY not in calls[0]["url"]
    assert "Not stored" not in next(tmp_path.glob("*.json")).read_text(encoding="utf-8")
    answers.append(requests.ConnectionError(f"Max retries exceeded with key={FAKE_KEY}"))
    with pytest.raises(RuntimeError) as info:
        place_details_live("ChIJabc", FAKE_KEY)
    assert FAKE_KEY not in str(info.value)
    answers.append(FakeResponse(403))
    with pytest.raises(RuntimeError) as info:
        search_places("halal butcher", AREA, FAKE_KEY, tmp_path)
    assert FAKE_KEY not in str(info.value)
    with pytest.raises(ValueError):
        place_details_live("../evil", FAKE_KEY)
    answers.append(FakeResponse(200, {"displayName": {"text": "Abyssinia Market"}, "formattedAddress": "1 Main St"}))
    details = place_details_live("ChIJabc", FAKE_KEY)
    assert details["name"] == "Abyssinia Market" and details["note"] == UNVERIFIED_NOTE


def test_place_queries_fill_in_the_cuisines():
    queries = place_queries(["ethiopian"])
    assert ("grocery", "ethiopian", "ethiopian grocery store") in queries
    assert ("butcher", "halal", "halal butcher") in queries


# ------------------------------------------------------------------ Open Food Facts and linking
def _export(tmp_path) -> Path:
    path = tmp_path / "food.parquet"
    pd.DataFrame({
        "code": ["1", "2", "3", "4"],
        "product_name": [[{"lang": "main", "text": "Lee Kum Kee Soy Sauce"}], [{"lang": "fr", "text": "Sauce soja"}],
                         [{"lang": "en", "text": "Doubanjiang chili bean paste"}], None],
        "brands": ["Lee Kum Kee", "Kikkoman", "Pixian", None],
        "categories_tags": [["en:condiments", "en:soy-sauces"], ["en:soy-sauces"], ["en:pastes"], []],
        "origins_tags": [["en:china"], [], ["en:china"], []],
        "manufacturing_places_tags": [[], ["en:netherlands"], [], []],
        "countries_tags": [["en:united-states"], ["en:france"], ["en:united-states", "en:china"], []],
        "stores_tags": [[], [], [], []], "allergens_tags": [["en:soybeans"], ["en:soybeans"], [], []],
        "traces_tags": [[], [], [], []], "ingredients_analysis_tags": [[], [], [], []],
    }).to_parquet(path, row_group_size=2)
    return path


def test_off_products_link_and_suggest_where_to_buy(tmp_path):
    products = off_products_by_country(_export(tmp_path), tmp_path / "compact.parquet", n_row_groups=None)
    assert products["product_name"].tolist()[:3] == ["Lee Kum Kee Soy Sauce", "Sauce soja", "Doubanjiang chili bean paste"]
    assert products["home_country"].tolist() == ["China", "", "China", ""]   # Netherlands: no product is sold there
    assert products["sold_in_us"].tolist() == [True, False, True, False]
    assert off_products_by_country("unused", tmp_path / "compact.parquet").equals(products)   # cached
    links = link_ingredients_to_products(["soy sauce", "doubanjiang", "saffron"], products)
    soy = links[links["ingredient"] == "soy sauce"]
    assert soy["code"].tolist() == ["1", "2"] and set(soy["match"]) == {"category"}           # US first
    assert links[links["ingredient"] == "doubanjiang"]["match"].tolist() == ["name"]
    places = pd.DataFrame({"name": ["Hong Kong Food Market", "Corner Store"], "category": ["grocery", "grocery"],
                           "cuisine": [[], []], "name_hint": ["chinese", ""]})
    tip = suggest_where_to_buy("soy sauce", "China", links, places)
    assert tip["home_brands"] == ["Lee Kum Kee"] and tip["stores_to_try"] == ["Hong Kong Food Market"]
    assert tip["store_match"] == "cuisine" and tip["note"] == UNVERIFIED_NOTE
    asian = places.assign(name_hint=["asian", ""])
    assert suggest_where_to_buy("soy sauce", "Japan", links, asian)["store_match"] == "region"
    latin = places.assign(name_hint=["latin american", ""])
    none = suggest_where_to_buy("soy sauce", "China", links, latin)      # never an unrelated store
    assert none["stores_to_try"] == [] and none["store_match"] == "none"
    recipes = pd.DataFrame({"origin_country": ["China", "China", "Unknown"],
                            "ingredient_list": [["soy sauce", "ginger"], ["soy sauce"], ["salt"]]})
    coverage = region_coverage(recipes, links, products, places).iloc[0]
    assert (coverage.origin_country, coverage.recipes, coverage.ingredients_linked_pct) == ("China", 2, 50.0)
    assert coverage.home_products_sold_in_us == 2 and coverage.nearby_places == 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
