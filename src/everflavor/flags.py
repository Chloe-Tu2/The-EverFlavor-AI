"""Restriction flags (5.4.2): keyword rules, used by the recipe table, the
validation checks and the safety filter, so they always agree."""
from __future__ import annotations

import re
from collections.abc import Sequence
from functools import cache

import pandas as pd

from .checks import require_columns
from .ingredients import ingredient_text
from .parsing import parse_label_list

__all__ = [
    "ALCOHOL_EXCEPTIONS",
    "ALCOHOL_KEYWORDS",
    "ALLIUM_EXCEPTIONS",
    "ALLIUM_KEYWORDS",
    "ANIMAL_EXCEPTIONS",
    "ANIMAL_KEYWORDS",
    "BEEF_EXCEPTIONS",
    "BEEF_KEYWORDS",
    "DAIRY_EXCEPTIONS",
    "DAIRY_KEYWORDS",
    "EGG_EXCEPTIONS",
    "EGG_KEYWORDS",
    "FISH_KEYWORDS",
    "FLAG_COLUMNS",
    "FLAG_RULES",
    "FOODCOM_TAG_CHECKS",
    "GELATIN_EXCEPTIONS",
    "GELATIN_KEYWORDS",
    "GLUTEN_EXCEPTIONS",
    "GLUTEN_FREE_FOODS",
    "GLUTEN_FREE_NAME",
    "GLUTEN_KEYWORDS",
    "HF_FREE_LABELS",
    "HONEY_EXCEPTIONS",
    "HONEY_KEYWORDS",
    "LAND_MEAT_KEYWORDS",
    "MEAT_EXCEPTIONS",
    "MEAT_KEYWORDS",
    "PEANUT_EXCEPTIONS",
    "PEANUT_KEYWORDS",
    "PORK_EXCEPTIONS",
    "PORK_KEYWORDS",
    "ROOT_VEGETABLE_EXCEPTIONS",
    "ROOT_VEGETABLE_KEYWORDS",
    "SESAME_KEYWORDS",
    "SHELLFISH_EXCEPTIONS",
    "SHELLFISH_KEYWORDS",
    "SOY_KEYWORDS",
    "TREE_NUT_EXCEPTIONS",
    "TREE_NUT_KEYWORDS",
    "add_foodcom_diet_flags",
    "add_hf_diet_flags",
    "add_keyword_flags",
    "foodcom_tag_agreement",
    "keyword_flag",
    "make_flag",
    "print_flag_counts",
]


# --- Keyword lists ---
# Matched as whole words in the ingredients and the recipe name.
# Sausages and cold cuts count as pork unless stated otherwise (the safe side)
PORK_KEYWORDS     = ["pork", "bacon", "ham", "prosciutto", "pancetta", "guanciale",
                     "sausage", "salami", "chorizo", "lard", "lardon", "pepperoni",
                     "kielbasa", "andouille", "bratwurst", "mortadella", "capicola",
                     "boston butt", "spare rib", "baby back rib", "hot dog",
                     "frankfurter", "wiener", "bologna"]
ALCOHOL_KEYWORDS  = ["wine", "beer", "ale", "lager", "rum", "vodka", "whiskey", "whisky",
                     "bourbon", "brandy", "cognac", "sherry", "liqueur", "liquor", "tequila", "gin",
                     "sake", "mirin", "champagne", "prosecco", "vermouth", "kahlua", "amaretto",
                     "marsala", "madeira", "schnapps", "triple sec", "grand marnier", "cointreau",
                     "curacao", "chambord", "frangelico", "baileys", "limoncello", "sambuca", "ouzo",
                     "kirsch", "calvados", "armagnac", "grappa", "mezcal", "pisco", "cachaca", "soju",
                     "shaoxing", "shaohsing", "hard cider"]
# Wheat, barley and rye, including products that are made from them
GLUTEN_KEYWORDS   = ["flour", "bread", "wheat", "pasta", "noodle", "barley", "rye",
                     "soy sauce", "breadcrumb", "cracker", "couscous", "semolina", "bulgur",
                     "spelt", "malt", "seitan", "farro", "orzo", "panko", "beer", "ale", "lager",
                     # pasta shapes and noodles
                     "spaghetti", "macaroni", "lasagna", "lasagne", "penne", "linguine",
                     "fettuccine", "fettuccini", "ditalini", "rigatoni", "ziti", "tortellini",
                     "ravioli", "gnocchi", "vermicelli", "ramen", "udon", "pastina", "pastini",
                     # breads, pastry and baked goods
                     "baguette", "bun", "bagel", "brioche", "croissant", "muffin", "biscuit",
                     "pita", "naan", "chapati", "roti", "paratha", "pretzel", "crouton", "pastry",
                     "pie crust", "pie shell", "phyllo", "filo", "dough", "cookie", "dumpling",
                     "wonton", "egg roll wrapper", "spring roll wrapper", "hoagie roll",
                     "dinner roll", "kaiser roll", "sub roll", "bread roll", "matzo", "matzah",
                     "graham", "stuffing", "breading", "bisquick", "cake mix", "brownie mix",
                     "waffle", "pasty", "pasties",
                     "farina", "wheat germ", "durum", "kamut", "freekeh", "triticale",
                     # sauces and soups usually made with wheat
                     "teriyaki", "hoisin", "oyster sauce", "gochujang", "shoyu", "ponzu", "soya sauce",
                     "cream of mushroom soup", "cream of chicken soup", "cream of celery soup",
                     "minestrone"]
DAIRY_KEYWORDS    = ["milk", "buttermilk", "cheese", "butter", "cream", "yogurt", "yoghurt",
                     "ghee", "mozzarella", "parmesan", "ricotta", "mascarpone", "feta", "whey",
                     "cheddar", "brie", "camembert", "gouda", "gruyere", "gorgonzola", "burrata",
                     "halloumi", "paneer", "queso", "provolone", "pecorino", "emmental", "manchego",
                     "labneh", "kefir", "quark", "creme fraiche", "half-and-half", "half and half",
                     "custard", "cheesecake", "casein", "caseinate", "whipped topping", "cool whip",
                     "alfredo", "bechamel", "tzatziki", "raita", "lassi"]
EGG_KEYWORDS      = ["egg", "egg white", "egg yolk", "mayonnaise", "mayo", "meringue", "eggnog",
                     "aioli", "hollandaise", "carbonara", "quiche", "frittata", "challah",
                     "brioche", "cheesecake", "macaron", "wonton"]
PEANUT_KEYWORDS   = ["peanut", "peanut butter", "peanut oil", "groundnut", "ground nut"]
TREE_NUT_KEYWORDS = ["almond", "walnut", "pecan", "cashew", "pistachio", "hazelnut",
                     "filbert", "macadamia", "brazil nut", "pine nut", "nut", "nutella",
                     "praline", "marzipan", "macaron", "frangipane", "amaretti", "pesto",
                     "baklava", "nougat", "gianduja", "marcona"]
FISH_KEYWORDS     = ["fish", "salmon", "tuna", "cod", "anchovy", "anchovies", "sardine",
                     "tilapia", "halibut", "trout", "mackerel", "haddock", "catfish",
                     "snapper", "swordfish", "mahi mahi", "flounder", "sole", "hake",
                     "snoek", "pollock", "bass", "kingfish", "orange roughy", "grouper",
                     "perch", "pike", "walleye", "monkfish", "whitefish", "herring",
                     "kipper", "eel", "carp", "bream", "branzino", "surimi", "roe",
                     "fish sauce", "worcestershire sauce", "bonito", "caviar",
                     "dashi", "katsuobushi", "nam pla", "nuoc mam", "caesar dressing"]
SHELLFISH_KEYWORDS = ["shrimp", "prawn", "crab", "crabmeat", "lobster", "langoustine",
                      "langostino", "scampi", "krill", "crawfish", "crayfish", "clam", "cockle",
                      "mussel", "scallop", "oyster", "squid", "calamari", "octopus", "conch",
                      "abalone", "whelk", "belacan", "bagoong", "snail", "escargot"]
SOY_KEYWORDS      = ["soy", "soya", "soy sauce", "soybean", "tofu", "tempeh", "edamame",
                     "miso", "tamari", "teriyaki", "hoisin", "gochujang", "doenjang", "natto",
                     "shoyu", "ponzu", "yuba"]
SESAME_KEYWORDS   = ["sesame", "tahini", "tahina", "halva", "halvah", "za'atar", "zaatar",
                     "za atar", "furikake", "gomasio", "gomashio", "benne", "hummus", "houmous",
                     "hummous", "baba ganoush", "baba ghanoush"]
LAND_MEAT_KEYWORDS = ["chicken", "beef", "lamb", "mutton", "goat", "turkey", "veal", "duck",
                      "venison", "goose", "rabbit", "bison", "elk", "quail", "pheasant",
                      "cornish hen", "game hen", "fryer", "meat", "steak", "sirloin",
                      "brisket", "chuck", "ground round", "rib eye", "ribeye",
                      "filet mignon", "tri-tip", "porterhouse", "short rib", "oxtail",
                      "pot roast", "rump roast", "round roast", "eye of round", "pastrami",
                      "jerky", "liver", "giblet", "suet", "tallow", "bone marrow",
                      "gelatin", "gelatine", "marshmallow", "jello", "jell-o"] + PORK_KEYWORDS
MEAT_KEYWORDS     = LAND_MEAT_KEYWORDS + FISH_KEYWORDS + SHELLFISH_KEYWORDS

# Base flags for the diet profiles in 5.4.7
BEEF_KEYWORDS     = ["beef", "veal", "steak", "brisket", "sirloin", "chuck", "ground round", "rib eye",
                     "ribeye", "filet mignon", "tri-tip", "porterhouse", "t-bone", "flank steak",
                     "skirt steak", "short rib", "oxtail", "pot roast", "rump roast", "round roast",
                     "eye of round", "pastrami", "corned beef", "bresaola", "jerky", "suet", "tallow",
                     "bone marrow", "hamburger", "cheeseburger", "bulgogi"]
GELATIN_KEYWORDS  = ["gelatin", "gelatine", "jello", "jell-o", "marshmallow", "gummy", "gummies", "aspic"]
HONEY_KEYWORDS    = ["honey"]
# Jain diets avoid vegetables that grow underground (onion and garlic are in the allium list)
ROOT_VEGETABLE_KEYWORDS = ["potato", "sweet potato", "yam", "carrot", "beet", "beetroot", "radish",
                           "daikon", "turnip", "parsnip", "rutabaga", "swede", "celeriac", "taro",
                           "cassava", "yuca", "jicama", "ginger", "horseradish", "burdock", "salsify",
                           "lotus root", "jerusalem artichoke", "sunchoke"]
ALLIUM_KEYWORDS   = ["onion", "garlic", "leek", "shallot", "scallion", "chive", "spring onion",
                     "green onion"]
ANIMAL_KEYWORDS   = MEAT_KEYWORDS + DAIRY_KEYWORDS + EGG_KEYWORDS + ["honey"]

# Phrases that contain a keyword but are not that food
# (removed from the text before keywords are matched, longest first)
PORK_EXCEPTIONS     = ["hot dog bun", "hot dog roll", "vegetarian sausage", "veggie sausage",
                       "vegan sausage", "vegetarian bacon", "turkey bacon", "turkey ham",
                       "turkey kielbasa", "turkey sausage", "chicken sausage"]
ALCOHOL_EXCEPTIONS  = ["wine vinegar", "sherry vinegar", "ginger ale", "ginger beer", "root beer",
                       "non-alcoholic", "alcohol-free", "alcohol free"]
# "gluten-free bread", "gluten free pasta", ...: the food after "gluten-free" is safe
GLUTEN_FREE_FOODS   = ["bread", "flour", "pasta", "noodle", "noodles", "spaghetti", "penne",
                       "macaroni", "cracker", "crackers", "breadcrumb", "breadcrumbs", "soy sauce",
                       "beer", "cookie", "cookies", "dough", "pizza crust", "pie crust", "baking mix",
                       "bisquick", "muffin", "muffins", "bun", "buns", "tortilla", "tortillas",
                       "oats", "teriyaki", "hoisin", "stuffing", "pretzel", "pretzels"]
GLUTEN_EXCEPTIONS   = (["rice flour", "almond flour", "coconut flour", "corn flour", "chickpea flour",
                        "tapioca flour", "potato flour", "cassava flour", "sorghum flour",
                        "arrowroot flour", "teff flour", "millet flour", "quinoa flour", "oat flour",
                        "banana flour", "rice noodle", "rice vermicelli", "rice stick", "rice paper",
                        "glass noodle", "cellophane noodle", "bean thread", "shirataki",
                        "kelp noodle", "zucchini noodle", "sweet potato noodle", "konjac",
                        "spaghetti squash", "cauliflower crust", "corn tortilla", "ginger ale",
                        "rice pasta", "corn pasta", "chickpea pasta", "lentil pasta", "rice cracker",
                        "pasta sauce", "spaghetti sauce", "rice stuffing",
                        "ginger beer", "root beer", "gluten-free", "gluten free"]
                       + [f"gluten{sep}free {food}" for sep in ("-", " ") for food in GLUTEN_FREE_FOODS])
DAIRY_EXCEPTIONS    = ["coconut milk", "almond milk", "soy milk", "oat milk", "rice milk",
                       "cashew milk", "coconut cream", "cream of tartar", "peanut butter",
                       "almond butter", "cashew butter", "apple butter", "cocoa butter",
                       "shea butter", "butter bean", "butter lettuce", "butterhead lettuce",
                       "vegan butter", "plant butter", "vegan cheese", "vegan cream cheese",
                       "dairy-free cheese", "dairy free cheese", "cashew cream", "oat cream",
                       "soy cream", "coconut yogurt", "soy yogurt", "almond yogurt", "vegan yogurt",
                       "non-dairy", "nondairy", "dairy-free", "dairy free"]
EGG_EXCEPTIONS      = ["eggless", "egg-free", "egg free", "egg replacer", "vegan mayo",
                       "vegan mayonnaise", "flax egg", "chia egg"]
PEANUT_EXCEPTIONS   = ["peanut-free", "peanut free"]
TREE_NUT_EXCEPTIONS = ["nut-free", "nut free", "tiger nut", "ground nut"]
SHELLFISH_EXCEPTIONS = ["oyster mushroom"]
MEAT_EXCEPTIONS     = ["oyster mushroom", "duck sauce", "lamb's lettuce", "vegetarian sausage",
                       "veggie sausage", "vegan sausage", "meatless", "meat substitute",
                       "steak sauce", "steak seasoning", "cauliflower steak",
                       "hot dog bun", "hot dog roll", "goat cheese", "goats cheese",
                       "goat's cheese", "goat milk", "goat's milk", "vegan marshmallow",
                       "vegetarian marshmallow"]
ANIMAL_EXCEPTIONS   = MEAT_EXCEPTIONS + DAIRY_EXCEPTIONS + EGG_EXCEPTIONS
BEEF_EXCEPTIONS     = ["tuna steak", "salmon steak", "fish steak", "swordfish steak", "cauliflower steak",
                       "steak sauce", "steak seasoning", "beefsteak tomato", "beef tomato",
                       "hamburger bun", "hamburger roll", "hamburger helper", "turkey jerky",
                       "mushroom jerky", "veggie burger"]
GELATIN_EXCEPTIONS  = ["agar", "vegan gelatin", "vegan marshmallow", "vegetarian marshmallow", "vegan gummy"]
HONEY_EXCEPTIONS    = ["honey crisp", "honeycrisp"]
ROOT_VEGETABLE_EXCEPTIONS = ["ground ginger", "dried ginger", "ginger powder", "ginger ale", "ginger beer"]
ALLIUM_EXCEPTIONS   = ["onion seed", "onion seeds"]

# Flag column -> (keywords, exceptions)
FLAG_RULES = {
    "contains_pork"     : (PORK_KEYWORDS, PORK_EXCEPTIONS),
    "contains_alcohol"  : (ALCOHOL_KEYWORDS, ALCOHOL_EXCEPTIONS),
    "contains_gluten"   : (GLUTEN_KEYWORDS, GLUTEN_EXCEPTIONS),
    "contains_dairy"    : (DAIRY_KEYWORDS, DAIRY_EXCEPTIONS),
    "contains_egg"      : (EGG_KEYWORDS, EGG_EXCEPTIONS),
    "contains_peanut"   : (PEANUT_KEYWORDS, PEANUT_EXCEPTIONS),
    "contains_tree_nut" : (TREE_NUT_KEYWORDS, TREE_NUT_EXCEPTIONS),
    "contains_fish"     : (FISH_KEYWORDS, ()),
    "contains_shellfish": (SHELLFISH_KEYWORDS, SHELLFISH_EXCEPTIONS),
    "contains_soy"      : (SOY_KEYWORDS, ()),
    "contains_sesame"   : (SESAME_KEYWORDS, ()),
    # Base flags used by the diet profiles (5.4.7)
    "contains_meat"     : (LAND_MEAT_KEYWORDS, MEAT_EXCEPTIONS),   # meat or poultry, not fish
    "contains_beef"     : (BEEF_KEYWORDS, BEEF_EXCEPTIONS),
    "contains_gelatin"  : (GELATIN_KEYWORDS, GELATIN_EXCEPTIONS),
    "contains_honey"    : (HONEY_KEYWORDS, HONEY_EXCEPTIONS),
    "contains_root_vegetable": (ROOT_VEGETABLE_KEYWORDS, ROOT_VEGETABLE_EXCEPTIONS),
    "contains_allium"   : (ALLIUM_KEYWORDS, ALLIUM_EXCEPTIONS),
}
FLAG_COLUMNS = list(FLAG_RULES) + ["vegetarian", "vegan"]


@cache
def _keyword_pattern(keywords):
    """Compile one whole-word regex for a tuple of keywords (plurals allowed)."""
    alternatives = "|".join(re.escape(k) for k in sorted(keywords, key=len, reverse=True))
    return re.compile(rf"\b(?:{alternatives})(?:s|es)?\b")


def make_flag(ingredient_str: object, keywords: Sequence[str], exceptions: Sequence[str] = ()) -> bool:
    """Check whether any keyword appears as a whole word in a text.

    Whole-word matching avoids false hits such as 'ham' in 'graham' or 'egg'
    in 'eggplant'; plural endings (-s, -es) still match. Exception phrases
    (for example 'coconut milk') are removed first, longest first, so they
    never trigger a keyword.

    Args:
        ingredient_str: The text to search (ingredients and name); anything else gives False.
        keywords: Words or phrases that mean the recipe has the flag.
        exceptions: Phrases to ignore before matching.

    Returns:
        True if a keyword is found.
    """
    if not isinstance(ingredient_str, str):
        return False
    text = ingredient_str.lower()
    for phrase in sorted(exceptions, key=len, reverse=True):
        text = text.replace(phrase, " ")
    return bool(_keyword_pattern(tuple(keywords)).search(text))

# A recipe name that declares the dish gluten-free
GLUTEN_FREE_NAME = r"\b(?:gluten[- ]?free|gf|flourless|celiac|coeliac)\b"


def add_keyword_flags(df: pd.DataFrame, ingredient_col: str, name_col: str | None = None) -> pd.DataFrame:
    """Add every restriction flag (FLAG_COLUMNS) from the ingredients and, if given, the name.

    The name catches what the ingredient list leaves out, such as "Grilled
    Lamb Chops with Tzatziki". A name that says "gluten-free" or "flourless"
    is not used for the gluten flag, because it describes the kind of dish.

    Args:
        df: Recipes.
        ingredient_col: Column with the ingredients (a list, or text).
        name_col: Column with the recipe name, or None to use the ingredients only.

    Returns:
        A copy of `df` with the flag columns added; `df` itself is not changed.

    Raises:
        ValueError: If a named column is missing.
    """
    require_columns(df, [ingredient_col] + ([name_col] if name_col else []), "add_keyword_flags")
    df = df.copy()
    text = df[ingredient_col].apply(ingredient_text)
    gluten_text = text
    if name_col is not None:
        names = df[name_col].fillna("").astype(str).str.lower()
        text = text + " | " + names
        # "Gluten-free bread" or "flourless cookies": the name describes the kind of dish,
        # not a wheat ingredient, so only the ingredients count for gluten
        gluten_text = text.where(~names.str.contains(GLUTEN_FREE_NAME), gluten_text)
    for col, (keywords, exceptions) in FLAG_RULES.items():
        source_text = gluten_text if col == "contains_gluten" else text
        df[col] = source_text.apply(lambda x, kw=keywords, ex=exceptions: make_flag(x, kw, ex))
    df["vegetarian"] = ~text.apply(lambda x: make_flag(x, MEAT_KEYWORDS, MEAT_EXCEPTIONS))
    df["vegan"]      = ~text.apply(lambda x: make_flag(x, ANIMAL_KEYWORDS, ANIMAL_EXCEPTIONS))
    return df


def add_foodcom_diet_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Add the restriction flags to Food.com recipes (columns 'ingredients' and 'name')."""
    return add_keyword_flags(df, "ingredients", name_col="name")


def keyword_flag(text: str, column: str) -> bool:
    """Work out one flag (any of FLAG_COLUMNS) directly from a text with the keyword rules.

    Args:
        text: Lowercase ingredients and name, for example "flour | butter | shortbread".
        column: The flag, for example "contains_pork" or "vegetarian".

    Returns:
        The flag's value: for "vegetarian" and "vegan", True means the text fits the diet.
    """
    if column == "vegetarian":
        return not make_flag(text, MEAT_KEYWORDS, MEAT_EXCEPTIONS)
    if column == "vegan":
        return not make_flag(text, ANIMAL_KEYWORDS, ANIMAL_EXCEPTIONS)
    keywords, exceptions = FLAG_RULES[column]
    return make_flag(text, keywords, exceptions)


# Flag column -> the "free of" label that rules it out
HF_FREE_LABELS = {
    "contains_gluten"   : "gluten-free",
    "contains_dairy"    : "dairy-free",
    "contains_egg"      : "egg-free",
    "contains_peanut"   : "peanut-free",
    "contains_tree_nut" : "tree-nut-free",
    "contains_fish"     : "fish-free",
    "contains_shellfish": "shellfish-free",
    "contains_soy"      : "soy-free",
}


def add_hf_diet_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Add the restriction flags to Hugging Face recipes.

    Keyword flags come from 'ingredient_lines' and 'recipe_name'. Where the
    dataset has a "free of" label (HF_FREE_LABELS), a recipe without that label
    is also flagged: either source is enough, the safe direction for a
    restriction filter. Vegetarian and vegan need the label AND no meat or
    animal keyword, because some labels are wrong.

    Args:
        df: Hugging Face recipes with 'ingredient_lines', 'recipe_name' and 'health_labels'.

    Returns:
        A copy of `df` with the flag columns added.
    """
    labels = df["health_labels"].apply(lambda x: set(parse_label_list(x)))
    df = add_keyword_flags(df, "ingredient_lines", name_col="recipe_name")
    for col, free_label in HF_FREE_LABELS.items():
        df[col] = df[col] | ~labels.apply(lambda s, label=free_label: label in s)
    df["vegetarian"] = labels.apply(lambda s: "vegetarian" in s) & df["vegetarian"]
    df["vegan"]      = labels.apply(lambda s: "vegan" in s) & df["vegan"]
    return df


# Food.com authors add dietary tags: (tag, our column, value our column should have)
FOODCOM_TAG_CHECKS = [
    ("vegetarian",    "vegetarian",        True),
    ("vegan",         "vegan",             True),
    ("gluten-free",   "contains_gluten",   False),
    ("dairy-free",    "contains_dairy",    False),
    ("egg-free",      "contains_egg",      False),
    ("nut-free",      "contains_tree_nut", False),
    ("non-alcoholic", "contains_alcohol",  False),
]


def foodcom_tag_agreement(df: pd.DataFrame) -> pd.DataFrame:
    """Compare our flags with the dietary tags Food.com authors added (FOODCOM_TAG_CHECKS).

    Args:
        df: Flagged Food.com recipes with their 'tags' column.

    Returns:
        One row per tag that appears: "recipes" with the tag and "agree (%)".
    """
    tag_sets = df["tags"].apply(lambda t: set(parse_label_list(t)))
    rows = {}
    for tag, column, expected in FOODCOM_TAG_CHECKS:
        tagged = tag_sets.apply(lambda s, tag=tag: tag in s)
        if tagged.any():
            rows[tag] = (int(tagged.sum()), (df.loc[tagged, column] == expected).mean() * 100)
    return pd.DataFrame(rows, index=["recipes", "agree (%)"]).T


def print_flag_counts(df: pd.DataFrame, title: str) -> None:
    """Print how many recipes have each flag, and what share of all recipes that is."""
    print(f"Restriction flag counts ({title}):")
    for flag in FLAG_COLUMNS:
        print(f"  {flag:20s}: {df[flag].sum():>8,} ({df[flag].mean() * 100:.1f}%)")
