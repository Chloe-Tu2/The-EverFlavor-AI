"""Every recipe as a node of the Food Graph, and what each one joins (the "all recipes in the graph" audit).

Each recipe is matched to its dish the way the app does it (`recipe_dish_links.fast_find`, equal to
`waiter.Knowledge.find`), then added with `FoodGraph.add_recipes`: `recipe_of` a dish, `named_for` a food or drink
entry, else `recipe_from` its place when the labels its source gave it name a place in the Food Taxonomy, else no
edge at all. Nothing is inferred.

    python scripts/knowledge/recipe_graph.py     # data/knowledge/recipe_graph_counts.json

Needs the processed recipe tables (notebook 01). Writes counts only, never recipe text.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.domain import KnowledgeGraph, Recipe
from everflavor.taxonomy import load_taxonomy

KNOW = ROOT / "data" / "knowledge"
OUT = KNOW / "recipe_graph_counts.json"
SPLITS = ("train", "val", "test")

sys.path.insert(0, str(Path(__file__).parent))
import recipe_dish_links as links


def text(value: object) -> str:
    return value if isinstance(value, str) and value != "Unknown" else ""


def main() -> None:
    kg = KnowledgeGraph.load(ROOT)
    taxonomy = load_taxonomy()
    graph = kg.food_graph(taxonomy)
    know = links.Knowledge.load(KNOW / "dishes.jsonl")
    longest = max(len(k.split()) for k in know.by_name)
    cols = ["recipe_id", "recipe_name", "source", "url", "dish_name", "origin_country", "origin_region"]
    df = pd.concat([pd.read_parquet(ROOT / "data" / "processed" / f"recipes_{s}.parquet", columns=cols)
                    for s in SPLITS], ignore_index=True)
    recipes = []
    for row in df.itertuples(index=False):
        entry, _ = links.fast_find(know, longest, str(row.dish_name), text(row.origin_country) or None)
        recipes.append(Recipe(str(row.recipe_id), str(row.recipe_name), str(row.source), str(row.url),
                              dish_id=str((entry or {}).get("qid") or ""), dish_name=str(row.dish_name),
                              origin_country=text(row.origin_country), origin_region=text(row.origin_region)))
    before = len(graph.nodes)
    graph.add_recipes(recipes, taxonomy)
    edges = {e.source: e for e in graph.edges if e.source.startswith("recipe:")}
    relation = Counter(edges[f"recipe:{r.recipe_id}"].relation if f"recipe:{r.recipe_id}" in edges else "none"
                       for r in recipes)
    by_source: dict[str, Counter] = {}
    for r in recipes:
        e = edges.get(f"recipe:{r.recipe_id}")
        by_source.setdefault(r.source, Counter())[e.relation if e else "none"] += 1
    place_only = Counter(graph.nodes[e.target].name for e in edges.values() if e.relation == "recipe_from")
    no_edge_country = Counter(r.origin_country or "(no country)" for r in recipes
                              if f"recipe:{r.recipe_id}" not in edges)
    out = {
        "about": "Every recipe as a Food Graph node and the one edge it gets (FoodGraph.add_recipes). Built by "
                 "scripts/knowledge/recipe_graph.py; counts only, no recipe text.",
        "built_on": date.today().isoformat(),
        "recipes": len(recipes), "recipe_nodes": len(graph.nodes) - before,
        "by_relation": dict(relation.most_common()),
        "by_source": {s: dict(c.most_common()) for s, c in sorted(by_source.items())},
        "recipe_from_by_place": dict(place_only.most_common()),
        "no_edge_by_country": dict(no_edge_country.most_common()),
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{out['recipe_nodes']:,} recipe nodes; {out['by_relation']}")


if __name__ == "__main__":
    main()
