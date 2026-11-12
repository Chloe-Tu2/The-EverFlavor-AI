"""Food.com recipes' own details from the CC0 Kaggle dataset "Food.com - Recipes and Reviews" (irkaal), joined by
recipe number: prep, cook and total time, servings, and the nutrition fields our data does not keep (sugar, fibre,
saturated fat, cholesterol), all per serving as the recipe lists them.

Its ingredient quantities are not used: they have no units ("1/4" of "sugar") and in most recipes their count does
not match the ingredients (docs/plans/local/RECIPE_ACCURACY.md), so showing them would mislead.

A row is kept only when the recipe's name matches ours too, so a renumbered recipe never borrows another's details.

    >>> details = foodcom_details(pd.read_parquet("recipes.parquet"), ours)   # ours: recipe_id, recipe_name
"""
from __future__ import annotations

import re

import pandas as pd

__all__ = ["DETAIL_COLUMNS", "foodcom_details", "iso_minutes"]

DETAIL_COLUMNS = ["recipe_id", "prep_minutes", "cook_minutes", "total_minutes", "servings_listed", "sugar_g",
                  "fiber_g", "saturated_fat_g", "cholesterol_mg"]
_ISO = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")
_KAGGLE = {"SugarContent": "sugar_g", "FiberContent": "fiber_g", "SaturatedFatContent": "saturated_fat_g",
           "CholesterolContent": "cholesterol_mg"}
MAX_MINUTES = 3 * 24 * 60     # a listed time over three days is a typo or a ferment, not shown as cooking time


def iso_minutes(value: object) -> float | None:
    """Minutes from an ISO 8601 duration ("PT1H20M" is 80), or None when missing, malformed, zero or too long."""
    found = _ISO.match(str(value)) if isinstance(value, str) else None
    if not found:
        return None
    days, hours, minutes, seconds = (int(part) if part else 0 for part in found.groups())
    total = days * 1440 + hours * 60 + minutes + seconds / 60
    return float(total) if 0 < total <= MAX_MINUTES else None


def _name_key(name: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def _numbers(df: pd.DataFrame, column: str) -> pd.Series:
    """A column as numbers (NaN where missing or not a number; all NaN when the column is missing)."""
    if column not in df:
        return pd.Series(float("nan"), index=df.index)
    return pd.Series(pd.to_numeric(df[column], errors="coerce"), index=df.index)


def foodcom_details(kaggle: pd.DataFrame, ours: pd.DataFrame) -> pd.DataFrame:
    """One row per Food.com recipe of ours whose number and name match the Kaggle dataset (DETAIL_COLUMNS).

    Args:
        kaggle: The dataset's recipes (RecipeId, Name, CookTime, PrepTime, TotalTime, RecipeServings and the
            nutrition columns).
        ours: Our recipes (recipe_id like "foodcom_123", recipe_name).
    """
    mine = ours[ours["recipe_id"].astype(str).str.startswith("foodcom_")][["recipe_id", "recipe_name"]].copy()
    mine["RecipeId"] = pd.to_numeric(mine["recipe_id"].str.removeprefix("foodcom_"), errors="coerce")
    joined = mine.dropna(subset=["RecipeId"]).merge(kaggle, on="RecipeId", how="inner")
    joined = joined[joined["recipe_name"].map(_name_key) == joined["Name"].map(_name_key)]
    out = pd.DataFrame({"recipe_id": joined["recipe_id"].to_numpy()})
    for column, name in (("PrepTime", "prep_minutes"), ("CookTime", "cook_minutes"), ("TotalTime", "total_minutes")):
        out[name] = joined[column].map(iso_minutes).to_numpy() if column in joined else None
    servings = _numbers(joined, "RecipeServings")
    out["servings_listed"] = servings.where((servings > 0) & (servings <= 100)).to_numpy()
    for column, name in _KAGGLE.items():
        values = _numbers(joined, column)
        out[name] = values.where(values >= 0).to_numpy()
    return out[DETAIL_COLUMNS]
