"""The Food Discovery Map's claims (places.py): every diet or cuisine claim has evidence; certified needs a record."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.places import (
    SPECIALTY_FILE,
    UNKNOWN_LABEL,
    cuisine_indicators,
    diet_evidence,
    diet_label,
    find_stores_for,
    load_place_evidence,
    load_specialty_ingredients,
    map_places,
    map_url,
    place_facts,
    specialty_in,
)


def test_certified_only_with_a_checked_record() -> None:
    row = pd.Series({"name": "Al-Aqsa Halal Meat", "diet_halal": True})
    assert [(e["level"], e["label"]) for e in diet_evidence(row)] == [("likely", "Likely halal-friendly")]
    record = {"tag": "halal", "source": "https://example.org/certified-list", "checked": "2026-11-11",
              "checked_by": "a teammate"}
    got = diet_evidence(row, [record])
    assert got[0]["level"] == "verified" and got[0]["label"] == "Halal-certified"
    assert diet_evidence(row, [dict(record, source="a phone call")])[0]["level"] == "likely"   # no link, no verified


def test_name_and_tags_are_likely_and_say_why_and_no_is_never_shown() -> None:
    by_name = diet_evidence(pd.Series({"name": "Trendy Vegan"}))
    assert by_name == [{"tag": "vegan", "level": "likely", "label": "Likely vegan-friendly",
                        "reason": "Its name says \"vegan\"", "source": "the business's name"}]
    assert diet_evidence(pd.Series({"name": "Joe's Grill", "diet_halal": False})) == []
    assert diet_evidence(pd.Series({"name": "Vegetables Galore"})) == []       # "vegetables" is not "vegetarian"


def test_words_never_claim_more_than_the_level() -> None:
    for tag in ("halal", "kosher", "vegetarian", "vegan"):
        assert "likely" in diet_label(tag, "likely").lower()
        assert diet_label(tag, "unknown") == UNKNOWN_LABEL
    with pytest.raises(ValueError):
        diet_label("organic", "verified")


def test_cuisine_is_reported_with_its_source_never_judged() -> None:
    row = pd.Series({"cuisine": np.array(["lebanese", "middle_eastern"]), "name_hint": "halal"})
    texts = [i["text"] for i in cuisine_indicators(row)]
    # a diet word in the name is a diet claim (with its own level), never a cuisine indicator
    assert texts == ["OpenStreetMap lists its cuisine as lebanese, Middle Eastern"]
    assert [i["text"] for i in cuisine_indicators(pd.Series({"name_hint": "persian"}))] == ["Its name suggests persian food"]
    assert not any("authentic" in t.lower() or "best" in t.lower() for t in texts)
    facts = place_facts(pd.Series({"name": None, "category": "grocery"}))
    assert facts["name"] == "Unnamed grocery" and facts["hours"] == "Hours not listed" and facts["diet"] == []
    assert facts["map_url"] == ""   # no location, no maps button


def test_open_in_maps_links_only_the_places_own_location() -> None:
    facts = place_facts(pd.Series({"name": "Shop", "category": "grocery", "lat": 29.76, "lng": -95.37}))
    assert facts["map_url"] == ("https://www.openstreetmap.org/?mlat=29.760000&mlon=-95.370000"
                                "#map=18/29.760000/-95.370000")
    assert map_url(float("nan"), 1.0) == "" and map_url(95.0, 1.0) == "" and map_url("29", "-95") == ""


def test_negated_names_and_numpy_flags() -> None:
    assert diet_evidence(pd.Series({"name": "Non-Halal Deli"})) == []
    assert diet_evidence(pd.Series({"name": "Not Kosher Pickles"})) == []
    assert diet_evidence(pd.Series({"name": "Shop", "diet_vegan": np.True_}))[0]["level"] == "likely"
    assert diet_evidence(pd.Series({"name": "Shop", "diet_vegan": np.nan})) == []


def test_specialty_table_is_valid_sourced_and_never_claims_stock(tmp_path: Path) -> None:
    table = load_specialty_ingredients()
    assert len(table) >= 40 and table["source_url"].str.startswith("https://").all()
    words = " ".join(table["note"]).lower()
    assert not any(w in words for w in (" carries", "certified", "authentic", "best "))
    bad = tmp_path / "bad.csv"
    bad.write_text(SPECIALTY_FILE.read_text(encoding="utf-8") + "x,harissa,moroccan,corner shop,n,http://a,l,\n",
                   encoding="utf-8")
    with pytest.raises(ValueError, match="harissa.*also|store kind|https"):
        load_specialty_ingredients(bad)


def test_look_for_matches_whole_words_only() -> None:
    table = load_specialty_ingredients()
    found = [i["ingredient"] for i in specialty_in(["2 tbsp harissa paste", "anchovy fillet", "za'atar"], table)]
    assert found == ["harissa", "za'atar"]          # "anchovy" is not "ancho"
    assert specialty_in(["salt", "water"], table) == []


PLACES = pd.DataFrame([
    {"osm_id": "node/1", "name": "Casablanca Market", "category": "grocery", "osm_kind": "deli",
     "cuisine": ["moroccan"], "name_hint": "", "lat": 29.7, "lng": -95.4},
    {"osm_id": "node/2", "name": "Middle East Foods", "category": "grocery", "osm_kind": "deli",
     "cuisine": [], "name_hint": "middle eastern", "lat": 29.7, "lng": -95.4},
    {"osm_id": "node/3", "name": "Big Supermarket", "category": "grocery", "osm_kind": "supermarket",
     "cuisine": [], "name_hint": "", "lat": 29.7, "lng": -95.4},
    {"osm_id": "node/4", "name": "Corner Stop", "category": "convenience", "osm_kind": "convenience",
     "cuisine": ["moroccan"], "name_hint": "", "lat": 29.7, "lng": -95.4},
    {"osm_id": "node/5", "name": "Fez Kitchen", "category": "restaurant", "osm_kind": "restaurant",
     "cuisine": ["moroccan"], "name_hint": "", "lat": 29.7, "lng": -95.4, "diet_halal": True},
    {"osm_id": "node/6", "name": "Taco Place", "category": "restaurant", "osm_kind": "restaurant",
     "cuisine": ["mexican"], "name_hint": "", "lat": 29.7, "lng": -95.4},
])


def test_find_stores_for_a_tagine_says_likely_with_a_reason() -> None:
    got = find_stores_for(["chicken", "preserved lemon", "ras el hanout"], "Morocco", PLACES,
                          load_specialty_ingredients())
    assert [i["ingredient"] for i in got["look_for"]] == ["ras el hanout", "preserved lemon"]
    stores = {s["name"]: s["why"] for s in got["stores"]}
    assert list(stores) == ["Casablanca Market", "Middle East Foods", "Big Supermarket"]   # never the convenience store
    assert stores["Casablanca Market"] == ("Likely carries Moroccan ingredients "
                                           "(OpenStreetMap lists its cuisine as moroccan)")
    assert all(w.startswith(("Likely carries", "A supermarket")) for w in stores.values())
    assert [e["name"] for e in got["eat"]] == ["Fez Kitchen"]
    assert find_stores_for(["salt"], None, PLACES, load_specialty_ingredients())["stores"][0]["name"] == "Big Supermarket"


def test_map_places_filters_and_decides_words_in_the_back_end(tmp_path: Path) -> None:
    rows = map_places(PLACES, ["restaurant"], cuisine="moroccan")
    assert rows["label"].tolist() == ["Fez Kitchen"] and rows["level"].tolist() == ["likely"]
    assert map_places(PLACES, ["restaurant"], diet="halal", level="verified").empty
    evidence = tmp_path / "evidence.csv"
    evidence.write_text("osm_id,name,tag,source,checked,checked_by\n"
                        "node/5,Fez Kitchen,halal,https://example.org/list,2026-11-16,a teammate\n", encoding="utf-8")
    verified = map_places(PLACES, ["restaurant"], diet="halal", level="verified",
                          evidence=load_place_evidence(evidence))
    assert verified["diet_text"].tolist() == ["Halal-certified"]
    assert load_place_evidence(tmp_path / "none.csv") == {}


def test_review_fixes_style_no_and_stated() -> None:
    assert diet_evidence(pd.Series({"name": "Kosher-style Deli"})) == []           # kosher-style is not kosher
    assert diet_evidence(pd.Series({"name": "Halal Bros", "diet_halal": False})) == []   # OSM's no beats the name
    stated = {"tag": "halal", "source": "https://example.org/menu", "checked": "2026-11-16", "basis": "business"}
    assert diet_evidence(pd.Series({"name": "X"}), [stated])[0]["label"] == "Halal: stated by the business"


def test_review_fixes_eat_bakery_chains_and_empty_filters() -> None:
    table = load_specialty_ingredients()
    assert find_stores_for(["fish sauce"], None, PLACES, table)["eat"] == []        # no country: no restaurants
    bakery = pd.DataFrame([{**PLACES.iloc[0].to_dict(), "osm_id": "node/9", "name": "Fez Bakery", "category": "bakery"}])
    twice = pd.concat([PLACES, bakery, PLACES.iloc[[0]].assign(osm_id="node/10")], ignore_index=True)
    stores = [(s["name"], s["why"]) for s in find_stores_for(["harissa"], "Morocco", twice, table)["stores"]]
    assert ("Fez Bakery", "A Moroccan bakery (OpenStreetMap lists its cuisine as moroccan)") in stores
    assert [n for n, _ in stores].count("Casablanca Market") == 1                   # one row per name
    assert map_places(PLACES, [], cuisine="moroccan", diet="halal").empty           # nothing picked: no crash
