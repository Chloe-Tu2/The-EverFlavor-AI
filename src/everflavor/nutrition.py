"""Nutrition per serving (5.4.3), plausibility checks (5.6) and matching recipes
to official USDA dishes and ingredients (5.8.2)."""
from __future__ import annotations

import ast
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer

from .ingredients import singular
from .progress import MIN_ROWS, progress_bar

__all__ = [
    "CANDIDATES",
    "DISH_MIN_SCORE",
    "DISH_TOP_K",
    "FOODCOM_DAILY_VALUES",
    "HF_NUTRIENT_CODES",
    "INGREDIENT_USDA",
    "MACRO_TOLERANCE",
    "NO_USDA_MATCH",
    "NUTRITION_LIMITS",
    "TITLE_FILLER",
    "add_foodcom_macros",
    "add_hf_macros",
    "dish_features",
    "ingredient_energy_features",
    "ingredient_nutrition_table",
    "match_dishes",
    "match_ingredients",
    "missing_hand_checked",
    "nutrition_checks",
]


FOODCOM_DAILY_VALUES = {  # new column: (percent column, daily value)
    "fat_g"    : ("fat_pdv", 65),
    "carbs_g"  : ("carbs_pdv", 300),
    "protein_g": ("protein_pdv", 50),
    "sodium_mg": ("sodium_pdv", 2400),
}
HF_NUTRIENT_CODES = {"protein_g": "PROCNT", "fat_g": "FAT", "carbs_g": "CHOCDF", "sodium_mg": "NA"}


def _parse_nutrition(nut_str: str) -> dict[str, float | None]:
    """Parse Food.com's 'nutrition' text into named values.

    Args:
        nut_str: Text such as '[51.5, 0.0, 13.0, 0.0, 2.0, 0.0, 4.0]': calories,
            then fat, sugar, sodium, protein, saturated fat and carbs as % daily value.

    Returns:
        The named values, or all None if the text cannot be read.
    """
    keys = ["calories", "fat_pdv", "sugar_pdv", "sodium_pdv",
            "protein_pdv", "sat_fat_pdv", "carbs_pdv"]
    try:
        values = ast.literal_eval(nut_str)
        return dict(zip(keys, values))
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return {k: None for k in keys}


def add_foodcom_macros(df: pd.DataFrame) -> pd.DataFrame:
    """Add calories per serving and macros in grams to Food.com recipes.

    Percent daily values become grams with FOODCOM_DAILY_VALUES (the FDA
    reference values on US labels when the recipes were posted).

    Returns:
        A new dataframe; `df` itself is not changed.
    """
    nut = pd.DataFrame(df["nutrition"].apply(_parse_nutrition).tolist(), index=df.index)
    nut = nut.rename(columns={"calories": "calories_per_serving"}).astype(float)
    df = df.drop(columns=[c for c in nut.columns if c in df.columns]).join(nut)
    for col, (pdv_col, daily_value) in FOODCOM_DAILY_VALUES.items():
        df[col] = df[pdv_col] * daily_value / 100
    return df


def _hf_nutrients_per_serving(total_nutrients: str, servings: float) -> dict[str, float]:
    """Return protein, fat, carbs (g) and sodium (mg) per serving from one Hugging Face recipe."""
    try:
        data = json.loads(total_nutrients)
    except (TypeError, ValueError):
        data = {}
    return {col: (data.get(code) or {}).get("quantity", np.nan) / servings
            for col, code in HF_NUTRIENT_CODES.items()}


def add_hf_macros(df: pd.DataFrame) -> pd.DataFrame:
    """Add macros per serving to Hugging Face recipes (a new dataframe; `df` is not changed)."""
    per_serving = pd.DataFrame(
        [_hf_nutrients_per_serving(t, s) for t, s in zip(df["total_nutrients"], df["servings"])],
        index=df.index)
    return df.drop(columns=[c for c in per_serving.columns if c in df.columns]).join(per_serving)


# ------------------------------------------------------------------ plausibility (5.6)
NUTRITION_LIMITS = {"min_kcal": 10, "max_sodium_mg": 5000, "max_protein_g": 150}
MACRO_TOLERANCE = 0.30   # macros may differ from listed calories by up to 30%


def nutrition_checks(df: pd.DataFrame) -> pd.DataFrame:
    """Run the plausibility checks on listed nutrition (NUTRITION_LIMITS, MACRO_TOLERANCE).

    Returns:
        One true/false column per check (True = passes), same index as `df`.
    """
    kcal = df["calories_per_serving"]
    macro_kcal = 4 * df["protein_g"] + 4 * df["carbs_g"] + 9 * df["fat_g"]
    return pd.DataFrame({
        f"at least {NUTRITION_LIMITS['min_kcal']} kcal": kcal >= NUTRITION_LIMITS["min_kcal"],
        f"sodium <= {NUTRITION_LIMITS['max_sodium_mg']:,} mg": df["sodium_mg"].isna() | (df["sodium_mg"] <= NUTRITION_LIMITS["max_sodium_mg"]),
        f"protein <= {NUTRITION_LIMITS['max_protein_g']} g": df["protein_g"].isna() | (df["protein_g"] <= NUTRITION_LIMITS["max_protein_g"]),
        "macros match calories": macro_kcal.isna() | ((macro_kcal - kcal).abs() <= MACRO_TOLERANCE * kcal.clip(lower=1)),
    })


# ------------------------------------------------------------------ USDA matching (5.8.2)
def _words(text: object) -> list[str]:
    """Return the lowercase words of a text, each in singular form."""
    return [singular(w) for w in re.findall(r"[a-z]+", str(text).lower())]


def _norm_text(text: object) -> str:
    """Return a text as lowercase singular words joined by spaces, for matching."""
    return " ".join(_words(text))


# Title words that say nothing about the dish itself
TITLE_FILLER = {"and", "with", "the", "for", "easy", "best", "homemade", "style", "recipe", "quick",
                "simple", "mom", "grandma", "old", "fashioned", "classic", "ii", "iii", "oamc"}


def _head_word(title: str) -> str:
    """Return the last meaningful word of a title, usually the dish: 'coconut cabbage curry' -> 'curry'."""
    meaningful = [w for w in _words(title) if len(w) > 2 and w not in TITLE_FILLER]
    return meaningful[-1] if meaningful else ""

DISH_TOP_K = 5         # matches kept per recipe
DISH_MIN_SCORE = 0.25  # weaker matches are ignored
CANDIDATES = 50        # only the most similar USDA entries are scored in detail (much faster)


def _top_candidates(similarity: sparse.csr_matrix, row: int) -> tuple[np.ndarray, np.ndarray]:
    """Return positions and similarities of the CANDIDATES most similar USDA entries for one row."""
    start, end = similarity.indptr[row], similarity.indptr[row + 1]
    positions, values = similarity.indices[start:end], similarity.data[start:end]
    if len(values) > CANDIDATES:
        keep = np.argpartition(-values, CANDIDATES)[:CANDIDATES]
        positions, values = positions[keep], values[keep]
    return positions, values


def match_dishes(titles: Sequence[str], dishes: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Find the closest USDA FNDDS dishes for each recipe title.

    Score = text similarity, +0.35 if the title's main word is in the first part
    of the USDA description (its food group, as in 'Rice, fried'), +0.1 if it
    appears later, -0.2 if it is missing. Matches scoring DISH_MIN_SCORE or less
    are ignored.

    Args:
        titles: Recipe titles.
        dishes: USDA dishes with a 'description' column.

    Returns:
        (scores, positions), each of shape (len(titles), DISH_TOP_K), best first;
        a score of 0 means no match.
    """
    vectorizer = TfidfVectorizer(token_pattern=r"[a-z]{3,}", sublinear_tf=True, ngram_range=(1, 2))
    dish_matrix = vectorizer.fit_transform(dishes["description"].map(_norm_text))
    similarity = (vectorizer.transform([_norm_text(t) for t in titles]) @ dish_matrix.T).tocsr()
    first_part = [set(_words(d.split(",")[0])) for d in dishes["description"]]
    anywhere = [set(_words(d)) for d in dishes["description"]]

    scores = np.zeros((len(titles), DISH_TOP_K))
    positions = np.zeros((len(titles), DISH_TOP_K), dtype=int)
    for row, title in enumerate(progress_bar(titles, "Matching USDA dishes", show=len(titles) >= MIN_ROWS)):
        candidates, text_score = _top_candidates(similarity, row)
        if len(candidates) == 0:
            continue
        head = _head_word(title)
        score = text_score + np.array(
            [0.35 if head in first_part[j] else 0.1 if head in anywhere[j] else -0.2 for j in candidates])
        best = np.argsort(-score)[:DISH_TOP_K]
        best = best[score[best] > DISH_MIN_SCORE]
        scores[row, :len(best)] = score[best]
        positions[row, :len(best)] = candidates[best]
    return scores, positions


def dish_features(dishes: pd.DataFrame, scores: np.ndarray, positions: np.ndarray) -> pd.DataFrame:
    """Summarize each recipe's matched USDA dishes.

    Args:
        dishes: USDA dishes with 'kcal_serving' and 'kcal_100g'.
        scores, positions: The output of `match_dishes`.

    Returns:
        One row per recipe: similarity-weighted calories per typical serving
        ('dish_kcal'), energy density ('dish_density') and the best score
        ('dish_score'); missing values where nothing matched.
    """
    matched = scores[:, 0] > 0
    weights = scores + 1e-9

    def dish_average(values):
        picked = values[positions]
        return np.where(matched, (picked * weights).sum(axis=1) / weights.sum(axis=1), np.nan)

    return pd.DataFrame({
        "dish_kcal"   : dish_average(dishes["kcal_serving"].to_numpy()),
        "dish_density": dish_average(dishes["kcal_100g"].to_numpy()),
        "dish_score"  : scores[:, 0],
    })


# Hand-checked matches for common ingredients that automatic matching gets wrong
FLOUR = "Wheat flour, white, all-purpose, enriched, bleached"
VEGETABLE_OIL = "Oil, soybean, salad or cooking"
BLACK_PEPPER = "Spices, pepper, black"
CAYENNE = "Spices, pepper, red or cayenne"
CHICKEN_BREAST = "Chicken, broiler or fryers, breast, skinless, boneless, meat only, raw"
CHICKEN_STOCK = "Soup, stock, chicken, home-prepared"
RIPE_OLIVE = "Olives, ripe, canned (small-extra large)"
MUSTARD_SEED = "Spices, mustard seed, ground"
GREEN_CHILI = "Peppers, hot chili, green, raw"
VEGETABLE_BROTH = "Soup, vegetable broth, ready to serve"
HAM = "Ham, sliced, regular (approximately 11% fat)"
PINEAPPLE = "Pineapple, raw, all varieties"
CORN = "Corn, sweet, yellow, raw"
SMOKED_SAUSAGE = "Sausage, smoked link sausage, pork"
RED_CHILI = "Peppers, hot chili, red, raw"
BREAD_CRUMB = "Bread, crumbs, dry, grated, plain"
SPIRIT = "Alcoholic beverage, distilled, all (gin, rum, vodka, whiskey) 80 proof"
PINEAPPLE_JUICE = "Pineapple juice, canned or bottled, unsweetened, with added ascorbic acid"
PINEAPPLE_IN_JUICE = "Pineapple, canned, juice pack, solids and liquids"
SWEET_COCONUT = "Nuts, coconut meat, dried (desiccated), sweetened, flaked, canned"
WATER = "Water, bottled, generic"
TOMATO = "Tomatoes, red, ripe, raw, year round average"
WHOLE_MILK = "Milk, whole, 3.25% milkfat, with added vitamin D"
DRY_PASTA = "Pasta, dry, enriched"
OATS = "Cereals, oats, regular and quick, not fortified, dry"
RICE = "Rice, white, long-grain, regular, raw, enriched"
MINT = "Spearmint, fresh"
DILL = "Dill weed, fresh"
LEMON_PEEL = "Lemon peel, raw"
ORANGE_PEEL = "Orange peel, raw"
CHEDDAR = "Cheese, cheddar (Includes foods for USDA's Food Distribution Program)"
PEANUT_BUTTER = "Peanut butter, smooth style, with salt (Includes foods for USDA's Food Distribution Program)"
HALF_AND_HALF = "Cream, fluid, half and half"
WHITE_BREAD = "Bread, white, commercially prepared (includes soft bread crumbs)"
BEEF_BROTH = "Soup, beef broth or bouillon canned, ready-to-serve"
SEMISWEET = "Candies, semisweet chocolate"
RED_WINE = "Alcoholic beverage, wine, table, red"
FROZEN_SPINACH = "Spinach, frozen, chopped or leaf, unprepared (Includes foods for USDA's Food Distribution Program)"
COCOA = "Cocoa, dry powder, unsweetened"
COOKING_SPRAY = "Oil, PAM cooking spray, original"
RUSSET = "Potatoes, russet, flesh and skin, raw (Includes foods for USDA's Food Distribution Program)"
SALMON = "Fish, salmon, Atlantic, farmed, raw"
TACO_SEASONING = "Seasoning mix, dry, taco, original"
MARSHMALLOW = "Candies, marshmallows"
LAMB = "Lamb, composite of trimmed retail cuts, separable lean and fat, trimmed to 1/8\" fat, choice, raw"
WHITE_FISH = "Fish, cod, Atlantic, raw"
SCALLOP = "Mollusks, scallop, mixed species, raw"
INGREDIENT_USDA = {
    "sugar": "Sugars, granulated", "powdered sugar": "Sugars, powdered", "confectioners' sugar": "Sugars, powdered",
    "flour": FLOUR, "olive oil": "Oil, olive, salad or cooking", "vegetable oil": VEGETABLE_OIL,
    "oil": VEGETABLE_OIL, "canola oil": VEGETABLE_OIL,
    "pepper": BLACK_PEPPER, "black pepper": BLACK_PEPPER, "ground pepper": BLACK_PEPPER,
    "milk": WHOLE_MILK,
    "tomato": TOMATO,
    "green onion": "Onions, spring or scallions (includes tops and bulb), raw",
    "baking powder": "Leavening agents, baking powder, double-acting, sodium aluminum sulfate",
    "cinnamon": "Spices, cinnamon, ground", "ground cinnamon": "Spices, cinnamon, ground",
    "vanilla": "Vanilla extract", "vanilla extract": "Vanilla extract",
    "sour cream": "Cream, sour, cultured", "garlic powder": "Spices, garlic powder",
    "soy sauce": "Soy sauce made from soy and wheat (shoyu)",
    "cheddar cheese": "Cheese, cheddar (Includes foods for USDA's Food Distribution Program)",
    "parmesan cheese": "Cheese, parmesan, grated", "cream cheese": "Cheese, cream",
    "mozzarella cheese": "Cheese, mozzarella, whole milk",
    "mayonnaise": "Salad dressing, mayonnaise, regular", "potato": "Potatoes, flesh and skin, raw",
    "butter": "Butter, salted", "egg": "Egg, whole, raw, fresh",
    "heavy cream": "Cream, fluid, heavy whipping", "whipping cream": "Cream, fluid, heavy whipping",
    "chicken broth": CHICKEN_STOCK, "chicken stock": CHICKEN_STOCK,
    "chicken breast": CHICKEN_BREAST, "boneless skinless chicken breast": CHICKEN_BREAST,
    "ground beef": "Beef, ground, 80% lean meat / 20% fat, raw",
    "cumin": "Spices, cumin seed", "ground cumin": "Spices, cumin seed", "paprika": "Spices, paprika",
    "chili powder": "Spices, chili powder", "oregano": "Spices, oregano, dried",
    "dried oregano": "Spices, oregano, dried", "cayenne pepper": CAYENNE, "cayenne": CAYENNE,
    "nutmeg": "Spices, nutmeg, ground", "ground nutmeg": "Spices, nutmeg, ground",
    "worcestershire sauce": "Sauce, worcestershire", "lime juice": "Lime juice, raw",
    "dijon mustard": "Mustard, prepared, yellow",
    "red bell pepper": "Peppers, sweet, red, raw", "green bell pepper": "Peppers, sweet, green, raw",
    "green pepper": "Peppers, sweet, green, raw",
    "walnut": "Nuts, walnuts, english", "pecan": "Nuts, pecans", "almond": "Nuts, almonds",
    "bacon": "Pork, cured, bacon, unprepared", "cornstarch": "Cornstarch",
    "zucchini": "Squash, summer, zucchini, includes skin, raw", "banana": "Bananas, raw", "spinach": "Spinach, raw",
    "coconut milk": "Nuts, coconut milk, canned (liquid expressed from grated meat and water)",
    "rice": RICE,
    # Generic words the automatic matching sent to a processed food (corned beef, a pork olive loaf ...)
    "beef": "Beef, composite of trimmed retail cuts, separable lean and fat, trimmed to 1/8\" fat, all grades, raw",
    "black olive": RIPE_OLIVE, "olive": RIPE_OLIVE, "kalamata olive": RIPE_OLIVE,
    "green olive": "Olives, pickled, canned or bottled, green",
    "dry mustard": MUSTARD_SEED, "ground mustard": MUSTARD_SEED, "mustard powder": MUSTARD_SEED,
    "green chile": GREEN_CHILI, "green chili": GREEN_CHILI,
    "vegetable stock": VEGETABLE_BROTH, "vegetable broth": VEGETABLE_BROTH,
    "low sodium chicken broth": "Soup, chicken broth, low sodium, canned",
    "cream of chicken soup": "Soup, cream of chicken, canned, condensed",
    "ham": HAM, "cooked ham": HAM, "pineapple chunk": PINEAPPLE, "pineapple": PINEAPPLE,
    "corn kernel": CORN, "whole kernel corn": CORN, "corn": CORN,
    "mashed potato": "Potatoes, mashed, home-prepared, whole milk and butter added",
    "pinto bean": "Beans, pinto, canned, drained solids", "firm tofu": "Tofu, raw, firm, prepared with calcium sulfate",
    "dried onion flake": "Onions, dehydrated flakes", "pizza sauce": "Sauce, pizza, canned, ready-to-serve",
    "flaked coconut": SWEET_COCONUT, "sweetened flaked coconut": SWEET_COCONUT,
    "sherry wine": "Alcoholic beverage, wine, dessert, dry", "sherry": "Alcoholic beverage, wine, dessert, dry",
    "creme fraiche": "Cream, sour, cultured",
    "low-sodium chicken broth": "Soup, chicken broth, low sodium, canned",
    "sausage": SMOKED_SAUSAGE, "andouille sausage": SMOKED_SAUSAGE,
    "hot dog": "Frankfurter, beef, unheated", "chicken piece": "Chicken, broilers or fryers, meat and skin, raw",
    "creamed corn": "Corn, sweet, yellow, canned, cream style, regular pack", "agave nectar": "Sweetener, syrup, agave",
    "red chili": RED_CHILI, "chili": RED_CHILI, "chili flake": CAYENNE, "red pepper flake": CAYENNE,
    "pitted black olive": RIPE_OLIVE, "pimento stuffed olive": "Olives, pickled, canned or bottled, green",
    "dried breadcrumb": BREAD_CRUMB, "bread crumb": BREAD_CRUMB, "dry bread crumb": BREAD_CRUMB,
    "tomatoes and green chili": "Tomatoes, red, ripe, canned, with green chilies",
    "whiskey": SPIRIT, "tequila": SPIRIT, "bourbon": SPIRIT, "brandy": SPIRIT,
    "espresso": "Beverages, coffee, brewed, espresso, restaurant-prepared",
    "corned beef": "Beef, cured, corned beef, brisket, raw",
    "pineapple juice": PINEAPPLE_JUICE, "unsweetened pineapple juice": PINEAPPLE_JUICE,
    "pineapple in juice": PINEAPPLE_IN_JUICE, "pineapple chunks in juice": PINEAPPLE_IN_JUICE,
    "crushed pineapple": PINEAPPLE_IN_JUICE,
    # Hand-check of the 450 most-used automatic matches (2026-10-10): tomato paste had become almond paste,
    # whole milk dried milk, beef broth fish broth, mint an After Eight candy, cold water a cheese food ...
    **{name: WATER for name in ("cold water", "warm water", "hot water", "boiling water", "ice water", "ice",
                                "ice cube", "lukewarm water")},
    **{name: TOMATO for name in ("cherry tomato", "grape tomato", "roma tomato", "plum tomato")},
    **{name: BLACK_PEPPER for name in ("cracked black pepper", "coarse ground black pepper",
                                       "salt & freshly ground black pepper", "salt and pepper to taste",
                                       "freshly ground black pepper")},
    **{name: "Salt, table" for name in ("salt to taste", "garlic salt", "celery salt", "seasoning salt",
                                        "kosher salt", "sea salt")},
    **{name: DRY_PASTA for name in ("pasta", "penne pasta", "penne", "elbow macaroni", "spaghetti",
                                    "lasagna noodle", "fettuccine", "linguine", "rotini pasta")},
    **{name: OATS for name in ("oats", "oatmeal", "quick-cooking oats", "rolled oats", "old-fashioned oats")},
    **{name: RICE for name in ("white rice", "basmati rice", "long grain rice", "jasmine rice")},
    "tomato paste": "Tomato products, canned, paste, without salt added (Includes foods for USDA's Food "
                    "Distribution Program)",
    "tomato puree": "Tomato products, canned, puree, without salt added",
    "buttermilk": "Milk, buttermilk, fluid, cultured, lowfat", "whole milk": WHOLE_MILK,
    "dried thyme": "Spices, thyme, dried", "dried basil": "Spices, basil, dried",
    "dried rosemary": "Spices, rosemary, dried", "dried parsley": "Spices, parsley, dried",
    "thyme leaf": "Thyme, fresh", "basil leaf": "Basil, fresh", "parsley leaf": "Parsley, fresh",
    "mint": MINT, "mint leaf": MINT, "fresh mint": MINT, "dill": DILL, "fresh dill": DILL,
    "white pepper": "Spices, pepper, white", "cinnamon stick": "Spices, cinnamon, ground",
    "lemon zest": LEMON_PEEL, "lemon rind": LEMON_PEEL, "lemon peel": LEMON_PEEL, "orange zest": ORANGE_PEEL,
    "orange rind": ORANGE_PEEL, "lemon wedge": "Lemons, raw, without peel",
    "cheese": CHEDDAR, "parmigiano-reggiano cheese": "Cheese, parmesan, hard",
    "american cheese": "Cheese, pasteurized process, American, fortified with vitamin D",
    "cottage cheese": "Cheese, cottage, creamed, large or small curd",
    "salsa": "Sauce, salsa, ready-to-serve", "shortening": "Shortening, vegetable, household, composite",
    "peanut butter": PEANUT_BUTTER, "creamy peanut butter": PEANUT_BUTTER,
    "sweet potato": "Sweet potato, raw, unprepared (Includes foods for USDA's Food Distribution Program)",
    "coconut": SWEET_COCONUT, "bell pepper": "Peppers, sweet, green, raw",
    "half-and-half": HALF_AND_HALF, "half-and-half cream": HALF_AND_HALF,
    "light cream": "Cream, fluid, light (coffee cream or table cream)",
    "bread": WHITE_BREAD, "white bread": WHITE_BREAD, "french bread": "Bread, french or vienna (includes sourdough)",
    "hamburger bun": "Rolls, hamburger or hotdog, plain",
    "beef broth": BEEF_BROTH, "beef bouillon": BEEF_BROTH,
    "chocolate chip": SEMISWEET, "semi-sweet chocolate chip": SEMISWEET, "semisweet chocolate chip": SEMISWEET,
    "nut": "Nuts, walnuts, english", "slivered almond": "Nuts, almonds", "hazelnut": "Nuts, hazelnuts or filberts",
    "red wine": RED_WINE, "dry red wine": RED_WINE,
    "chicken": "Chicken, broilers or fryers, meat only, raw",
    "cooked chicken": "Chicken, broilers or fryers, meat only, cooked, roasted",
    "chicken thigh": "Chicken, broilers or fryers, dark meat, thigh, meat only, raw",
    "boneless chicken breast": CHICKEN_BREAST,
    "yeast": "Leavening agents, yeast, baker's, active dry", "sesame seed": "Seeds, sesame seeds, whole, dried",
    "frozen pea": "Peas, green, frozen, unprepared (Includes foods for USDA's Food Distribution Program)",
    "frozen corn": "Corn, sweet, yellow, frozen, kernels cut off cob, unprepared (Includes foods for USDA's Food "
                   "Distribution Program)",
    "frozen spinach": FROZEN_SPINACH, "frozen chopped spinach": FROZEN_SPINACH,
    "cooked rice": "Rice, white, long-grain, regular, enriched, cooked",
    "brown rice": "Rice, brown, long-grain, raw (Includes foods for USDA's Food Distribution Program)",
    "dried cranberry": "Cranberries, dried, sweetened (Includes foods for USDA's Food Distribution Program)",
    "dried apricot": "Apricots, dried, sulfured, uncooked", "egg noodle": "Noodles, egg, dry, enriched",
    "cocoa powder": COCOA, "cocoa": COCOA, "caster sugar": "Sugars, granulated", "icing sugar": "Sugars, powdered",
    "cooking oil": VEGETABLE_OIL, "cooking spray": COOKING_SPRAY, "nonstick cooking spray": COOKING_SPRAY,
    "russet potato": RUSSET, "baking potato": RUSSET, "yukon gold potato": "Potatoes, white, flesh and skin, raw",
    "kidney bean": "Beans, kidney, red, mature seeds, canned, drained solids",
    "cannellini bean": "Beans, white, mature seeds, canned", "white bean": "Beans, white, mature seeds, canned",
    "salmon": SALMON, "salmon fillet": SALMON,
    "tuna": "Fish, tuna, light, canned in water, drained solids (Includes foods for USDA's Food Distribution "
            "Program)",
    "pumpkin puree": "Pumpkin, canned, without salt", "light soy sauce": "Soy sauce made from soy and wheat (shoyu)",
    "bean sprout": "Mung beans, mature seeds, sprouted, raw",
    "sunflower seed": "Seeds, sunflower seed kernels, dried",
    "splenda sugar substitute": "Sweeteners, tabletop, sucralose, SPLENDA packets",
    "taco seasoning": TACO_SEASONING, "taco seasoning mix": TACO_SEASONING,
    "greek yogurt": "Yogurt, Greek, plain, lowfat",
    "graham cracker crumb": "Cookies, graham crackers, plain or honey (includes cinnamon)",
    "yellow squash": "Squash, summer, crookneck and straightneck, raw",
    "water chestnut": "Waterchestnuts, chinese, canned, solids and liquids",
    "artichoke heart": "Artichokes, (globe or french), frozen, unprepared",
    "unflavored gelatin": "Gelatins, dry powder, unsweetened", "marshmallow": MARSHMALLOW,
    "miniature marshmallow": MARSHMALLOW, "mini marshmallow": MARSHMALLOW,
    "chicken bouillon cube": "Soup, chicken broth cubes, dry", "beef bouillon cube": "Soup, beef broth, cubed, dry",
    "chicken bouillon granule": "Soup, chicken broth or bouillon, dry",
    "kosher salt and freshly ground black pepper": "Salt, table", "fine sea salt": "Salt, table",
    "quick oats": OATS, "vegetable oil cooking spray": COOKING_SPRAY, "chicken breast half": CHICKEN_BREAST,
    "plain breadcrumb": BREAD_CRUMB, "italian seasoned breadcrumb": BREAD_CRUMB, "mint sprig": MINT,
    "mini chocolate chip": SEMISWEET, "instant yeast": "Leavening agents, yeast, baker's, active dry",
    "baking cocoa": COCOA, "low-fat buttermilk": "Milk, buttermilk, fluid, cultured, lowfat",
    "chunky salsa": "Sauce, salsa, ready-to-serve", "coconut flake": SWEET_COCONUT,
    # Generic meat, fish and tofu (2026-10-10): "pork" was salt pork (748 kcal), "scallop" a squash
    "pork": "Pork, fresh, composite of trimmed retail cuts (leg, loin, shoulder, and spareribs), separable lean and "
            "fat, raw",
    "lamb": LAMB, "mutton": LAMB, "veal": "Veal, composite of trimmed retail cuts, separable lean and fat, raw",
    "turkey": "Turkey, whole, meat only, raw", "fish": WHITE_FISH, "white fish": WHITE_FISH,
    "white fish fillet": WHITE_FISH, "fish fillet": WHITE_FISH, "tuna steak": "Fish, tuna, fresh, yellowfin, raw",
    "crab": "Crustaceans, crab, blue, raw", "crabmeat": "Crustaceans, crab, blue, raw",
    "scallop": SCALLOP, "sea scallop": SCALLOP, "bay scallop": SCALLOP,
    "tofu": "Tofu, raw, regular, prepared with calcium sulfate",
    "cooked brown rice": "Rice, brown, long-grain, cooked (Includes foods for USDA's Food Distribution Program)",
}
# Names with no fair USDA SR Legacy entry: better no match than a wrong one (curry leaf is not drumstick leaves)
NO_USDA_MATCH = {"curry leaf", "lemongrass", "vanilla bean", "herb", "garam masala", "italian seasoning",
                 "cajun seasoning", "seasoning", "skinless", "lime zest", "dried italian seasoning"}


# Words for a processed or ready-made food (singular, as _norm_text writes them)
# that change the food itself. Not "canned", "prepared" or "sweetened": for prepared mustard, cream
# soups or cranberry sauce the ready-made food is what the recipe means
PROCESSING_WORDS = {"cured", "corned", "smoked", "frozen", "pickled", "candied", "babyfood", "entree",
                    "concentrate", "fried", "breaded", "restaurant", "fast", "microwaved"}
# Forms that change the amount of water (and so the calories per 100 g) when the name does not ask for them:
# "whole milk" is not dried milk, "chickpea" is not chickpea flour
FORM_WORDS = {"dried", "dry", "powder", "dehydrated", "flour", "mix"}
# ... except foods that recipes weigh dry (pasta, rice, oats, lentils): "orzo pasta" is dry pasta
BOUGHT_DRY = {"pasta", "spaghetti", "macaroni", "noodle", "rice", "cereal", "oat", "bean", "lentil", "pea",
              "chickpea", "couscous", "quinoa"}


def _brand_words(description: str) -> set[str]:
    """Brand names in a USDA description (written in capitals, e.g. HERSHEY'S, PAM)."""
    return {w.lower().strip("'S").strip("'") for w in re.findall(r"\b[A-Z][A-Z']{2,}\b", description)} - {"usda"}


def match_ingredients(names: Sequence[str], foods: pd.DataFrame) -> dict[str, tuple[int, str]]:
    """Match ingredient names to USDA SR Legacy foods.

    Hand-checked matches (INGREDIENT_USDA) come first. Otherwise the most
    similar description wins, preferring one that starts with the ingredient,
    raw foods and short (generic) descriptions.

    Args:
        names: Normalized ingredient names.
        foods: USDA foods with a 'description' column.

    Returns:
        {ingredient: (row in `foods`, "hand-checked" or "automatic")} for the names that match.
    """
    vectorizer = TfidfVectorizer(token_pattern=r"[a-z]{3,}")
    food_matrix = vectorizer.fit_transform(foods["description"].map(_norm_text))
    vocabulary = set(vectorizer.vocabulary_)
    similarity = (vectorizer.transform([_norm_text(n) for n in names]) @ food_matrix.T).tocsr()
    first_part = [_norm_text(d.split(",")[0]) for d in foods["description"]]
    is_raw = foods["description"].str.contains("raw", case=False).to_numpy()
    n_details = foods["description"].str.count(",").to_numpy()   # fewer details = more generic food
    row_of = {d: i for i, d in enumerate(foods["description"])}
    words = [set(_norm_text(d).split()) for d in foods["description"]]
    processing = [w & PROCESSING_WORDS for w in words]
    forms = [set() if first_part[j].split()[-1:] and first_part[j].split()[-1] in BOUGHT_DRY else w & FORM_WORDS
             for j, w in enumerate(words)]
    brands = [_brand_words(d) for d in foods["description"]]

    matches = {}
    for row, name in enumerate(progress_bar(names, "Matching USDA ingredients", show=len(names) >= MIN_ROWS)):
        if name in INGREDIENT_USDA:
            matches[name] = (row_of[INGREDIENT_USDA[name]], "hand-checked")
            continue
        candidates, text_score = _top_candidates(similarity, row)
        if len(candidates) == 0 or name in NO_USDA_MATCH:
            continue
        target = _norm_text(name)
        last = target.split()[-1:]
        bonus = np.array([0.5 if first_part[j] == target else 0.25 if first_part[j].split()[-1:] == last else 0.0
                          for j in candidates])
        # "beef" should not become corned beef, nor "vegetable stock" a canned soup: processing the
        # name does not ask for counts against a food
        asked = set(target.split())
        processed = np.array([len(processing[j] - asked) + bool(forms[j] - asked) for j in candidates])
        # every word of the name should be there: "tomato paste" is not almond paste, "beef broth" not fish broth
        # (words USDA never uses, like "garnish" or "halve", are left out)
        meaningful = {w for w in asked if w in vocabulary} or asked
        covered = np.array([len(meaningful & words[j]) / len(meaningful) for j in candidates])
        branded = np.array([bool(brands[j]) and not brands[j] & asked for j in candidates])
        score = (text_score + bonus + 0.1 * is_raw[candidates] - 0.02 * n_details[candidates] - 0.15 * processed
                 + 0.15 * (covered - 1) - 0.2 * branded)
        best = int(np.argmax(score))
        if score[best] > 0.45:
            matches[name] = (candidates[best], "automatic")
    return matches


def ingredient_nutrition_table(ingredient_lists: pd.Series, foods: pd.DataFrame,
                               nutrient_columns: Sequence[str]) -> tuple[pd.DataFrame, Counter]:
    """Build the USDA nutrition table for every ingredient name in the recipes.

    Args:
        ingredient_lists: One normalized ingredient list per recipe.
        foods: USDA foods (from `usda_table`).
        nutrient_columns: The per-100 g columns to copy, for example "kcal_100g".

    Returns:
        (table, counts): one row per matched name, most used first, and how many
        recipes use each ingredient name.
    """
    counts = Counter(i for ingredients in ingredient_lists for i in set(ingredients))
    matches = match_ingredients(sorted(counts), foods)
    names = list(matches)
    rows = [matches[name][0] for name in names]
    table = (
        foods.iloc[rows][["fdc_id", "description", *nutrient_columns]]
        .rename(columns={"description": "usda_description"})
        .assign(ingredient=names,
                recipes=[counts[name] for name in names],
                match=[matches[name][1] for name in names])
        .loc[:, ["ingredient", "recipes", "match", "fdc_id", "usda_description", *nutrient_columns]]
        .sort_values("recipes", ascending=False)
        .reset_index(drop=True)
    )
    return table, counts


def ingredient_energy_features(ingredient_lists: pd.Series, kcal_per_100g: Mapping[str, float]) -> pd.DataFrame:
    """Describe how energy-dense each recipe's ingredients are.

    Amounts are unknown, so these are not totals: the mean and highest kcal per
    100 g of the matched ingredients, and the share above 300 and 500 kcal.

    Returns:
        One row per recipe (same index as `ingredient_lists`); missing values
        when no ingredient matched.
    """
    ingredient_kcal = ingredient_lists.explode().map(kcal_per_100g).astype(float).dropna()
    by_recipe = ingredient_kcal.groupby(level=0)
    return pd.DataFrame({
        "ing_kcal_mean"     : by_recipe.mean(),
        "ing_kcal_max"      : by_recipe.max(),
        "ing_share_over_300": (ingredient_kcal > 300).groupby(level=0).mean(),
        "ing_share_over_500": (ingredient_kcal > 500).groupby(level=0).mean(),
    }).reindex(ingredient_lists.index)   # recipes with no matched ingredient get missing values


def missing_hand_checked(foods: pd.DataFrame) -> list[str]:
    """Return the hand-checked USDA descriptions that are not in `foods` (should be none)."""
    return sorted(set(INGREDIENT_USDA.values()) - set(foods["description"]))
