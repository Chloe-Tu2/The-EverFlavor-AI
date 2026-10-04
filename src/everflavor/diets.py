"""Diet profiles (5.4.7): each diet is a rule over the restriction flags."""
import pandas as pd

DIET_PROFILES = {
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
NUTRITION_DIETS = {
    "lower_sodium": ("sodium_mg", 600),
    "low_carb"    : ("carbs_g", 15),
}
DIET_COLUMNS = list(DIET_PROFILES) + list(NUTRITION_DIETS)


def meets_diet(flags, diet):
    """For a dataframe of flag columns, True where the recipe fits the diet."""
    rule = DIET_PROFILES[diet]
    fits = pd.Series(True, index=flags.index)
    for column in rule.get("require", []):
        fits &= flags[column].astype(bool)
    for column in rule.get("without", []):
        fits &= ~flags[column].astype(bool)
    for first, second in rule.get("not_together", []):
        fits &= ~(flags[first].astype(bool) & flags[second].astype(bool))
    return fits


def diet_flags_needed(diet):
    """The flag columns a diet rule looks at."""
    rule = DIET_PROFILES[diet]
    return ({*rule.get("require", []), *rule.get("without", [])}
            | {column for pair in rule.get("not_together", []) for column in pair})


def add_diet_profiles(df):
    """Add one true/false column per diet."""
    for diet in DIET_PROFILES:
        df[diet] = meets_diet(df, diet)
    for diet, (column, limit) in NUTRITION_DIETS.items():
        df[diet] = df["nutrition_plausible"] & (df[column] <= limit)
    return df


def describe_diet_rules():
    """One readable line per diet rule."""
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
