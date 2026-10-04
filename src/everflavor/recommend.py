"""The rule-based recipe recommender and its safety filter (6.3).

The safety filter re-checks each recipe's ingredients and name with the same
keyword rules (flags.py) and diet rules (diets.py) used to build the data.
"""
from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from .checks import require_columns
from .diets import diet_flags_needed, meets_diet
from .flags import (
    ANIMAL_EXCEPTIONS,
    ANIMAL_KEYWORDS,
    FLAG_RULES,
    MEAT_EXCEPTIONS,
    MEAT_KEYWORDS,
    keyword_flag,
    make_flag,
)
from .ingredients import ingredient_text


def passes_safety_filter(row: pd.Series, avoid: Sequence[str] = (), vegetarian: bool = False,
                         vegan: bool = False, diets: Sequence[str] = ()) -> bool:
    """Re-check one recipe's ingredients and name against the user's restrictions.

    Independent of the stored flags, so a wrong flag cannot let a recipe through.

    Args:
        row: One recipe with 'ingredient_list' and 'recipe_name'.
        avoid: Flag columns that must be False, for example ("contains_pork",).
        vegetarian: Require a vegetarian recipe.
        vegan: Require a vegan recipe.
        diets: Diet profiles from DIET_PROFILES to require, for example ("halal_friendly",).

    Returns:
        True if the recipe is safe for every restriction.
    """
    text = ingredient_text(row["ingredient_list"]) + " | " + str(row["recipe_name"]).lower()
    for diet in diets:
        flags = pd.DataFrame([{column: keyword_flag(text, column) for column in diet_flags_needed(diet)}])
        if not meets_diet(flags, diet).iloc[0]:
            return False
    for flag in avoid:
        keywords, exceptions = FLAG_RULES[flag]
        if make_flag(text, keywords, exceptions):
            return False
    if vegetarian and make_flag(text, MEAT_KEYWORDS, MEAT_EXCEPTIONS):
        return False
    return not (vegan and make_flag(text, ANIMAL_KEYWORDS, ANIMAL_EXCEPTIONS))


def baseline_recommend(
    df: pd.DataFrame,
    cuisine_family: str | None = None,
    calorie_target: float = 500,
    vegetarian_only: bool = False,
    vegan_only: bool = False,
    gluten_free: bool = False,
    avoid: Sequence[str] = (),
    diets: Sequence[str] = (),
    top_n: int = 5,
) -> pd.DataFrame:
    """Recommend recipes with simple rules (the Week 6 baseline model).

    Filters by cuisine, dietary flags and diet profiles, keeps recipes with
    plausible listed nutrition, ranks them by distance to the calorie target,
    and re-checks the best candidates with the safety filter.

    Args:
        df: The preprocessed recipe table.
        cuisine_family: One of the five families, or None for all.
        calorie_target: Desired calories per serving.
        vegetarian_only: Restrict to vegetarian recipes.
        vegan_only: Restrict to vegan recipes.
        gluten_free: Restrict to gluten-free recipes.
        avoid: Flag columns to exclude, for example ("contains_pork", "contains_alcohol").
        diets: Diet profiles to require, for example ("halal_friendly",).
        top_n: Number of recommendations.

    Returns:
        The top recipes with a 'calorie_distance' column, or an empty dataframe
        when nothing matches.
    """
    require_columns(df, ["recipe_name", "ingredient_list", "cuisine_family", "calories_per_serving",
                         "nutrition_plausible", "vegetarian", "vegan", "contains_gluten", *avoid, *diets],
                    "baseline_recommend")
    results = df.copy()

    # Step 1: Filter by cuisine family
    if cuisine_family:
        results = results[results["cuisine_family"] == cuisine_family]

    # Step 2: Apply dietary flags
    if vegetarian_only:
        results = results[results["vegetarian"] == True]
    if vegan_only:
        results = results[results["vegan"] == True]
    if gluten_free:
        results = results[results["contains_gluten"] == False]
    for flag in avoid:
        results = results[results[flag] == False]
    for diet in diets:
        results = results[results[diet]]

    # Step 3: Keep only recipes with plausible nutrition data
    results = results[results["nutrition_plausible"]]

    if results.empty:
        print("No recipes matched the given filters.")
        return pd.DataFrame()

    # Step 4: Rank by distance to calorie target
    results["calorie_distance"] = (results["calories_per_serving"] - calorie_target).abs()
    results = results.sort_values("calorie_distance")

    # Step 5: Safety filter on the best candidates
    all_avoid = tuple(avoid) + (("contains_gluten",) if gluten_free else ())
    candidates = results.head(top_n * 20)
    safe = candidates[candidates.apply(
        lambda r: passes_safety_filter(r, all_avoid, vegetarian_only, vegan_only, diets), axis=1)]
    if len(safe) < len(candidates):
        print(f"(safety filter removed {len(candidates) - len(safe)} of {len(candidates)} candidates)")

    return safe.head(top_n)
