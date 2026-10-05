"""Dish variants (notebook 06): halal, vegan, gluten-free ... versions of a dish, made by swapping
only the ingredients that break the diet, then re-checking the whole dish with the flag rules.

A variant is a suggestion, never a certification: the ingredient swaps come from what home cooks
reported (notebook 04) or from cooking guidance, and every variant is checked again before use."""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from functools import lru_cache

import pandas as pd

from .diets import DIET_PROFILES
from .flags import flags_for_term, keyword_flag
from .progress import MIN_ROWS, progress_bar

__all__ = [
    "GUIDANCE_SWAPS",
    "MIN_SWAP_REVIEWS",
    "TARGETS",
    "TARGET_CAUTIONS",
    "diet_blockers",
    "dish_variants",
    "make_variant",
    "target_rules",
]

# Target diet -> what it rules out: flags ("without"), and "vegetarian" / "vegan" when the dish must be one
TARGETS: dict[str, dict[str, list[str]]] = {
    "vegetarian": {"require": ["vegetarian"], "without": []},
    "vegan": {"require": ["vegan"], "without": []},
    "gluten_free": {"require": [], "without": ["contains_gluten"]},
    "dairy_free": {"require": [], "without": ["contains_dairy"]},
    "egg_free": {"require": [], "without": ["contains_egg"]},
    "nut_free": {"require": [], "without": ["contains_peanut", "contains_tree_nut"]},
    "alcohol_free": {"require": [], "without": ["contains_alcohol", "contains_alcohol_extract"]},
    **{diet: {"require": list(rule.get("require", [])), "without": list(rule.get("without", []))}
       for diet, rule in DIET_PROFILES.items() if diet in ("halal_friendly", "kosher_friendly", "pescatarian",
                                                            "no_beef", "jain_friendly", "lacto_vegetarian")},
}
# What a variant can not promise, shown with it
TARGET_CAUTIONS = {
    "halal_friendly": "Any meat must come from a halal source; this only removes forbidden ingredients.",
    "kosher_friendly": "Ingredients must be certified kosher; this only removes forbidden ingredients and "
                       "meat-with-dairy.",
    "gluten_free": "Use products labeled gluten-free: oats, sauces and stocks can carry wheat.",
    "nut_free": "Check labels for 'may contain nuts' when cooking for an allergy.",
}
# Swaps from cooking guidance, used when no reviewer reported a swap for that ingredient. Each is
# checked against the target like any other swap.
GUIDANCE_SWAPS = {
    "bacon": ["turkey bacon", "smoked tempeh"], "ham": ["smoked turkey"], "pork": ["chicken"],
    "ground pork": ["ground turkey"], "pork sausage": ["chicken sausage"], "pancetta": ["smoked turkey"],
    "lard": ["vegetable shortening"], "gelatin": ["agar"],
    "red wine": ["beef stock"], "white wine": ["vegetable stock"], "dry white wine": ["vegetable stock"],
    "beer": ["vegetable stock"], "mirin": ["rice vinegar"], "sherry": ["apple juice"], "rum": ["pineapple juice"],
    "vanilla extract": ["vanilla bean"], "brandy": ["apple juice"],
    "butter": ["olive oil", "vegan butter"], "milk": ["oat milk", "soy milk"], "heavy cream": ["coconut cream"],
    "sour cream": ["coconut yogurt"], "cream cheese": ["vegan cream cheese"], "parmesan cheese": ["nutritional yeast"],
    "egg": ["flax egg"], "mayonnaise": ["vegan mayonnaise"], "honey": ["maple syrup"],
    "flour": ["rice flour"], "all-purpose flour": ["gluten-free flour"], "soy sauce": ["tamari"],
    "breadcrumb": ["gluten-free breadcrumb"], "pasta": ["rice noodle"], "spaghetti": ["rice noodle"],
    "chicken broth": ["vegetable broth"], "beef broth": ["vegetable broth"], "chicken stock": ["vegetable stock"],
    "ground beef": ["lentil", "ground turkey"], "chicken": ["tofu", "chickpea"], "beef": ["mushroom", "jackfruit"],
    "shrimp": ["chicken"], "fish sauce": ["soy sauce"], "anchovy": ["capers"], "worcestershire sauce": ["soy sauce"],
    "peanut": ["sunflower seed"], "peanut butter": ["sunflower seed butter"], "almond": ["sunflower seed"],
    "walnut": ["pumpkin seed"], "pecan": ["pumpkin seed"],
    # Jain, Vaishnava and Buddhist cooking replace onion and garlic with a pinch of asafoetida (hing)
    "garlic": ["asafoetida"], "onion": ["asafoetida"], "red onion": ["asafoetida"], "green onion": ["asafoetida"],
    "shallot": ["asafoetida"], "garlic clove": ["asafoetida"], "garlic powder": ["asafoetida"],
}
# A reviewed swap must be reported by at least this many reviews (one review can describe anything)
MIN_SWAP_REVIEWS = 3


def target_rules(target: str) -> tuple[frozenset[str], tuple[str, ...]]:
    """(flags the target rules out, "vegetarian" / "vegan" it requires), from TARGETS."""
    rule = TARGETS[target]
    return frozenset(rule["without"]), tuple(rule["require"])


@lru_cache(maxsize=200_000)
def _breaks(ingredient: str, target: str) -> bool:
    """Whether one ingredient on its own breaks the target diet (cached: the same names repeat)."""
    without, require = target_rules(target)
    if without & set(flags_for_term(ingredient)):
        return True
    return any(not keyword_flag(ingredient, diet) for diet in require)


def diet_blockers(ingredients: Iterable[str], target: str) -> list[str]:
    """The ingredients that break a target diet, in recipe order ([] when the dish already fits).

    Args:
        ingredients: Normalized ingredient names (notebook 01's ingredient_list).
        target: A key of TARGETS ("vegan", "halal_friendly" ...).

    Returns:
        Each blocking ingredient once.
    """
    return [i for i in dict.fromkeys(ingredients) if _breaks(str(i).lower(), target)]


def _swap_table(swaps: pd.DataFrame | None, min_reviews: int = MIN_SWAP_REVIEWS) -> dict[str, list[tuple[str, float, str]]]:
    """original -> [(substitute, n_reviews, source)], reviewed swaps first (most reviews first), then guidance."""
    table: dict[str, list[tuple[str, float, str]]] = {}
    if swaps is not None and len(swaps):
        reviewed = swaps[swaps["n_reviews"] >= min_reviews].sort_values("n_reviews", ascending=False)
        for original, substitute, n in reviewed[["original", "substitute", "n_reviews"]].itertuples(index=False):
            table.setdefault(str(original), []).append((str(substitute), float(n), "reviews"))
    for original, substitutes in GUIDANCE_SWAPS.items():
        table.setdefault(original, []).extend((s, 0.0, "guidance") for s in substitutes)
    return table


def make_variant(ingredients: Sequence[str], target: str,
                 swap_table: Mapping[str, Sequence[tuple[str, float, str]]],
                 avoid: Iterable[str] = ()) -> dict:
    """Make one dish fit a target diet by swapping only the ingredients that break it.

    Each blocking ingredient gets the best substitute that fits the target itself
    (most reviews first, then cooking guidance). The whole new ingredient list is
    then checked again with the same rules, so a swap can never sneak a forbidden
    ingredient back in. A variant exists only when every blocker has a safe swap.

    Args:
        ingredients: The dish's normalized ingredient names.
        target: A key of TARGETS.
        swap_table: _swap_table(...) output: original -> [(substitute, n_reviews, source)].
        avoid: Extra ingredient names the person does not want as substitutes.

    Returns:
        {"status": "fits" | "variant" | "no_variant", "swaps": [(original, substitute, source)],
        "ingredients": new list, "missing": blockers with no safe swap, "min_reviews": the
        fewest reviews behind any reviewed swap (None when all came from guidance),
        "caution": TARGET_CAUTIONS text or ""}.
    """
    ingredients = [str(i) for i in ingredients]
    blockers = diet_blockers(ingredients, target)
    caution = TARGET_CAUTIONS.get(target, "")
    if not blockers:
        return {"status": "fits", "swaps": [], "ingredients": ingredients, "missing": [], "min_reviews": None,
                "caution": caution}
    avoid = set(avoid)
    chosen: dict[str, tuple[str, float, str]] = {}
    missing = []
    for blocker in blockers:
        option = next((o for o in swap_table.get(blocker, [])
                       if o[0] not in avoid and o[0] != blocker and not _breaks(o[0], target)), None)
        if option is None:
            missing.append(blocker)
        else:
            chosen[blocker] = option
    new = list(dict.fromkeys(chosen[i][0] if i in chosen else i for i in ingredients))
    if missing or diet_blockers(new, target):   # the final check, on the whole new dish
        return {"status": "no_variant", "swaps": [], "ingredients": ingredients, "missing": missing or blockers,
                "min_reviews": None, "caution": caution}
    reviewed = [n for _, n, source in chosen.values() if source == "reviews"]
    return {"status": "variant", "swaps": [(b, s, src) for b, (s, _, src) in chosen.items()], "ingredients": new,
            "missing": [], "min_reviews": int(min(reviewed)) if reviewed else None, "caution": caution}


def dish_variants(recipes: pd.DataFrame, targets: Sequence[str], swaps: pd.DataFrame | None = None,
                  min_reviews: int = MIN_SWAP_REVIEWS) -> pd.DataFrame:
    """Variants of many dishes for several target diets.

    Args:
        recipes: Recipes with recipe_id, recipe_name and ingredient_list.
        targets: Keys of TARGETS.
        swaps: Notebook 04's ingredient_substitutions table (None uses guidance swaps only).
        min_reviews: Fewest reviews a reported swap needs (MIN_SWAP_REVIEWS).

    Returns:
        One row per recipe and target: recipe_id, recipe_name, target, status, n_swaps,
        swaps ("butter -> olive oil; milk -> oat milk"), variant_ingredients, missing,
        min_reviews, caution.
    """
    table = _swap_table(swaps, min_reviews)
    rows = []
    items = list(recipes[["recipe_id", "recipe_name", "ingredient_list"]].itertuples(index=False))
    for recipe_id, name, ingredients in progress_bar(items, "Dish variants", show=len(items) >= MIN_ROWS):
        for target in targets:
            v = make_variant(list(ingredients), target, table)
            rows.append({"recipe_id": recipe_id, "recipe_name": name, "target": target, "status": v["status"],
                         "n_swaps": len(v["swaps"]), "swaps": "; ".join(f"{a} -> {b}" for a, b, _ in v["swaps"]),
                         "variant_ingredients": v["ingredients"] if v["status"] == "variant" else [],
                         "missing": v["missing"], "min_reviews": v["min_reviews"], "caution": v["caution"]})
    return pd.DataFrame(rows)
