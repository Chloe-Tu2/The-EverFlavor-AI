"""Diet profiles (5.4.7): each diet is a rule over the restriction flags."""
from __future__ import annotations

import pandas as pd

from .checks import require_columns

__all__ = [
    "ALLERGENS_NOT_FLAGGED",
    "ALLERGEN_SETS",
    "DIET_COLUMNS",
    "DIET_PROFILES",
    "NUTRITION_DIETS",
    "add_diet_profiles",
    "describe_diet_rules",
    "diet_flags_needed",
    "meets_diet",
]


DIET_PROFILES: dict[str, dict[str, list]] = {
    # Policy P18 (approved): alcohol-based flavor extracts, insect carmine and rennet named without halal
    # sourcing are not halal-friendly; shrimp and molluscs are
    "halal_friendly" : {"without": ["contains_pork", "contains_alcohol", "contains_gelatin", "contains_pet_meat",
                                    "contains_alcohol_extract", "contains_carmine", "contains_rennet"]},
    # Fish without fins and scales, rabbit, horse ... and insect-based carmine are not kosher (P11)
    "kosher_friendly": {"without": ["contains_pork", "contains_shellfish", "contains_gelatin",
                                    "contains_scaleless_fish", "contains_unclean_meat", "contains_carmine",
                                    "contains_pet_meat"],
                        "not_together": [("contains_meat", "contains_dairy")]},
    "pescatarian"    : {"without": ["contains_meat"]},
    "no_beef"        : {"without": ["contains_beef", "contains_gelatin"]},
    "jain_friendly"  : {"require": ["vegetarian"],
                        "without": ["contains_egg", "contains_honey", "contains_alcohol",
                                    "contains_root_vegetable", "contains_allium"]},
    # --- More religious and cultural diets ---
    # Common in India: vegetarian without egg
    "lacto_vegetarian": {"require": ["vegetarian"], "without": ["contains_egg"]},
    # Vaishnava, ISKCON and Swaminarayan practice: no egg, onion, garlic or mushrooms, no alcohol
    "vaishnava_friendly": {"require": ["vegetarian"],
                           "without": ["contains_egg", "contains_allium", "contains_mushroom", "contains_alcohol"]},
    # Mahayana Buddhist vegetarian (China, Korea, Vietnam, Japan): no egg, no five pungent plants
    # (garlic, onion, leek, chives, asafoetida), no alcohol
    "buddhist_vegetarian": {"require": ["vegetarian"],
                            "without": ["contains_egg", "contains_allium", "contains_asafoetida",
                                        "contains_alcohol"]},
    # Orthodox Christian and Ethiopian / Eritrean Orthodox fasting days: no meat, fish, dairy or egg;
    # shellfish is allowed (stricter days also leave out oil and wine)
    "orthodox_fasting": {"without": ["contains_meat", "contains_fish", "contains_dairy", "contains_egg"]},
    # Seventh-day Adventist "clean" foods: no pork, shellfish, scaleless fish or other unclean meat,
    # no alcohol, coffee or tea
    "adventist_friendly": {"without": ["contains_pork", "contains_shellfish", "contains_scaleless_fish",
                                       "contains_unclean_meat", "contains_pet_meat", "contains_alcohol",
                                       "contains_coffee_or_tea"]},
    # Latter-day Saints: no alcohol, coffee or tea
    "lds_friendly"   : {"without": ["contains_alcohol", "contains_coffee_or_tea"]},
    # Rastafari Ital: plant-based, no alcohol, no added salt
    "ital_friendly"  : {"require": ["vegan"], "without": ["contains_alcohol", "contains_added_salt"]},
    # --- Medical screens (policy P17): ingredients to avoid, never medical advice ---
    # Alpha-gal syndrome (CDC): mammal meat and gelatin; some people must also avoid dairy
    "alpha_gal_friendly": {"without": ["contains_red_meat", "contains_gelatin"]},
    # Pregnancy (FDA / CDC): alcohol, high-mercury fish, raw animal foods, soft cheeses
    "pregnancy_friendly": {"without": ["contains_alcohol", "contains_high_mercury_fish", "contains_raw_animal",
                                       "contains_soft_cheese"]},
    # G6PD deficiency: fava beans
    "g6pd_friendly"  : {"without": ["contains_fava"]},
    "gout_friendly"  : {"without": ["contains_high_purine"]},
    # MAOI medicines
    "low_tyramine"   : {"without": ["contains_high_tyramine"]},
    "nightshade_free": {"without": ["contains_nightshade"]},
}

# Allergens that must be labeled, by country or region, as our flags. A flag can be broader than
# the law (gluten for wheat, tree nuts for walnut, poultry for chicken): the safe direction.
ALLERGEN_SETS: dict[str, list[str]] = {
    # FDA: the 9 major allergens (FALCPA, FASTER Act); "shellfish" there means crustaceans
    "US": ["contains_dairy", "contains_egg", "contains_fish", "contains_crustacean", "contains_tree_nut",
           "contains_peanut", "contains_gluten", "contains_soy", "contains_sesame"],
    # EU Regulation 1169/2011, Annex II (the UK keeps the same 14)
    "EU_UK": ["contains_gluten", "contains_crustacean", "contains_egg", "contains_fish", "contains_peanut",
              "contains_soy", "contains_dairy", "contains_tree_nut", "contains_celery", "contains_mustard",
              "contains_sesame", "contains_sulfites", "contains_lupin", "contains_mollusc"],
    # Health Canada priority allergens
    "Canada": ["contains_peanut", "contains_tree_nut", "contains_sesame", "contains_dairy", "contains_egg",
               "contains_fish", "contains_crustacean", "contains_mollusc", "contains_soy", "contains_gluten",
               "contains_mustard", "contains_sulfites"],
    # FSANZ (Food Standards Australia New Zealand)
    "Australia_NZ": ["contains_peanut", "contains_tree_nut", "contains_dairy", "contains_egg", "contains_sesame",
                     "contains_fish", "contains_crustacean", "contains_mollusc", "contains_soy", "contains_gluten",
                     "contains_lupin", "contains_sulfites"],
    # Japan, mandatory: wheat, buckwheat, egg, milk, peanut, shrimp, crab, walnut, cashew (2026)
    "Japan": ["contains_gluten", "contains_buckwheat", "contains_egg", "contains_dairy", "contains_peanut",
              "contains_crustacean", "contains_tree_nut"],
    # Japan, recommended: almond, macadamia, abalone, squid, salmon, mackerel, salmon roe, beef, pork,
    # chicken, sesame, soy, gelatin (and fruits listed in ALLERGENS_NOT_FLAGGED)
    "Japan_recommended": ["contains_tree_nut", "contains_mollusc", "contains_fish", "contains_beef",
                          "contains_pork", "contains_poultry", "contains_sesame", "contains_soy",
                          "contains_gelatin"],
    # South Korea (MFDS): egg, milk, buckwheat, peanut, soy, wheat, mackerel, crab, shrimp, pork, sulfites,
    # walnut, chicken, beef, squid, shellfish (oyster, abalone, mussel), pine nut (and peach, tomato)
    "South_Korea": ["contains_egg", "contains_dairy", "contains_buckwheat", "contains_peanut", "contains_soy",
                    "contains_gluten", "contains_fish", "contains_crustacean", "contains_pork",
                    "contains_sulfites", "contains_tree_nut", "contains_poultry", "contains_beef",
                    "contains_mollusc"],
}
# Allergens on those lists that have no flag yet
ALLERGENS_NOT_FLAGGED: dict[str, list[str]] = {
    "Japan_recommended": ["orange", "kiwi", "banana", "peach", "yam", "apple"],
    "South_Korea": ["peach", "tomato"],
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
    width = max(len(d) for d in DIET_COLUMNS)
    for diet, rule in DIET_PROFILES.items():
        without = [c.replace("contains_", "") for c in rule.get("without", [])]
        parts = [f"no {', '.join(without)}"] if without else []
        parts += [f"must be {c}" for c in rule.get("require", [])]
        parts += [f"not {a.replace('contains_', '')} with {b.replace('contains_', '')}"
                  for a, b in rule.get("not_together", [])]
        lines.append(f"{diet:{width}s}: {'; '.join(parts)}")
    for diet, (column, limit) in NUTRITION_DIETS.items():
        lines.append(f"{diet:{width}s}: {column} at most {limit} per serving (listed nutrition only)")
    return lines
