"""Knowledge assets read straight off the Food Graph, for features that do not exist yet (the waiter's chat in
0.8.0, Explore and World Tour, the map from a recipe). Every line and link comes from a graph edge with its
evidence; nothing is written by a model and nothing is guessed.

    python scripts/knowledge/graph_assets.py

Writes, in data/knowledge/:
- walter_context.json: per dish, the waiter's fixed-template lines (`WalterContextService`) and the names behind them;
- discovery_paths.json: per dish, the next dishes to try (`GraphRecommendationService.discovery_candidates`), each
  with its reason, relation and evidence, and where the dish sits (World > zone > ... > place);
- map_prep.json: per country, the OpenStreetMap cuisine tag the map looks for, how many of our dishes and recipes
  it has, and how many pilot-area places carry that tag (when the places table is present).
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

from everflavor.domain import (
    GraphRecommendationService,
    KnowledgeGraph,
    WalterContextService,
)
from everflavor.stores import COUNTRY_CUISINES
from everflavor.taxonomy import load_taxonomy

KNOW = ROOT / "data" / "knowledge"
DISCOVERY_LIMIT = 8


def save(name: str, data: object) -> None:
    (KNOW / name).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main() -> None:
    kg = KnowledgeGraph.load(ROOT)
    graph = kg.food_graph(load_taxonomy())
    walter, rec = WalterContextService(graph), GraphRecommendationService(graph)
    counts = json.loads((KNOW / "dish_recipe_counts.json").read_text(encoding="utf-8"))["dishes"]
    about = {"built_on": date.today().isoformat(), "by": "scripts/knowledge/graph_assets.py",
             "sources": "the Food Graph: data/knowledge/dishes.jsonl, dish_families.json (Wikidata, CC0), "
                        "data/reference/food_taxonomy.csv"}

    context, paths = {}, {}
    for q, dish in sorted(kg.dishes.items()):
        ctx = walter.context(q)
        if ctx is None or dish.kind != "dish":   # dishes only; foods and drinks have no family or variants
            continue
        context[q] = {"dish": ctx.dish, "lines": ctx.lines(), "kind_of": list(ctx.kind_of), "variants": list(ctx.variants),
                      "variants_not_in_everflavor": list(ctx.variants_not_in_everflavor), "related": list(ctx.related),
                      "countries": list(ctx.countries), "places": list(ctx.places),
                      "recipes": counts.get(q, {}).get("recipes", 0)}
        paths[q] = {"dish": dish.name,
                    "next": [{"qid": s.node.id.removeprefix("dish:"), "name": s.node.name, "reason": s.reason,
                              "relation": s.relation, "evidence": s.evidence}
                             for s in rec.discovery_candidates(q, DISCOVERY_LIMIT)]}
    with_lines = sum(bool(c["lines"]) for c in context.values())
    save("walter_context.json", {"about": about, "dishes_with_lines": with_lines, "dishes": context})
    save("discovery_paths.json", {"about": about, "limit": DISCOVERY_LIMIT,
                                  "dishes_with_a_next_dish": sum(bool(p["next"]) for p in paths.values()),
                                  "dishes": paths})

    places_file = ROOT / "data" / "processed" / "places.parquet"
    tags: Counter = Counter()
    if places_file.exists():
        places = pd.read_parquet(places_file)
        col = next((c for c in ("cuisines", "cuisine") if c in places.columns), None)
        if col:
            for v in places[col].dropna():
                values = str(v).replace(",", ";").split(";") if isinstance(v, str) else list(v)   # array or text
                for t in values:
                    tags[str(t).strip().lower()] += 1
    by_country: dict[str, dict] = {}
    for d in kg.dishes.values():
        if d.kind != "dish":
            continue
        for c in [n.name for n in graph.countries_of(d.dish_id)] or [d.country]:
            if c:
                e = by_country.setdefault(c, {"cuisine_tag": COUNTRY_CUISINES.get(c, ""), "dishes": 0, "recipes": 0})
                e["dishes"] += 1
                e["recipes"] += counts.get(d.dish_id, {}).get("recipes", 0)
    for c, e in by_country.items():
        e["pilot_places_with_tag"] = tags.get(e["cuisine_tag"], 0) if e["cuisine_tag"] and tags else None
    save("map_prep.json", {"about": {**about, "places": "data/processed/places.parquet (OpenStreetMap, ODbL), "
                                     "the Greater Houston pilot area" if tags else "not present when built"},
                           "countries": dict(sorted(by_country.items())),
                           # cuisine tags on pilot-area places that no country's cuisine word matches yet
                           "place_tags_without_a_country": {t: n for t, n in tags.most_common()
                                                            if t and t not in set(COUNTRY_CUISINES.values())}})
    no_tag = sorted(c for c, e in by_country.items() if not e["cuisine_tag"])
    print(f"walter context {len(context)} dishes ({with_lines} with lines); discovery {len(paths)}; "
          f"map prep {len(by_country)} countries ({len(no_tag)} without a cuisine tag)")


if __name__ == "__main__":
    main()
