"""Ingredient names: cleaning and normalizing (5.4.4), used by the pipeline and the agents."""
from __future__ import annotations

import re
from collections.abc import Iterable
from functools import cache

import numpy as np

from .parsing import parse_list_string

__all__ = [
    "INGREDIENT_SYNONYMS",
    "IRREGULAR_PLURALS",
    "KEEP_AS_IS",
    "PREP_PATTERN",
    "QUANTITY_PATTERN",
    "SPLIT_INGREDIENTS",
    "UNIT_PATTERN",
    "UNIT_WORDS",
    "clean_ingredients",
    "hf_ingredient_foods",
    "ingredient_text",
    "ingredient_tokens",
    "normalize_ingredient",
    "normalize_ingredient_list",
    "singular",
    "unique_ingredients",
]


# Exact names that mean the same ingredient
INGREDIENT_SYNONYMS = {
    "garlic clove": "garlic", "clove garlic": "garlic", "large egg": "egg",
    "all-purpose flour": "flour", "all purpose flour": "flour", "plain flour": "flour",
    "kosher salt": "salt", "sea salt": "salt", "table salt": "salt",
    "granulated sugar": "sugar", "white sugar": "sugar",
    "unsalted butter": "butter", "salted butter": "butter",
    "extra virgin olive oil": "olive oil", "extra-virgin olive oil": "olive oil",
    "ground black pepper": "black pepper", "fresh ground black pepper": "black pepper",
    "freshly ground black pepper": "black pepper",
    "scallion": "green onion", "spring onion": "green onion",
    "courgette": "zucchini", "aubergine": "eggplant",
    "fresh cilantro": "cilantro", "fresh coriander": "cilantro", "coriander leaf": "cilantro",
    "garbanzo bean": "chickpea", "chick pea": "chickpea",
}
# Entries that are really two ingredients
SPLIT_INGREDIENTS = {
    "salt and pepper": ["salt", "pepper"],
    "salt & pepper": ["salt", "pepper"],
    "salt and black pepper": ["salt", "black pepper"],
    "salt and freshly ground black pepper": ["salt", "black pepper"],
}
# Leading quantities and units, as in CulinaryDB lines such as
# "1/2 cup grated parmesan cheese" or "2 cloves garlic, minced"
QUANTITY_PATTERN = re.compile(r"^(?:[\d½¼¾⅓⅔⅛]+(?:[./-][\d½¼¾⅓⅔⅛]+)?\s+)+")
UNIT_WORDS = ["cups?", "c", "tablespoons?", "tbsps?", "tbs", "teaspoons?", "tsps?", "ounces?",
              "oz", "pounds?", "lbs?", "grams?", "g", "kg", "kilograms?", "ml", "milliliters?",
              "liters?", "litres?", "l", "pints?", "quarts?", "gallons?", "cans?", "packages?",
              "pkgs?", "jars?", "bottles?", "sticks?", "cloves?", "heads?", "bunch(?:es)?",
              "slices?", "pieces?", "pinch(?:es)?", "dash(?:es)?", "handfuls?", "sprigs?",
              "stalks?", "envelopes?", "containers?", "box(?:es)?", "bags?", "large", "medium",
              "small", "extra-large", "whole", "of"]
UNIT_PATTERN = re.compile(r"^(?:(?:" + "|".join(UNIT_WORDS) + r")\.?\s+)+")
# Preparation words at the start of a name ("chopped onion" -> "onion")
PREP_PATTERN = re.compile(r"^(?:(?:chopped|minced|diced|sliced|grated|shredded|crushed|peeled|"
                          r"fresh|freshly|finely|coarsely|thinly|roughly)\s+)+")

# Words that look plural but are not, and irregular plurals
KEEP_AS_IS = {"molasses", "hummus", "couscous", "asparagus", "citrus", "swiss", "grits",
              "greens", "brussels", "bitters", "schnapps", "oats"}
IRREGULAR_PLURALS = {"leaves": "leaf", "loaves": "loaf", "halves": "half",
                     "cookies": "cookie", "brownies": "brownie", "pies": "pie",
                     # "-ies" words whose singular ends in "ie" or "i", not "y" ("chilies" is not "chily")
                     "chilies": "chili", "chillies": "chili", "chilis": "chili", "veggies": "veggie",
                     "smoothies": "smoothie", "zucchinis": "zucchini", "beanies": "beanie"}


def singular(word: str) -> str:
    """Return a simple singular form of one word ('tomatoes' -> 'tomato', 'leaves' -> 'leaf')."""
    if word in IRREGULAR_PLURALS:
        return IRREGULAR_PLURALS[word]
    if word in KEEP_AS_IS or len(word) <= 3:
        return word
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith("oes"):
        return word[:-2]
    if word.endswith(("ches", "shes", "sses", "xes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def normalize_ingredient(name: object) -> list[str]:
    """Normalize one ingredient name so that variants count as one ingredient.

    Steps: drop notes in brackets, strip a leading quantity and unit ("1/2 cup
    ..."), keep only the part before a comma or " or " ("onion, chopped",
    "canola oil or vegetable oil"), drop leading preparation words, then apply
    synonyms and a simple singular form.

    Args:
        name: One raw ingredient, for example "2 Large Eggs".

    Returns:
        Usually one name (["egg"]); two for entries such as "salt and pepper";
        none if nothing is left.
    """
    text = re.sub(r"\(.*?\)", " ", str(name).lower())   # drop notes in brackets
    text = re.sub(r"\s+", " ", text).strip(" ,.;:-")
    quantity = QUANTITY_PATTERN.match(text)
    if quantity:
        text = UNIT_PATTERN.sub("", text[quantity.end():])
    text = text.split(",")[0].split(" or ")[0]
    text = PREP_PATTERN.sub("", text).strip(" ,.;:-")
    if text in SPLIT_INGREDIENTS:
        return SPLIT_INGREDIENTS[text]
    text = INGREDIENT_SYNONYMS.get(text, text)
    words = text.split()
    if words:
        words[-1] = singular(words[-1])
        text = " ".join(words)
    text = INGREDIENT_SYNONYMS.get(text, text)
    return [text] if text else []


def normalize_ingredient_list(items: Iterable[object]) -> list[str]:
    """Normalize every ingredient in a list and drop repeats, keeping the order."""
    out = []
    for item in items:
        out.extend(normalize_ingredient(item))
    return list(dict.fromkeys(out))


def clean_ingredients(raw: object) -> list[str]:
    """Parse a raw ingredient list (Python or JSON text) into lowercase names with single spaces."""
    return [re.sub(r"\s+", " ", str(i).lower().strip()) for i in parse_list_string(raw)]


@cache
def _changes_a_flag(longer: str, food: str) -> bool:
    """True when `longer` ("groundnut oil") sets a restriction flag differently from `food` ("oil")."""
    # flags.py imports this module, so it is imported here, when first needed
    from .flags import FLAG_COLUMNS, keyword_flag
    return any(keyword_flag(longer, c) != keyword_flag(food, c) for c in (*FLAG_COLUMNS, "vegetarian", "vegan"))


def hf_ingredient_foods(raw: object) -> list[str]:
    """Return the plain food names from Hugging Face's 'ingredients' JSON.

    Each entry looks like {"food": "kosher salt", "text": "1 tablespoon kosher salt"};
    the 'food' field has no quantities, so it is the better ingredient name. But it can drop
    the word that matters for a restriction ("3 tbsp groundnut oil" -> "oil", "cooked turkey
    bacon" -> "bacon"), so the word before the food is kept whenever it changes a flag.
    """
    names = []
    for d in parse_list_string(raw):
        if not (isinstance(d, dict) and d.get("food")):
            continue
        food = str(d["food"])
        before = re.search(r"([a-z][a-z\-]*)\s+" + re.escape(food.lower()) + r"\b", str(d.get("text", "")).lower())
        longer = f"{before.group(1)} {food}" if before else ""
        names.append(longer if longer and _changes_a_flag(longer.lower(), food.lower()) else food)
    return names


def ingredient_text(value: object) -> str:
    """Turn an ingredient list (or its text form) into one lowercase string joined by ' | '."""
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, (list, tuple, np.ndarray)):
        return " | ".join(str(v) for v in value).lower()
    return ""


def unique_ingredients(ingredients: Iterable[str]) -> list[str]:
    """Return each ingredient once, in order (the analyzer for the text features)."""
    return list(dict.fromkeys(ingredients))


def ingredient_tokens(ingredients: Iterable[str]) -> list[str]:
    """Return the ingredients as tokens for the cuisine classifier (6.6).

    Lives in this module so a saved model can be loaded anywhere the
    everflavor package can be imported.
    """
    return list(ingredients)
