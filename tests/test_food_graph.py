"""The Food Graph: World down to a recipe, every edge from a source, traversal that never guesses."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.domain import (
    FoodGraph,
    FoodNode,
    KnowledgeGraph,
    dish_from_record,
    recipe_from_row,
)
from everflavor.domain.food_graph import NODE_TYPES, RELATIONS, load_families
from everflavor.taxonomy import load_taxonomy

ROOT = Path(__file__).resolve().parents[1]
TAX = load_taxonomy()


def small_graph() -> FoodGraph:
    """Biryani (ours) with one variant we have and one we do not; a dumpling family; a Sichuan dish; a grouping."""
    dishes = {q: dish_from_record({"qid": q, "name": n, "country": c, "region": r, "origin": o})
              for q, n, c, r, o in [("Q1", "Biryani", "India", None, ["India"]),
                                    ("Q2", "Hyderabadi biryani", "India", None, None),
                                    ("Q3", "Jiaozi", "China", None, ["China"]),
                                    ("Q4", "Wonton", "China", None, None),
                                    ("Q5", "Mapo tofu", "China", "Sichuan", None),
                                    ("Q6", "Finger food", "Atlantis", None, None)]}
    families = [
        {"qid": "Q1", "name": "biryani", "kind": "family", "members": [
            {"qid": "Q2", "name": "Hyderabadi biryani", "in_everflavor": True},
            {"qid": "Q90", "name": "Sindhi biryani", "in_everflavor": False, "wikipedia": "https://en.wikipedia.org/wiki/Sindhi_biryani"}]},
        {"qid": "Q50", "name": "dumpling", "kind": "family", "members": [
            {"qid": "Q3", "name": "Jiaozi", "in_everflavor": True}, {"qid": "Q4", "name": "Wonton", "in_everflavor": True},
            {"qid": "Q91", "name": "Khinkali", "in_everflavor": False}]},
        {"qid": "Q6", "name": "finger food", "kind": "grouping", "members": [
            {"qid": "Q3", "name": "Jiaozi", "in_everflavor": True}, {"qid": "Q1", "name": "Biryani", "in_everflavor": True}]},
    ]
    return FoodGraph.build(dishes, TAX, families)


def test_nodes_and_edges_use_the_schema():
    g = small_graph()
    assert {n.node_type for n in g.nodes.values()} <= set(NODE_TYPES)
    assert {e.relation for e in g.edges} <= set(RELATIONS) and all(e.evidence for e in g.edges)
    sindhi = g.nodes["dish:Q90"]
    assert sindhi.node_type == "variant" and not sindhi.in_everflavor and sindhi.url.endswith("Sindhi_biryani")
    assert g.nodes["family:Q50"].node_type == "dish_family" and g.nodes["dish:Q91"].node_type == "dish"
    assert g.node("dish:nothing") is None
    with pytest.raises(ValueError):
        g.add_node(FoodNode("x", "x", "x", "planet"))


def test_variants_families_and_related_come_only_from_edges():
    g = small_graph()
    assert [n.name for n in g.variants_of("Q1")] == ["Hyderabadi biryani", "Sindhi biryani"]   # ours first
    assert [n.name for n in g.variants_of("Q1", everflavor_only=True)] == ["Hyderabadi biryani"]
    assert [n.name for n in g.variant_of("Q2")] == ["Biryani"]
    assert [n.name for n in g.families_of("Q3")] == ["dumpling"]   # the grouping is not a family
    assert len(g.families_of("Q3", kind=None)) == 2
    assert [n.name for n in g.related("Q3")] == ["Wonton"]
    assert [n.name for n in g.related("Q3", everflavor_only=False)] == ["Wonton", "Khinkali"]
    assert [n.name for n in g.related("Q2")] == ["Biryani"]
    assert g.related("Q5") == [] and g.families_of("Q5") == []   # no family edge: nothing related, no guess
    assert g.variants_of("Q6") == []   # a grouping that is also a dish gives no variants
    assert g.related("Q3", max_group=2) == []   # the dumpling family (3 members) is too broad at this limit


def test_places_countries_and_ancestors():
    g = small_graph()
    assert [n.name for n in g.places_of("Q5")] == ["Sichuan"]
    assert [n.name for n in g.countries_of("Q5")] == ["China"]
    places = [n.name for n in g.ancestors("dish:Q5", ("origin", "eaten_in", "part_of"))]
    assert places[:3] == ["Sichuan", "China", "East Asia"] and places[-1] == "World"
    assert g.places_of("Q6") == []   # Atlantis is not in the taxonomy: no place edge, not a wrong one
    assert {n.name for n in g.siblings("place:cn_sichuan")} >= {"Hunan", "Guangdong"}
    assert "dish:Q5" in {n.id for n in g.children("place:cn_sichuan")}
    path = g.path("Q3")
    assert [n.name for n in path["families"]] == ["dumpling"] and [n.name for n in path["countries"]] == ["China"]


def test_recipes_join_their_dish():
    g = small_graph()
    linked = recipe_from_row({"url": "https://example.org/r/9", "recipe_name": "Pork Jiaozi", "ingredient_lines": "[]"})
    from dataclasses import replace
    assert g.add_recipes([replace(linked, dish_id="Q3"), recipe_from_row({"url": "https://e.org/2",
                                                                          "recipe_name": "Mystery"})]) == 1
    assert [n.name for n in g.recipes_of("Q3")] == ["Pork Jiaozi"]
    assert g.ancestors("recipe:https://example.org/r/9", ("recipe_of", "in_family"))[1].name == "dumpling"


def test_the_real_graph_links_dishes_to_families_and_places():
    """The committed tables: the family file is beside dishes.jsonl, and the graph reads it."""
    assert load_families(ROOT / "data" / "knowledge" / "dish_families.json")
    kg = KnowledgeGraph.load(ROOT)
    g = kg.food_graph(TAX)
    assert g is kg.food_graph(TAX)   # built once
    counts = g.counts()
    assert counts["dish_family"] >= 100 and counts["variant"] >= 1000 and counts["edge:in_family"] >= 2000
    biryani = next(d.dish_id for d in kg.dishes.values() if d.name == "Biryani")
    assert "Sindhi biryani" in {n.name for n in g.variants_of(biryani)}
    assert [n.name for n in g.countries_of(biryani)] == ["India"]
