"""Which recipes the app links to a dish, and how many recipes each dish has (the recipe -> dish linking audit).

Every recipe is matched the way the app matches it (`waiter.Knowledge.find` on the recipe name, the recipe's
country breaking ties). `find` checks every known name against each title, too slow for 290,000 recipes, so this
script uses an equal, faster version (all word runs of the title looked up at once) and first checks that both
give the same dish on 3,000 random recipes.

    python scripts/knowledge/recipe_dish_links.py     # data/knowledge/dish_recipe_counts.json

Needs the processed recipe tables (notebook 01). Writes only counts and dish ids, never recipe text.
"""
from __future__ import annotations

import json
import random
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.waiter import GENERIC, Knowledge, _norm

SPLITS = ("train", "val", "test")
OUT = ROOT / "data" / "knowledge" / "dish_recipe_counts.json"


def fast_find(know: Knowledge, longest: int, dish_name: str, country: str | None) -> tuple[dict | None, str]:
    """`Knowledge.find`, by looking up each run of words of the title (same rules, same tie-break)."""
    by_name = know.by_name
    name = _norm(dish_name)
    if name in by_name:
        return by_name[name], "exact"
    name = re.split(r" (with|on|in|over|served|topped) ", name)[0]
    if name in by_name:
        return by_name[name], "head"
    tokens = name.split()
    hits = set()
    for n in range(1, min(longest, len(tokens)) + 1):
        for i in range(len(tokens) - n + 1):
            k = " ".join(tokens[i:i + n])
            if (k in by_name and len(k) >= 4 and k not in GENERIC and by_name[k].get("kind") == "dish"
                    and (n > 1 or i + n == len(tokens))):
                hits.add(k)
    if not hits:
        return None, "none"
    # ties keep the order of the name index, as find's stable sort does
    order = {k: i for i, k in enumerate(by_name) if k in hits}
    best = max(hits, key=lambda k: (len(k), by_name[k].get("country") == country, -order[k]))
    return by_name[best], "inside"


def main() -> None:
    know = Knowledge.load(ROOT / "data" / "knowledge" / "dishes.jsonl")
    longest = max(len(k.split()) for k in know.by_name)
    cols = ["recipe_id", "source", "recipe_name", "origin_country"]
    df = pd.concat([pd.read_parquet(ROOT / "data" / "processed" / f"recipes_{s}.parquet", columns=cols) for s in SPLITS],
                   ignore_index=True)

    def country(c: object) -> str | None:
        return c if isinstance(c, str) and c != "Unknown" else None

    for i in random.Random(0).sample(range(len(df)), 3000):
        a = know.find(df.recipe_name[i], country(df.origin_country[i]))
        b, _ = fast_find(know, longest, df.recipe_name[i], country(df.origin_country[i]))
        if (a or {}).get("qid") != (b or {}).get("qid"):
            raise SystemExit(f"the fast match differs from Knowledge.find on {df.recipe_name[i]!r}")

    found = [fast_find(know, longest, str(n), country(c)) for n, c in zip(df.recipe_name, df.origin_country)]
    df["qid"] = [str(e.get("qid") or "") if e else "" for e, _ in found]
    df["match"] = [how for _, how in found]
    entries = {str(d.get("qid")): d for d in know.dishes if d.get("qid")}
    linked = df[df.qid != ""]
    dishes = {}
    for q, g in linked.groupby("qid"):
        e = entries.get(q, {})
        dishes[q] = {"name": e.get("name", ""), "country": e.get("country") or "", "kind": e.get("kind", ""),
                     "recipes": len(g), "by_source": {s: int(n) for s, n in g.source.value_counts().items()},
                     "by_match": {m: int(n) for m, n in g.match.value_counts().items()}}
    without = sorted(q for q, e in entries.items() if e.get("kind") == "dish" and q not in dishes)
    out = {
        "about": "Recipes per dish, as the app links them (waiter.Knowledge.find on the recipe name). Built by "
                 "scripts/knowledge/recipe_dish_links.py; counts only, no recipe text.",
        "built_on": date.today().isoformat(),
        "recipes": len(df), "linked": len(linked),
        "by_match": {m: int(n) for m, n in df.match.value_counts().items()},
        "by_source": {s: {"recipes": len(g), "linked": int((g.qid != "").sum())} for s, g in df.groupby("source")},
        "dishes": dict(sorted(dishes.items())),
        "dishes_without_recipes": without,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{out['linked']:,} of {out['recipes']:,} recipes linked to {len(dishes):,} entries; "
          f"{len(without):,} dishes without a recipe; by match {out['by_match']}")


if __name__ == "__main__":
    main()
