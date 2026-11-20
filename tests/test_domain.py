"""The domain entities (roadmap phase 1): built from today's tables, linked by id, nothing invented."""
import json
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.confidence import Confidence
from everflavor.domain import (
    KnowledgeGraph,
    dish_from_record,
    dish_id_for,
    ingredient_id_for,
    load_pronunciations,
    place_from_row,
    recipe_from_row,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def graph() -> KnowledgeGraph:
    return KnowledgeGraph.load(ROOT)


def recipe_row(**changes):
    row = {"url": "https://example.org/r/1", "recipe_name": "Easy Beef Tacos - Ww Friendly", "source": "Example",
           "ingredient_lines": '["1 lb ground beef", "8 corn tortillas", "1 1/2 cups plain flour, sifted"]',
           "servings": 4.0, "calories_per_serving": float("nan"), "protein_g": 20.5, "origin_country": "Unknown",
           "origin_region": None, "image_url": "https://example.org/p.jpg"}
    return {**row, **changes}


def test_dish_ids_are_the_qid_or_a_country_slug():
    assert dish_id_for("Q191655", "Taco", "Mexico") == "Q191655"
    assert dish_id_for(None, "Chiles en Nogada", "Mexico") == "mexico-chiles-en-nogada"
    assert dish_id_for("not a qid", "Grandma's Casserole") == "grandma-s-casserole"
    with pytest.raises(ValueError):
        dish_id_for("", "  ")


def test_a_dish_keeps_its_sourced_facts_and_links_ingredients_by_id():
    record = {"qid": "Q1", "name": "Test dish", "kind": "dish", "country": "Peru", "region": None,
              "made_from": ["Plain Flour", "http://www.wikidata.org/x", "butter"],
              "fun_facts": [{"text": "A fact.", "topic": "origin", "source": "Wikipedia: Test"}],
              "sources": [{"name": "Wikidata", "url": "https://www.wikidata.org/wiki/Q1", "licence": "CC0"}],
              "learn_more": [{"level": "quick", "title": "T", "url": "https://en.wikipedia.org/wiki/T"}]}
    dish = dish_from_record(record)
    assert dish.dish_id == "Q1" and dish.region == "" and dish.made_from == ("flour", "butter")
    assert dish.facts[0].text == "A fact." and dish.sources[0].licence == "CC0" and dish.learn_more[0].level == "quick"
    assert dish_from_record({"qid": "Q2", "name": "Bare"}).facts == ()   # a raw entry: nothing is made up
    with pytest.raises(FrozenInstanceError):
        dish.name = "Other"   # type: ignore[misc]


def test_a_recipe_owns_its_lines_and_amounts_but_no_flags():
    recipe = recipe_from_row(recipe_row())
    assert recipe.recipe_id == recipe.url and recipe.dish_name.lower() == "beef tacos"
    flour = recipe.lines[2]
    assert (flour.amount, flour.unit, flour.ingredient_id) == (1.5, "cup", "flour")
    assert recipe.ingredient_ids == ("ground beef", "corn tortilla", "flour")
    assert recipe.origin_country == "" and recipe.nutrition.calories is None and recipe.nutrition.protein_g == 20.5
    assert not hasattr(recipe, "flags") and recipe.dish_id == ""
    with pytest.raises(ValueError):
        recipe_from_row(recipe_row(url=""))


def test_the_graph_links_a_recipe_to_its_dish_as_the_app_does(graph):
    recipe = graph.link_dish(recipe_from_row(recipe_row()))
    dish = graph.get_dish(recipe.dish_id)
    assert dish is not None and dish.name == "Taco" and dish.pronunciation and dish.pronunciation.lang == "es"
    assert graph.where_from(recipe)[0] == "Mexico"   # Wikidata's origin, not the cuisine list (United States)
    unknown = graph.link_dish(recipe_from_row(recipe_row(recipe_name="Zzq Mystery Bake", origin_country="Peru")))
    assert unknown.dish_id == "" and graph.where_from(unknown) == ("Peru", "")


def test_ingredients_carry_their_risks_with_confidence(graph):
    teriyaki = graph.ingredient("teriyaki sauce")
    by_flag = {r.flag: r for r in teriyaki.risks}
    assert by_flag["contains_soy"].confidence is Confidence.VERIFIED
    assert by_flag["contains_alcohol"].confidence is Confidence.LIKELY
    assert by_flag["contains_alcohol"].source.startswith("https://") and "teriyaki glaze" in teriyaki.aliases
    assert graph.ingredient("harissa").specialty is not None and graph.ingredient("water").risks == ()
    assert [i.ingredient_id for i in graph.ingredients_of(recipe_from_row(recipe_row()))][-1] == "flour"
    assert ingredient_id_for("2 teaspoons Peanut Butter") == "peanut butter"


def test_places_keep_their_claims_and_evidence():
    place = place_from_row({"osm_id": "node/1", "name": "Halal Corner Market", "lat": 29.7, "lng": -95.3,
                            "category": "grocery", "cuisine": None, "diet_halal": None})
    assert place.claims[0].tag == "halal" and place.claims[0].level == "likely"
    assert "name" in place.claims[0].reason
    with pytest.raises(ValueError):
        place_from_row({"osm_id": "node/2", "lat": None, "lng": 1.0})


def test_dish_families_give_related_dishes(tmp_path):
    """Notebook 15's families: a dish's families, and related dishes EverFlavor has, closest family first."""
    dishes = {q: dish_from_record({"qid": q, "name": n}) for q, n in
              [("Q1", "Dumpling"), ("Q2", "Jiaozi"), ("Q3", "Wonton"), ("Q4", "Biryani"), ("Q5", "Momo")]}
    families = {"families": [
        {"qid": "Q1", "name": "dumpling", "kind": "family", "members": [
            {"qid": "Q2", "in_everflavor": True}, {"qid": "Q3", "in_everflavor": True},
            {"qid": "Q5", "in_everflavor": True}, {"qid": "Q99", "in_everflavor": False}]},
        {"qid": "Q7", "name": "Chinese dumpling", "kind": "family", "members": [
            {"qid": "Q2", "in_everflavor": True}, {"qid": "Q3", "in_everflavor": True}]},
        {"qid": "Q8", "name": "pork dish", "kind": "category", "members": [{"qid": "Q2", "in_everflavor": True}]}],
        "dish_families": {"Q2": ["Q1", "Q7", "Q8", "Q404"], "Q3": ["Q1", "Q7"]}}
    path = tmp_path / "dish_families.json"
    path.write_text(json.dumps(families), encoding="utf-8")
    graph = KnowledgeGraph(dishes=dishes)
    graph.load_families(path)
    assert [f["name"] for f in graph.families_of("Q2")] == ["dumpling", "Chinese dumpling"]
    assert len(graph.families_of("Q2", kind=None)) == 3
    assert [d.name for d in graph.related("Q2")] == ["Wonton", "Dumpling", "Momo"]   # closest family first
    assert graph.related("Q4") == [] and graph.families_of("Q4") == []
    empty = KnowledgeGraph(dishes={})
    empty.load_families(tmp_path / "missing.json")   # no file: no families, no error
    assert empty.families == {}


def test_every_table_loads_into_entities(graph):
    """All of the notebook's dishes become Dishes with unique ids; every demo recipe and place loads."""
    assert len(graph.dishes) >= 4000 and all(d.dish_id.startswith("Q") for d in graph.dishes.values())
    spoken = load_pronunciations()
    assert sum(1 for q in spoken if graph.dishes.get(q, None) and graph.dishes[q].pronunciation) >= len(spoken) // 2
    recipes = pd.read_parquet(ROOT / "data" / "demo" / "recipes_test.parquet")
    loaded = [recipe_from_row(r) for r in recipes.to_dict("records")]
    assert len({r.recipe_id for r in loaded}) == len(recipes)
    places = pd.read_parquet(ROOT / "data" / "demo" / "places.parquet").head(300)
    assert len(KnowledgeGraph(dishes={}, places={p.place_id: p for p in
                                                 (place_from_row(r) for r in places.to_dict("records"))}).places) == 300
