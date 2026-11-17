"""The rule-based recipe recommender and its safety filter (6.3).

The safety filter re-checks each recipe's ingredients and name with the same
keyword rules (flags.py) and diet rules (diets.py) used to build the data.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence

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
    recipe_text,
)
from .preferences import drop_skipped

__all__ = [
    "SORT_ORDERS",
    "baseline_recommend",
    "fit_checks",
    "passes_safety_filter",
    "recipe_minutes",
    "what_blocks",
    "why_it_fits",
    "within_calories",
]


SORT_ORDERS = ("calories", "quickest", "protein")
# The safety re-check reads candidates in chunks of top_n * 20, best first, until top_n pass. It stops after
# this many candidates (one chunk at least), so a table whose stored flags are stale cannot hang a search;
# the stop is logged as a warning.
MAX_SAFETY_CHECKS = 2000

logger = logging.getLogger(__name__)


def _is(df: pd.DataFrame, column: str, value: bool) -> pd.Series:
    """Rows where a stored flag has this value; a missing value (a nullable column) never counts."""
    return (df[column] == value).fillna(False).astype(bool)


def _fits(df: pd.DataFrame, column: str) -> pd.Series:
    """Rows where a stored diet column is True; a missing value never counts."""
    return df[column].astype("boolean").fillna(False).astype(bool)


def recipe_minutes(df: pd.DataFrame) -> pd.Series:
    """Each recipe's time: its own (`minutes`), else the estimate (`minutes_estimate`), else NaN."""
    own = df["minutes"] if "minutes" in df.columns else pd.Series(float("nan"), index=df.index)
    if "minutes_estimate" in df.columns:
        own = own.fillna(df["minutes_estimate"])
    return pd.to_numeric(own, errors="coerce")


def what_blocks(df: pd.DataFrame, avoid: Sequence[str] = (), diets: Sequence[str] = (), vegetarian: bool = False,
                vegan: bool = False, max_minutes: float | None = None,
                min_protein_g: float | None = None) -> list[dict[str, object]]:
    """When nothing fits: for each of the user's choices, how many recipes would fit without that one choice, most
    first (the app offers to drop it). A quick count on the stored flags and diet columns, before the safety
    re-check, so it says where recipes are, not that they are safe: whatever is shown next is checked again.
    Each choice is counted the way baseline_recommend filters it: every name in `avoid` is a stored column that
    must be False, "vegan" included (the choice "vegan recipes only" is the `vegan` argument).

    Returns:
        One {"kind", "choice", "recipes"} per choice; kind is "avoid", "diet", "vegetarian", "vegan", "time" or
        "protein".
    """
    plausible = df["nutrition_plausible"].astype("boolean").fillna(False) if "nutrition_plausible" in df else True
    masks: list[tuple[str, str, pd.Series]] = []
    for flag in avoid:
        if flag in df.columns:
            masks.append(("avoid", flag, _is(df, flag, False)))
    for diet in diets:
        if diet in df.columns:
            masks.append(("diet", diet, _fits(df, diet)))
    if vegetarian:
        masks.append(("vegetarian", "vegetarian", df["vegetarian"] == True))   # a nullable column: == True, not truthiness
    if vegan:
        masks.append(("vegan", "vegan", df["vegan"] == True))
    if max_minutes is not None:
        masks.append(("time", f"{max_minutes:g}", recipe_minutes(df) <= max_minutes))
    if min_protein_g is not None and "protein_g" in df.columns:
        masks.append(("protein", f"{min_protein_g:g}", df["protein_g"] >= min_protein_g))
    counts = []
    for i, (kind, choice, _) in enumerate(masks):
        keep = pd.Series(plausible, index=df.index)
        for j, (_, _, mask) in enumerate(masks):
            if j != i:
                keep &= mask.fillna(False)
        counts.append((int(keep.sum()), kind, choice))
    counts.sort(key=lambda c: -c[0])
    return [{"kind": kind, "choice": choice, "recipes": n} for n, kind, choice in counts]


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
    # recipe_text decodes disguised and foreign words, as the safety gate (check_recipe) and the flags do
    text = recipe_text(row["ingredient_list"], row["recipe_name"])
    # Never served, whatever the user asked for (policy P24)
    if make_flag(text, *FLAG_RULES["contains_pet_meat"]):
        return False
    for diet in diets:
        flags = pd.DataFrame([{column: keyword_flag(text, column) for column in diet_flags_needed(diet)}])
        if not meets_diet(flags, diet).iloc[0]:
            return False
    for flag in avoid:
        if flag == "vegan":
            if not make_flag(text, ANIMAL_KEYWORDS, ANIMAL_EXCEPTIONS):
                return False
            continue

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
    skip: Sequence[str] = (),
    max_minutes: float | None = None,
    min_protein_g: float | None = None,
    sort_by: str = "calories",
) -> pd.DataFrame:
    """Recommend recipes with simple rules (the Week 6 baseline model).

    Filters by cuisine, dietary flags and diet profiles (the stored columns), keeps recipes with
    plausible listed nutrition, ranks them by distance to the calorie target,
    and re-checks the candidates with the safety filter, best first, until `top_n` pass.
    A diet with no stored column in `df` is checked by the safety filter alone.

    The optional filters and orders (the app's "Under 30 min", "High protein" and "Sort by") only narrow or reorder
    what passed; every recipe returned still passes the same safety filter.

    Args:
        df: The preprocessed recipe table.
        cuisine_family: One of the five families, or None for all.
        calorie_target: Desired calories per serving.
        vegetarian_only: Restrict to vegetarian recipes.
        vegan_only: Restrict to vegan recipes.
        gluten_free: Restrict to gluten-free recipes.
        avoid: Flag columns to exclude, for example ("contains_pork", "contains_alcohol").
        diets: Diet profiles to require, for example ("halal_friendly",).
        skip: Foods the user doesn't eat (not allergies), left out by name: a recipe that mentions one in its
            ingredients or its name is dropped (preferences.py; never a safety check).
        top_n: Number of recommendations.
        max_minutes: Keep recipes that take at most this long: the recipe's own time, or the estimate
            (minutes_estimate) when it gives none; a recipe with neither is left out.
        min_protein_g: Keep recipes with at least this much protein per serving.
        sort_by: "calories" (closest to the target, the default), "quickest" or "protein" (most first). The other
            two orders look only at recipes within 20% of the calorie target (at least 100 kcal either way).

    Returns:
        The top recipes with a 'calorie_distance' column; no rows (same columns) when
        nothing matches.

    Raises:
        ValueError: If `calorie_target` is not positive, `sort_by` is not one of the three orders, or
            `cuisine_family` is not one of the families in `df` (case is ignored: "asian" means "Asian").
    """
    require_columns(df, ["recipe_name", "ingredient_list", "cuisine_family", "calories_per_serving",
                         "nutrition_plausible", "vegetarian", "vegan", "contains_gluten"],
                    "baseline_recommend")
    if not calorie_target > 0:
        raise ValueError(f"calorie_target must be a positive number of kcal, got {calorie_target!r}")
    if sort_by not in SORT_ORDERS:
        raise ValueError(f"sort_by must be one of {SORT_ORDERS}, got {sort_by!r}")
    # Each filter is a mask over df; the rows are copied once, after every mask is known
    keep = _fits(df, "nutrition_plausible")   # Step 3 of the baseline: plausible nutrition data only

    # Step 1: Filter by cuisine family (an unknown name is an error, not "no recipes")
    if cuisine_family:
        families = {str(f).lower(): f for f in df["cuisine_family"].dropna().unique()}
        if str(cuisine_family).strip().lower() not in families:
            raise ValueError(f"unknown cuisine_family {cuisine_family!r}; one of {sorted(families.values())}")
        keep &= (df["cuisine_family"] == families[str(cuisine_family).strip().lower()]).fillna(False).astype(bool)

    # Step 2: Apply dietary flags and the stored diet columns
    if vegetarian_only:
        keep &= _is(df, "vegetarian", True)
    if vegan_only:
        keep &= _is(df, "vegan", True)
    if gluten_free:
        keep &= _is(df, "contains_gluten", False)
    for flag in avoid:
        if flag in df.columns:
            keep &= _is(df, flag, False)
    # Without this, a strict diet (Jain, Ital) found nothing: almost none of the best-ranked recipes fit it,
    # and the safety filter only read the first top_n * 20. The safety filter still re-checks every result.
    for diet in diets:
        if diet in df.columns:
            keep &= _fits(df, diet)

    # Step 3b: The optional time and protein filters
    if max_minutes is not None:
        keep &= (recipe_minutes(df) <= max_minutes).fillna(False).astype(bool)
    if min_protein_g is not None and "protein_g" in df.columns:
        keep &= (df["protein_g"] >= min_protein_g).fillna(False).astype(bool)

    results = drop_skipped(df[keep], skip)

    if results.empty:
        logger.info("No recipes matched the given filters.")
        return results.assign(calorie_distance=pd.Series(dtype=float))

    # Step 4: Rank by distance to calorie target (or, near the target, by time or protein)
    results = results.assign(calorie_distance=(results["calories_per_serving"] - calorie_target).abs())
    results = results.sort_values("calorie_distance", kind="stable")
    if sort_by != "calories":
        near = results[results["calorie_distance"] <= max(100.0, 0.2 * calorie_target)]
        if sort_by == "quickest":
            results = near.assign(_key=recipe_minutes(near)).sort_values("_key", kind="stable").drop(columns="_key")
        elif "protein_g" in near.columns:
            results = near.sort_values("protein_g", ascending=False, kind="stable")

    # Step 5: Safety filter, best candidates first, a chunk at a time until top_n pass
    all_avoid = tuple(avoid) + (("contains_gluten",) if gluten_free else ())
    chunk = max(1, top_n * 20)
    limit = max(MAX_SAFETY_CHECKS, chunk)
    safe_parts: list[pd.DataFrame] = []
    found = checked = 0
    while found < top_n and checked < min(len(results), limit):
        candidates = results.iloc[checked:min(checked + chunk, limit)]
        passed = candidates.apply(
            lambda r: passes_safety_filter(r, all_avoid, vegetarian_only, vegan_only, diets), axis=1).astype(bool)
        safe_parts.append(candidates[passed])
        found += int(passed.sum())
        checked += len(candidates)
    if found < checked:
        logger.info("safety filter removed %d of %d candidates", checked - found, checked)
    if found < top_n and checked < len(results):
        logger.warning("safety filter stopped after %d of %d candidates with %d of %d found",
                       checked, len(results), found, top_n)

    return pd.concat(safe_parts).head(top_n) if safe_parts else results.head(0)


def why_it_fits(avoid: Iterable[str] = (), diets: Iterable[str] = (), vegetarian: bool = False,
                vegan: bool = False) -> str:
    """The checks a recommended recipe passed, in plain words, for the card ("Checked for you: no peanut, no tree
    nut, halal-friendly ingredients, vegetarian"). It only restates the filters baseline_recommend applied; diet
    labels say "...-friendly ingredients", never the diet itself (a screen, not a certification).

    Returns:
        The line, or "" when the profile asks for nothing.
    """
    parts = fit_checks(avoid, diets, vegetarian, vegan)
    return "Checked for you: " + ", ".join(parts) if parts else ""


def fit_checks(avoid: Iterable[str] = (), diets: Iterable[str] = (), vegetarian: bool = False,
               vegan: bool = False) -> list[str]:
    """Each check a recommended recipe passed, one short item each, for the card's tick list ("no peanut",
    "halal-friendly ingredients", "vegetarian"). Like why_it_fits, it only restates the filters baseline_recommend
    applied."""
    parts = ["no " + flag.removeprefix("contains_").replace("_", " ") for flag in avoid]
    parts += [diet.removesuffix("_friendly").replace("_", " ") + "-friendly ingredients"
              if diet.endswith("_friendly") else diet.replace("_", " ") for diet in diets]
    parts += ["vegan"] if vegan else ["vegetarian"] if vegetarian else []
    return parts


def within_calories(calories: object, target: object) -> bool:
    """True when a recipe's calories per serving are known and at most the user's target per meal (policy,
    med27-coder's UX brief 2026-11-11: "Within your calorie target" is shown only then; never a guess)."""
    try:
        kcal, goal = float(calories), float(target)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return goal > 0 and 0 < kcal <= goal   # NaN fails both comparisons
