"""Restriction flags (5.4.2): keyword rules, used by the recipe table, the
validation checks and the safety filter, so they always agree."""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from functools import cache

import pandas as pd

from .checks import require_columns
from .ingredients import ingredient_text
from .parsing import parse_label_list
from .progress import MIN_ROWS, progress_bar

__all__ = [
    "ACCENT_REQUIRED",
    "ALCOHOL_EXCEPTIONS",
    "ALCOHOL_EXTRACT_EXCEPTIONS",
    "ALCOHOL_EXTRACT_KEYWORDS",
    "ALCOHOL_KEYWORDS",
    "ALLIUM_EXCEPTIONS",
    "ALLIUM_KEYWORDS",
    "ANIMAL_EXCEPTIONS",
    "ANIMAL_KEYWORDS",
    "ASAFOETIDA_KEYWORDS",
    "BEEF_EXCEPTIONS",
    "BEEF_KEYWORDS",
    "BUCKWHEAT_EXCEPTIONS",
    "BUCKWHEAT_KEYWORDS",
    "CARMINE_KEYWORDS",
    "CELERY_KEYWORDS",
    "COFFEE_TEA_EXCEPTIONS",
    "COFFEE_TEA_KEYWORDS",
    "COMPOUND_INGREDIENTS",
    "CRUSTACEAN_KEYWORDS",
    "DAIRY_EXCEPTIONS",
    "DAIRY_KEYWORDS",
    "EGG_EXCEPTIONS",
    "EGG_KEYWORDS",
    "FAVA_KEYWORDS",
    "FISH_EXCEPTIONS",
    "FISH_KEYWORDS",
    "FLAG_COLUMNS",
    "FLAG_RULES",
    "FOODCOM_TAG_CHECKS",
    "FOOD_NAME_GROUPS",
    "GELATIN_EXCEPTIONS",
    "GELATIN_KEYWORDS",
    "GLUTEN_EXCEPTIONS",
    "GLUTEN_FREE_FOODS",
    "GLUTEN_FREE_NAME",
    "GLUTEN_KEYWORDS",
    "HF_FREE_LABELS",
    "HIGH_MERCURY_FISH_KEYWORDS",
    "HIGH_PURINE_EXCEPTIONS",
    "HIGH_PURINE_KEYWORDS",
    "HIGH_TYRAMINE_EXCEPTIONS",
    "HIGH_TYRAMINE_KEYWORDS",
    "HONEY_EXCEPTIONS",
    "HONEY_KEYWORDS",
    "LAND_MEAT_EXCEPTIONS",
    "LAND_MEAT_KEYWORDS",
    "LUPIN_KEYWORDS",
    "MEAT_EXCEPTIONS",
    "MEAT_KEYWORDS",
    "MOLLUSC_KEYWORDS",
    "MUSHROOM_EXCEPTIONS",
    "MUSHROOM_KEYWORDS",
    "MUSTARD_KEYWORDS",
    "NIGHTSHADE_EXCEPTIONS",
    "NIGHTSHADE_KEYWORDS",
    "NOT_MEAT_LOOKALIKES",
    "PEANUT_EXCEPTIONS",
    "PEANUT_KEYWORDS",
    "PET_MEAT_EXCEPTIONS",
    "PET_MEAT_KEYWORDS",
    "PORK_EXCEPTIONS",
    "PORK_KEYWORDS",
    "POULTRY_EXCEPTIONS",
    "POULTRY_KEYWORDS",
    "PROCESSED_MEAT_EXCEPTIONS",
    "PROCESSED_MEAT_KEYWORDS",
    "RAW_ANIMAL_EXCEPTIONS",
    "RAW_ANIMAL_KEYWORDS",
    "RED_MEAT_EXCEPTIONS",
    "RED_MEAT_KEYWORDS",
    "ROOT_VEGETABLE_EXCEPTIONS",
    "ROOT_VEGETABLE_KEYWORDS",
    "SALT_EXCEPTIONS",
    "SALT_KEYWORDS",
    "SCALELESS_FISH_EXCEPTIONS",
    "SCALELESS_FISH_KEYWORDS",
    "SESAME_KEYWORDS",
    "SHELLFISH_EXCEPTIONS",
    "SHELLFISH_KEYWORDS",
    "SOFT_CHEESE_KEYWORDS",
    "SOY_KEYWORDS",
    "SULFITE_EXCEPTIONS",
    "SULFITE_KEYWORDS",
    "TREE_NUT_EXCEPTIONS",
    "TREE_NUT_KEYWORDS",
    "UNCLEAN_MEAT_EXCEPTIONS",
    "UNCLEAN_MEAT_KEYWORDS",
    "WINE_NAMES",
    "WINE_NAME_EXCEPTIONS",
    "WINE_NAME_GROUPS",
    "add_foodcom_diet_flags",
    "add_hf_diet_flags",
    "add_keyword_flags",
    "explain_flag",
    "flags_for_term",
    "foodcom_tag_agreement",
    "keyword_flag",
    "make_flag",
    "name_text",
    "named_foods",
    "not_named_foods",
    "print_flag_counts",
    "recipe_text",
    "spelling_variants",
    "term_group_of",
    "term_groups",
    "term_names",
    "wine_name_groups",
    "wine_names",
    "with_spellings",
]


# --- Ready-made ingredients whose allergens are hidden from the recipe (5.13) ---
# Ingredient -> the flags it adds. Each entry comes from Open Food Facts evidence
# (most matching products declare the allergen) and is listed with the team's
# decision in docs/flag_review/compound_ingredients_review.csv; 5.13 checks that
# the two agree. Entries only ever add flags (the safe direction).
COMPOUND_INGREDIENTS: dict[str, list[str]] = {
    "worcestershire sauce": ["contains_gluten"],
    "semi-sweet chocolate chip": ["contains_dairy", "contains_soy"],
    "semisweet chocolate": ["contains_soy"],
    "hoisin sauce": ["contains_sesame"],
    "yellow cake mix": ["contains_soy"],
    "white chocolate chip": ["contains_dairy", "contains_soy"],
    "white chocolate": ["contains_dairy", "contains_soy"],
    "ranch dressing": ["contains_dairy", "contains_egg", "contains_soy"],
    "italian dressing": ["contains_soy"],
    "tomato soup": ["contains_dairy"],
    "graham cracker": ["contains_soy"],
    "condensed cream of mushroom soup": ["contains_soy"],
    "cream of celery soup": ["contains_soy"],
    "butterscotch chip": ["contains_dairy", "contains_soy"],
    "ritz cracker": ["contains_soy"],
    "condensed cream of chicken soup": ["contains_soy"],
    "seasoned bread crumb": ["contains_dairy"],
    "alfredo sauce": ["contains_soy"],
    "white cake mix": ["contains_soy"],
    "oreo cookie": ["contains_soy"],
    "ranch dressing mix": ["contains_dairy"],
    "vanilla wafer": ["contains_gluten"],
    "basil pesto": ["contains_dairy"],
    "dark chocolate chip": ["contains_soy"],
    "ramen noodle": ["contains_soy"],
    "devil's food cake mix": ["contains_soy"],
    "angel food cake": ["contains_egg", "contains_gluten"],
    "biscuit": ["contains_dairy", "contains_soy"],
    "pizza crust": ["contains_gluten"],  # dairy rejected in review: it varies by product
    "thousand island dressing": ["contains_soy"],
    "cheddar cheese soup": ["contains_gluten"],
    "asafoetida powder": ["contains_gluten"],
    "asafoetida": ["contains_gluten"],   # same product as "asafoetida powder"
    "hing": ["contains_gluten"],
    "chili seasoning mix": ["contains_gluten"],
    "soba noodle": ["contains_soy"],
    "mushroom soup": ["contains_dairy", "contains_gluten"],
    "brown gravy mix": ["contains_dairy", "contains_gluten"],
    "pancake mix": ["contains_gluten"],
    "condensed cheddar cheese soup": ["contains_gluten", "contains_soy"],
    "semi-sweet chocolate": ["contains_soy"],
    "condensed cream of celery soup": ["contains_soy"],
    "stove top stuffing mix": ["contains_soy"],
    "green enchilada sauce": ["contains_soy"],
    "cornbread mix": ["contains_gluten"],
    "pesto": ["contains_dairy"],
    "red enchilada sauce": ["contains_soy"],
    "cookie": ["contains_dairy"],
    "chocolate frosting": ["contains_soy"],
    "christmas pudding": ["contains_egg", "contains_gluten"],
}


def name_text(name: object) -> str:
    """Return a recipe name ready for flag matching: lowercase, without COMPOUND_INGREDIENTS.

    A ready-made ingredient only counts when it is in the ingredient list: "Vegan
    Cookies" names the dish, it is not a store-bought cookie with milk in it.

    Args:
        name: The recipe name (anything that is not text gives "").

    Returns:
        The lowercase name with every COMPOUND_INGREDIENTS phrase removed.
    """
    text = name.lower() if isinstance(name, str) else ""
    for phrase in sorted(COMPOUND_INGREDIENTS, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(phrase)}(?:s|es)?\b", " ", text)
    return text


def recipe_text(ingredients: object, name: object) -> str:
    """Return the text the flag rules read: the ingredients, then the name (see name_text).

    Args:
        ingredients: The ingredient list (or text).
        name: The recipe name.

    Returns:
        Lowercase "ingredient | ingredient | name".
    """
    return ingredient_text(ingredients) + " | " + name_text(name)


def _compounds(*flags: str) -> list[str]:
    """Return the COMPOUND_INGREDIENTS that add any of `flags`."""
    return [name for name, adds in COMPOUND_INGREDIENTS.items() if set(adds) & set(flags)]


# --- Keyword lists ---
# Matched as whole words in the ingredients and the recipe name.
# Sausages and cold cuts count as pork unless stated otherwise (the safe side)
PORK_KEYWORDS     = ["pork", "bacon", "ham", "prosciutto", "pancetta", "guanciale",
                     "sausage", "salami", "chorizo", "lard", "lardon", "pepperoni",
                     "kielbasa", "andouille", "bratwurst", "mortadella", "capicola",
                     "boston butt", "spare rib", "baby back rib", "hot dog",
                     "frankfurter", "wiener", "bologna", "jamon", "jamón",
                     # cured pork and pork dishes named without "pork" (found by an ingredient-name probe)
                     "speck", "nduja", "chicharron", "char siu", "coppa", "lardo",
                     # pork dishes and cold cuts a red-team probe found missing (2026-10-10)
                     "carnitas", "porchetta", "lechon", "lechón", "tonkatsu", "cotechino", "soppressata",
                     "black pudding", "blood sausage", "scrapple", "chashu", "boudin", "rillettes", "spam",
                     "pâté"]
# Wines and ciders named without the word "wine" ("1 cup chardonnay", "1/2 cup tawny port"), policy P23.
# Each wine lists its other names ("aliases") and the look-alikes that are not wine ("not_wine").
# Write each name once, with its accents: spelling_variants adds the plain and hyphenated forms.
# Plain "cider" stays out: in US recipes it means apple juice
WINE_NAME_GROUPS: dict[str, dict[str, list[str]]] = {
    "port": {"aliases": ["ruby port", "tawny port", "white port", "porto"],
             # Port Salut is a cheese, Port-a-Pitt a barbecue restaurant, Port Huron a city
             "not_wine": ["port salut", "port-a-pitt", "port huron"]},
    "merlot": {}, "zinfandel": {}, "chardonnay": {},
    "cabernet": {"aliases": ["cabernet sauvignon", "cabernet franc"]},
    "sauvignon blanc": {}, "pinot noir": {},
    "pinot grigio": {"aliases": ["pinot gris"]},
    "riesling": {}, "chianti": {},
    # Shiraz is also a city in Iran: salad-e shirazi is a cucumber and tomato salad
    "shiraz": {"aliases": ["syrah"], "not_wine": ["shiraz salad", "salad shiraz", "salad-e shirazi"]},
    "malbec": {},
    "beaujolais": {"not_wine": ["café beaujolais"]},
    "sauternes": {}, "moscato": {}, "lambrusco": {}, "sangiovese": {}, "tempranillo": {}, "grenache": {},
    "gewürztraminer": {}, "retsina": {},
    # Without its accent "rose" is the flower, so only "rosé" and "rose wine" count (ACCENT_REQUIRED)
    "rosé": {"aliases": ["rosé wine"], "not_wine": ["rosé water", "rosé syrup"]},
    # Sangria made without wine; a wine in the ingredient list still sets the flag
    "sangria": {"not_wine": ["virgin sangria", "virgin white sangria", "mock sangria", "non-alcoholic sangria",
                             "nonalcoholic sangria", "alcohol-free sangria", "sangria non-alcoholic",
                             "sangria nonalcoholic"]},
    "cava": {}, "amontillado": {}, "oloroso": {}, "umeshu": {}, "makgeolli": {}, "huangjiu": {}, "mijiu": {},
    "shochu": {},
    "hard cider": {"aliases": ["dry cider", "alcoholic cider", "scrumpy", "perry"]},
}
# Names whose plain spelling means something else
ACCENT_REQUIRED = ["rosé"]


def spelling_variants(phrase: str, keep_accents: bool = False) -> list[str]:
    """Return every way a recipe may spell a phrase: with and without accents, hyphens or spaces.

    Args:
        phrase: The phrase, written with its accents ("café beaujolais").
        keep_accents: True when the plain spelling means something else ("rosé" and "rose").

    Returns:
        The phrase first, then its other spellings, each once
        ("café beaujolais", "café-beaujolais", "cafe beaujolais", "cafe-beaujolais").
    """
    forms = [phrase.lower()]
    if not keep_accents:
        plain = unicodedata.normalize("NFKD", forms[0])
        forms.append("".join(c for c in plain if not unicodedata.combining(c)))
    forms += [f.replace(" ", "-") for f in forms] + [f.replace("-", " ") for f in forms]
    return list(dict.fromkeys(forms))


def with_spellings(phrases: Sequence[str]) -> list[str]:
    """Return phrases with all their spellings (spelling_variants), each once, in order.

    Args:
        phrases: Keywords or exception phrases.

    Returns:
        Every phrase followed by its other spellings; the names in ACCENT_REQUIRED keep their accents.
    """
    return list(dict.fromkeys(s for p in phrases for s in spelling_variants(p, keep_accents=p in ACCENT_REQUIRED)))


def _same_name(groups: dict[str, dict[str, list[str]]], name: str) -> list[str]:
    """Return the spellings of a group's name and its aliases."""
    return with_spellings([name, *groups[name].get("aliases", [])])


def term_names(groups: dict[str, dict[str, list[str]]]) -> list[str]:
    """Return every name in a set of name groups, in every spelling (the primary list).

    Args:
        groups: Name -> {"aliases": [...], ...}, such as WINE_NAME_GROUPS or FOOD_NAME_GROUPS.

    Returns:
        Each name and its aliases, with and without accents, hyphens or spaces
        (except the names in ACCENT_REQUIRED), each once.
    """
    return list(dict.fromkeys(s for name in groups for s in _same_name(groups, name)))


def term_groups(groups: dict[str, dict[str, list[str]]], not_key: str = "not_this") -> dict[str, dict[str, list[str]]]:
    """Return, for each name, the names that mean the same thing and the look-alikes that do not.

    Built on term_names(), so each group lists only names the flags look for.

    Args:
        groups: Name -> {"aliases": [...], not_key: [...]}.
        not_key: The key that holds the look-alikes ("not_this", or "not_wine" in WINE_NAME_GROUPS).

    Returns:
        {"chestnut": {"same": ["chestnut", ...], "not_this": ["water chestnut", ...]}, ...}
    """
    known = term_names(groups)
    return {name: {"same": [s for s in known if s in _same_name(groups, name)],
                   "not_this": with_spellings(group.get(not_key, []))}
            for name, group in groups.items()}


def wine_names() -> list[str]:
    """Return every wine name the alcohol and sulfite flags look for, in every spelling (term_names)."""
    return term_names(WINE_NAME_GROUPS)


def wine_name_groups() -> dict[str, dict[str, list[str]]]:
    """Return, for each wine, the names that mean the same wine and the look-alikes that are not wine.

    Returns:
        {"rosé": {"same_wine": ["rosé", "rosé wine", ...], "not_wine": ["rosé water", ...]}, ...}
    """
    return {name: {"same_wine": g["same"], "not_wine": g["not_this"]}
            for name, g in term_groups(WINE_NAME_GROUPS, not_key="not_wine").items()}


# Foods named in ways the keyword lists miss, found in review round 4. Each lists the flags it
# sets, its other names ("aliases") and the look-alikes that are not it ("not_this").
FOOD_NAME_GROUPS: dict[str, dict[str, list[str]]] = {
    "pilchard": {"flags": ["contains_fish"]},
    "sprat": {"flags": ["contains_fish"], "aliases": ["brisling"]},
    "whitebait": {"flags": ["contains_fish"]},
    "turbot": {"flags": ["contains_fish"]},
    "plaice": {"flags": ["contains_fish"]},
    "barramundi": {"flags": ["contains_fish"]},
    "lingcod": {"flags": ["contains_fish"]},
    "john dory": {"flags": ["contains_fish"]},
    # Chestnuts are tree nuts (FDA); water chestnuts are a vegetable, chestnut mushrooms a mushroom
    "chestnut": {"flags": ["contains_tree_nut"], "aliases": ["marron glacé", "châtaigne"],
                 "not_this": ["water chestnut", "chestnut mushroom"]},
    # Plain "buffalo" stays out: buffalo wings, buffalo sauce and buffalo mozzarella are not buffalo meat
    "buffalo meat": {"flags": ["contains_red_meat"],
                     "aliases": ["ground buffalo", "buffalo steak", "buffalo mince", "minced buffalo"]},
}


def named_foods(flag: str) -> list[str]:
    """Return the FOOD_NAME_GROUPS names (and aliases, every spelling) that set a flag."""
    return term_names({n: g for n, g in FOOD_NAME_GROUPS.items() if flag in g["flags"]})


def not_named_foods(flag: str) -> list[str]:
    """Return the look-alikes of the FOOD_NAME_GROUPS foods that set a flag, every spelling."""
    return with_spellings([p for g in FOOD_NAME_GROUPS.values() if flag in g["flags"] for p in g.get("not_this", [])])


WINE_NAMES = wine_names()
WINE_NAME_EXCEPTIONS = list(dict.fromkeys(p for g in wine_name_groups().values() for p in g["not_wine"]))
ALCOHOL_KEYWORDS  = ["wine", "beer", "ale", "lager", "rum", "vodka", "whiskey", "whisky",
                     "bourbon", "brandy", "cognac", "sherry", "liqueur", "liquor", "tequila", "gin",
                     "sake", "mirin", "champagne", "prosecco", "vermouth", "kahlua", "amaretto",
                     "marsala", "madeira", "schnapps", "triple sec", "grand marnier", "cointreau",
                     "curacao", "chambord", "frangelico", "baileys", "limoncello", "sambuca", "ouzo",
                     "kirsch", "calvados", "armagnac", "grappa", "mezcal", "pisco", "cachaca", "soju",
                     "shaoxing", "shaohsing", "hard cider"] + WINE_NAMES
# Policy (docs/flag_review/flag_policies.csv): oats count as gluten unless labeled gluten-free,
# because most oats are grown and milled next to wheat
# Wheat, barley and rye, including products that are made from them
GLUTEN_KEYWORDS   = ["flour", "bread", "wheat", "pasta", "noodle", "barley", "rye", "oat", "oatmeal",
                     "roll", "rawa", "rava", "sooji", "suji",
                     "soy sauce", "breadcrumb", "cracker", "couscous", "semolina", "bulgur",
                     "spelt", "malt", "seitan", "farro", "orzo", "panko", "beer", "ale", "lager",
                     "brewer's yeast", "brewers yeast", "communion wafer",
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
                     "farina", "wheat germ", "durum", "kamut", "freekeh", "triticale", "einkorn", "emmer",
                     # most soba is part wheat (100% buckwheat soba is in the exceptions)
                     "soba",
                     # sauces and soups usually made with wheat
                     "teriyaki", "hoisin", "oyster sauce", "gochujang", "shoyu", "ponzu", "soya sauce",
                     "cream of mushroom soup", "cream of chicken soup", "cream of celery soup",
                     "minestrone"] + _compounds("contains_gluten")
DAIRY_KEYWORDS    = (["milk", "buttermilk", "cheese", "butter", "cream", "yogurt", "yoghurt",
                     "ghee", "mozzarella", "parmesan", "ricotta", "mascarpone", "feta", "whey",
                     "cheddar", "brie", "camembert", "gouda", "gruyere", "gorgonzola", "burrata",
                     "halloumi", "paneer", "queso", "provolone", "pecorino", "emmental", "manchego",
                     "labneh", "kefir", "quark", "creme fraiche", "half-and-half", "half and half",
                     "custard", "cheesecake", "casein", "caseinate", "whipped topping", "cool whip",
                     "alfredo", "bechamel", "tzatziki", "raita", "lassi", "smen", "niter kibbeh",
                     "niter kebbeh",
                     # cheeses and dairy foods named without "cheese" or "milk"
                     "parmigiano", "grana padano", "comte", "raclette", "fontina", "asiago", "roquefort",
                     "taleggio", "havarti", "jarlsberg", "edam", "muenster", "colby", "monterey jack",
                     "pepper jack", "velveeta", "cotija", "chevre", "stracciatella", "scamorza",
                     "caciocavallo", "kashkaval", "labne", "skyr", "dahi", "curd", "khoa", "khoya", "malai",
                     "rabri", "kulfi", "gelato", "dulce de leche", "cajeta", "lactose", "bearnaise"]
                    + _compounds("contains_dairy"))
EGG_KEYWORDS      = ["egg", "egg white", "egg yolk", "mayonnaise", "mayo", "meringue", "eggnog",
                     "aioli", "hollandaise", "carbonara", "quiche", "frittata", "challah",
                     "brioche", "cheesecake", "macaron", "wonton",
                     # Egg Beaters and similar "egg substitutes" are made from egg whites
                     "eggbeater", "egg beater", "egg substitute",
                     "custard", "albumen", "bearnaise", "lemon curd", "lime curd", "orange curd", "passion fruit curd",
                     "fruit curd"] + _compounds("contains_egg")
# Policy: a plain "nut" may be peanuts, so it sets the peanut flag too
PEANUT_KEYWORDS   = ["peanut", "peanut butter", "peanut oil", "groundnut", "ground nut",
                     "nut", "arachis", "goober",
                     # the bottled sauce; a dish named "satay" is the grilled skewers, whose sauce varies
                     # by region (peanut, turmeric, sweet soy, or none): team decision 2026-10-05
                     "satay sauce",
                     # dishes and products made with peanuts (red-team probe, 2026-10-10); mole poblano and
                     # massaman curry usually have peanuts: flagged on the safe side
                     "gado gado", "gado-gado", "kare-kare", "kare kare", "mole poblano", "massaman", "pb2"] + _compounds("contains_peanut")
TREE_NUT_KEYWORDS = ["almond", "walnut", "pecan", "cashew", "pistachio", "hazelnut",
                     "filbert", "macadamia", "brazil nut", "pine nut", "nut", "nutella",
                     "praline", "marzipan", "macaron", "frangipane", "amaretti", "pesto",
                     "baklava", "nougat", "gianduja", "marcona", "pignoli", "pinoli", "orgeat", "dukkah"] + _compounds("contains_tree_nut") + named_foods("contains_tree_nut")
FISH_KEYWORDS     = ["fish", "salmon", "tuna", "cod", "anchovy", "anchovies", "sardine",
                     "tilapia", "halibut", "trout", "mackerel", "haddock", "catfish",
                     "snapper", "swordfish", "mahi mahi", "flounder", "sole", "hake",
                     "snoek", "pollock", "bass", "kingfish", "orange roughy", "grouper",
                     "perch", "pike", "walleye", "monkfish", "whitefish", "herring",
                     "kipper", "eel", "carp", "bream", "branzino", "surimi", "roe",
                     "fish sauce", "worcestershire sauce", "bonito", "caviar",
                     "dashi", "katsuobushi", "nam pla", "nuoc mam", "caesar dressing",
                     "shark", "unagi", "sturgeon", "skate", "stingray", "fugu", "pufferfish", "lamprey",
                     "marlin", "tilefish", "bullhead", "worcestershire", "imitation crab", "bacalao",
                     "bacalhau", "baccala", "tarama", "taramasalata",
                     # Policy: unspecified "seafood" may be fish or shellfish, so it sets both
                     "seafood"] + _compounds("contains_fish") + named_foods("contains_fish")
# Shellfish is two allergen groups that the EU, Canada, Australia / NZ, Japan and Korea label
# separately: many people allergic to shrimp can eat clams, and the reverse. Policy P5 / P10:
# unspecified "seafood" may be either, so it sets both
# surimi (imitation crab) is fish, but often has crab extract: crustacean too, on the safe side
CRUSTACEAN_KEYWORDS = ["shrimp", "prawn", "crab", "crabmeat", "lobster", "langoustine", "langostino", "surimi",
                       "scampi", "krill", "crawfish", "crayfish", "belacan", "bagoong", "shrimp paste",
                       "xo sauce",
                       "seafood", "frutti di mare"] + _compounds("contains_crustacean", "contains_shellfish")
# Land snails count as molluscs too (EU Regulation 1169/2011)
MOLLUSC_KEYWORDS  = ["clam", "cockle", "mussel", "scallop", "oyster", "squid", "calamari", "octopus",
                     "cuttlefish", "conch", "abalone", "whelk", "periwinkle", "geoduck", "snail", "escargot",
                     "xo sauce",
                     "seafood", "frutti di mare"] + _compounds("contains_mollusc", "contains_shellfish")
SHELLFISH_KEYWORDS = list(dict.fromkeys(CRUSTACEAN_KEYWORDS + MOLLUSC_KEYWORDS))
SOY_KEYWORDS      = ["soy", "soya", "soy sauce", "soybean", "tofu", "tempeh", "edamame",
                     "miso", "tamari", "teriyaki", "hoisin", "gochujang", "doenjang", "natto",
                     "shoyu", "ponzu", "yuba", "okara"] + _compounds("contains_soy")
SESAME_KEYWORDS   = ["sesame", "tahini", "tahina", "halva", "halvah", "za'atar", "zaatar",
                     "za atar", "furikake", "gomasio", "gomashio", "benne", "hummus", "houmous",
                     "hummous", "baba ganoush", "baba ghanoush", "gingelly", "dukkah"] + _compounds("contains_sesame")
LAND_MEAT_KEYWORDS = (["chicken", "beef", "lamb", "mutton", "goat", "turkey", "veal", "duck",
                      "venison", "goose", "rabbit", "bison", "elk", "quail", "pheasant",
                      "cornish hen", "game hen", "fryer", "meat", "steak", "sirloin",
                      "brisket", "chuck", "ground round", "rib eye", "ribeye",
                      "filet mignon", "tri-tip", "porterhouse", "short rib", "oxtail",
                      "pot roast", "rump roast", "round roast", "eye of round", "pastrami",
                      "jerky", "liver", "giblet", "suet", "tallow", "bone marrow",
                      "gelatin", "gelatine", "marshmallow", "jello", "jell-o", "schmaltz", "poultry",
                      "panna cotta", "collagen",
                      "kidney", "tripe", "oxtail", "sweetbread", "horse", "boar", "moose", "kangaroo",
                      "squab", "partridge", "guinea fowl", "poussin", "capon", "foie gras", "mince",
                      "ground meat", "minced meat", "hare", "camel", "alligator", "crocodile", "frog leg",
                      "frogs leg", "frogs' leg", "turtle meat", "turtle soup", "snapping turtle", "squirrel",
                      "guinea pig", "opossum", "possum", "raccoon", "armadillo"]
                     + PORK_KEYWORDS + _compounds("contains_meat"))

# Base flags for the diet profiles in 5.4.7
BEEF_KEYWORDS     = ["beef", "veal", "steak", "brisket", "sirloin", "chuck", "ground round", "rib eye",
                     "ribeye", "filet mignon", "tri-tip", "porterhouse", "t-bone", "flank steak",
                     "skirt steak", "short rib", "oxtail", "pot roast", "rump roast", "round roast",
                     "eye of round", "pastrami", "corned beef", "bresaola", "jerky", "suet", "tallow",
                     "bone marrow", "hamburger", "cheeseburger", "bulgogi"]
# Red meat: meat from mammals, pork included (USDA; WHO / IARC also counts offal). Poultry is
# "white meat"; fish and shellfish are their own groups (contains_fish, contains_shellfish).
RED_MEAT_KEYWORDS = (BEEF_KEYWORDS + PORK_KEYWORDS
                     + ["lamb", "mutton", "goat", "venison", "bison", "elk", "rabbit", "horse", "boar",
                        "moose", "kangaroo", "liver", "kidney", "tripe", "sweetbread", "mince", "merguez",
                        "ground meat", "minced meat"] + named_foods("contains_red_meat"))
POULTRY_KEYWORDS  = ["chicken", "turkey", "duck", "goose", "quail", "pheasant", "cornish hen", "game hen",
                     "poussin", "guinea fowl", "squab", "partridge", "capon", "poultry", "fryer",
                     "foie gras", "schmaltz"]
# Processed meat (WHO / IARC): cured, salted, smoked or fermented meat, poultry included
PROCESSED_MEAT_KEYWORDS = ["bacon", "ham", "prosciutto", "pancetta", "guanciale", "lardon", "salami",
                           "pepperoni", "sausage", "chorizo", "kielbasa", "andouille", "bratwurst",
                           "mortadella", "capicola", "hot dog", "frankfurter", "wiener", "bologna",
                           "corned beef", "pastrami", "jerky", "bresaola", "biltong", "spam",
                           "luncheon meat", "lunch meat", "deli meat", "cold cut", "jamon", "jamón",
                           "speck", "merguez", "boerewors"]
# Meat from animals kept as household pets (dogs, cats, guinea pigs). The project never
# recommends it (policy P24): such recipes are removed in 5.6 and the safety filter rejects them
PET_MEAT_KEYWORDS = ["dog meat", "dogmeat", "cat meat", "puppy meat", "kitten meat", "bosintang",
                     "boshintang", "gaejang", "thit cho", "thịt chó", "thit meo", "thịt mèo",
                     "xiangrou", "guinea pig", "cuy"]
# Every kind of land meat counts for contains_meat and rules out "vegetarian"
LAND_MEAT_KEYWORDS = list(dict.fromkeys(LAND_MEAT_KEYWORDS + BEEF_KEYWORDS + RED_MEAT_KEYWORDS
                                        + POULTRY_KEYWORDS + PROCESSED_MEAT_KEYWORDS + PET_MEAT_KEYWORDS))
MEAT_KEYWORDS     = LAND_MEAT_KEYWORDS + FISH_KEYWORDS + SHELLFISH_KEYWORDS
GELATIN_KEYWORDS  = ["gelatin", "gelatine", "jello", "jell-o", "marshmallow", "gummy", "gummies", "aspic",
                     "panna cotta", "collagen", "jelly bean"]   # set with gelatin; collagen is animal-made
HONEY_KEYWORDS    = ["honey"]
# Jain diets avoid vegetables that grow underground (onion and garlic are in the allium list)
ROOT_VEGETABLE_KEYWORDS = ["potato", "sweet potato", "yam", "carrot", "beet", "beetroot", "radish",
                           "daikon", "turnip", "parsnip", "rutabaga", "swede", "celeriac", "taro",
                           "cassava", "yuca", "jicama", "ginger", "horseradish", "burdock", "salsify",
                           "lotus root", "jerusalem artichoke", "sunchoke"]
ALLIUM_KEYWORDS   = ["onion", "garlic", "leek", "shallot", "scallion", "chive", "spring onion",
                     "green onion"]
# Asafoetida (hing) is one of the five pungent plants Mahayana Buddhists avoid. It is NOT in the
# allium list: Jain and many Hindu cooks use it instead of onion and garlic (policy P16)
ASAFOETIDA_KEYWORDS = ["asafoetida", "asafetida", "hing"]
MUSHROOM_KEYWORDS = ["mushroom", "shiitake", "portobello", "portabella", "portabello", "portobella",
                     "cremini", "crimini", "chanterelle", "porcini", "morel", "enoki", "maitake", "shimeji",
                     "wood ear", "cloud ear", "king trumpet", "cep",
                     # policy P19: savory truffles only, not chocolate truffles
                     "black truffle", "white truffle", "truffle oil", "truffle salt", "truffle butter",
                     "truffle paste"]
# Red coloring made from insects: not vegan, not kosher (policy P11)
CARMINE_KEYWORDS  = ["carmine", "cochineal", "carminic acid", "crimson lake", "natural red 4"]
# Rennet named in the ingredients (policy P18: animal rennet without confirmed halal sourcing is
# not halal-friendly). Cheese made with rennet is not flagged: labels rarely say which rennet is used
RENNET_KEYWORDS   = ["rennet", "rennin", "rennet tablet", "junket tablet", "junket rennet", "calf rennet",
                     "animal rennet"]
RENNET_EXCEPTIONS = ["vegetable rennet", "vegetarian rennet", "microbial rennet", "plant rennet",
                     "non-animal rennet", "nonanimal rennet"]
ANIMAL_KEYWORDS   = MEAT_KEYWORDS + DAIRY_KEYWORDS + EGG_KEYWORDS + ["honey"] + CARMINE_KEYWORDS

# --- Allergens labeled outside the US (EU / UK, Canada, Australia / NZ, Japan, Korea) ---
# Policy P12: mustard greens count (EU and UK guidance treats mustard leaves as a possible
# source), and so do mixes that are mostly celery (mirepoix, Old Bay seasoning)
MUSTARD_KEYWORDS  = ["mustard", "dijon", "mustard seed", "mustard oil", "mustard green", "dry mustard",
                     "honey mustard", "kasundi", "piccalilli"] + _compounds("contains_mustard")
CELERY_KEYWORDS   = ["celery", "celeriac", "celery root", "celery seed", "celery salt", "mirepoix",
                     "old bay"] + _compounds("contains_celery")
LUPIN_KEYWORDS    = ["lupin", "lupine", "lupini"] + _compounds("contains_lupin")
# Buckwheat is not wheat and has no gluten, but Japan and Korea label it: soba noodles
BUCKWHEAT_KEYWORDS = ["buckwheat", "soba", "kasha", "kuttu", "pizzoccheri", "naengmyeon",
                      "memil"] + _compounds("contains_buckwheat")
# Policy P13: ingredients that usually contain added sulfites, so "may contain sulfites"
SULFITE_KEYWORDS  = ["sulfite", "sulphite", "metabisulfite", "metabisulphite", "sulfur dioxide",
                     "sulphur dioxide", "wine", "sherry", "champagne", "prosecco", "vermouth", "marsala",
                     "madeira", "port wine", "hard cider", *WINE_NAMES, "dried apricot", "golden raisin", "sultana",
                     "maraschino", "dried fruit", "sulphured molasses", "sulfured molasses"] + _compounds("contains_sulfites")

# --- Religious and cultural diets ---
# Fish without fins and scales are not kosher, and not "clean" for Seventh-day Adventists or
# Rastafari (policy P11; swordfish and sturgeon lose their scales, so they count)
SCALELESS_FISH_KEYWORDS = ["catfish", "eel", "unagi", "shark", "monkfish", "swordfish", "sturgeon",
                           "caviar", "skate", "stingray", "fugu", "pufferfish", "lamprey", "bullhead"]
# Land animals that are not kosher or Adventist "clean" besides pork (policy P11)
UNCLEAN_MEAT_KEYWORDS = ["rabbit", "hare", "horse", "camel", "kangaroo", "alligator", "crocodile",
                         "frog leg", "frogs leg", "frogs' leg", "turtle meat", "turtle soup", "snapping turtle",
                         "squirrel", "guinea pig", "opossum", "possum", "raccoon", "armadillo"]
# Policy P15: Latter-day Saints avoid coffee and tea, decaf included; herbal teas are not "tea"
COFFEE_TEA_KEYWORDS = ["coffee", "espresso", "instant coffee", "cappuccino", "latte", "mocha", "tea",
                       "green tea", "black tea", "matcha", "chai", "earl grey", "oolong", "kahlua",
                       "coffee liqueur", "tia maria", "yerba mate"]
# Many Rastafari (Ital diet) cook without added salt
SALT_KEYWORDS     = ["salt"]
# Flavor extracts and bitters are made with alcohol (vanilla extract is about 35%). Kept apart from
# contains_alcohol (alcohol-free diets and pregnancy differ); halal_friendly rules them out (policy P18).
# A plain "vanilla" in an ingredient list almost always means the liquid extract
ALCOHOL_EXTRACT_KEYWORDS = ["vanilla", "vanilla extract", "vanilla essence", "pure vanilla", "almond extract",
                            "lemon extract", "orange extract", "peppermint extract", "mint extract",
                            "coconut extract", "rum extract", "brandy extract", "maple extract", "anise extract",
                            "banana extract", "raspberry extract", "strawberry extract", "cherry extract",
                            "hazelnut extract", "flavoring extract", "bitters", "angostura"]

# --- Medical diets: a screen for the ingredients to talk about with a doctor, never advice (P17) ---
# G6PD deficiency (favism). Policy P14: falafel counts (Egyptian falafel is made from fava beans)
FAVA_KEYWORDS     = ["fava", "faba", "broad bean", "ful", "ful medames", "foul medames", "ful mudammas",
                     "habas", "falafel", "ta'ameya", "taameya", "bissara"]
# Tomato, potato, peppers and chilies, eggplant (plain "pepper" is black pepper, not a nightshade)
NIGHTSHADE_KEYWORDS = ["tomato", "tomatillo", "potato", "eggplant", "aubergine", "brinjal", "bell pepper",
                       "red pepper", "green pepper", "yellow pepper", "orange pepper", "sweet pepper",
                       "hot pepper", "chili", "chile", "chilli", "jalapeno", "jalapeño", "serrano", "habanero",
                       "poblano", "chipotle", "ancho", "anaheim", "scotch bonnet", "cayenne", "paprika",
                       "pimento", "pimiento", "pepperoncini", "banana pepper", "piquillo", "sriracha",
                       "harissa", "gochujang", "gochugaru", "hot sauce", "tabasco", "salsa", "ketchup",
                       "catsup", "marinara", "pepper jack", "goji", "tamarillo"]
# FDA / EPA "choices to avoid" in pregnancy and for young children
HIGH_MERCURY_FISH_KEYWORDS = ["king mackerel", "marlin", "orange roughy", "shark", "swordfish", "tilefish",
                              "bigeye tuna"]
# Raw or undercooked animal foods (pregnancy). Notebook 02's cooking methods can refine this later
RAW_ANIMAL_KEYWORDS = ["sushi", "sashimi", "tartare", "carpaccio", "ceviche", "poke", "crudo", "gravlax",
                       "gravad lax", "lox", "smoked salmon", "raw egg", "raw oyster", "raw milk",
                       "unpasteurized", "unpasteurised", "medium rare", "medium-rare", "kitfo", "yukhoe",
                       "kibbeh nayeh", "mett", "tiramisu", "eggnog"]
# Soft and mold-ripened cheeses (pregnancy: Listeria) unless pasteurized or cooked until hot
SOFT_CHEESE_KEYWORDS = ["brie", "camembert", "blue cheese", "roquefort", "gorgonzola", "danish blue",
                        "queso fresco", "queso blanco", "queso panela", "chevre", "chèvre", "raw milk cheese"]
# Gout: high-purine foods
HIGH_PURINE_KEYWORDS = ["liver", "liverwurst", "kidney", "sweetbread", "brain", "anchovy", "anchovies",
                        "sardine", "herring", "mackerel", "mussel", "scallop", "trout", "roe", "caviar",
                        "beer", "yeast extract", "marmite", "vegemite", "meat extract"]
# MAOI medicines: high-tyramine foods (aged cheese, cured meat, fermented foods)
HIGH_TYRAMINE_KEYWORDS = ["cheddar", "parmesan", "parmigiano", "pecorino", "romano", "gouda", "gruyere",
                          "emmental", "swiss cheese", "blue cheese", "gorgonzola", "roquefort", "stilton",
                          "brie", "camembert", "aged cheese", "salami", "pepperoni", "chorizo",
                          "summer sausage", "mortadella", "prosciutto", "soppressata", "pastrami",
                          "sauerkraut", "kimchi", "miso", "natto", "soy sauce", "fish sauce", "shrimp paste",
                          "belacan", "bagoong", "yeast extract", "marmite", "vegemite", "fava", "broad bean",
                          "tap beer", "draft beer", "chianti"]

# Phrases that contain a keyword but are not that food
# (removed from the text before keywords are matched, longest first)
# Not meat at all, though named like pork products: excepted by the pork, meat and processed-meat flags
# alike (notebook 01 rerun, 2026-10-10: "Vegan Mushroom Pâté" lost its vegan flag when only pork knew)
NOT_MEAT_LOOKALIKES = ["tonkatsu sauce", "mushroom pâté", "vegan pâté", "vegetarian pâté", "pâte brisée",
                       "pâte sucrée", "pâte sablée", "pâte à choux", "pâte feuilletée", "pate brisee",
                       "pate sucree", "pate sablee", "pate a choux", "plant-based chorizo", "vegan chorizo",
                       "soy chorizo", "soyrizo"]
PORK_EXCEPTIONS     = ["hot dog bun", "hot dog roll", "vegetarian sausage", "veggie sausage",
                       "vegan sausage", "vegetarian bacon", "turkey bacon", "turkey ham",
                       "turkey kielbasa", "turkey sausage", "chicken sausage", "merguez sausage",
                       "merguez", "lamb sausage", "beef sausage", "vegan bacon", "char siu sauce",
                       # halal-certified versions are made without pork (red-team round, 2026-10-10)
                       "halal chorizo", "halal sausage", "halal pepperoni", "halal salami", "halal hot dog",
                       "halal bacon", "halal ham", "halal frankfurter", "halal bologna",
                       "halal-certified chorizo", "halal certified chorizo", "halal-certified sausage",
                       "halal certified sausage", "halal-certified pepperoni", "halal-certified salami",
                       "plant-based chorizo", "vegan chorizo", "soy chorizo", "soyrizo",
                       "tonkatsu sauce", "chicken liver pâté", "duck pâté", "salmon pâté", "mushroom pâté",
                       "vegan pâté", "vegetarian pâté",
                       # French pastry doughs ("pâte"), which look like "pâté" without accents
                       "pâte brisée", "pâte sucrée", "pâte sablée", "pâte à choux", "pâte feuilletée",
                       "pate brisee", "pate sucree", "pate sablee", "pate a choux",
                       # meat named after a pork product, and plant-based look-alikes
                       "turkey pepperoni", "beef pepperoni", "chicken pepperoni", "turkey chorizo",
                       "beef chorizo", "chicken chorizo", "turkey salami", "beef salami", "beef hot dog",
                       "turkey hot dog", "chicken hot dog", "beef frankfurter", "turkey frankfurter",
                       "beef bologna", "turkey bologna", "beyond sausage", "beyond beef", "beyond burger",
                       "beyond meat", "impossible beef", "impossible pork", "impossible sausage",
                       "plant-based sausage", "plant based sausage", "plant-based beef", "plant based beef",
                       "plant-based chicken", "plant based chicken", "vegan chicken", "vegetarian chicken",
                       "vegan pepperoni", "vegetarian pepperoni", "vegan chorizo", "vegetarian chorizo",
                       "soy chorizo", "vegan ham", "vegan beef"]
ALCOHOL_EXCEPTIONS  = ["sherry wine vinegar", "wine vinegar", "sherry vinegar", "ginger ale", "ginger beer", "root beer",
                       "non-alcoholic", "alcohol-free", "alcohol free"] + WINE_NAME_EXCEPTIONS
# "gluten-free bread", "gluten free pasta", ...: the food after "gluten-free" is safe
GLUTEN_FREE_FOODS   = ["bread", "flour", "pasta", "noodle", "noodles", "spaghetti", "penne",
                       "macaroni", "cracker", "crackers", "breadcrumb", "breadcrumbs", "soy sauce",
                       "beer", "cookie", "cookies", "dough", "pizza crust", "pie crust", "baking mix",
                       "bisquick", "muffin", "muffins", "bun", "buns", "tortilla", "tortillas",
                       "oats", "rolled oats", "oat", "oatmeal", "oat flour", "teriyaki", "hoisin",
                       "stuffing", "pretzel", "pretzels"]
GLUTEN_EXCEPTIONS   = (["rice flour", "almond flour", "coconut flour", "corn flour", "chickpea flour",
                        "tapioca flour", "potato flour", "cassava flour", "sorghum flour",
                        "arrowroot flour", "teff flour", "millet flour", "quinoa flour",
                        "banana flour", "rice noodle", "rice vermicelli", "rice stick", "rice paper",
                        "glass noodle", "cellophane noodle", "bean thread", "shirataki",
                        "kelp noodle", "zucchini noodle", "sweet potato noodle", "konjac",
                        "spaghetti squash", "cauliflower crust", "corn tortilla", "ginger ale",
                        "rice pasta", "corn pasta", "chickpea pasta", "lentil pasta", "rice cracker",
                        "pasta sauce", "spaghetti sauce", "rice stuffing",
                        "ginger beer", "root beer", "gluten-free", "gluten free",
                        # "roll" that is not bread
                        "sushi roll", "california roll", "rice paper roll", "summer roll", "cabbage roll",
                        "lettuce roll", "fruit roll", "rice roll",
                        "100% buckwheat soba", "juwari soba", "buckwheat soba"]
                       + [f"gluten{sep}free {food}" for sep in ("-", " ") for food in GLUTEN_FREE_FOODS])
DAIRY_EXCEPTIONS    = ["coconut milk", "almond milk", "soy milk", "oat milk", "rice milk",
                       "cashew milk", "coconut cream", "cream of tartar", "peanut butter",
                       "almond butter", "cashew butter", "apple butter", "cocoa butter",
                       "shea butter", "butter bean", "butter lettuce", "butterhead lettuce",
                       "vegan butter", "plant butter", "vegan cheese", "vegan cream cheese",
                       "dairy-free cheese", "dairy free cheese", "cashew cream", "oat cream",
                       "soy cream", "coconut yogurt", "soy yogurt", "almond yogurt", "vegan yogurt",
                       "non-dairy", "nondairy", "dairy-free", "dairy free",
                       "bean curd", "soy curd", "tofu curd", "custard apple", "vegan gelato",
                       "dairy-free gelato", "dairy free gelato"]
EGG_EXCEPTIONS      = ["eggless", "egg-free", "egg free", "egg replacer", "vegan mayo",
                       "vegan mayonnaise", "flax egg", "chia egg",
                       "custard apple", "custard powder", "vegan custard", "eggless custard",
                       "custard cup", "custard style", "custard-style", "bird's custard", "bird's eye custard"]
PEANUT_EXCEPTIONS   = ["peanut-free", "peanut free", "nut-free", "nut free", "pine nut", "brazil nut",
                       "tiger nut", "macadamia nut", "cashew nut", "pistachio nut", "pecan nut", "hazel nut",
                       "kola nut", "betel nut", "candle nut", "candlenut"]
TREE_NUT_EXCEPTIONS = ["nut-free", "nut free", "tiger nut", "ground nut"] + not_named_foods("contains_tree_nut")
# Oyster mushrooms, often listed as "wild mushrooms (such as oyster, shiitake ...)"
OYSTER_MUSHROOM_PHRASES = ["oyster mushroom", "king oyster", "such as oyster", "oyster, shiitake",
                           "oyster, crimini", "oyster and shiitake", "shiitake and oyster",
                           "oyster or shiitake", "shiitake or oyster"]
NOT_SEAFOOD_PHRASES = ["seafood seasoning", "seafood boil seasoning", "seafood sauce"]
FISH_EXCEPTIONS     = ["mock caviar", "texas caviar", "cowboy caviar", "southwestern caviar",
                       "eggplant caviar", "poor man's caviar", "vegetarian caviar",
                       "vegan worcestershire", "vegetarian worcestershire"] + NOT_SEAFOOD_PHRASES
SHELLFISH_EXCEPTIONS = OYSTER_MUSHROOM_PHRASES + NOT_SEAFOOD_PHRASES
# Used for "vegetarian" (all meat, fish and shellfish keywords)
MEAT_EXCEPTIONS     = OYSTER_MUSHROOM_PHRASES + FISH_EXCEPTIONS + NOT_MEAT_LOOKALIKES + [
                       "duck sauce", "lamb's lettuce", "vegetarian sausage",
                       "veggie sausage", "vegan sausage", "meatless", "meat substitute",
                       "steak sauce", "steak seasoning", "cauliflower steak",
                       "hot dog bun", "hot dog roll", "goat cheese", "goats cheese",
                       "goat's cheese", "goat milk", "goat's milk", "vegan marshmallow",
                       "vegetarian marshmallow", "portobello steak", "portabella steak",
                       "portobella steak", "mushroom steak", "kidney bean", "horseradish", "chicken-fried",
                       "chicken fried", "poultry seasoning", "air fryer", "air-fryer", "deep fryer",
                       "horse gram", "welsh rabbit", "welsh rarebit",
                       # meat named after a pork product, and plant-based look-alikes
                       "beyond sausage", "beyond beef", "beyond burger", "beyond meat", "impossible beef",
                       "impossible pork", "impossible sausage", "plant-based sausage", "plant based sausage",
                       "plant-based beef", "plant based beef", "plant-based chicken", "plant based chicken",
                       "vegan chicken", "vegetarian chicken", "vegan pepperoni", "vegetarian pepperoni",
                       "vegan chorizo", "vegetarian chorizo", "soy chorizo", "vegan ham", "vegan beef"]
# Used for contains_meat (land meat only): a fish steak is not meat
LAND_MEAT_EXCEPTIONS = MEAT_EXCEPTIONS + ["tuna steak", "salmon steak", "fish steak", "swordfish steak",
                                          "halibut steak", "cod steak"]
# Goat cheese and goat milk are not meat, but they are animal products, so they stay for "vegan"
ANIMAL_EXCEPTIONS   = [p for p in MEAT_EXCEPTIONS if not p.startswith("goat")] + DAIRY_EXCEPTIONS + EGG_EXCEPTIONS
BEEF_EXCEPTIONS     = ["tuna steak", "salmon steak", "fish steak", "swordfish steak", "cauliflower steak",
                       "steak sauce", "steak seasoning", "beefsteak tomato", "beef tomato",
                       "hamburger bun", "hamburger roll", "hamburger helper", "turkey jerky",
                       "mushroom jerky", "veggie burger", "portobello steak", "portabella steak",
                       "portobella steak", "mushroom steak", "halibut steak", "cod steak",
                       # meat named after a pork product, and plant-based look-alikes
                       "beyond beef", "impossible beef", "plant-based beef", "plant based beef",
                       "vegan beef"]
# A pork look-alike made of another red meat ("beef hot dog", "lamb sausage") is still red meat
RED_MEATS = ("beef", "all-beef", "all beef", "kosher", "reduced-fat beef", "lamb", "merguez", "mutton", "goat",
             "veal", "bison", "venison")
RED_MEAT_EXCEPTIONS = LAND_MEAT_EXCEPTIONS + BEEF_EXCEPTIONS + [
                       p for p in PORK_EXCEPTIONS if not p.startswith(RED_MEATS)] + [
                       "chicken liver", "duck liver", "goose liver", "turkey bacon", "turkey ham",
                       "turkey sausage", "chicken sausage", "turkey jerky"]
POULTRY_EXCEPTIONS  = LAND_MEAT_EXCEPTIONS
PROCESSED_MEAT_EXCEPTIONS = NOT_MEAT_LOOKALIKES + ["vegetarian sausage", "veggie sausage", "vegan sausage", "vegetarian bacon",
                             "vegan bacon", "hot dog bun", "hot dog roll", "meatless",
                             # meat named after a pork product, and plant-based look-alikes
                             "beyond sausage", "beyond beef", "beyond burger", "beyond meat",
                             "impossible beef", "impossible pork", "impossible sausage",
                             "plant-based sausage", "plant based sausage", "plant-based beef",
                             "plant based beef", "plant-based chicken", "plant based chicken",
                             "vegan chicken", "vegetarian chicken", "vegan pepperoni",
                             "vegetarian pepperoni", "vegan chorizo", "vegetarian chorizo", "soy chorizo",
                             "vegan ham", "vegan beef"]
GELATIN_EXCEPTIONS  = ["agar", "vegan gelatin", "vegan marshmallow", "vegetarian marshmallow", "vegan gummy"]
HONEY_EXCEPTIONS    = ["honey crisp", "honeycrisp"]
ROOT_VEGETABLE_EXCEPTIONS = ["ground ginger", "dried ginger", "ginger powder", "ginger ale", "ginger beer"]
ALLIUM_EXCEPTIONS   = ["onion seed", "onion seeds"]
MUSHROOM_EXCEPTIONS = ["chocolate truffle"]
# "Chuka soba" and "Okinawa soba" are wheat noodles; yakisoba is one word, so it never matches
BUCKWHEAT_EXCEPTIONS = ["chuka soba", "okinawa soba"]
SULFITE_EXCEPTIONS  = ["unsulfured", "unsulphured", "sulfite-free", "sulfite free", "sulphite-free",
                       "sulphite free", "no added sulfites"] + WINE_NAME_EXCEPTIONS
# "Eel sauce" (unagi sauce) is soy sauce, mirin and sugar
SCALELESS_FISH_EXCEPTIONS = FISH_EXCEPTIONS + ["eel sauce", "unagi sauce"]
# "Welsh rabbit" is cheese on toast; horse gram is a lentil
UNCLEAN_MEAT_EXCEPTIONS = ["welsh rabbit", "welsh rarebit", "horse gram", "horseradish"]
# Dishes named after the drink they are served with, creamers and herbal teas
COFFEE_TEA_EXCEPTIONS = ["coffee cake", "coffeecake", "coffee creamer", "coffee-mate", "coffee mate",
                         "tea cake", "teacake", "tea sandwich", "tea biscuit", "tea bread", "tea party",
                         "tea time", "teatime", "high tea", "afternoon tea", "tea towel", "herbal tea",
                         "herb tea", "chamomile tea", "camomile tea", "peppermint tea", "rooibos tea",
                         "hibiscus tea", "fruit tea", "ginger tea", "long island iced tea", "long island tea"]
SALT_EXCEPTIONS     = ["salt-free", "salt free", "no-salt", "no salt", "salt substitute", "epsom salt"]
# Vanilla products that are not the liquid extract
ALCOHOL_EXTRACT_EXCEPTIONS = ["vanilla bean", "vanilla pod", "vanilla powder", "vanilla sugar", "vanilla ice cream",
                              "vanilla pudding", "vanilla instant pudding", "vanilla yogurt", "vanilla greek yogurt",
                              "vanilla wafer", "vanilla frosting", "vanilla cake mix", "vanilla protein",
                              "vanilla almond milk", "vanilla soy milk", "vanilla soymilk", "vanilla coconut milk",
                              "vanilla creamer", "vanilla chip", "vanilla cookie", "vanilla bean ice cream",
                              "alcohol-free", "alcohol free", "non-alcoholic",
                              # the phrase must cover the keyword it clears ("alcohol-free vanilla")
                              "alcohol-free vanilla", "alcohol free vanilla", "non-alcoholic vanilla",
                              "nonalcoholic vanilla", "vanilla glycerite", "glycerin vanilla"]
NIGHTSHADE_EXCEPTIONS = ["sweet potato", "serrano ham", "jamon serrano", "jamón serrano"]
RAW_ANIMAL_EXCEPTIONS = ["sushi rice", "sushi vinegar", "sushi nori", "vegetable sushi", "vegetarian sushi",
                         "veggie sushi", "vegan sushi", "cucumber sushi", "avocado sushi", "poke cake",
                         "cooked eggnog", "eggnog flavored", "eggnog-flavored", "store-bought eggnog"]
HIGH_PURINE_EXCEPTIONS = ["kidney bean", "root beer", "ginger beer", "non-alcoholic beer", "alcohol-free beer"]
HIGH_TYRAMINE_EXCEPTIONS = ["romano bean"]
# Hot dogs, chili dogs and corn dogs are sausages; yukgaejang is a spicy beef soup
PET_MEAT_EXCEPTIONS = ["hot dog", "chili dog", "chilli dog", "corn dog", "coney dog", "yuk gaejang",
                       "yook gaejang"]

# Flag column -> (keywords, exceptions)
FLAG_RULES = {
    "contains_pork"     : (PORK_KEYWORDS, PORK_EXCEPTIONS),
    "contains_alcohol"  : (ALCOHOL_KEYWORDS, ALCOHOL_EXCEPTIONS),
    "contains_gluten"   : (GLUTEN_KEYWORDS, GLUTEN_EXCEPTIONS),
    "contains_dairy"    : (DAIRY_KEYWORDS, DAIRY_EXCEPTIONS),
    "contains_egg"      : (EGG_KEYWORDS, EGG_EXCEPTIONS),
    "contains_peanut"   : (PEANUT_KEYWORDS, PEANUT_EXCEPTIONS),
    "contains_tree_nut" : (TREE_NUT_KEYWORDS, TREE_NUT_EXCEPTIONS),
    "contains_fish"     : (FISH_KEYWORDS, FISH_EXCEPTIONS),
    "contains_shellfish": (SHELLFISH_KEYWORDS, SHELLFISH_EXCEPTIONS),
    "contains_crustacean": (CRUSTACEAN_KEYWORDS, SHELLFISH_EXCEPTIONS),
    "contains_mollusc"  : (MOLLUSC_KEYWORDS, SHELLFISH_EXCEPTIONS),
    "contains_soy"      : (SOY_KEYWORDS, ()),
    "contains_sesame"   : (SESAME_KEYWORDS, ()),
    # Allergens labeled outside the US (diets.ALLERGEN_SETS)
    "contains_mustard"  : (MUSTARD_KEYWORDS, ()),
    "contains_celery"   : (CELERY_KEYWORDS, ()),
    "contains_lupin"    : (LUPIN_KEYWORDS, ()),
    "contains_buckwheat": (BUCKWHEAT_KEYWORDS, BUCKWHEAT_EXCEPTIONS),
    "contains_sulfites" : (SULFITE_KEYWORDS, SULFITE_EXCEPTIONS),
    # Base flags used by the diet profiles (5.4.7)
    "contains_meat"     : (LAND_MEAT_KEYWORDS, LAND_MEAT_EXCEPTIONS),   # meat or poultry, not fish
    "contains_beef"     : (BEEF_KEYWORDS, BEEF_EXCEPTIONS),
    "contains_red_meat" : (RED_MEAT_KEYWORDS, RED_MEAT_EXCEPTIONS),     # mammals, pork included
    "contains_poultry"  : (POULTRY_KEYWORDS, POULTRY_EXCEPTIONS),       # "white meat"
    "contains_processed_meat": (PROCESSED_MEAT_KEYWORDS, PROCESSED_MEAT_EXCEPTIONS),
    "contains_gelatin"  : (GELATIN_KEYWORDS, GELATIN_EXCEPTIONS),
    "contains_honey"    : (HONEY_KEYWORDS, HONEY_EXCEPTIONS),
    "contains_root_vegetable": (ROOT_VEGETABLE_KEYWORDS, ROOT_VEGETABLE_EXCEPTIONS),
    "contains_allium"   : (ALLIUM_KEYWORDS, ALLIUM_EXCEPTIONS),
    "contains_asafoetida": (ASAFOETIDA_KEYWORDS, ()),
    "contains_mushroom" : (MUSHROOM_KEYWORDS, MUSHROOM_EXCEPTIONS),
    "contains_carmine"  : (CARMINE_KEYWORDS, ()),
    "contains_rennet"   : (RENNET_KEYWORDS, RENNET_EXCEPTIONS),
    "contains_scaleless_fish": (SCALELESS_FISH_KEYWORDS, SCALELESS_FISH_EXCEPTIONS),
    "contains_unclean_meat": (UNCLEAN_MEAT_KEYWORDS, UNCLEAN_MEAT_EXCEPTIONS),
    "contains_pet_meat" : (PET_MEAT_KEYWORDS, PET_MEAT_EXCEPTIONS),
    "contains_coffee_or_tea": (COFFEE_TEA_KEYWORDS, COFFEE_TEA_EXCEPTIONS),
    "contains_added_salt": (SALT_KEYWORDS, SALT_EXCEPTIONS),
    "contains_alcohol_extract": (ALCOHOL_EXTRACT_KEYWORDS, ALCOHOL_EXTRACT_EXCEPTIONS),
    # Medical screens (policy P17): ingredients to discuss with a doctor, never medical advice
    "contains_fava"     : (FAVA_KEYWORDS, ()),
    "contains_nightshade": (NIGHTSHADE_KEYWORDS, NIGHTSHADE_EXCEPTIONS),
    "contains_high_mercury_fish": (HIGH_MERCURY_FISH_KEYWORDS, ()),
    "contains_raw_animal": (RAW_ANIMAL_KEYWORDS, RAW_ANIMAL_EXCEPTIONS),
    "contains_soft_cheese": (SOFT_CHEESE_KEYWORDS, ()),
    "contains_high_purine": (HIGH_PURINE_KEYWORDS, HIGH_PURINE_EXCEPTIONS),
    "contains_high_tyramine": (HIGH_TYRAMINE_KEYWORDS, HIGH_TYRAMINE_EXCEPTIONS),
}
FLAG_COLUMNS = list(FLAG_RULES) + ["vegetarian", "vegan"]


@cache
def _exception_pattern(phrases: tuple[str, ...]) -> re.Pattern[str] | None:
    """Compile one regex for exception phrases in every spelling, longest first (cached).

    Longest first removes 'sweet potato' before 'potato'. A phrase must start a word,
    so 'oat milk' is not removed from 'goat milk'; its end may run on ('kidney beans').
    """
    if not phrases:
        return None
    alternatives = "|".join(re.escape(p) for p in sorted(with_spellings(phrases), key=len, reverse=True))
    return re.compile(rf"\b(?:{alternatives})")


def _spellings_of_text(text: str) -> list[str]:
    """Return the text, plus its form without accents when it has any ("jalapeño" -> "jalapeno")."""
    if text.isascii():
        return [text]
    plain = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    return [text, plain]


def _without_phrases(text: str, phrases: Sequence[str]) -> str:
    """Replace every exception phrase in `text` with a space, longest first."""
    pattern = _exception_pattern(tuple(phrases))
    return pattern.sub(" ", text) if pattern else text


@cache
def _keyword_pattern(keywords):
    """Compile one whole-word regex for a tuple of keywords in every spelling (plurals allowed)."""
    alternatives = "|".join(re.escape(k) for k in sorted(with_spellings(keywords), key=len, reverse=True))
    return re.compile(rf"\b(?:{alternatives})(?:s|es)?\b")


def make_flag(ingredient_str: object, keywords: Sequence[str], exceptions: Sequence[str] = ()) -> bool:
    """Check whether any keyword appears as a whole word in a text.

    Whole-word matching avoids false hits such as 'ham' in 'graham' or 'egg'
    in 'eggplant'; plural endings (-s, -es) still match. Exception phrases
    (for example 'coconut milk') are removed first, longest first, so they
    never trigger a keyword. Keywords and exceptions match in every spelling
    (spelling_variants), and accented text is also read without its accents.

    Args:
        ingredient_str: The text to search (ingredients and name); anything else gives False.
        keywords: Words or phrases that mean the recipe has the flag.
        exceptions: Phrases to ignore before matching.

    Returns:
        True if a keyword is found.
    """
    if not isinstance(ingredient_str, str):
        return False
    pattern = _keyword_pattern(tuple(keywords))
    return any(pattern.search(_without_phrases(text, exceptions)) for text in _spellings_of_text(ingredient_str.lower()))

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
        # Ready-made ingredients count only in the ingredient list, not in the dish name
        text = text + " | " + names.apply(name_text)
        # "Gluten-free bread" or "flourless cookies": the name describes the kind of dish,
        # not a wheat ingredient, so only the ingredients count for gluten
        gluten_text = text.where(~names.str.contains(GLUTEN_FREE_NAME), gluten_text)
    rules = progress_bar(FLAG_RULES.items(), "Restriction flags", show=len(df) >= MIN_ROWS)
    for col, (keywords, exceptions) in rules:
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


def explain_flag(text: object, column: str) -> list[str]:
    """Return the keywords that set a flag, so a reviewer can see why it fired.

    Args:
        text: Lowercase ingredients and name, as for keyword_flag.
        column: Any of FLAG_COLUMNS. For "vegetarian" and "vegan" the keywords
            returned are the ones that rule the diet out.

    Returns:
        The matched keywords (as written in the text), each once; [] if none.
        Hugging Face recipes can also get a flag from the dataset's own labels
        (HF_FREE_LABELS), which this function does not see.
    """
    if not isinstance(text, str):
        return []
    keywords: Sequence[str]
    exceptions: Sequence[str]
    if column == "vegetarian":
        keywords, exceptions = MEAT_KEYWORDS, MEAT_EXCEPTIONS
    elif column == "vegan":
        keywords, exceptions = ANIMAL_KEYWORDS, ANIMAL_EXCEPTIONS
    else:
        keywords, exceptions = FLAG_RULES[column]
    pattern = _keyword_pattern(tuple(keywords))
    found: dict[str, str] = {}   # spelling without accents -> the keyword as written in the text
    for t in _spellings_of_text(text.lower()):
        for m in pattern.finditer(_without_phrases(t, exceptions)):
            found.setdefault(_spellings_of_text(m.group(0))[-1], m.group(0))   # "jalapeño" once, not twice
    return list(found.values())


def flags_for_term(term: str) -> list[str]:
    """Return the flags a word or phrase sets on its own, such as "chestnut" -> ["contains_tree_nut"].

    Args:
        term: An ingredient, in any spelling ("jalapeño" or "jalapeno").

    Returns:
        The FLAG_RULES columns the term sets, in FLAG_COLUMNS order; [] if none.
    """
    return [flag for flag, (keywords, exceptions) in FLAG_RULES.items() if make_flag(term, keywords, exceptions)]


def term_group_of(term: str) -> str | None:
    """Return the name group (WINE_NAME_GROUPS or FOOD_NAME_GROUPS) a spelling belongs to.

    Args:
        term: A name in any spelling, such as "syrah" or "brisling".

    Returns:
        The group's name ("shiraz", "sprat"), or None when the term is in no group.
    """
    term = term.lower()
    for groups, not_key in ((WINE_NAME_GROUPS, "not_wine"), (FOOD_NAME_GROUPS, "not_this")):
        for name, group in term_groups(groups, not_key).items():
            if term in group["same"]:
                return name
    return None


# Flag column -> the "free of" label that rules it out
HF_FREE_LABELS = {
    "contains_gluten"   : "gluten-free",
    "contains_dairy"    : "dairy-free",
    "contains_egg"      : "egg-free",
    "contains_peanut"   : "peanut-free",
    "contains_tree_nut" : "tree-nut-free",
    "contains_fish"     : "fish-free",
    "contains_shellfish": "shellfish-free",
    # The dataset has no separate crustacean / mollusc labels, so "shellfish-free" rules out both
    "contains_crustacean": "shellfish-free",
    "contains_mollusc"  : "shellfish-free",
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
    width = max(len(flag) for flag in FLAG_COLUMNS)
    for flag in FLAG_COLUMNS:
        print(f"  {flag:{width}s}: {df[flag].sum():>8,} ({df[flag].mean() * 100:.1f}%)")
