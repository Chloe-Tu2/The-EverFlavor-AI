"""Give the live site's demo data what the map, Explore by place and the nutrition estimate need.

The live site (Streamlit Cloud) has only what is in git: `data/demo/`. This script adds, from the full data on a
computer that ran the notebooks:

1. `origin_country` and `origin_region` on the 3,000 demo recipes (Hugging Face rows, matched by name to the same
   rows in `data/processed`; no match: "Unknown"), so Explore by place works;
2. `places.parquet`: notebook 03's OpenStreetMap places for the map (ODbL: credited on the map);
3. `usda_ingredient_nutrition.csv` (the columns the estimate reads) and `usda_portions.json` (household weights
   from the USDA SR Legacy files, public domain), so Check my recipe can estimate nutrition.

Run from the project folder: `python scripts/demo_extras.py`. It only adds files and columns; nothing else in the
demo data changes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DEMO, FULL = ROOT / "data" / "demo", ROOT / "data" / "processed"
SPLITS = ("train", "val", "test")
USDA_COLUMNS = ["ingredient", "fdc_id", "kcal_100g", "carbs_100g", "protein_100g", "sodium_mg_100g"]


def add_origins() -> None:
    full = pd.concat([pd.read_parquet(FULL / f"recipes_{s}.parquet",
                                      columns=["source", "recipe_name", "origin_country", "origin_region"])
                      for s in SPLITS])
    hf = full[full["source"] == "huggingface"].drop_duplicates("recipe_name")
    origin = hf.set_index("recipe_name")[["origin_country", "origin_region"]]
    for split in SPLITS:
        path = DEMO / f"recipes_{split}.parquet"
        demo = pd.read_parquet(path).drop(columns=["origin_country", "origin_region"], errors="ignore")
        demo["origin_country"] = demo["recipe_name"].map(origin["origin_country"]).fillna("Unknown")
        demo["origin_region"] = demo["recipe_name"].map(origin["origin_region"])
        demo.to_parquet(path, index=False)
        print(f"{path.name}: {int((demo['origin_country'] != 'Unknown').sum())} of {len(demo)} with a country")


def add_places() -> None:
    places = pd.read_parquet(FULL / "places.parquet")
    places.to_parquet(DEMO / "places.parquet", index=False)
    print(f"places.parquet: {len(places):,} places")


def add_usda() -> None:
    from everflavor.calories import usda_portions
    table = pd.read_csv(FULL / "usda_ingredient_nutrition.csv")
    table = table.dropna(subset=["fdc_id", "kcal_100g"])[USDA_COLUMNS]
    table.to_csv(DEMO / "usda_ingredient_nutrition.csv", index=False)
    portions = usda_portions(ROOT / "data" / "raw" / "usda_fdc")
    used = set(table["fdc_id"].astype(int))
    kept = {str(fdc): weights for fdc, weights in portions.items() if fdc in used}
    (DEMO / "usda_portions.json").write_text(json.dumps(kept, separators=(",", ":")), encoding="utf-8")
    print(f"usda: {len(table):,} ingredients, household weights for {len(kept):,} foods")


if __name__ == "__main__":
    add_origins()
    add_places()
    add_usda()
