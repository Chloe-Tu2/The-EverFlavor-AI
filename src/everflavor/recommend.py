"""The rule-based recipe recommender and its safety filter (6.3).

The safety filter re-checks each recipe's ingredients and name with the same
keyword rules (flags.py) and diet rules (diets.py) used to build the data.
"""
import pandas as pd

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


def passes_safety_filter(row, avoid=(), vegetarian=False, vegan=False, diets=()):
    """Re-check one recipe's ingredients and name against the restrictions.

    Independent of the stored flags, so a wrong flag cannot let a recipe through.
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
    df,
    cuisine_family=None,
    calorie_target=500,
    vegetarian_only=False,
    vegan_only=False,
    gluten_free=False,
    avoid=(),
    diets=(),
    top_n=5
):
    """Simple rule-based recipe recommender (baseline model).

    Filters by cuisine and dietary flags, then ranks by
    proximity to the calorie target.

    Args:
        df (pd.DataFrame): The preprocessed recipe dataframe.
        cuisine_family (str | None): One of the five EverFlavor families, or None for all.
        calorie_target (float): Desired calories per serving.
        vegetarian_only (bool): Restrict to vegetarian recipes.
        vegan_only (bool): Restrict to vegan recipes.
        gluten_free (bool): Restrict to gluten-free recipes.
        avoid (tuple): Flag columns to exclude, e.g. ("contains_pork", "contains_alcohol").
        diets (tuple): Diet profiles from 5.4.7 to require, e.g. ("halal_friendly",).
        top_n (int): Number of recommendations to return.

    Returns:
        pd.DataFrame: Top N matching recipes sorted by calorie distance.
    """
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
