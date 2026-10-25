"""Two small tables next to the recipe data, for the app, until notebook 01 makes them itself:

- data/processed/recipe_times.parquet: recipe_id, minutes_estimate, minutes_source, from cooking_time.py (fitted
  on the train split's Food.com recipes; real times are never replaced).
- data/processed/recipe_photos.parquet: recipe_id, image_url, photo_ok, from the downloaded photos'
  manifest (data/raw/recipe_photos/manifest.csv, docs/plans/RECIPE_PHOTOS.md): photo_ok is False for pictures
  shared by 3 or more recipes (site logos such as Food Network's, found by image hash) and for tiny files.

    python scripts/recipe_extras.py [times] [photos]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import cast

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.cooking_time import estimate_minutes, fit_time_model

PROCESSED = ROOT / "data" / "processed"
MANIFEST = ROOT / "data" / "raw" / "recipe_photos" / "manifest.csv"
SHARED = 3              # a picture used by this many recipes or more is a logo or placeholder
TINY_BYTES = 5_000      # smaller files are icons, not photos


def recipes() -> pd.DataFrame:
    return pd.concat([pd.read_parquet(PROCESSED / f"recipes_{split}.parquet") for split in ("train", "val", "test")],
                     ignore_index=True)


def times() -> None:
    df = recipes()
    start = time.time()
    model = fit_time_model(cast(pd.DataFrame, df[df["split"] == "train"]))
    out = estimate_minutes(model, df)
    out.insert(0, "recipe_id", df["recipe_id"].values)
    out.to_parquet(PROCESSED / "recipe_times.parquet", index=False)
    print(f"recipe_times.parquet: {len(out):,} rows in {time.time() - start:.0f} s;",
          out["minutes_source"].value_counts().to_dict())


def photos() -> None:
    m = pd.read_csv(MANIFEST)
    m = cast(pd.DataFrame, m[m["recipe_id"].notna() & (m["http_status"] == 200)])
    shared = cast(pd.Series, m.groupby("ahash")["recipe_id"].transform("nunique")) >= SHARED
    m = m.assign(photo_ok=~shared & (m["bytes"] >= TINY_BYTES))
    out = cast(pd.DataFrame, m.drop_duplicates("recipe_id")[["recipe_id", "url", "photo_ok"]])
    out = out.rename(columns={"url": "image_url"})
    out.to_parquet(PROCESSED / "recipe_photos.parquet", index=False)
    print(f"recipe_photos.parquet: {len(out):,} recipes, {(~out['photo_ok']).sum():,} photos hidden (logos, tiny)")


if __name__ == "__main__":
    jobs = sys.argv[1:] or ["photos", "times"]
    for job in jobs:
        {"times": times, "photos": photos}[job]()
