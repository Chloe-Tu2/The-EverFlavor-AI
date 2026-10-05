"""Nutrition quality (notebook 07): what a recipe's macros say per serving, and which of its
ingredients are rich in fiber, iron, calcium and vitamins (USDA SR Legacy, already downloaded).

Recipes list ingredients without amounts, so vitamin totals per recipe can not be computed honestly.
The ingredient tags say "has an ingredient rich in iron", never "this dish gives you X mg of iron"."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from .checks import require_columns
from .sources import USDA_DOWNLOADS, download_usda, usda_table

__all__ = [
    "DAILY_VALUES",
    "MACRO_LABELS",
    "RICH_SHARE",
    "SMALL_AMOUNT_CATEGORIES",
    "ingredient_micronutrients",
    "macro_quality",
    "recipe_rich_in",
]

# Column -> (USDA SR Legacy nutrient name, FDA Daily Value for adults (2020 label), unit)
DAILY_VALUES: dict[str, tuple[str, float, str]] = {
    "fiber": ("Fiber, total dietary", 28.0, "g"),
    "iron": ("Iron, Fe", 18.0, "mg"),
    "calcium": ("Calcium, Ca", 1300.0, "mg"),
    "potassium": ("Potassium, K", 4700.0, "mg"),
    "magnesium": ("Magnesium, Mg", 420.0, "mg"),
    "vitamin_c": ("Vitamin C, total ascorbic acid", 90.0, "mg"),
    "vitamin_a": ("Vitamin A, RAE", 900.0, "µg"),
    "vitamin_d": ("Vitamin D (D2 + D3)", 20.0, "µg"),
    "vitamin_b12": ("Vitamin B-12", 2.4, "µg"),
    "folate": ("Folate, DFE", 400.0, "µg"),
}
# FDA calls a food "high in" a nutrient at 20% of the Daily Value per serving; without portion sizes we
# apply it per 100 g, and say so wherever the tag is shown
RICH_SHARE = 0.20
# Foods used in small amounts: 100 g of cinnamon is rich in iron, but a recipe uses a teaspoon
SMALL_AMOUNT_CATEGORIES = {"Spices and Herbs", "Fats and Oils"}
# Per-serving macro labels (shares of calories): a dish is labeled when it meets the rule
MACRO_LABELS = {
    "high_protein": "at least 20% of calories from protein",
    "lower_fat": "less than 30% of calories from fat",
    "lower_carb": "less than 26% of calories from carbohydrate",
    "lower_sodium_density": "at most 1 mg sodium per kcal",
}


def _categories(folder: str | Path) -> dict[int, str]:
    """fdc_id -> USDA food category ("Spices and Herbs" ...) from the SR Legacy download."""
    _, key = USDA_DOWNLOADS["sr_legacy"]
    with zipfile.ZipFile(download_usda("sr_legacy", folder)) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".json"))
        foods = json.loads(archive.read(name))[key]
    return {int(f["fdcId"]): (f.get("foodCategory") or {}).get("description", "") for f in foods}


def ingredient_micronutrients(matches: pd.DataFrame, usda_folder: str | Path) -> pd.DataFrame:
    """Per 100 g micronutrients, % of Daily Value and "rich in" tags for matched ingredients.

    Args:
        matches: Notebook 01's USDA ingredient table (usda_ingredient_nutrition.csv):
            ingredient and fdc_id (its SR Legacy food).
        usda_folder: Where the USDA bulk downloads are kept (data/raw/usda_fdc).

    Returns:
        ingredient, fdc_id, usda_description and match (when `matches` has them: "automatic"
        matches are not hand-checked, and generic words can match a cured or processed food),
        usda_category, each DAILY_VALUES nutrient per 100 g, its share of
        the Daily Value (`<nutrient>_dv`), and rich_in (nutrients at RICH_SHARE or more, empty
        for SMALL_AMOUNT_CATEGORIES).
    """
    require_columns(matches, ["ingredient", "fdc_id"], "ingredient_micronutrients")
    usda = usda_table("sr_legacy", usda_folder, nutrients={name: col for col, (name, _, _) in DAILY_VALUES.items()})
    usda = usda.reindex(columns=[*usda.columns, *(c for c in DAILY_VALUES if c not in usda)])  # nutrients no food has
    usda["usda_category"] = usda["fdc_id"].map(_categories(usda_folder))
    keep = ["ingredient", "fdc_id"] + [c for c in ("usda_description", "match") if c in matches]
    out = (matches[keep].dropna(subset=["fdc_id"]).astype({"fdc_id": int})
           .merge(usda[["fdc_id", "usda_category", *DAILY_VALUES]], on="fdc_id", how="left"))
    for column, (_, daily, _) in DAILY_VALUES.items():
        out[f"{column}_dv"] = (out[column] / daily).round(3)
    small = out["usda_category"].isin(SMALL_AMOUNT_CATEGORIES)
    dv = out[[f"{c}_dv" for c in DAILY_VALUES]].to_numpy()
    out["rich_in"] = [[] if is_small else [c for c, share in zip(DAILY_VALUES, row) if share >= RICH_SHARE]
                      for is_small, row in zip(small, dv)]
    return out


def macro_quality(recipes: pd.DataFrame) -> pd.DataFrame:
    """Shares of calories from protein, fat and carbohydrate per serving, and the MACRO_LABELS.

    Uses 4 / 9 / 4 kcal per gram. Shares are computed from the macros themselves, so they
    add up to 100% even when a source's calorie figure differs a little.

    Args:
        recipes: Recipes with calories_per_serving, protein_g, fat_g, carbs_g and sodium_mg.

    Returns:
        A copy with protein_pct_kcal, fat_pct_kcal, carb_pct_kcal, protein_g_per_100kcal,
        sodium_mg_per_kcal and one True / False column per MACRO_LABELS key (missing values: False).
    """
    require_columns(recipes, ["calories_per_serving", "protein_g", "fat_g", "carbs_g", "sodium_mg"], "macro_quality")
    out = recipes.copy()
    kcal_from = pd.DataFrame({"protein": out["protein_g"] * 4, "fat": out["fat_g"] * 9, "carb": out["carbs_g"] * 4})
    total = kcal_from.sum(axis=1).replace(0, np.nan)
    for part in ("protein", "fat", "carb"):
        out[f"{part}_pct_kcal"] = (100 * kcal_from[part] / total).round(1)
    calories = out["calories_per_serving"].where(out["calories_per_serving"] > 0)
    out["protein_g_per_100kcal"] = (100 * out["protein_g"] / calories).round(2)
    out["sodium_mg_per_kcal"] = (out["sodium_mg"] / calories).round(2)
    out["high_protein"] = out["protein_pct_kcal"].ge(20)
    out["lower_fat"] = out["fat_pct_kcal"].lt(30)
    out["lower_carb"] = out["carb_pct_kcal"].lt(26)
    out["lower_sodium_density"] = out["sodium_mg_per_kcal"].le(1)
    return out


def recipe_rich_in(recipes: pd.DataFrame, ingredients: pd.DataFrame) -> pd.Series:
    """For each recipe, the nutrients at least one of its ingredients is rich in (per 100 g).

    Args:
        recipes: Recipes with ingredient_list.
        ingredients: ingredient_micronutrients(...) output.

    Returns:
        A sorted list of nutrient names per recipe ([] when none), aligned with `recipes`.
    """
    rich = {i: set(r) for i, r in zip(ingredients["ingredient"], ingredients["rich_in"]) if len(r)}
    return recipes["ingredient_list"].map(
        lambda items: sorted(set().union(*(rich.get(str(i), set()) for i in items))) if len(items) else [])
