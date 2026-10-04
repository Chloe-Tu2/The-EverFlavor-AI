"""Cooking methods and cooking fats (notebook 02): reference table, rule labels,
the checks that compare them with Food.com's own tags, and how much alcohol is
left after cooking.

Safety rule: these labels can add a caution (for example "frying oil not
stated") but never clear a restriction flag. Fat guesses are recommendations
only.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

from .checks import require_columns
from .flags import make_flag
from .parsing import parse_list_string
from .progress import MIN_ROWS, progress_bar

__all__ = [
    "ALCOHOL_ADDED_AT_END",
    "ALCOHOL_FLAMBE",
    "ALCOHOL_NO_HEAT",
    "ALCOHOL_RETENTION_BY_MINUTES",
    "COOKING_METHODS",
    "FAT_EXCEPTIONS",
    "FAT_KEYWORDS",
    "FAT_NUTRIENTS",
    "FLAMBE_PATTERN",
    "FOODCOM_METHOD_TAGS",
    "FRIED_DISHES",
    "GENERIC_FRY",
    "GENERIC_OILS",
    "HEATED_METHODS",
    "HEAT_WORDS",
    "METHOD_PATTERNS",
    "NOT_FRIED_NAME",
    "REFERENCE_FILE",
    "SPECIFIC_FATS",
    "add_alcohol_estimate",
    "add_cooking_labels",
    "alcohol_left_range",
    "alcohol_retention",
    "fat_reference",
    "fats_from_ingredients",
    "method_label_agreement",
    "methods_from_instructions",
    "methods_from_tags",
    "top_fats_by_group",
]

REFERENCE_FILE = Path("data/reference/cooking_fats.csv")

# ------------------------------------------------------------------ cooking methods
COOKING_METHODS = ["deep_fry", "pan_fry", "stir_fry", "bake_roast", "grill_broil", "boil_simmer",
                   "steam", "slow_cook", "pressure_cook", "microwave", "smoke", "no_cook"]

# Words in the instructions that show each method (no_cook is worked out from HEAT_WORDS)
METHOD_PATTERNS = {
    "deep_fry"     : r"\bdeep[- ]?fr(?:y|ied|ies|ying|yer)\b|\bfryer\b|\b(?:inches|inch|in\.|cm) (?:of )?(?:hot )?oil\b"
                     r"|\boil (?:should be |to |reaches |is )?(?:about |approximately |at )?3[4-9]\d\b"
                     r"|\bfry (?:in batches|until golden)\b|\b(?:into|in) (?:the )?hot (?:oil|fat|lard|shortening)\b"
                     r"|\bto a depth of\b|\bdrop (?:by )?(?:heaping )?(?:table|tea)?spoon(?:ful)?s? into\b",
    "pan_fry"      : r"\bpan[- ]?fr(?:y|ied|ying)\b|\bsaut[eé](?:e|ed|ing|s)?\b|\bshallow[- ]?fr\w*",
    "stir_fry"     : r"\bstir[- ]?fr(?:y|ied|ies|ying)\b|\bwok\b",
    "bake_roast"   : r"\bbak(?:e|ed|es|ing)\b|\broast(?:ed|ing|s)?\b|\boven\b|\bbread (?:machine|maker)\b",
    "grill_broil"  : r"\bgrill(?:ed|ing|s)?\b|\bbroil(?:ed|er|ing|s)?\b|\bbarbecue\w*|\bbbq\b|\bchar[- ]?grill\w*",
    "boil_simmer"  : r"\bboil(?:ed|ing|s)?\b|\bsimmer(?:ed|ing|s)?\b|\bpoach(?:ed|ing)?\b|\bblanch(?:ed|ing)?\b",
    "steam"        : r"\bsteam(?:ed|ing|er)?\b",
    "slow_cook"    : r"\bslow[- ]?cook\w*|\bcrock[- ]?pot\b",
    "pressure_cook": r"\bpressure[- ]?cook\w*|\binstant ?pot\b",
    "microwave"    : r"\bmicrowav\w*",
    "smoke"        : r"\bsmoker\b|\bwood chips\b|\bsmoke (?:for|at|until|over)\b",
}
# Plain "fry" or "skillet": pan-frying, unless the recipe is already deep-fried or stir-fried
GENERIC_FRY = r"\bfry\b|\bfried\b|\bfrying\b|\bskillet\b"
# Any of these means the recipe is heated, so it is not "no_cook"
HEAT_WORDS = (r"\bheat\w*|\bcook\w*|\bwarm\w*|\btoast\w*|\bmelt\w*|\bbrown(?:ed|ing)?\b|\bsear\w*|\bfry\b"
              r"|\bfried\b|\bfrying\b|\bscald\w*|\bcaramel\w*|\bscramble\w*")
# Whole phrases that use a method word without the method ("baking soda" is not baking,
# "slits to let steam escape" is not steaming, "serve with steamed rice" is a side dish)
_METHOD_EXCEPTIONS = ["baking soda", "baking powder", "boiling water", "boiled water", "roasted red pepper",
                      "roasted peppers", "roasted garlic", "fried onions", "smoked paprika", "smoked salmon",
                      "steamed rice", "the steam", "let steam", "allow steam", "steam to escape",
                      "steam can escape", "steam escape", "steam holes", "steam vents", "vent steam",
                      "steam rises", "steam-jacketed", "steaming hot", "until steaming", "serve with steamed",
                      "served with steamed", "serve over steamed", "served over steamed", "over steamed",
                      "on steamed", "with steamed"]
_METHOD_EXCEPTION_PATTERN = re.compile(r"\b(?:" + "|".join(map(re.escape, _METHOD_EXCEPTIONS)) + r")\b")

# Food.com tags (added by the person who posted the recipe) that name a method.
# "stove-top" is left out: it covers frying, boiling and simmering alike.
FOODCOM_METHOD_TAGS = {
    "deep-fry": "deep_fry", "stir-fry": "stir_fry",
    "oven": "bake_roast", "baking": "bake_roast", "roast": "bake_roast",
    "grilling": "grill_broil", "broil": "grill_broil", "barbecue": "grill_broil",
    "steam": "steam", "crock-pot-slow-cooker": "slow_cook", "pressure-cooker": "pressure_cook",
    "microwave": "microwave", "smoker": "smoke", "no-cook": "no_cook",
}

# Names that say the dish is fried in fat (deep, shallow or stir-fried), for recipes without instructions
FRIED_DISHES = ["fried", "deep fried", "deep-fried", "fritter", "tempura", "pakora", "bhaji", "samosa",
                "falafel", "churro", "doughnut", "donut", "beignet", "funnel cake", "hush puppy",
                "hush puppies", "tostone", "chicharron", "chicharrones", "katsu", "tonkatsu", "karaage",
                "croquette", "arancini", "egg roll", "puff puff", "akara", "mandazi", "vada", "jalebi",
                "zeppole", "french fries", "fries", "corn dog", "chimichanga", "koeksister", "chin chin",
                "bitterballen"]
# Names that look fried but are not fried in fat ("Oven-Fried Chicken", "Air Fryer Fries", "Baked Samosas")
NOT_FRIED_NAME = r"\b(?:oven|air)[- ]?fr(?:ied|y|yer|ies)\b|\bbaked\b|\bunfried\b"


def _clean_method_text(text: object) -> str:
    """Lowercase instructions with the _METHOD_EXCEPTIONS phrases removed."""
    if not isinstance(text, str):
        return ""
    return _METHOD_EXCEPTION_PATTERN.sub(" ", text.lower())


def methods_from_instructions(text: object) -> list[str]:
    """Find the cooking methods that a recipe's instructions describe.

    Args:
        text: The instructions; anything that is not text gives no methods.

    Returns:
        The methods in COOKING_METHODS order, for example ["pan_fry", "boil_simmer"].
        "no_cook" is returned when the instructions name no heat at all;
        an empty list when there are no instructions.
    """
    clean = _clean_method_text(text)
    if len(clean.strip()) < 20:
        return []
    found = [m for m, pattern in METHOD_PATTERNS.items() if re.search(pattern, clean)]
    if not {"deep_fry", "stir_fry"} & set(found) and re.search(GENERIC_FRY, clean):
        found.append("pan_fry")
    if not found and not re.search(HEAT_WORDS, clean):
        found = ["no_cook"]
    return [m for m in COOKING_METHODS if m in found]


def methods_from_tags(tags: object) -> list[str]:
    """Return the cooking methods named by Food.com tags (a list or its text form)."""
    names = {FOODCOM_METHOD_TAGS[t] for t in parse_list_string(tags) if t in FOODCOM_METHOD_TAGS}
    return [m for m in COOKING_METHODS if m in names]


# ------------------------------------------------------------------ cooking fats
# fat_id (as in data/reference/cooking_fats.csv) -> words in an ingredient name.
# Order matters: the first match wins, so specific names come before "butter" or "oil".
FAT_KEYWORDS = {
    "peanut_oil"     : ["peanut oil", "groundnut oil"],
    "sesame_oil"     : ["sesame oil", "gingelly oil"],
    "olive_oil"      : ["olive oil"],
    "canola_oil"     : ["canola oil", "rapeseed oil"],
    "soybean_oil"    : ["soybean oil", "soya oil", "soy oil"],
    "corn_oil"       : ["corn oil"],
    "sunflower_oil"  : ["sunflower oil", "sunflower seed oil"],
    "coconut_oil"    : ["coconut oil"],
    "palm_oil"       : ["palm oil", "red palm oil", "dende oil", "dendê oil"],
    "mustard_oil"    : ["mustard oil"],
    "avocado_oil"    : ["avocado oil"],
    "grapeseed_oil"  : ["grapeseed oil", "grape seed oil"],
    "rice_bran_oil"  : ["rice bran oil"],
    "cottonseed_oil" : ["cottonseed oil"],
    "safflower_oil"  : ["safflower oil"],
    "almond_oil"     : ["almond oil"],
    "walnut_oil"     : ["walnut oil"],
    "hazelnut_oil"   : ["hazelnut oil"],
    "vegetable_oil"  : ["vegetable oil", "salad oil", "corn and canola oil"],
    "cooking_spray"  : ["cooking spray", "nonstick cooking spray", "non-stick cooking spray", "pam"],
    "ghee"           : ["ghee", "clarified butter", "niter kibbeh", "niter kebbeh", "smen", "usli ghee"],
    "margarine"      : ["margarine", "oleo", "vegan butter", "plant butter", "plant-based butter"],
    "shortening"     : ["shortening", "crisco"],
    "lard"           : ["lard", "manteca", "pork fat"],
    "beef_tallow"    : ["tallow", "beef dripping", "beef drippings", "beef fat"],
    "suet"           : ["suet"],
    "bacon_fat"      : ["bacon fat", "bacon grease", "bacon dripping", "bacon drippings"],
    "chicken_fat"    : ["chicken fat", "schmaltz"],
    "duck_goose_fat" : ["duck fat", "goose fat"],
    "butter"         : ["butter"],
}
# Ingredient phrases that contain a fat word but are not that fat
FAT_EXCEPTIONS = ["peanut butter", "almond butter", "cashew butter", "nut butter", "seed butter",
                  "sunflower butter", "apple butter", "cocoa butter", "shea butter", "butter bean",
                  "butter lettuce", "butterhead", "butter flavor", "butter extract", "butter-flavored",
                  "butter flavored", "butter cracker", "butter cookie", "butterscotch", "pumpkin butter",
                  "oil-packed", "oil packed", "packed in oil", "in olive oil", "in oil", "chili oil",
                  "chile oil", "truffle oil", "fish oil", "orange oil", "lemon oil", "peppermint oil",
                  "oil of"]
# Ingredient names that say only "oil"
GENERIC_OILS = {"oil", "cooking oil", "frying oil", "oil for frying", "oil for deep frying",
                "oil for deep-frying", "neutral oil", "light oil", "oil for greasing", "deep frying oil",
                "deep-frying oil", "high heat oil", "flavorless oil", "mild oil"}
# Fats whose source is known; "vegetable oil" and "cooking spray" are blends,
# so they are known to be plant-based but not which plant
SPECIFIC_FATS = [f for f in FAT_KEYWORDS if f not in ("vegetable_oil", "cooking_spray")]


def fats_from_ingredients(ingredients: Iterable[object] | None) -> list[str]:
    """Return the cooking fats in an ingredient list, as fat_id values.

    Each ingredient gives at most one fat (the first FAT_KEYWORDS match, after
    removing FAT_EXCEPTIONS such as "peanut butter"). An ingredient that says
    only "oil" (GENERIC_OILS) gives "oil_unspecified".

    Args:
        ingredients: Normalized ingredient names, for example ["olive oil", "garlic"];
            None (a recipe without a list) gives [].

    Returns:
        fat_id values in the order found, each once; [] if there are none.
    """
    found = (_fat_of(str(item).lower().strip()) for item in (ingredients if ingredients is not None else []))
    return list(dict.fromkeys(f for f in found if f))


@cache
def _fat_of(name: str) -> str | None:
    """Return the fat_id of one lowercase ingredient name, or None (cached: names repeat a lot)."""
    if name in GENERIC_OILS:
        return "oil_unspecified"
    return next((fat_id for fat_id, keywords in FAT_KEYWORDS.items()
                 if make_flag(name, keywords, FAT_EXCEPTIONS)), None)


# ------------------------------------------------------------------ labels for the recipe table
def add_cooking_labels(df: pd.DataFrame, foodcom_tags: Mapping[str, object] | None = None) -> pd.DataFrame:
    """Add the rule-based cooking labels to the recipe table.

    New columns:
        methods_instructions: methods found in the instructions ([] if there are none)
        methods_tags: methods from Food.com tags ([] for other sources or untagged recipes)
        has_instructions: the recipe has instructions with enough text to check
        has_tags: the recipe has Food.com tags (it may still have no method tag)
        fried_by_name: the name says the dish is fried in fat (FRIED_DISHES, unless NOT_FRIED_NAME)
        cooking_fats: fat_id values from the ingredients
        fat_specific: a fat with a known source is listed (SPECIFIC_FATS)
        frying_fat_unknown: fried (by tags, instructions or name) but no specific fat listed

    Args:
        df: Recipes with 'recipe_id', 'recipe_name', 'ingredient_list' and 'instructions'.
        foodcom_tags: Food.com tags per recipe_id ("foodcom_<id>"), or None.

    Returns:
        A copy of `df` with the columns above; `df` itself is not changed.

    Raises:
        ValueError: If a needed column is missing.
    """
    require_columns(df, ["recipe_id", "recipe_name", "ingredient_list", "instructions"], "add_cooking_labels")
    df = df.copy()
    # Reading every recipe's steps is the slow part (about a minute for 290,000 recipes)
    steps = progress_bar(df["instructions"], "Cooking methods from the steps", show=len(df) >= MIN_ROWS)
    df["methods_instructions"] = pd.Series([methods_from_instructions(t) for t in steps], index=df.index,
                                           dtype=object)
    df["has_instructions"] = df["methods_instructions"].str.len() > 0
    tags = df["recipe_id"].map(foodcom_tags or {})
    df["has_tags"] = tags.notna()
    df["methods_tags"] = tags.apply(methods_from_tags)
    names = df["recipe_name"].fillna("").astype(str).str.lower()
    df["fried_by_name"] = names.apply(lambda n: make_flag(n, FRIED_DISHES)) & ~names.str.contains(NOT_FRIED_NAME)
    df["cooking_fats"] = df["ingredient_list"].apply(fats_from_ingredients)
    df["fat_specific"] = df["cooking_fats"].apply(lambda fats: any(f in SPECIFIC_FATS for f in fats))
    fried = (df["fried_by_name"]
             | df["methods_tags"].apply(lambda m: "deep_fry" in m)
             | df["methods_instructions"].apply(lambda m: "deep_fry" in m))
    df["frying_fat_unknown"] = fried & ~df["fat_specific"]
    return df


# ------------------------------------------------------------------ alcohol left after cooking
# USDA Table of Nutrient Retention Factors, Release 6 (2007): share of the alcohol
# still in the dish after baking or simmering with the alcohol stirred in, by minutes
ALCOHOL_RETENTION_BY_MINUTES = [(15, 0.40), (30, 0.35), (60, 0.25), (90, 0.20), (120, 0.10), (150, 0.05)]
ALCOHOL_ADDED_AT_END = 0.85    # added to boiling liquid and taken off the heat
ALCOHOL_FLAMBE = 0.75          # flamed
ALCOHOL_NO_HEAT = (0.70, 1.0)  # no heat: 70% after a night in the fridge, all of it when served at once
FLAMBE_PATTERN = r"\bflamb[eé]\w*|\bignite\w*|\bset (?:it )?alight\b|\bcarefully light\b"
HEATED_METHODS = [m for m in COOKING_METHODS if m != "no_cook"]


def alcohol_retention(minutes: float) -> float:
    """Return the USDA share of alcohol left after `minutes` of baking or simmering.

    Args:
        minutes: Cooking time; 15 minutes or less gives the 15-minute value,
            more than 2.5 hours the 2.5-hour value (5%).

    Returns:
        The share left, from 0.05 to 0.40.
    """
    for limit, share in ALCOHOL_RETENTION_BY_MINUTES:
        if minutes <= limit:
            return share
    return ALCOHOL_RETENTION_BY_MINUTES[-1][1]


def alcohol_left_range(methods: Iterable[str], instructions: object, minutes: float | None) -> tuple[float, float]:
    """Estimate how much of a recipe's alcohol is left after cooking, as a range.

    A recipe rarely says when the alcohol goes in, so the range runs from "added at
    the start and cooked the whole time" to "added at the end" (USDA retention
    factors). The recipe's time includes preparation, so the low end can be too low.

    Args:
        methods: Cooking methods (from the instructions or the tags).
        instructions: The steps, used to spot flambé; anything else is ignored.
        minutes: Total recipe time; missing (None or NaN) or 0 means unknown.

    Returns:
        (lowest share, highest share) of the alcohol left, between 0 and 1.
    """
    methods = set(methods)
    heated = bool(methods & set(HEATED_METHODS))
    if not heated:
        return ALCOHOL_NO_HEAT
    flambe = isinstance(instructions, str) and re.search(FLAMBE_PATTERN, instructions.lower()) is not None
    high = ALCOHOL_FLAMBE if flambe and methods <= {"pan_fry"} else ALCOHOL_ADDED_AT_END
    if minutes is not None and not pd.isna(minutes) and minutes > 0:
        low = alcohol_retention(minutes)
    else:
        low = ALCOHOL_RETENTION_BY_MINUTES[-1][1]
    return min(low, high), high


def add_alcohol_estimate(df: pd.DataFrame) -> pd.DataFrame:
    """Add alcohol_left_min and alcohol_left_max (shares) for recipes that contain alcohol.

    Information only: the estimate never clears contains_alcohol or
    contains_alcohol_extract, because for halal, pregnancy, children and people
    avoiding alcohol any amount can matter (policy P18).

    Args:
        df: Recipes after add_cooking_labels, with the alcohol flags, 'instructions' and 'minutes'.

    Returns:
        A copy of `df` with the two columns added (empty for recipes without alcohol).

    Raises:
        ValueError: If a needed column is missing.
    """
    needed = ["contains_alcohol", "contains_alcohol_extract", "methods_instructions", "methods_tags",
              "instructions", "minutes"]
    require_columns(df, needed, "add_alcohol_estimate")
    df = df.copy()
    has_alcohol = df["contains_alcohol"] | df["contains_alcohol_extract"]
    rows = df.loc[has_alcohol]
    minutes = pd.to_numeric(rows["minutes"], errors="coerce")
    ranges = pd.Series([alcohol_left_range([*from_text, *from_tags], text, time)
                        for from_text, from_tags, text, time in zip(rows["methods_instructions"], rows["methods_tags"],
                                                                    rows["instructions"], minutes)],
                       index=rows.index, dtype=object)
    df["alcohol_left_min"] = ranges.str[0].reindex(df.index).astype(float)
    df["alcohol_left_max"] = ranges.str[1].reindex(df.index).astype(float)
    return df


def method_label_agreement(df: pd.DataFrame) -> pd.DataFrame:
    """Compare instruction rules with Food.com tags, method by method.

    Only recipes that have both instructions and tags are counted. A missing
    tag does not prove a method is absent (tags are optional), so 'rule_finds_tag'
    (how many tagged recipes the rules also find) is the main check.

    Args:
        df: Output of add_cooking_labels.

    Returns:
        One row per method that Food.com can tag: 'tagged', 'rule', 'both',
        'rule_finds_tag' (both / tagged) and 'tag_confirms_rule' (both / rule).

    Raises:
        ValueError: If the label columns are missing.
    """
    require_columns(df, ["methods_instructions", "methods_tags", "has_instructions", "has_tags"],
                    "method_label_agreement")
    both_sources = df[df["has_instructions"] & df["has_tags"]]
    rows = []
    for method in dict.fromkeys(FOODCOM_METHOD_TAGS.values()):
        tagged = both_sources["methods_tags"].apply(lambda m, x=method: x in m)
        rule = both_sources["methods_instructions"].apply(lambda m, x=method: x in m)
        both = int((tagged & rule).sum())
        rows.append({"method": method, "tagged": int(tagged.sum()), "rule": int(rule.sum()), "both": both,
                     "rule_finds_tag": both / tagged.sum() if tagged.any() else np.nan,
                     "tag_confirms_rule": both / rule.sum() if rule.any() else np.nan})
    return pd.DataFrame(rows).set_index("method")


def top_fats_by_group(df: pd.DataFrame, group_col: str, top: int = 3, min_recipes: int = 50) -> pd.DataFrame:
    """Return the most-used specific fats per group (for example per cuisine family or country).

    Args:
        df: Output of add_cooking_labels.
        group_col: Column to group by.
        top: Fats kept per group.
        min_recipes: Groups with fewer recipes that name a specific fat are left out.

    Returns:
        One row per group: 'recipes_with_fat' and 'top_fats' (for example
        "olive_oil 46% | butter 15% | vegetable_oil 8%"), where each share is
        of the group's recipes that name a specific fat or a blend.

    Raises:
        ValueError: If a needed column is missing.
    """
    require_columns(df, [group_col, "cooking_fats"], "top_fats_by_group")
    rows = []
    for group, part in df.groupby(group_col):
        fats = part["cooking_fats"].apply(lambda f: [x for x in f if x != "oil_unspecified"])
        named = fats[fats.str.len() > 0]
        if len(named) < min_recipes:
            continue
        shares = named.explode().value_counts() / len(named)
        rows.append({group_col: group, "recipes_with_fat": len(named),
                     "top_fats": " | ".join(f"{f} {s:.0%}" for f, s in shares.head(top).items())})
    # Name the columns, so a result with no group (all too small) is an empty table, not an error
    table = pd.DataFrame(rows, columns=[group_col, "recipes_with_fat", "top_fats"])
    return table.sort_values("recipes_with_fat", ascending=False).reset_index(drop=True)


# ------------------------------------------------------------------ reference table
# USDA nutrient name -> column, read with sources.usda_table(..., nutrients=FAT_NUTRIENTS)
FAT_NUTRIENTS = {"Fatty acids, total saturated": "saturated_g_100g",
                 "Fatty acids, total monounsaturated": "mono_g_100g",
                 "Fatty acids, total polyunsaturated": "poly_g_100g"}


def fat_reference(reference: pd.DataFrame, usda: pd.DataFrame | None = None) -> pd.DataFrame:
    """Join the cooking-fat reference table with its USDA fat breakdown.

    Args:
        reference: data/reference/cooking_fats.csv.
        usda: SR Legacy foods with 'fdc_id' and the FAT_NUTRIENTS columns, or
            None to return the reference table unchanged.

    Returns:
        A copy of `reference`, plus 'usda_description' and the FAT_NUTRIENTS
        columns (grams per 100 g) when `usda` is given.

    Raises:
        ValueError: If a needed column is missing, or a fat_id is repeated.
    """
    require_columns(reference, ["fat_id", "usda_fdc_id"], "fat_reference")
    if reference["fat_id"].duplicated().any():
        repeated = reference.loc[reference["fat_id"].duplicated(), "fat_id"].tolist()
        raise ValueError(f"fat_reference: repeated fat_id {repeated}")
    out = reference.copy()
    if usda is None:
        return out
    require_columns(usda, ["fdc_id", "description", *FAT_NUTRIENTS.values()], "fat_reference")
    usda_part = (usda[["fdc_id", "description", *FAT_NUTRIENTS.values()]]
                 .rename(columns={"fdc_id": "usda_fdc_id", "description": "usda_description"}))
    out["usda_fdc_id"] = pd.to_numeric(out["usda_fdc_id"], errors="coerce").astype("Int64")
    usda_part["usda_fdc_id"] = usda_part["usda_fdc_id"].astype("Int64")
    # One USDA row per food, so a food listed twice cannot repeat a fat in the table
    usda_part = usda_part.drop_duplicates("usda_fdc_id")
    return out.merge(usda_part, on="usda_fdc_id", how="left")
