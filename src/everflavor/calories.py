"""Calorie calculator (Week 7, roadmap step 1): ingredient amounts -> grams -> USDA calories.

A recipe line such as "1 1/2 cups chopped onion" is split into an amount (1.5), a unit (cup)
and an ingredient (onion). Grams come from the unit itself (g, oz, lb ...) or from USDA SR
Legacy's own household weights for that food (1 cup chopped onion = 160 g, 1 large egg = 50 g).
Calories are grams x the food's kcal per 100 g, summed and divided by servings.

Every answer says how much of the recipe it could count: a line without an amount ("salt to
taste") or without a USDA match is listed, never silently counted as zero.
"""
from __future__ import annotations

import json
import re
import zipfile
from collections.abc import Mapping, Sequence
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

from .ingredients import normalize_ingredient
from .sources import USDA_DOWNLOADS, download_usda

__all__ = [
    "CATEGORY_G_PER_ML",
    "COUNT_WORDS",
    "DEFAULT_COUNT_GRAMS",
    "MASS_GRAMS",
    "NEGLIGIBLE",
    "UNIT_ALIASES",
    "VOLUME_ML",
    "calorie_accuracy",
    "grams_for",
    "parse_ingredient_line",
    "recipe_calories",
    "usda_portions",
]

# Grams in one mass unit
MASS_GRAMS = {"g": 1.0, "kg": 1000.0, "mg": 0.001, "oz": 28.3495, "lb": 453.592}
# Millilitres in one volume unit (US measures; a "pinch" is 1/16 tsp, a "dash" 1/8 tsp)
VOLUME_ML = {"ml": 1.0, "l": 1000.0, "tsp": 4.92892, "tbsp": 14.7868, "fl oz": 29.5735, "cup": 236.588,
             "pint": 473.176, "quart": 946.353, "gallon": 3785.41, "pinch": 0.308, "dash": 0.616}
# Spellings in recipes -> one unit name (longest first when matching, so "fl oz" beats "oz")
UNIT_ALIASES = {
    "g": "g", "gram": "g", "grams": "g", "gr": "g", "kg": "kg", "kilogram": "kg", "kilograms": "kg",
    "mg": "mg", "oz": "oz", "ounce": "oz", "ounces": "oz", "lb": "lb", "lbs": "lb", "pound": "lb",
    "pounds": "lb", "ml": "ml", "milliliter": "ml", "milliliters": "ml", "millilitre": "ml",
    "millilitres": "ml", "l": "l", "liter": "l", "liters": "l", "litre": "l", "litres": "l",
    "tsp": "tsp", "tsps": "tsp", "teaspoon": "tsp", "teaspoons": "tsp", "t": "tsp",
    "tbsp": "tbsp", "tbsps": "tbsp", "tbs": "tbsp", "tbl": "tbsp", "tablespoon": "tbsp",
    "tablespoons": "tbsp", "T": "tbsp", "fl oz": "fl oz", "fluid ounce": "fl oz", "fluid ounces": "fl oz",
    "c": "cup", "cup": "cup", "cups": "cup", "pint": "pint", "pints": "pint", "pt": "pint",
    "quart": "quart", "quarts": "quart", "qt": "quart", "gallon": "gallon", "gallons": "gallon",
    "pinch": "pinch", "pinches": "pinch", "dash": "dash", "dashes": "dash",
}
# Words for "one of the item"; USDA's own weight for the size is used ("2 large eggs")
COUNT_WORDS = {"large": "large", "medium": "medium", "small": "small", "whole": "each", "each": "each",
               "piece": "each", "pieces": "each", "clove": "clove", "cloves": "clove", "slice": "slice",
               "slices": "slice", "stalk": "stalk", "stalks": "stalk", "sprig": "sprig", "sprigs": "sprig",
               "leaf": "leaf", "leaves": "leaf", "can": "can", "cans": "can", "fillet": "fillet",
               "fillets": "fillet", "breast": "breast", "breasts": "breast", "head": "head", "heads": "head"}
# Typical grams per millilitre by USDA food category, for a cup or spoon of a food USDA gives no
# volume weight for (flour is about 0.55, not water's 1.0); an estimate, shown as "category density"
CATEGORY_G_PER_ML = {"Spices and Herbs": 0.5, "Cereal Grains and Pasta": 0.55, "Baked Products": 0.45,
                     "Nut and Seed Products": 0.55, "Sweets": 0.85, "Legumes and Legume Products": 0.8,
                     "Fats and Oils": 0.92, "Dairy and Egg Products": 1.03, "Beverages": 1.0,
                     "Fruits and Fruit Juices": 0.65, "Vegetables and Vegetable Products": 0.6,
                     "Soups, Sauces, and Gravies": 1.05, "Snacks": 0.4, "Breakfast Cereals": 0.3,
                     "Beef Products": 0.85, "Pork Products": 0.85, "Poultry Products": 0.85,
                     "Finfish and Shellfish Products": 0.85, "Sausages and Luncheon Meats": 0.85,
                     "Lamb, Veal, and Game Products": 0.85}
# Grams for one counted item when USDA gives none for that food (a US can is 14.5 oz)
DEFAULT_COUNT_GRAMS = {"can": 411.0}
# Ingredients that add no meaningful calories in recipe amounts, even with no amount given
# ("salt to taste"): counted as 0 kcal ("negligible"), not as a gap
NEGLIGIBLE = {"salt", "pepper", "black pepper", "white pepper", "salt and pepper", "water", "ice", "ice cube",
              "cold water", "boiling water", "warm water", "hot water", "kosher salt", "sea salt", "table salt",
              "baking soda", "cream of tartar", "food coloring", "cooking spray", "nonstick cooking spray"}
_UNICODE_FRACTIONS = {"½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4", "⅕": "1/5", "⅛": "1/8",
                      "⅜": "3/8", "⅝": "5/8", "⅞": "7/8", "⅙": "1/6", "⅚": "5/6"}
_NUMBER = r"\d+(?:\s+|-)\d+/\d+|\d+/\d+|\d+(?:\.\d+)?"   # mixed, then fraction, then whole
_AMOUNT = re.compile(rf"^\s*(?P<a>{_NUMBER}|an?\b)(?:\s*(?:-|to|or)\s*(?P<b>{_NUMBER}))?\s*", re.IGNORECASE)
# "1 (14 ounce) can tomatoes": the size in brackets is the amount of one can
_PACKAGE = re.compile(rf"^\(\s*(?P<n>{_NUMBER})\s*-?\s*(?P<u>[a-z. ]+?)\s*\)\s*", re.IGNORECASE)
_UNIT_WORDS = sorted(UNIT_ALIASES, key=len, reverse=True)
_PREP_WORDS = ("peeled|seeded|cored|pitted|trimmed|rinsed|drained|shredded|grated|chopped|minced|diced|sliced|"
               "crushed|cubed|halved|quartered|julienned|cooled|softened|melted|beaten|"
               "finely|coarsely|thinly|freshly|lightly|roughly")
# A weight written in brackets is the line's total: "1/2 cup (35g) breadcrumbs", "(about 2 pounds)"
_WRITTEN_WEIGHT = re.compile(r"\(\s*(?:about|approx\.?|approximately|~)?\s*(?P<n>\d+(?:\.\d+)?)\s*"
                             r"(?P<u>g|grams?|kg|oz|ounces?|lbs?|pounds?)\b", re.IGNORECASE)


def _number(text: str) -> float:
    """'1 1/2', '1-1/2', '3/4', '2.5' -> a float."""
    text = text.strip().replace("-", " ")
    return float(sum(Fraction(part) for part in text.split()))


def parse_ingredient_line(line: object) -> dict:
    """Split one recipe line into amount, unit and ingredient.

    Handles fractions ("1 1/2", "1-1/2", "½"), ranges ("2-3" and "2 to 3" give the middle),
    "a" / "an", abbreviations ("tbsp", "T", "c"), a package size in brackets
    ("1 (14 ounce) can tomatoes" = 14 oz) and size words ("2 large eggs").

    Returns:
        {"amount": float or None, "unit": a MASS_GRAMS / VOLUME_ML key, a COUNT_WORDS value or
        None, "ingredient": the normalized name ("" when none), "text": the original line}.
        amount is None when the line gives none ("salt to taste").
    """
    text = "" if line is None or (isinstance(line, float) and np.isnan(line)) else str(line)
    for symbol, fraction in _UNICODE_FRACTIONS.items():
        text = re.sub(rf"(\d)\s*{symbol}", rf"\1 {fraction}", text).replace(symbol, fraction)
    text = re.sub(r"(\d)\s*/\s*(\d)", r"\1/\2", text.replace("⁄", "/"))   # "1 ⁄ 2", "1 /2" -> "1/2"
    rest = text.strip()
    amount: float | None = None
    unit: str | None = None
    match = _AMOUNT.match(rest)
    if match and rest:
        first = 1.0 if match.group("a").lower() in ("a", "an") else _number(match.group("a"))
        amount = (first + _number(match.group("b"))) / 2 if match.group("b") else first
        rest = rest[match.end():]
        package = _PACKAGE.match(rest)
        if package:
            size_unit = UNIT_ALIASES.get(package.group("u").strip().rstrip(".").lower())
            if size_unit:
                amount *= _number(package.group("n"))
                unit = size_unit
                rest = re.sub(r"^(?:cans?|packages?|jars?|bottles?|cartons?|containers?|bags?|boxes?)\b\s*",
                              "", rest[package.end():], flags=re.IGNORECASE)
    if amount is not None and unit is None:
        for word in _UNIT_WORDS:
            hit = re.match(rf"{re.escape(word)}\.?(?=\s|$|,)", rest, flags=0 if word == "T" else re.IGNORECASE)
            if hit and (word != "t" or rest[:1] == "t"):
                unit = UNIT_ALIASES[word]
                rest = rest[hit.end():].lstrip(" .")
                break
    if amount is not None and unit is None:
        first_word = rest.split(" ", 1)[0].lower().strip(",")
        if first_word in COUNT_WORDS:
            unit = COUNT_WORDS[first_word]
            rest = rest[len(first_word):]
    written = _WRITTEN_WEIGHT.search(text)
    if written and amount is not None and unit not in MASS_GRAMS:
        amount, unit = float(written.group("n")), UNIT_ALIASES[written.group("u").lower()]
    rest = re.sub(r"^\s*of\s+", "", rest)
    # "salt to taste", "parsley for garnish", "nuts (optional)": the phrase is not part of the name
    rest = re.sub(r"\s*,?\s*\(?\b(?:to taste|as needed|if needed|optional|for (?:garnish|serving|drizzling|"
                  r"dusting|frying|greasing|the pan|topping)\b).*$", "", rest, flags=re.IGNORECASE)
    # "peeled and shredded carrots" is one ingredient, not "peeled" and "carrots"; words that change
    # the food ("cooked rice", "toasted almonds") are kept: USDA lists those foods separately
    rest = re.sub(rf"\b({_PREP_WORDS})\s*(?:,|and|&)\s*(?=(?:{_PREP_WORDS})\b)", r"\1 ", rest, flags=re.IGNORECASE)
    rest = re.sub(rf"^\s*(?:(?:{_PREP_WORDS})\b\s*,?\s*)+", "", rest, flags=re.IGNORECASE)
    names = normalize_ingredient(rest)
    return {"amount": amount, "unit": unit, "ingredient": names[0] if names else "", "text": text}


def usda_portions(usda_folder: str | Path) -> dict[int, dict[str, float]]:
    """USDA SR Legacy household weights: fdc_id -> {unit: grams for one unit}.

    Volume units missing for a food are filled from the ones it has (1 cup = 16 tbsp = 48 tsp
    = 8 fl oz), and "each" is the medium size, else large, else the first counted portion.
    """
    _, key = USDA_DOWNLOADS["sr_legacy"]
    with zipfile.ZipFile(download_usda("sr_legacy", usda_folder)) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".json"))
        foods = json.loads(archive.read(name))[key]
    table: dict[int, dict[str, float]] = {}
    for food in foods:
        units: dict[str, float] = {}
        for portion in food.get("foodPortions", []):
            grams, amount = portion.get("gramWeight"), portion.get("amount") or 1
            modifier = str(portion.get("modifier", "")).lower()
            word = modifier.split(",")[0].split("(")[0].strip()
            # "cup, chopped" -> cup; "large", "potato large (3 in dia)" -> large; "clove" -> clove
            unit = UNIT_ALIASES.get(word) or next((COUNT_WORDS[t] for t in re.findall(r"[a-z]+", word)
                                                   if t in COUNT_WORDS), None)
            if grams and unit and unit not in units:
                units[unit] = float(grams) / float(amount)
        cup_ml = next(((units[u] / VOLUME_ML[u]) for u in ("cup", "tbsp", "tsp", "fl oz") if u in units), None)
        if cup_ml:   # grams per ml for this food
            for u in ("cup", "tbsp", "tsp", "fl oz", "pint", "quart", "pinch", "dash", "ml", "l"):
                units.setdefault(u, cup_ml * VOLUME_ML[u])
        category = (food.get("foodCategory") or {}).get("description", "")
        if not cup_ml and category in CATEGORY_G_PER_ML:
            units["_g_per_ml"] = CATEGORY_G_PER_ML[category]   # used only for volumes, as an estimate
        each = next((units[u] for u in ("medium", "large", "small", "each", "piece") if u in units), None)
        if each:
            units.setdefault("each", each)
        table[int(food["fdcId"])] = units
    return table


def grams_for(amount: float | None, unit: str | None, fdc_id: int | None,
              portions: Mapping[int, Mapping[str, float]]) -> tuple[float | None, str]:
    """Grams for an amount of one food, and how they were found.

    Returns:
        (grams or None, method): "mass" (g, oz ...), "usda portion" (USDA's weight for that
        food and unit), "category density" or "water density" (a volume of a food USDA gives no
        volume weight for: a typical density for its category, else 1 g/ml; estimates),
        "standard size" (a can), or why it could not be done ("no amount", "no USDA weight for <unit>").
    """
    if amount is None:
        return None, "no amount"
    if unit in MASS_GRAMS:
        return amount * MASS_GRAMS[unit], "mass"
    food = portions.get(int(fdc_id), {}) if fdc_id is not None else {}
    # No unit ("1 shallot", "1 garlic clove"): one item, as USDA counts it for that food
    for option in [unit] if unit else ["each", "clove", "slice", "medium", "large"]:
        if option in food:
            return amount * food[option], "usda portion"
    if unit in ("large", "small", "medium") and "each" in food:
        return amount * food["each"], "usda portion"
    if unit in VOLUME_ML and "_g_per_ml" in food:
        return amount * VOLUME_ML[unit] * food["_g_per_ml"], "category density"
    if unit in VOLUME_ML:
        return amount * VOLUME_ML[unit], "water density"
    if unit in DEFAULT_COUNT_GRAMS:
        return amount * DEFAULT_COUNT_GRAMS[unit], "standard size"
    unit = unit or "each"
    return None, f"no USDA weight for {unit}"


def recipe_calories(lines: Sequence[object], servings: float | None, matches: Mapping[str, int],
                    kcal_100g: Mapping[int, float], portions: Mapping[int, Mapping[str, float]],
                    grams: Sequence[float | None] | None = None, names: Sequence[str | None] | None = None) -> dict:
    """Calories of a recipe from its ingredient lines.

    Args:
        lines: The recipe's ingredient lines as written ("2 large eggs").
        servings: Servings the recipe makes; missing or 0 gives totals only.
        matches: Normalized ingredient name -> USDA SR Legacy fdc_id (notebook 01's
            usda_ingredient_nutrition.csv, or nutrition.match_ingredients).
        kcal_100g: fdc_id -> kcal per 100 g.
        portions: usda_portions(...).
        grams: Known gram weights per line (Hugging Face lists them); None = parse the amounts.
        names: Clean ingredient names per line when the source gives them ("green cabbage");
            None = the name parsed from the line. Clean names match USDA foods more often.

    Returns:
        {"kcal_total", "kcal_per_serving" (None without servings), "counted_share" (share of
        lines with grams and a USDA match), "lines" (a table: text, ingredient, grams, method,
        fdc_id, kcal), "not_counted" (the lines left out, with why)}.
    """
    rows = []
    for i, line in enumerate(lines):
        parsed = parse_ingredient_line(line)
        if names is not None and names[i]:
            parsed["ingredient"] = (normalize_ingredient(names[i]) or [parsed["ingredient"]])[0]
        fdc = matches.get(parsed["ingredient"])
        known = grams[i] if grams is not None else None
        weight: float | None
        kcal: float | None
        if known is not None and not pd.isna(known):
            weight, method = float(known), "given"
        else:
            weight, method = grams_for(parsed["amount"], parsed["unit"], fdc, portions)
        if parsed["ingredient"] in NEGLIGIBLE:
            kcal, method = 0.0, "negligible"
        else:
            if fdc is None:
                method = "no USDA match" if parsed["ingredient"] else "no ingredient"
            kcal = (weight * kcal_100g[fdc] / 100 if weight is not None and fdc is not None and fdc in kcal_100g
                    else None)
        rows.append({"text": parsed["text"], "ingredient": parsed["ingredient"], "grams": weight,
                     "method": method, "fdc_id": fdc, "kcal": kcal})
    table = pd.DataFrame(rows, columns=["text", "ingredient", "grams", "method", "fdc_id", "kcal"])
    counted = table["kcal"].notna()
    total = float(table.loc[counted, "kcal"].sum())
    per_serving = total / servings if servings and not pd.isna(servings) and servings > 0 else None
    return {"kcal_total": round(total, 1), "kcal_per_serving": None if per_serving is None else round(per_serving, 1),
            "counted_share": round(float(counted.mean()), 3) if len(table) else 0.0,
            "lines": table, "not_counted": table.loc[~counted, ["text", "method"]].reset_index(drop=True)}


def calorie_accuracy(estimated: Sequence[float], reference: Sequence[float], tolerance: float = 0.05) -> dict:
    """How close calculated calories are to reference values (proposal success metric 1).

    Returns:
        {"n", "median_error" (relative), "within" (share within `tolerance`), "within_10pct"}.
        Pairs with a missing or non-positive reference are left out.
    """
    est, ref = np.asarray(estimated, dtype=float), np.asarray(reference, dtype=float)
    keep = np.isfinite(est) & np.isfinite(ref) & (ref > 0)
    err = np.abs(est[keep] - ref[keep]) / ref[keep]
    if not len(err):
        return {"n": 0, "median_error": None, "within": None, "within_10pct": None}
    return {"n": len(err), "median_error": round(float(np.median(err)), 4),
            "within": round(float((err <= tolerance).mean()), 3), "within_10pct": round(float((err <= 0.10).mean()), 3)}
