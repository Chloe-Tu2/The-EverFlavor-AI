"""Diet profiles (5.4.7): each diet is a rule over the restriction flags."""
from __future__ import annotations

import pandas as pd

from .checks import require_columns

__all__ = [
    "DIET_COLUMNS",
    "DIET_PROFILES",
    "NUTRITION_DIETS",
    "add_diet_profiles",
    "describe_diet_rules",
    "diet_flags_needed",
    "meets_diet",
]


DIET_PROFILES: dict[str, dict[str, list]] = {
    "halal_friendly" : {"without": ["contains_pork", "contains_alcohol", "contains_gelatin"]},
    "kosher_friendly": {"without": ["contains_pork", "contains_shellfish", "contains_gelatin"],
                        "not_together": [("contains_meat", "contains_dairy")]},
    "pescatarian"    : {"without": ["contains_meat"]},
    "no_beef"        : {"without": ["contains_beef", "contains_gelatin"]},
    "jain_friendly"  : {"require": ["vegetarian"],
                        "without": ["contains_egg", "contains_honey", "contains_alcohol",
                                    "contains_root_vegetable", "contains_allium"]},
}
# Nutrition-based diets: (column, highest value per serving). Only listed,
# plausible nutrition can qualify; estimates from 5.8 never do.
NUTRITION_DIETS: dict[str, tuple[str, int]] = {
    "lower_sodium": ("sodium_mg", 600),
    "low_carb"    : ("carbs_g", 15),
}
DIET_COLUMNS = list(DIET_PROFILES) + list(NUTRITION_DIETS)


def meets_diet(flags: pd.DataFrame, diet: str) -> pd.Series:
    """Check which recipes fit a diet from DIET_PROFILES.

    Args:
        flags: One row per recipe, with at least the flag columns the diet uses.
        diet: A key of DIET_PROFILES, for example "halal_friendly".

    Returns:
        True/False per recipe, with the same index as `flags`.

    Raises:
        ValueError: If `diet` is unknown or a needed flag column is missing.
    """
    if diet not in DIET_PROFILES:
        raise ValueError(f"Unknown diet '{diet}'. Known diets: {', '.join(DIET_PROFILES)}.")
    require_columns(flags, sorted(diet_flags_needed(diet)), "meets_diet")
    rule = DIET_PROFILES[diet]
    fits = pd.Series(True, index=flags.index)
    for column in rule.get("require", []):
        fits &= flags[column].astype(bool)
    for column in rule.get("without", []):
        fits &= ~flags[column].astype(bool)
    for first, second in rule.get("not_together", []):
        fits &= ~(flags[first].astype(bool) & flags[second].astype(bool))
    return fits


def diet_flags_needed(diet: str) -> set[str]:
    """Return the flag columns a diet's rule looks at."""
    rule = DIET_PROFILES[diet]
    return ({*rule.get("require", []), *rule.get("without", [])}
            | {column for pair in rule.get("not_together", []) for column in pair})


def add_diet_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """Add one true/false column per diet (DIET_PROFILES and NUTRITION_DIETS).

    Nutrition-based diets only count recipes whose listed nutrition is plausible.

    Args:
        df: Recipes with the flag columns, `nutrition_plausible` and the nutrition columns.

    Returns:
        A copy of `df` with the diet columns added; `df` itself is not changed.

    Raises:
        ValueError: If a needed column is missing.
    """
    require_columns(df, ["nutrition_plausible", *(column for column, _ in NUTRITION_DIETS.values())],
                    "add_diet_profiles")
    df = df.copy()
    for diet in DIET_PROFILES:
        df[diet] = meets_diet(df, diet)
    for diet, (column, limit) in NUTRITION_DIETS.items():
        df[diet] = df["nutrition_plausible"] & (df[column] <= limit)
    return df


def describe_diet_rules() -> list[str]:
    """Return one readable line per diet rule, for printing."""
    lines = []
    for diet, rule in DIET_PROFILES.items():
        parts = [f"no {', '.join(c.replace('contains_', '') for c in rule.get('without', []))}"]
        parts += [f"must be {c}" for c in rule.get("require", [])]
        parts += [f"not {a.replace('contains_', '')} with {b.replace('contains_', '')}"
                  for a, b in rule.get("not_together", [])]
        lines.append(f"{diet:16s}: {'; '.join(parts)}")
    for diet, (column, limit) in NUTRITION_DIETS.items():
        lines.append(f"{diet:16s}: {column} at most {limit} per serving (listed nutrition only)")
    return lines
