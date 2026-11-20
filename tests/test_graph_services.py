"""Services on the Food Graph: suggestions with their reasons, the waiter's context, cookbook groups, map links.
Every answer must come from an edge; a dish without edges gets nothing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.domain import (
    CookbookGrouping,
    FoodGraph,
    GraphRecommendationService,
    Ingredient,
    MapLinks,
    Place,
    Specialty,
    WalterContextService,
    dish_from_record,
)
from everflavor.taxonomy import load_taxonomy

TAX = load_taxonomy()


def graph() -> FoodGraph:
    rows = [("Q1", "Biryani", "India", None, ["India"], "dish"), ("Q2", "Hyderabadi biryani", "India", None, None, "dish"),
            ("Q3", "Chapati", "India", None, ["India"], "dish"), ("Q4", "Roti", "India", None, None, "dish"),
            ("Q5", "Mapo tofu", "China", "Sichuan", None, "dish"), ("Q6", "Kung Pao chicken", "China", "Sichuan", None, "dish"),
            ("Q7", "Char siu", "China", "Guangdong", None, "dish"), ("Q8", "Black tea", "China", None, None, "food or drink"),
            ("Q9", "Sandwich", "China", None, ["United Kingdom"], "dish"), ("Q10", "Chapli kebab", "Pakistan", None, None, "dish")]
    dishes = {q: dish_from_record({"qid": q, "name": n, "country": c, "region": r, "origin": o, "kind": k})
              for q, n, c, r, o, k in rows}
    families = [
        {"qid": "Q1", "name": "biryani", "kind": "family", "members": [
            {"qid": "Q2", "name": "Hyderabadi biryani", "in_everflavor": True},
            {"qid": "Q90", "name": "Sindhi biryani", "in_everflavor": False}]},
        {"qid": "Q50", "name": "flatbread", "kind": "family", "members": [
            {"qid": "Q3", "name": "Chapati", "in_everflavor": True}, {"qid": "Q4", "name": "Roti", "in_everflavor": True}]},
    ]
    return FoodGraph.build(dishes, TAX, families)


def test_related_dishes_and_variants_say_why():
    rec = GraphRecommendationService(graph())
    assert [(s.node.name, s.reason) for s in rec.related_dishes("Q3")] == [("Roti", "same family: flatbread")]
    assert [(s.node.name, s.reason) for s in rec.related_dishes("Q2")] == [("Biryani", "the dish this is a version of")]
    assert [s.node.name for s in rec.related_variants("Q1")] == ["Hyderabadi biryani", "Sindhi biryani"]
    assert [(s.node.name, s.reason) for s in rec.related_variants("Q2")] == [("Sindhi biryani",
                                                                             "another version of Biryani")]
    assert rec.family_members("Q3") == {"flatbread": [rec.graph.nodes["dish:Q4"]]}
    assert rec.related_dishes("Q5") == [] and rec.related_variants("Q5") == []   # no family edge: nothing
    assert all(s.evidence for s in rec.discovery_candidates("Q3"))


def test_place_neighbours_use_origin_and_only_dishes():
    rec = GraphRecommendationService(graph())
    from_china = [s.node.name for s in rec.country_neighbors("Q5")]
    assert "Kung Pao chicken" in from_china and "Char siu" in from_china
    assert "Black tea" not in from_china          # a drink on the cuisine list, not a dish
    assert "Sandwich" not in from_china           # Wikidata says it is from the United Kingdom: eaten here, not from here
    assert [s.node.name for s in rec.cuisine_neighbors("Q5")] == ["Kung Pao chicken"]
    nearby = rec.region_neighbors("Q5")
    assert nearby and nearby[0].node.name == "Char siu" and nearby[0].reason == "from Guangdong, next to Sichuan"
    assert "Chapli kebab" in {s.node.name for s in rec.discover_region_neighbors("Q3")}
    groups = rec.dishes_at("place:cn_sichuan")
    assert sum(len(v) for v in groups.values()) == 2 and set(groups) == {"Other"}


def test_walter_context_only_repeats_the_graph():
    walter = WalterContextService(graph())
    ctx = walter.context("Q3")
    assert ctx is not None and ctx.kind_of == ("flatbread",) and ctx.related == ("Roti",) and ctx.countries == ("India",)
    assert ctx.lines() == ["Chapati is a kind of flatbread.", "If you enjoy Chapati, you may also like Roti.",
                           "It is from India."]
    biryani = walter.context("Q1")
    assert biryani is not None and biryani.variants == ("Hyderabadi biryani",)
    assert biryani.variants_not_in_everflavor == ("Sindhi biryani",)
    assert walter.context("Q404") is None
    assert walter.context("Q5").lines() == ["It is from Sichuan."]   # type: ignore[union-attr]


def test_cookbook_groups_and_map_links():
    g = graph()
    book = CookbookGrouping(g)
    assert book.by_family(["Q3", "Q4", "Q2", "Q5"]) == {"flatbread": ["Q3", "Q4"], "Biryani": ["Q2"], "Other": ["Q5"]}
    assert list(book.by_country(["Q3", "Q5", "Q7"])) == ["China", "India"]
    places = [Place("node/1", "Taj", 29.7, -95.3, "restaurant", ("indian",)),
              Place("node/2", "Spice Hub", 29.7, -95.3, "spices", ("moroccan",)),
              Place("node/3", "Corner Shop", 29.7, -95.3, "grocery", ()),
              Place("node/4", "Burger Bar", 29.7, -95.3, "restaurant", ("burger",))]
    links = MapLinks(g, places)
    assert [p.name for p in links.places_for_dish("Q1")] == ["Taj"]
    assert links.places_for_dish("Q404") == []
    harissa = Ingredient("harissa", "harissa", specialty=Specialty("a chili paste", ("moroccan",), ("grocery", "spices"),
                                                                   "https://en.wikipedia.org/wiki/Harissa", "CC BY-SA 4.0"))
    assert [p.name for p in links.places_for_ingredient(harissa)] == ["Spice Hub", "Corner Shop"]   # cuisine match first
    assert links.places_for_ingredient(Ingredient("water", "water")) == []
    assert [p.name for p in links.regional_food_locations("place:south_asia")] == ["Taj"]
    assert {n.name for n in links.related_places("place:cn_sichuan")} >= {"Guangdong"}


def test_variants_get_their_own_wikidata_country_and_map_places():
    """A version we do not have keeps the country Wikidata gives it (never its parent dish's)."""
    dishes = {"Q1": dish_from_record({"qid": "Q1", "name": "Biryani", "country": "India", "origin": ["India"]})}
    families = [{"qid": "Q1", "name": "biryani", "kind": "family", "members": [
        {"qid": "Q90", "name": "Sindhi biryani", "country": "Pakistan", "in_everflavor": False},
        {"qid": "Q91", "name": "Mystery biryani", "country": "", "in_everflavor": False}]}]
    g = FoodGraph.build(dishes, TAX, families)
    assert [n.name for n in g.countries_of("Q90")] == ["Pakistan"] and g.countries_of("Q91") == []
    links = MapLinks(g, [Place("node/1", "Karachi Grill", 29.7, -95.3, "restaurant", ("pakistani",)),
                         Place("node/2", "Taj", 29.7, -95.3, "restaurant", ("indian",))])
    assert [p.name for p in links.places_for_variant("Q90")] == ["Karachi Grill"]
    assert links.places_for_variant("Q91") == []          # unknown country: no places, not India's
    assert [p.name for p in links.places_for_country("India")] == ["Taj"]
    rec = GraphRecommendationService(g)
    assert rec.graph_path("Q90")["countries"][0].name == "Pakistan"
    assert [s.node.name for s in rec.explore_variant("Q1")] == ["Mystery biryani", "Sindhi biryani"]


def test_a_dish_leads_to_its_wikidata_ingredients():
    from everflavor.domain import KnowledgeGraph
    kg = KnowledgeGraph(dishes={"Q1": dish_from_record({"qid": "Q1", "name": "Gazpacho",
                                                        "made_from": ["tomato", "olive oil", "bread"]})})
    links = MapLinks(FoodGraph.build(kg.dishes), [])
    assert [i.ingredient_id for i in links.ingredients_for_dish(kg, "Q1")] == ["tomato", "olive oil", "bread"]
    assert links.ingredients_for_dish(kg, "Q404") == []
