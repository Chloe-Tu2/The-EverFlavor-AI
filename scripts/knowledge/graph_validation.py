"""Food Graph validation: orphan nodes, places that do not reach World, cycles in families and versions, family
links the graph had to drop, and dishes with more than one valid place (for a person, never settled here).
Nothing is changed.

    python scripts/knowledge/graph_validation.py

Writes docs/audits/food_graph_validation_report.md and data/knowledge/quality/food_graph_validation.json.
"""
from __future__ import annotations

import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from quality_reports import save_json, save_md, table

from everflavor.domain import KnowledgeGraph
from everflavor.domain.food_graph import FoodGraph
from everflavor.taxonomy import Taxonomy, load_taxonomy

TODAY = date.today().isoformat()
PLACE_EDGES = {"origin", "eaten_in"}


def place_problems(graph: FoodGraph, taxonomy: Taxonomy) -> dict[str, list[str]]:
    """Places that do not reach World by `part_of`, and part_of cycles."""
    world = {f"place:{n.slug}" for n in taxonomy.nodes.values() if n.level == "world"}
    lost, cycles = [], []
    for nid in graph.nodes:
        if not nid.startswith("place:"):
            continue
        seen, todo, ok = {nid}, [nid], nid in world
        while todo and not ok:
            for e in graph._up.get(todo.pop(), []):
                if e.relation != "part_of":
                    continue
                if e.target in world:
                    ok = True
                elif e.target == nid:
                    cycles.append(nid)
                elif e.target not in seen:
                    seen.add(e.target)
                    todo.append(e.target)
        if not ok:
            lost.append(nid)
    return {"not_reaching_world": sorted(lost), "part_of_cycles": sorted(set(cycles))}


def cycles(graph: FoodGraph, relations: set[str]) -> list[str]:
    """Nodes that reach themselves through `relations` (a family inside itself)."""
    out = []
    for nid in graph.nodes:
        seen, todo = set(), [nid]
        while todo:
            for e in graph._up.get(todo.pop(), []):
                if e.relation not in relations:
                    continue
                if e.target == nid:
                    out.append(nid)
                    todo = []
                    break
                if e.target not in seen:
                    seen.add(e.target)
                    todo.append(e.target)
    return sorted(set(out))


def validate(kg: KnowledgeGraph, taxonomy: Taxonomy) -> dict:
    graph = kg.food_graph(taxonomy)
    ours = {nid: n for nid, n in graph.nodes.items() if n.node_type == "dish" and n.in_everflavor}
    no_edge = sorted(nid for nid in ours if graph.degree(nid) == 0)
    no_place = sorted(nid for nid in ours if not any(e.relation in PLACE_EDGES for e in graph._up.get(nid, [])))
    country_missing = Counter(d.country for d in kg.dishes.values() if d.country and not taxonomy.node_for(d.country))
    origin_missing = Counter(c for d in kg.dishes.values() for c in d.origin if not taxonomy.node_for(c))
    # Family members the graph could not attach: the member is a list article, or the edge would point to itself
    families = list(kg.families.values())
    empty = sorted(f"family:{f['qid']}" for f in families
                   if f"family:{f['qid']}" in graph.nodes and not graph._down.get(f"family:{f['qid']}"))
    # More than one valid place: Wikidata gives several countries of origin, or the origin is not where its
    # cuisine list puts it. Both can be right; a person decides what the page shows first.
    multi_origin = sorted(d.dish_id for d in kg.dishes.values() if len(set(d.origin)) > 1)
    elsewhere = sorted(d.dish_id for d in kg.dishes.values()
                       if d.origin and d.country and d.country not in d.origin)
    return {
        "counts": graph.counts(), "dishes": len(ours),
        **place_problems(graph, taxonomy),
        "family_cycles": cycles(graph, {"in_family", "variant_of"}),
        "dishes_without_edges": no_edge, "dishes_without_a_place": no_place,
        "countries_not_in_place_tree": dict(country_missing.most_common()),
        "origins_not_in_place_tree": dict(origin_missing.most_common()),
        "families_without_members": empty,
        "dishes_with_several_origins": multi_origin,
        "dishes_listed_outside_their_origin": elsewhere,
    }


def main() -> None:
    kg = KnowledgeGraph.load(ROOT)
    taxonomy = load_taxonomy()
    res = validate(kg, taxonomy)
    save_json("food_graph_validation.json", {"by": "scripts/knowledge/graph_validation.py",
                                             "sources": "data/knowledge/dishes.jsonl, dish_families.json, "
                                                        "data/reference/food_taxonomy.csv", **res})
    name = {d: kg.dishes[d.split(":", 1)[1]].name for d in res["dishes_without_a_place"]
            if d.split(":", 1)[1] in kg.dishes}
    c = res["counts"]
    errors = [("places that do not reach World", res["not_reaching_world"]),
              ("cycles in the place tree", res["part_of_cycles"]),
              ("cycles in families or versions", res["family_cycles"]),
              ("our dishes with no edge at all", res["dishes_without_edges"])]
    lines = [f"# Food Graph validation ({TODAY})", "",
             ("`scripts/knowledge/graph_validation.py` built the Food Graph as the app does (dishes, families, "
              "versions and the place tree; recipes are counted in `data/knowledge/recipe_graph_counts.json`) and "
              "checked its links. **Nothing was changed.**"), "",
             (f"Nodes: {c.get('dish', 0):,} dishes ({res['dishes']:,} ours, foods and drinks included),{c.get('variant', 0):,} versions, "
              f"{c.get('dish_family', 0):,} families, and the places. Edges: "
              + ", ".join(f"{k.split(':')[1]} {v:,}" for k, v in sorted(c.items()) if k.startswith("edge:")) + "."),
             "", "## Broken links (should be zero)", ""]
    lines += table(["Check", "Found"], [[k, len(v)] for k, v in errors])
    for k, v in errors:
        if v:
            lines += ["", f"{k[0].upper() + k[1:]}: " + ", ".join(f"`{x}`" for x in v[:30])]
    lines += ["", "## Gaps (not errors: the source has no link yet)", ""]
    lines += table(["Gap", "Found"], [
        ["our dishes with no place edge (no origin and no cuisine-list place in the tree)",
         len(res["dishes_without_a_place"])],
        ["cuisine-list countries not in the place tree", len(res["countries_not_in_place_tree"])],
        ["Wikidata origins not in the place tree", len(res["origins_not_in_place_tree"])],
        ["family groups with no member left (members were list articles)", len(res["families_without_members"])]])
    if name:
        lines += ["", "Dishes with no place: " + ", ".join(sorted(name.values())[:40])
                  + ("..." if len(name) > 40 else "") + "."]
    if res["countries_not_in_place_tree"]:
        lines += ["", "Cuisine-list countries not in the tree: " + ", ".join(
            f"{k} ({v})" for k, v in res["countries_not_in_place_tree"].items()) + "."]
    if res["origins_not_in_place_tree"]:
        lines += ["", "Wikidata origins not in the tree (20 most used): " + ", ".join(
            f"{k} ({v})" for k, v in list(res["origins_not_in_place_tree"].items())[:20]) + "."]
    lines += ["", "## More than one valid place (for a person)", "",
              ("Both kinds can be right, so nothing is settled here: the dish keeps every place its sources give. "
               "They are listed in `data/knowledge/quality/food_graph_validation.json` and counted in "
               "`docs/governance/needs_human_review.md`."), ""]
    lines += table(["Case", "Dishes"], [
        ["Wikidata gives more than one country of origin", len(res["dishes_with_several_origins"])],
        ["the cuisine list puts it in a country that is not its origin",
         len(res["dishes_listed_outside_their_origin"])]])
    save_md("food_graph_validation_report.md", lines)
    print("graph:", {k: len(v) if isinstance(v, (list, dict)) else v for k, v in res.items() if k != "counts"})


if __name__ == "__main__":
    main()
