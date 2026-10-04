"""The preprocessing pipeline (5.3-5.7, 5.10): cleaning, one call per source,
combining, splitting and the validation rules."""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from .checks import require_columns
from .cuisine import cuisine_names, map_cuisine, origin_from_labels
from .diets import DIET_COLUMNS, DIET_PROFILES, NUTRITION_DIETS, meets_diet
from .flags import (
    FLAG_COLUMNS,
    add_foodcom_diet_flags,
    add_hf_diet_flags,
    add_keyword_flags,
)
from .ingredients import (
    clean_ingredients,
    hf_ingredient_foods,
    normalize_ingredient_list,
)
from .nutrition import add_foodcom_macros, add_hf_macros, nutrition_checks
from .parsing import parse_label_list, parse_list_string

__all__ = [
    "ALLOWED_FAMILIES",
    "ALLOWED_SOURCES",
    "BOOL_COLUMNS",
    "COMMON_COLUMNS",
    "EXTRA_COLUMNS",
    "MAX_KCAL_PER_SERVING",
    "MAX_MINUTES",
    "MAX_SERVINGS",
    "ORIGIN_LABEL_COLUMN",
    "RAW_COLUMNS",
    "SOURCE_PRIORITY",
    "clean_foodcom",
    "clean_huggingface",
    "combine_sources",
    "run_pipeline",
    "split_by_ingredient_group",
    "split_tables",
    "validate_recipes",
]


# Recipes above this many kcal per serving are treated as data errors
MAX_KCAL_PER_SERVING = 3000
# Hugging Face recipes with more servings than this are bulk or catering
# entries whose per-serving values are not reliable
MAX_SERVINGS = 50
MAX_MINUTES = 1440   # cook times over 24 hours are data errors


def _drop(df: pd.DataFrame, keep: pd.Series, message: str, verbose: bool) -> pd.DataFrame:
    """Keep the rows where `keep` is True; print how many were dropped if `verbose`."""
    before = len(df)
    df = df[keep]
    if verbose:
        print(f"Dropped {before - len(df):,} {message}")
    return df


def clean_foodcom(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
    """Clean raw Food.com recipes (5.3.1).

    Drops rows missing a name, ingredients or nutrition, repeated names (the
    first is kept) and cook times over 24 hours.

    Args:
        df: Raw Food.com recipes (RAW_recipes.csv).
        verbose: Print how many rows each step drops.

    Returns:
        A new dataframe; `df` itself is not changed.
    """
    df = _drop(df, df[["name", "ingredients", "nutrition"]].notna().all(axis=1),
               "rows with missing name/ingredients/nutrition", verbose)
    df = _drop(df, ~df.duplicated(subset=["name"], keep="first"), "duplicate recipe names", verbose)
    return _drop(df, df["minutes"] <= MAX_MINUTES, "recipes with cook time > 24 hours", verbose).copy()


def clean_huggingface(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
    """Clean raw Hugging Face recipes (5.3.2) and add calories per serving.

    Drops rows missing a name, calories, cuisine or servings, repeated names,
    recipes with 0 or more than MAX_SERVINGS servings, and recipes over
    MAX_KCAL_PER_SERVING kcal per serving ('calories' is for the whole recipe).

    Args:
        df: Raw Hugging Face recipes.
        verbose: Print how many rows each step drops.

    Returns:
        A new dataframe with 'calories_per_serving'; `df` itself is not changed.
    """
    df = df.copy()
    df["servings"] = pd.to_numeric(df["servings"], errors="coerce")
    df = _drop(df, df[["recipe_name", "calories", "cuisine_type", "servings"]].notna().all(axis=1),
               "rows with missing name/calories/cuisine/servings", verbose)
    df = _drop(df, ~df.duplicated(subset=["recipe_name"], keep="first"), "duplicate recipe names", verbose)
    df = _drop(df, (df["servings"] > 0) & (df["servings"] <= MAX_SERVINGS),
               f"recipes with zero or more than {MAX_SERVINGS} servings", verbose).copy()
    # 'calories' is for the whole recipe; convert to per serving
    df["calories_per_serving"] = df["calories"] / df["servings"]
    return _drop(df, df["calories_per_serving"] <= MAX_KCAL_PER_SERVING,
                 f"recipes with more than {MAX_KCAL_PER_SERVING:,} kcal per serving", verbose).copy()


# Columns every source ends up with (missing values are NaN / None)
COMMON_COLUMNS = (["recipe_id", "source", "recipe_name", "cuisine_family", "cuisine_raw",
                   "ingredient_list", "complexity", "calories_per_serving", "protein_g",
                   "fat_g", "carbs_g", "sodium_mg", "servings", "minutes", "instructions", "url",
                   "origin_country", "origin_region"]
                  + FLAG_COLUMNS)


# Raw columns each source needs, and the column holding its own origin labels (5.4.6)
RAW_COLUMNS = {
    "foodcom"    : ["id", "name", "ingredients", "nutrition", "minutes", "tags", "steps"],
    "huggingface": ["recipe_name", "calories", "cuisine_type", "servings", "total_nutrients",
                    "ingredients", "ingredient_lines", "health_labels"],
    "culinarydb" : ["recipe_id", "recipe_name", "ingredients", "cuisine"],
    "themealdb"  : ["recipe_id", "recipe_name", "ingredients", "area", "source_url"],
}
ORIGIN_LABEL_COLUMN = {"foodcom": "tags", "huggingface": "cuisine_type", "culinarydb": "cuisine", "themealdb": "area"}


def _prepare_foodcom(df: pd.DataFrame) -> pd.DataFrame:
    """Food.com: clean, nutrition, ingredients, flags, cuisine from tags, IDs and steps."""
    df = clean_foodcom(df)
    df = add_foodcom_macros(df)
    df = df[df["calories_per_serving"] <= MAX_KCAL_PER_SERVING].copy()
    df["ingredient_list"] = df["ingredients"].apply(clean_ingredients).apply(normalize_ingredient_list)
    df = add_foodcom_diet_flags(df)
    df["cuisine_family"] = df["tags"].apply(lambda t: map_cuisine(t, substring_match=False))
    df["cuisine_raw"]    = df["tags"].apply(cuisine_names)
    df["recipe_id"]      = "foodcom_" + df["id"].astype(str)
    df["recipe_name"]    = df["name"].str.replace(r"\s+", " ", regex=True).str.strip()
    df["instructions"]   = df["steps"].apply(lambda s: "\n".join(map(str, parse_list_string(s))))
    return df


def _prepare_huggingface(df: pd.DataFrame) -> pd.DataFrame:
    """Hugging Face: IDs, clean, nutrition per serving, ingredients, flags (with labels), cuisine."""
    df["recipe_id"] = "hf_" + df.index.astype(str)
    df = clean_huggingface(df)
    df = add_hf_macros(df)
    df["ingredient_list"] = df["ingredients"].apply(hf_ingredient_foods).apply(normalize_ingredient_list)
    df = add_hf_diet_flags(df)
    df["cuisine_family"] = df["cuisine_type"].apply(map_cuisine)
    df["cuisine_raw"]    = df["cuisine_type"].apply(lambda x: ", ".join(parse_label_list(x)))
    return df


def _prepare_recipe_list(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """CulinaryDB and TheMealDB: ingredient lists only, with a region or country label."""
    cuisine_col = ORIGIN_LABEL_COLUMN[source]
    df = df.dropna(subset=["recipe_name", "ingredients"])
    df = df.drop_duplicates(subset=["recipe_name"], keep="first").copy()
    df["ingredient_list"] = df["ingredients"].apply(lambda x: normalize_ingredient_list(parse_list_string(x)))
    df = add_keyword_flags(df, "ingredients", name_col="recipe_name")
    df["cuisine_family"] = df[cuisine_col].apply(map_cuisine)
    df["cuisine_raw"]    = df[cuisine_col].fillna("").astype(str).str.lower()
    df["recipe_id"]      = source + "_" + df["recipe_id"].astype(str)
    if source == "themealdb":
        df["url"] = df["source_url"]
    return df


def run_pipeline(df_in: pd.DataFrame, source: str = "foodcom") -> pd.DataFrame:
    """Turn one raw source into clean recipes with every feature (5.5).

    Uses the same functions as the step-by-step cells in 5.3 and 5.4, so both
    paths give the same result.

    Args:
        df_in: The raw recipes of one source (not changed).
        source: "foodcom", "huggingface", "culinarydb" or "themealdb".

    Returns:
        One row per recipe with exactly the COMMON_COLUMNS (missing values as NaN).

    Raises:
        ValueError: If `source` is unknown or a needed raw column is missing.
    """
    if source not in RAW_COLUMNS:
        raise ValueError(f"Unknown source '{source}'. Use one of: {', '.join(RAW_COLUMNS)}.")
    require_columns(df_in, RAW_COLUMNS[source], f"run_pipeline[{source}]")
    df = df_in.copy()
    if source == "foodcom":
        df = _prepare_foodcom(df)
    elif source == "huggingface":
        df = _prepare_huggingface(df)
    else:
        df = _prepare_recipe_list(df, source)

    df["source"]     = source
    df["complexity"] = df["ingredient_list"].apply(lambda x: len(set(x)))
    origins = df[ORIGIN_LABEL_COLUMN[source]].apply(origin_from_labels)
    df["origin_country"], df["origin_region"] = origins.str[0], origins.str[1]
    for col in COMMON_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    return df[COMMON_COLUMNS].reset_index(drop=True)


# Lower number = kept when the same title appears in several sources
SOURCE_PRIORITY = ["huggingface", "foodcom", "themealdb", "culinarydb"]


def combine_sources(frames: Sequence[pd.DataFrame]) -> tuple[pd.DataFrame, pd.Series, int]:
    """Stack the cleaned sources into one recipe table (5.6.1).

    Duplicate titles keep the copy from the source that comes first in
    SOURCE_PRIORITY; recipes with fewer than 2 ingredients are dropped; the
    quality columns are added (has_nutrition, nutrition_plausible,
    cuisine_labeled, ingredient_group).

    Args:
        frames: Outputs of `run_pipeline`, one per source.

    Returns:
        (combined table, recipes per source before removing duplicates,
        recipes dropped for having fewer than 2 ingredients).
    """
    df_all = pd.concat(frames, ignore_index=True)
    counts_before = df_all["source"].value_counts()

    title_key = (df_all["recipe_name"].astype(str).str.lower()
                 .str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip())
    priority = df_all["source"].map({s: i for i, s in enumerate(SOURCE_PRIORITY)})
    keep_order = priority.sort_values(kind="stable").index
    df_all = df_all.loc[keep_order][~title_key.loc[keep_order].duplicated()].reset_index(drop=True)

    before = len(df_all)
    df_all = df_all[df_all["complexity"] >= 2].reset_index(drop=True)
    dropped_small = before - len(df_all)

    # A vegan recipe must also be vegetarian (keeps the two flags consistent)
    df_all["vegan"] = df_all["vegan"] & df_all["vegetarian"]

    df_all["has_nutrition"] = df_all["calories_per_serving"].notna()
    df_all["nutrition_plausible"] = df_all["has_nutrition"] & nutrition_checks(df_all).all(axis=1)

    df_all["cuisine_labeled"] = df_all["cuisine_family"] != "Other"
    same_ingredients = df_all["ingredient_list"].apply(lambda l: "|".join(sorted(set(l))))
    # Recipes with only 2 ingredients are too generic to call duplicates: each is its own group
    df_all["ingredient_group"] = same_ingredients.where(df_all["complexity"] >= 3, df_all["recipe_id"])
    return df_all, counts_before, dropped_small


def _safe_strata(labels: pd.Series) -> pd.Series | None:
    """Return the labels for stratifying, or None if any label has fewer than 2 rows."""
    return labels if labels.value_counts().min() >= 2 else None


def split_by_ingredient_group(df_all: pd.DataFrame, seed: int = 42, min_per_family: int = 10,
                              verbose: bool = True) -> pd.DataFrame:
    """Assign every recipe to train (70%), val (15%) or test (15%) (5.7.1).

    Ingredient groups are split, not single recipes, so near-duplicates never
    end up in different splits. Each group is stratified by the cuisine family
    of its first recipe; families with fewer than `min_per_family` groups are
    grouped with "Other" for the split only.

    Args:
        df_all: The combined table from `combine_sources`.
        seed: Random seed, recorded in the dataset record.
        min_per_family: Smallest family that is stratified on its own.
        verbose: Print notes when families are merged or stratifying is impossible.

    Returns:
        A copy of `df_all` with a 'split' column; `df_all` itself is not changed.
    """
    require_columns(df_all, ["ingredient_group", "cuisine_family"], "split_by_ingredient_group")
    df_all = df_all.copy()
    groups = df_all.groupby("ingredient_group")["cuisine_family"].first()
    family_counts = groups.value_counts()
    small_families = [f for f in family_counts[family_counts < min_per_family].index if f != "Other"]
    strata = groups.where(~groups.isin(small_families), "Other")
    if small_families and verbose:
        print(f"Families with fewer than {min_per_family} groups, grouped with 'Other' for stratifying: {small_families}")

    # Split positions (0, 1, 2, ...) rather than the group keys themselves:
    # this works with every pandas version, including pandas 3, whose
    # default text type is not accepted by train_test_split as an index.
    positions = np.arange(len(groups))
    strata_by_pos = pd.Series(strata.to_numpy(dtype=object))

    # First split: 70% train, 30% temp (split again into val + test)
    _train_pos, temp_pos = train_test_split(
        positions, test_size=0.30, stratify=_safe_strata(strata_by_pos), random_state=seed)

    # Second split: 50% of temp = 15% val, 50% of temp = 15% test
    temp_strata = strata_by_pos.iloc[temp_pos].reset_index(drop=True)
    if _safe_strata(temp_strata) is None and verbose:
        print("Note: too few groups to stratify the val/test split; using a random split instead.")
    val_rel, test_rel = train_test_split(
        np.arange(len(temp_pos)), test_size=0.50, stratify=_safe_strata(temp_strata), random_state=seed)

    split_of_group = pd.Series("train", index=groups.index, dtype=object)
    split_of_group.iloc[temp_pos[val_rel]] = "val"
    split_of_group.iloc[temp_pos[test_rel]] = "test"
    df_all["split"] = df_all["ingredient_group"].map(split_of_group)
    return df_all


def split_tables(df_all: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return the train, validation and test tables (call again after adding columns to df_all)."""
    train, val, test = (df_all[df_all["split"] == name].reset_index(drop=True) for name in ("train", "val", "test"))
    return train, val, test


# ------------------------------------------------------------------ validation (5.10)
ALLOWED_FAMILIES = {"Asian", "European", "Latin American", "African", "Middle Eastern", "Other"}
ALLOWED_SOURCES = set(SOURCE_PRIORITY)
EXTRA_COLUMNS = ["has_nutrition", "nutrition_plausible", "cuisine_labeled", "ingredient_group", "split",
                 "nutrition_source", "calories_est_min", "calories_est_max", "usda_dish", "usda_dish_kcal",
                 "origin_source", "origin_confidence", *DIET_COLUMNS]
BOOL_COLUMNS = FLAG_COLUMNS + DIET_COLUMNS + ["has_nutrition", "nutrition_plausible", "cuisine_labeled"]


def validate_recipes(df: pd.DataFrame, origin_min_confidence: float) -> dict[str, bool]:
    """Run every data rule on the final recipe table (5.10).

    Args:
        df: The final combined table.
        origin_min_confidence: The confidence threshold used for predicted countries.

    Returns:
        {rule: passed}; a single failing "columns present" rule if columns are missing.
    """
    missing = [c for c in COMMON_COLUMNS + EXTRA_COLUMNS if c not in df.columns]
    if missing:
        return {f"columns present (missing: {missing})": False}
    kcal = df["calories_per_serving"].dropna()
    estimated = df["nutrition_source"] == "estimated"
    servings = df["servings"].dropna()
    rules = {
        "recipe_id is unique"                         : df["recipe_id"].is_unique,
        "every recipe has a name"                     : df["recipe_name"].notna().all(),
        "cuisine_family has only allowed values"      : df["cuisine_family"].isin(ALLOWED_FAMILIES).all(),
        "source has only allowed values"              : df["source"].isin(ALLOWED_SOURCES).all(),
        "every recipe has at least 2 ingredients"     : (df["complexity"] >= 2).all(),
        "flags are true/false only"                   : all(df[c].dtype == bool for c in BOOL_COLUMNS),
        f"calories between 0 and {MAX_KCAL_PER_SERVING:,} kcal": kcal.between(0, MAX_KCAL_PER_SERVING).all(),
        f"servings between 1 and {MAX_SERVINGS}"      : servings.between(1, MAX_SERVINGS).all(),
        "plausible nutrition only where data exists"  : (~df["nutrition_plausible"] | df["has_nutrition"]).all(),
        "every recipe has calories (listed or estimated)": df["calories_per_serving"].notna().all(),
        "estimates only where listed data was missing or unbelievable": (estimated == ~df["nutrition_plausible"]).all(),
        "every estimate lies inside its likely range" : df.loc[estimated, "calories_per_serving"].between(
            df.loc[estimated, "calories_est_min"], df.loc[estimated, "calories_est_max"]).all(),
        "vegan recipes are also vegetarian"           : (~df["vegan"] | df["vegetarian"]).all(),
        "recipes with meat are not vegetarian"        : (~df["contains_meat"] | ~df["vegetarian"]).all(),
        "red meat and poultry also count as meat"     : (~(df["contains_red_meat"] | df["contains_poultry"])
                                                         | df["contains_meat"]).all(),
        "crustaceans and molluscs also count as shellfish": (~(df["contains_crustacean"] | df["contains_mollusc"])
                                                             | df["contains_shellfish"]).all(),
        "scaleless fish also count as fish"           : (~df["contains_scaleless_fish"] | df["contains_fish"]).all(),
        "unclean meat also counts as meat"            : (~df["contains_unclean_meat"] | df["contains_meat"]).all(),
        "every diet column follows its rule (5.4.7)"  : all((df[d] == meets_diet(df, d)).all() for d in DIET_PROFILES),
        "nutrition diets only with listed nutrition"  : (~df[list(NUTRITION_DIETS)].any(axis=1) | df["nutrition_plausible"]).all(),
        "origin_source has only allowed values"       : df["origin_source"].isin(["labeled", "predicted", "unknown"]).all(),
        "country is Unknown only when origin is unknown": ((df["origin_country"] == "Unknown") == (df["origin_source"] == "unknown")).all(),
        "predicted countries meet the confidence bar" : (df.loc[df["origin_source"] == "predicted", "origin_confidence"] >= origin_min_confidence).all(),
        "every recipe is in exactly one split"        : df["split"].isin(["train", "val", "test"]).all(),
        "no ingredient group spans two splits"        : (df.groupby("ingredient_group")["split"].nunique() == 1).all(),
    }
    return {rule: bool(passed) for rule, passed in rules.items()}
