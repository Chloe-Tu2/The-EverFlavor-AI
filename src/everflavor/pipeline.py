"""The preprocessing pipeline (5.3-5.7, 5.10): cleaning, one call per source,
combining, splitting and the validation rules."""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

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

# Recipes above this many kcal per serving are treated as data errors
MAX_KCAL_PER_SERVING = 3000
# Hugging Face recipes with more servings than this are bulk or catering
# entries whose per-serving values are not reliable
MAX_SERVINGS = 50
MAX_MINUTES = 1440   # cook times over 24 hours are data errors


def _drop(df, keep, message, verbose):
    before = len(df)
    df = df[keep]
    if verbose:
        print(f"Dropped {before - len(df):,} {message}")
    return df


def clean_foodcom(df, verbose=False):
    """Food.com cleaning (5.3.1): missing fields, duplicate names, cook times over 24 hours."""
    df = _drop(df, df[["name", "ingredients", "nutrition"]].notna().all(axis=1),
               "rows with missing name/ingredients/nutrition", verbose)
    df = _drop(df, ~df.duplicated(subset=["name"], keep="first"), "duplicate recipe names", verbose)
    return _drop(df, df["minutes"] <= MAX_MINUTES, "recipes with cook time > 24 hours", verbose)


def clean_huggingface(df, verbose=False):
    """Hugging Face cleaning (5.3.2): missing fields, duplicates, servings, calories per serving."""
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


def run_pipeline(df_in, source="foodcom"):
    """Apply the full EverFlavor preprocessing pipeline to a raw dataframe.

    Uses the same helper functions as the step-by-step cells above,
    so both paths produce the same features.

    Args:
        df_in (pd.DataFrame): The raw input dataframe.
        source (str): 'foodcom', 'huggingface', 'culinarydb' or 'themealdb'.

    Returns:
        pd.DataFrame: Cleaned recipes with the COMMON_COLUMNS.
    """
    df = df_in.copy()

    if source == "foodcom":
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

    elif source == "huggingface":
        df["recipe_id"] = "hf_" + df.index.astype(str)
        df = clean_huggingface(df)
        df = add_hf_macros(df)
        df["ingredient_list"] = df["ingredients"].apply(hf_ingredient_foods).apply(normalize_ingredient_list)
        df = add_hf_diet_flags(df)
        df["cuisine_family"] = df["cuisine_type"].apply(map_cuisine)
        df["cuisine_raw"]    = df["cuisine_type"].apply(lambda x: ", ".join(parse_label_list(x)))

    elif source in ("culinarydb", "themealdb"):
        cuisine_col = "cuisine" if source == "culinarydb" else "area"
        df = df.dropna(subset=["recipe_name", "ingredients"])
        df = df.drop_duplicates(subset=["recipe_name"], keep="first").copy()
        df["ingredient_list"] = df["ingredients"].apply(lambda x: normalize_ingredient_list(parse_list_string(x)))
        df = add_keyword_flags(df, "ingredients", name_col="recipe_name")
        df["cuisine_family"] = df[cuisine_col].apply(map_cuisine)
        df["cuisine_raw"]    = df[cuisine_col].fillna("").astype(str).str.lower()
        df["recipe_id"]      = source + "_" + df["recipe_id"].astype(str)
        if source == "themealdb":
            df["url"] = df["source_url"]

    else:
        raise ValueError(f"Unknown source '{source}'. Use 'foodcom', 'huggingface', 'culinarydb' or 'themealdb'.")

    df["source"]     = source
    df["complexity"] = df["ingredient_list"].apply(lambda x: len(set(x)))
    # Country and region from the source's own labels (5.4.6)
    origin_labels = {"foodcom": "tags", "huggingface": "cuisine_type",
                     "culinarydb": "cuisine", "themealdb": "area"}[source]
    origins = df[origin_labels].apply(origin_from_labels)
    df["origin_country"], df["origin_region"] = origins.str[0], origins.str[1]
    for col in COMMON_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    return df[COMMON_COLUMNS].reset_index(drop=True)


# Lower number = kept when the same title appears in several sources
SOURCE_PRIORITY = ["huggingface", "foodcom", "themealdb", "culinarydb"]


def combine_sources(frames):
    """Stack the cleaned sources into one table (5.6.1).

    Duplicate titles keep the copy from the highest-priority source; recipes with
    fewer than 2 ingredients are dropped; quality columns are added.
    Returns (df_all, counts per source before removing duplicates, recipes dropped for < 2 ingredients).
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


def safe_strata(labels):
    """Return the labels for stratifying, or None if any group has fewer than 2 rows."""
    return labels if labels.value_counts().min() >= 2 else None


def split_by_ingredient_group(df_all, seed=42, min_per_family=10, verbose=True):
    """Add a 'split' column (train 70% / val 15% / test 15%) to the combined table (5.7.1).

    Ingredient groups are split, not single recipes, so near-duplicates never end
    up in different splits. Each group is stratified by the cuisine family of its
    first recipe; families with fewer than `min_per_family` groups are grouped with
    'Other' for the split only.
    """
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
        positions, test_size=0.30, stratify=safe_strata(strata_by_pos), random_state=seed)

    # Second split: 50% of temp = 15% val, 50% of temp = 15% test
    temp_strata = strata_by_pos.iloc[temp_pos].reset_index(drop=True)
    if safe_strata(temp_strata) is None and verbose:
        print("Note: too few groups to stratify the val/test split; using a random split instead.")
    val_rel, test_rel = train_test_split(
        np.arange(len(temp_pos)), test_size=0.50, stratify=safe_strata(temp_strata), random_state=seed)

    split_of_group = pd.Series("train", index=groups.index, dtype=object)
    split_of_group.iloc[temp_pos[val_rel]] = "val"
    split_of_group.iloc[temp_pos[test_rel]] = "test"
    df_all["split"] = df_all["ingredient_group"].map(split_of_group)
    return df_all


def split_tables(df_all):
    """The train, validation and test tables (call again after adding columns to df_all)."""
    return tuple(df_all[df_all["split"] == name].reset_index(drop=True) for name in ("train", "val", "test"))


# ------------------------------------------------------------------ validation (5.10)
ALLOWED_FAMILIES = {"Asian", "European", "Latin American", "African", "Middle Eastern", "Other"}
ALLOWED_SOURCES = set(SOURCE_PRIORITY)
EXTRA_COLUMNS = ["has_nutrition", "nutrition_plausible", "cuisine_labeled", "ingredient_group", "split",
                 "nutrition_source", "calories_est_min", "calories_est_max", "usda_dish", "usda_dish_kcal",
                 "origin_source", "origin_confidence", *DIET_COLUMNS]
BOOL_COLUMNS = FLAG_COLUMNS + DIET_COLUMNS + ["has_nutrition", "nutrition_plausible", "cuisine_labeled"]


def validate_recipes(df, origin_min_confidence):
    """Run every rule on a recipe table. Returns a dict {rule: passed}."""
    missing = [c for c in COMMON_COLUMNS + EXTRA_COLUMNS if c not in df.columns]
    if missing:
        return {f"columns present (missing: {missing})": False}
    kcal = df["calories_per_serving"].dropna()
    estimated = df["nutrition_source"] == "estimated"
    servings = df["servings"].dropna()
    return {
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
        "every diet column follows its rule (5.4.7)"  : all((df[d] == meets_diet(df, d)).all() for d in DIET_PROFILES),
        "nutrition diets only with listed nutrition"  : (~df[list(NUTRITION_DIETS)].any(axis=1) | df["nutrition_plausible"]).all(),
        "origin_source has only allowed values"       : df["origin_source"].isin(["labeled", "predicted", "unknown"]).all(),
        "country is Unknown only when origin is unknown": ((df["origin_country"] == "Unknown") == (df["origin_source"] == "unknown")).all(),
        "predicted countries meet the confidence bar" : (df.loc[df["origin_source"] == "predicted", "origin_confidence"] >= origin_min_confidence).all(),
        "every recipe is in exactly one split"        : df["split"].isin(["train", "val", "test"]).all(),
        "no ingredient group spans two splits"        : (df.groupby("ingredient_group")["split"].nunique() == 1).all(),
    }
