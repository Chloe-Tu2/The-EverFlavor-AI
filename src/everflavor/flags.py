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
    "PEANUT_EXCEPTIONS",
    "PEANUT_KEYWORDS",
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
    "add_foodcom_diet_flags",
    "add_hf_diet_flags",
    "add_keyword_flags",
    "explain_flag",
    "foodcom_tag_agreement",
    "keyword_flag",
    "make_flag",
    "print_flag_counts",
]


# --- Ready-made ingredients whose allergens are hidden from the recipe (5.13) ---
# Ingredient -> the flags it adds. Each entry comes from Open Food Facts evidence
# (most matching products declare the allergen) and is listed with the team's
# decision in docs/flag_review/compound_ingredients_review.csv; 5.13 checks that
# the two agree. Entries only ever add flags (the safe direction).
COMPOUND_INGREDIENTS: dict[str, list[str]] = {
    "christmas pudding": ["contains_gluten", "contains_egg"],
}


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
                     "frankfurter", "wiener", "bologna", "jamon", "jamón"]
ALCOHOL_KEYWORDS  = ["wine", "beer", "ale", "lager", "rum", "vodka", "whiskey", "whisky",
                     "bourbon", "brandy", "cognac", "sherry", "liqueur", "liquor", "tequila", "gin",
                     "sake", "mirin", "champagne", "prosecco", "vermouth", "kahlua", "amaretto",
                     "marsala", "madeira", "schnapps", "triple sec", "grand marnier", "cointreau",
                     "curacao", "chambord", "frangelico", "baileys", "limoncello", "sambuca", "ouzo",
                     "kirsch", "calvados", "armagnac", "grappa", "mezcal", "pisco", "cachaca", "soju",
                     "shaoxing", "shaohsing", "hard cider"]
# Policy (docs/flag_review/flag_policies.csv): oats count as gluten unless labeled gluten-free,
# because most oats are grown and milled next to wheat
# Wheat, barley and rye, including products that are made from them
GLUTEN_KEYWORDS   = ["flour", "bread", "wheat", "pasta", "noodle", "barley", "rye", "oat", "oatmeal",
                     "roll", "rawa", "rava", "sooji", "suji",
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
                     "minestrone"] + _compounds("contains_gluten")
DAIRY_KEYWORDS    = ["milk", "buttermilk", "cheese", "butter", "cream", "yogurt", "yoghurt",
                     "ghee", "mozzarella", "parmesan", "ricotta", "mascarpone", "feta", "whey",
                     "cheddar", "brie", "camembert", "gouda", "gruyere", "gorgonzola", "burrata",
                     "halloumi", "paneer", "queso", "provolone", "pecorino", "emmental", "manchego",
                     "labneh", "kefir", "quark", "creme fraiche", "half-and-half", "half and half",
                     "custard", "cheesecake", "casein", "caseinate", "whipped topping", "cool whip",
                     "alfredo", "bechamel", "tzatziki", "raita", "lassi", "smen", "niter kibbeh",
                     "niter kebbeh"] + _compounds("contains_dairy")
EGG_KEYWORDS      = ["egg", "egg white", "egg yolk", "mayonnaise", "mayo", "meringue", "eggnog",
                     "aioli", "hollandaise", "carbonara", "quiche", "frittata", "challah",
                     "brioche", "cheesecake", "macaron", "wonton"] + _compounds("contains_egg")
# Policy: a plain "nut" may be peanuts, so it sets the peanut flag too
PEANUT_KEYWORDS   = ["peanut", "peanut butter", "peanut oil", "groundnut", "ground nut",
                     "nut"] + _compounds("contains_peanut")
TREE_NUT_KEYWORDS = ["almond", "walnut", "pecan", "cashew", "pistachio", "hazelnut",
                     "filbert", "macadamia", "brazil nut", "pine nut", "nut", "nutella",
                     "praline", "marzipan", "macaron", "frangipane", "amaretti", "pesto",
                     "baklava", "nougat", "gianduja", "marcona"] + _compounds("contains_tree_nut")
FISH_KEYWORDS     = ["fish", "salmon", "tuna", "cod", "anchovy", "anchovies", "sardine",
                     "tilapia", "halibut", "trout", "mackerel", "haddock", "catfish",
                     "snapper", "swordfish", "mahi mahi", "flounder", "sole", "hake",
                     "snoek", "pollock", "bass", "kingfish", "orange roughy", "grouper",
                     "perch", "pike", "walleye", "monkfish", "whitefish", "herring",
                     "kipper", "eel", "carp", "bream", "branzino", "surimi", "roe",
                     "fish sauce", "worcestershire sauce", "bonito", "caviar",
                     "dashi", "katsuobushi", "nam pla", "nuoc mam", "caesar dressing",
                     "shark", "unagi", "sturgeon", "skate", "stingray", "fugu", "pufferfish", "lamprey",
                     "marlin", "tilefish", "bullhead",
                     # Policy: unspecified "seafood" may be fish or shellfish, so it sets both
                     "seafood"] + _compounds("contains_fish")
# Shellfish is two allergen groups that the EU, Canada, Australia / NZ, Japan and Korea label
# separately: many people allergic to shrimp can eat clams, and the reverse. Policy P5 / P10:
# unspecified "seafood" may be either, so it sets both
CRUSTACEAN_KEYWORDS = ["shrimp", "prawn", "crab", "crabmeat", "lobster", "langoustine", "langostino",
                       "scampi", "krill", "crawfish", "crayfish", "belacan", "bagoong", "shrimp paste",
                       "seafood", "frutti di mare"] + _compounds("contains_crustacean", "contains_shellfish")
# Land snails count as molluscs too (EU Regulation 1169/2011)
MOLLUSC_KEYWORDS  = ["clam", "cockle", "mussel", "scallop", "oyster", "squid", "calamari", "octopus",
                     "cuttlefish", "conch", "abalone", "whelk", "periwinkle", "geoduck", "snail", "escargot",
                     "seafood", "frutti di mare"] + _compounds("contains_mollusc", "contains_shellfish")
SHELLFISH_KEYWORDS = list(dict.fromkeys(CRUSTACEAN_KEYWORDS + MOLLUSC_KEYWORDS))
SOY_KEYWORDS      = ["soy", "soya", "soy sauce", "soybean", "tofu", "tempeh", "edamame",
                     "miso", "tamari", "teriyaki", "hoisin", "gochujang", "doenjang", "natto",
                     "shoyu", "ponzu", "yuba"] + _compounds("contains_soy")
SESAME_KEYWORDS   = ["sesame", "tahini", "tahina", "halva", "halvah", "za'atar", "zaatar",
                     "za atar", "furikake", "gomasio", "gomashio", "benne", "hummus", "houmous",
                     "hummous", "baba ganoush", "baba ghanoush", "gingelly"] + _compounds("contains_sesame")
LAND_MEAT_KEYWORDS = (["chicken", "beef", "lamb", "mutton", "goat", "turkey", "veal", "duck",
                      "venison", "goose", "rabbit", "bison", "elk", "quail", "pheasant",
                      "cornish hen", "game hen", "fryer", "meat", "steak", "sirloin",
                      "brisket", "chuck", "ground round", "rib eye", "ribeye",
                      "filet mignon", "tri-tip", "porterhouse", "short rib", "oxtail",
                      "pot roast", "rump roast", "round roast", "eye of round", "pastrami",
                      "jerky", "liver", "giblet", "suet", "tallow", "bone marrow",
                      "gelatin", "gelatine", "marshmallow", "jello", "jell-o", "schmaltz", "poultry",
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
                        "moose", "kangaroo", "liver", "kidney", "tripe", "sweetbread", "mince",
                        "ground meat", "minced meat"])
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
# Every kind of land meat counts for contains_meat and rules out "vegetarian"
LAND_MEAT_KEYWORDS = list(dict.fromkeys(LAND_MEAT_KEYWORDS + BEEF_KEYWORDS + RED_MEAT_KEYWORDS
                                        + POULTRY_KEYWORDS + PROCESSED_MEAT_KEYWORDS))
MEAT_KEYWORDS     = LAND_MEAT_KEYWORDS + FISH_KEYWORDS + SHELLFISH_KEYWORDS
GELATIN_KEYWORDS  = ["gelatin", "gelatine", "jello", "jell-o", "marshmallow", "gummy", "gummies", "aspic"]
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
                     "madeira", "port wine", "hard cider", "dried apricot", "golden raisin", "sultana",
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
# contains_alcohol: whether they count for halal is a team policy (P18), not decided yet.
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
PORK_EXCEPTIONS     = ["hot dog bun", "hot dog roll", "vegetarian sausage", "veggie sausage",
                       "vegan sausage", "vegetarian bacon", "turkey bacon", "turkey ham",
                       "turkey kielbasa", "turkey sausage", "chicken sausage", "merguez sausage",
                       "merguez", "lamb sausage", "beef sausage", "vegan bacon"]
ALCOHOL_EXCEPTIONS  = ["sherry wine vinegar", "wine vinegar", "sherry vinegar", "ginger ale", "ginger beer", "root beer",
                       "non-alcoholic", "alcohol-free", "alcohol free"]
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
                        "lettuce roll", "fruit roll", "rice roll"]
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
PEANUT_EXCEPTIONS   = ["peanut-free", "peanut free", "nut-free", "nut free", "pine nut", "brazil nut",
                       "tiger nut", "macadamia nut", "cashew nut", "pistachio nut", "pecan nut", "hazel nut",
                       "kola nut", "betel nut", "candle nut", "candlenut"]
TREE_NUT_EXCEPTIONS = ["nut-free", "nut free", "tiger nut", "ground nut"]
# Oyster mushrooms, often listed as "wild mushrooms (such as oyster, shiitake ...)"
OYSTER_MUSHROOM_PHRASES = ["oyster mushroom", "king oyster", "such as oyster", "oyster, shiitake",
                           "oyster, crimini", "oyster and shiitake", "shiitake and oyster",
                           "oyster or shiitake", "shiitake or oyster"]
NOT_SEAFOOD_PHRASES = ["seafood seasoning", "seafood boil seasoning", "seafood sauce"]
FISH_EXCEPTIONS     = ["mock caviar", "texas caviar", "cowboy caviar", "southwestern caviar",
                       "eggplant caviar", "poor man's caviar", "vegetarian caviar"] + NOT_SEAFOOD_PHRASES
SHELLFISH_EXCEPTIONS = OYSTER_MUSHROOM_PHRASES + NOT_SEAFOOD_PHRASES
# Used for "vegetarian" (all meat, fish and shellfish keywords)
MEAT_EXCEPTIONS     = OYSTER_MUSHROOM_PHRASES + FISH_EXCEPTIONS + [
                       "duck sauce", "lamb's lettuce", "vegetarian sausage",
                       "veggie sausage", "vegan sausage", "meatless", "meat substitute",
                       "steak sauce", "steak seasoning", "cauliflower steak",
                       "hot dog bun", "hot dog roll", "goat cheese", "goats cheese",
                       "goat's cheese", "goat milk", "goat's milk", "vegan marshmallow",
                       "vegetarian marshmallow", "portobello steak", "portabella steak",
                       "portobella steak", "mushroom steak", "kidney bean", "horseradish", "chicken-fried",
                       "chicken fried", "poultry seasoning", "air fryer", "air-fryer", "deep fryer",
                       "horse gram", "welsh rabbit", "welsh rarebit"]
# Used for contains_meat (land meat only): a fish steak is not meat
LAND_MEAT_EXCEPTIONS = MEAT_EXCEPTIONS + ["tuna steak", "salmon steak", "fish steak", "swordfish steak",
                                          "halibut steak", "cod steak"]
ANIMAL_EXCEPTIONS   = MEAT_EXCEPTIONS + DAIRY_EXCEPTIONS + EGG_EXCEPTIONS
BEEF_EXCEPTIONS     = ["tuna steak", "salmon steak", "fish steak", "swordfish steak", "cauliflower steak",
                       "steak sauce", "steak seasoning", "beefsteak tomato", "beef tomato",
                       "hamburger bun", "hamburger roll", "hamburger helper", "turkey jerky",
                       "mushroom jerky", "veggie burger", "portobello steak", "portabella steak",
                       "portobella steak", "mushroom steak", "halibut steak", "cod steak"]
RED_MEAT_EXCEPTIONS = LAND_MEAT_EXCEPTIONS + BEEF_EXCEPTIONS + PORK_EXCEPTIONS + [
                       "chicken liver", "duck liver", "goose liver", "turkey bacon", "turkey ham",
                       "turkey sausage", "chicken sausage", "turkey jerky"]
POULTRY_EXCEPTIONS  = LAND_MEAT_EXCEPTIONS
PROCESSED_MEAT_EXCEPTIONS = ["vegetarian sausage", "veggie sausage", "vegan sausage", "vegetarian bacon",
                             "vegan bacon", "hot dog bun", "hot dog roll", "meatless"]
GELATIN_EXCEPTIONS  = ["agar", "vegan gelatin", "vegan marshmallow", "vegetarian marshmallow", "vegan gummy"]
HONEY_EXCEPTIONS    = ["honey crisp", "honeycrisp"]
ROOT_VEGETABLE_EXCEPTIONS = ["ground ginger", "dried ginger", "ginger powder", "ginger ale", "ginger beer"]
ALLIUM_EXCEPTIONS   = ["onion seed", "onion seeds"]
MUSHROOM_EXCEPTIONS = ["chocolate truffle"]
# "Chuka soba" and "Okinawa soba" are wheat noodles; yakisoba is one word, so it never matches
BUCKWHEAT_EXCEPTIONS = ["chuka soba", "okinawa soba"]
SULFITE_EXCEPTIONS  = ["unsulfured", "unsulphured", "sulfite-free", "sulfite free", "sulphite-free",
                       "sulphite free", "no added sulfites"]
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
                              "alcohol-free", "alcohol free", "non-alcoholic"]
NIGHTSHADE_EXCEPTIONS = ["sweet potato", "serrano ham", "jamon serrano", "jamón serrano"]
RAW_ANIMAL_EXCEPTIONS = ["sushi rice", "sushi vinegar", "sushi nori", "vegetable sushi", "vegetarian sushi",
                         "veggie sushi", "vegan sushi", "cucumber sushi", "avocado sushi", "poke cake",
                         "cooked eggnog", "eggnog flavored", "eggnog-flavored", "store-bought eggnog"]
HIGH_PURINE_EXCEPTIONS = ["kidney bean", "root beer", "ginger beer", "non-alcoholic beer", "alcohol-free beer"]
HIGH_TYRAMINE_EXCEPTIONS = ["romano bean"]

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
    "contains_scaleless_fish": (SCALELESS_FISH_KEYWORDS, SCALELESS_FISH_EXCEPTIONS),
    "contains_unclean_meat": (UNCLEAN_MEAT_KEYWORDS, UNCLEAN_MEAT_EXCEPTIONS),
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
    text = text.lower()
    for phrase in sorted(exceptions, key=len, reverse=True):
        text = text.replace(phrase, " ")
    return list(dict.fromkeys(m.group(0) for m in _keyword_pattern(tuple(keywords)).finditer(text)))


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
    for flag in FLAG_COLUMNS:
        print(f"  {flag:20s}: {df[flag].sum():>8,} ({df[flag].mean() * 100:.1f}%)")
