"""Nutrition per serving (5.4.3), plausibility checks (5.6) and matching recipes
to official USDA dishes and ingredients (5.8.2)."""
import ast
import json
import re
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from .ingredients import singular

FOODCOM_DAILY_VALUES = {  # new column: (percent column, daily value)
    "fat_g"    : ("fat_pdv", 65),
    "carbs_g"  : ("carbs_pdv", 300),
    "protein_g": ("protein_pdv", 50),
    "sodium_mg": ("sodium_pdv", 2400),
}
HF_NUTRIENT_CODES = {"protein_g": "PROCNT", "fat_g": "FAT", "carbs_g": "CHOCDF", "sodium_mg": "NA"}


def parse_nutrition(nut_str):
    """Parse the nutrition column from Food.com into named fields.

    Args:
        nut_str (str): A string like '[51.5, 0.0, 13.0, 0.0, 2.0, 0.0, 4.0]'.

    Returns:
        dict: Named nutrient values, or a dict of None values on failure.
    """
    keys = ["calories", "fat_pdv", "sugar_pdv", "sodium_pdv",
            "protein_pdv", "sat_fat_pdv", "carbs_pdv"]
    try:
        values = ast.literal_eval(nut_str)
        return dict(zip(keys, values))
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return {k: None for k in keys}


def add_foodcom_macros(df):
    """Add calories per serving and macros in grams to a Food.com dataframe."""
    nut = pd.DataFrame(df["nutrition"].apply(parse_nutrition).tolist(), index=df.index)
    nut = nut.rename(columns={"calories": "calories_per_serving"}).astype(float)
    df = df.drop(columns=[c for c in nut.columns if c in df.columns]).join(nut)
    for col, (pdv_col, daily_value) in FOODCOM_DAILY_VALUES.items():
        df[col] = df[pdv_col] * daily_value / 100
    return df


def hf_nutrients_per_serving(total_nutrients, servings):
    """Return protein, fat, carbs (g) and sodium (mg) per serving from a HF row."""
    try:
        data = json.loads(total_nutrients)
    except (TypeError, ValueError):
        data = {}
    return {col: (data.get(code) or {}).get("quantity", np.nan) / servings
            for col, code in HF_NUTRIENT_CODES.items()}


def add_hf_macros(df):
    """Add macros per serving to a Hugging Face dataframe."""
    per_serving = pd.DataFrame(
        [hf_nutrients_per_serving(t, s) for t, s in zip(df["total_nutrients"], df["servings"])],
        index=df.index)
    return df.drop(columns=[c for c in per_serving.columns if c in df.columns]).join(per_serving)


# ------------------------------------------------------------------ plausibility (5.6)
NUTRITION_LIMITS = {"min_kcal": 10, "max_sodium_mg": 5000, "max_protein_g": 150}
MACRO_TOLERANCE = 0.30   # macros may differ from listed calories by up to 30%


def nutrition_checks(df):
    """Return one true/false column per nutrition check (True = passes)."""
    kcal = df["calories_per_serving"]
    macro_kcal = 4 * df["protein_g"] + 4 * df["carbs_g"] + 9 * df["fat_g"]
    return pd.DataFrame({
        f"at least {NUTRITION_LIMITS['min_kcal']} kcal": kcal >= NUTRITION_LIMITS["min_kcal"],
        f"sodium <= {NUTRITION_LIMITS['max_sodium_mg']:,} mg": df["sodium_mg"].isna() | (df["sodium_mg"] <= NUTRITION_LIMITS["max_sodium_mg"]),
        f"protein <= {NUTRITION_LIMITS['max_protein_g']} g": df["protein_g"].isna() | (df["protein_g"] <= NUTRITION_LIMITS["max_protein_g"]),
        "macros match calories": macro_kcal.isna() | ((macro_kcal - kcal).abs() <= MACRO_TOLERANCE * kcal.clip(lower=1)),
    })


# ------------------------------------------------------------------ USDA matching (5.8.2)
def words(text):
    return [singular(w) for w in re.findall(r"[a-z]+", str(text).lower())]


def norm_text(text):
    return " ".join(words(text))


# Title words that say nothing about the dish itself
TITLE_FILLER = {"and", "with", "the", "for", "easy", "best", "homemade", "style", "recipe", "quick",
                "simple", "mom", "grandma", "old", "fashioned", "classic", "ii", "iii", "oamc"}


def head_word(title):
    """The last meaningful word of a title, usually the dish: 'coconut cabbage curry' -> 'curry'."""
    meaningful = [w for w in words(title) if len(w) > 2 and w not in TITLE_FILLER]
    return meaningful[-1] if meaningful else ""

DISH_TOP_K = 5         # matches kept per recipe
DISH_MIN_SCORE = 0.25  # weaker matches are ignored
CANDIDATES = 50        # only the most similar USDA entries are scored in detail (much faster)


def top_candidates(similarity, row):
    """Positions and similarities of the CANDIDATES most similar USDA entries for one row."""
    start, end = similarity.indptr[row], similarity.indptr[row + 1]
    positions, values = similarity.indices[start:end], similarity.data[start:end]
    if len(values) > CANDIDATES:
        keep = np.argpartition(-values, CANDIDATES)[:CANDIDATES]
        positions, values = positions[keep], values[keep]
    return positions, values


def match_dishes(titles, dishes):
    """Return (scores, positions) of the best USDA dishes for each title, shape (n, DISH_TOP_K).

    Score = text similarity, +0.35 if the title's main word is in the first
    part of the USDA description (its food group, as in 'Rice, fried'),
    +0.1 if it appears later, -0.2 if it is missing. A score of 0 means no match.
    """
    vectorizer = TfidfVectorizer(token_pattern=r"[a-z]{3,}", sublinear_tf=True, ngram_range=(1, 2))
    dish_matrix = vectorizer.fit_transform(dishes["description"].map(norm_text))
    similarity = (vectorizer.transform([norm_text(t) for t in titles]) @ dish_matrix.T).tocsr()
    first_part = [set(words(d.split(",")[0])) for d in dishes["description"]]
    anywhere = [set(words(d)) for d in dishes["description"]]

    scores = np.zeros((len(titles), DISH_TOP_K))
    positions = np.zeros((len(titles), DISH_TOP_K), dtype=int)
    for row, title in enumerate(titles):
        candidates, text_score = top_candidates(similarity, row)
        if len(candidates) == 0:
            continue
        head = head_word(title)
        score = text_score + np.array(
            [0.35 if head in first_part[j] else 0.1 if head in anywhere[j] else -0.2 for j in candidates])
        best = np.argsort(-score)[:DISH_TOP_K]
        best = best[score[best] > DISH_MIN_SCORE]
        scores[row, :len(best)] = score[best]
        positions[row, :len(best)] = candidates[best]
    return scores, positions


def dish_features(dishes, scores, positions):
    """USDA evidence per recipe from its matched dishes: similarity-weighted calories
    per typical serving, energy density, and the best match score."""
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
INGREDIENT_USDA = {
    "sugar": "Sugars, granulated", "powdered sugar": "Sugars, powdered", "confectioners' sugar": "Sugars, powdered",
    "flour": FLOUR, "olive oil": "Oil, olive, salad or cooking", "vegetable oil": VEGETABLE_OIL,
    "oil": VEGETABLE_OIL, "canola oil": VEGETABLE_OIL,
    "pepper": BLACK_PEPPER, "black pepper": BLACK_PEPPER, "ground pepper": BLACK_PEPPER,
    "milk": "Milk, whole, 3.25% milkfat, with added vitamin D",
    "tomato": "Tomatoes, red, ripe, raw, year round average",
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
    "rice": "Rice, white, long-grain, regular, raw, enriched",
}


def match_ingredients(names, foods):
    """Return {ingredient: (row in foods, 'hand-checked' or 'automatic')} for the names that match."""
    vectorizer = TfidfVectorizer(token_pattern=r"[a-z]{3,}")
    food_matrix = vectorizer.fit_transform(foods["description"].map(norm_text))
    similarity = (vectorizer.transform([norm_text(n) for n in names]) @ food_matrix.T).tocsr()
    first_part = [norm_text(d.split(",")[0]) for d in foods["description"]]
    is_raw = foods["description"].str.contains("raw", case=False).to_numpy()
    n_details = foods["description"].str.count(",").to_numpy()   # fewer details = more generic food
    row_of = {d: i for i, d in enumerate(foods["description"])}

    matches = {}
    for row, name in enumerate(names):
        if name in INGREDIENT_USDA:
            matches[name] = (row_of[INGREDIENT_USDA[name]], "hand-checked")
            continue
        candidates, text_score = top_candidates(similarity, row)
        if len(candidates) == 0:
            continue
        target = norm_text(name)
        last = target.split()[-1:]
        bonus = np.array([0.5 if first_part[j] == target else 0.25 if first_part[j].split()[-1:] == last else 0.0
                          for j in candidates])
        score = text_score + bonus + 0.1 * is_raw[candidates] - 0.02 * n_details[candidates]
        best = int(np.argmax(score))
        if score[best] > 0.45:
            matches[name] = (candidates[best], "automatic")
    return matches


def ingredient_nutrition_table(ingredient_lists, foods, nutrient_columns):
    """Match every ingredient name to a USDA food; one row per matched name, most used first."""
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


def ingredient_energy_features(ingredient_lists, kcal_per_100g):
    """How energy-dense each recipe's ingredients are (amounts are unknown, so not the total)."""
    ingredient_kcal = ingredient_lists.explode().map(kcal_per_100g).astype(float).dropna()
    by_recipe = ingredient_kcal.groupby(level=0)
    return pd.DataFrame({
        "ing_kcal_mean"     : by_recipe.mean(),
        "ing_kcal_max"      : by_recipe.max(),
        "ing_share_over_300": (ingredient_kcal > 300).groupby(level=0).mean(),
        "ing_share_over_500": (ingredient_kcal > 500).groupby(level=0).mean(),
    }).reindex(ingredient_lists.index)   # recipes with no matched ingredient get missing values


def missing_hand_checked(foods):
    """Hand-checked USDA descriptions that are not in the download (should be none)."""
    return sorted(set(INGREDIENT_USDA.values()) - set(foods["description"]))
