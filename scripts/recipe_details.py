"""Food.com recipes' own details for the dish page (src/everflavor/recipe_details.py), from the CC0 Kaggle dataset
"Food.com - Recipes and Reviews" (irkaal, the one notebook 10 uses for photos):

- data/processed/foodcom_details.parquet: recipe_id, prep, cook and total minutes, servings, sugar, fibre, saturated
  fat and cholesterol per serving, for our Food.com recipes whose number and name match.

    python scripts/recipe_details.py [path to recipes.parquet]

Without a path it uses Kaggle's download cache (kagglehub), downloading the dataset if needed (Kaggle API key).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.recipe_details import foodcom_details

PROCESSED = ROOT / "data" / "processed"
KAGGLE_DATASET = "irkaal/foodcom-recipes-and-reviews"
COLUMNS = ["RecipeId", "Name", "CookTime", "PrepTime", "TotalTime", "RecipeServings", "SugarContent", "FiberContent",
           "SaturatedFatContent", "CholesterolContent"]


def kaggle_recipes(path: str | None) -> Path:
    """The dataset's recipes.parquet: the path given, else kagglehub's cached (or new) download."""
    if path:
        return Path(path)
    import kagglehub  # only needed without a path
    return Path(kagglehub.dataset_download(KAGGLE_DATASET)) / "recipes.parquet"


def main(path: str | None = None) -> None:
    ours = pd.concat([pd.read_parquet(PROCESSED / f"recipes_{split}.parquet", columns=["recipe_id", "recipe_name"])
                      for split in ("train", "val", "test")], ignore_index=True)
    details = foodcom_details(pd.read_parquet(kaggle_recipes(path), columns=COLUMNS), ours)
    details.to_parquet(PROCESSED / "foodcom_details.parquet", index=False)
    foodcom = ours["recipe_id"].str.startswith("foodcom_").sum()
    print(f"{len(details):,} of {foodcom:,} Food.com recipes matched ({len(details) / foodcom:.1%})")
    for column in details.columns[1:]:
        print(f"  {column}: {details[column].notna().mean():.1%} known")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
