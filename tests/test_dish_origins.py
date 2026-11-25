"""The multi-origin dish policy (docs/governance/multi_origin_dish_policy.md): which countries a dish counts for."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "knowledge"))

import dish_origins


def dish(country: str, origin: list[str], qid: str = "Q1") -> dict:
    return {"qid": qid, "name": "test dish", "kind": "dish", "country": country, "origin": origin}


def test_listing_country_comes_first_then_wikidata_origins() -> None:
    assert dish_origins.countries_of(dish("Ethiopia", ["Ethiopia", "Eritrea"])) == ["Ethiopia", "Eritrea"]


def test_only_place_tree_countries_count_never_regions_or_old_states() -> None:
    d = dish("Turkey", ["Ottoman Empire", "Levant", "Scotland", "Korea", "Hong Kong"])
    assert dish_origins.countries_of(d) == ["Turkey"]


def test_label_aliases_name_the_same_country_once() -> None:
    assert dish_origins.countries_of(dish("Taiwan", ["People's Republic of China", "China"])) == ["Taiwan", "China"]


def test_a_person_can_drop_an_added_country(monkeypatch) -> None:
    monkeypatch.setattr(dish_origins, "dropped", lambda: frozenset({("Q9", "Eritrea")}))
    assert dish_origins.countries_of(dish("Ethiopia", ["Eritrea"], qid="Q9")) == ["Ethiopia"]


def test_a_dish_without_a_country_still_counts_for_its_origins() -> None:
    assert dish_origins.countries_of(dish("", ["Jordan"])) == ["Jordan"]
