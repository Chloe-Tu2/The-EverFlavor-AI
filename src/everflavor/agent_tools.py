"""The agents' tools (roadmap step 3): recipe ideas, calories, where to buy, substitutions.

Each tool is an `llm.Tool` built for one user: the restrictions come from the `UserProfile` given
here, never from the model's arguments (extra arguments such as "avoid": [] are ignored). Anything a
tool suggests to eat is re-checked with the safety gate before the model sees it, so a model can only
pass on suggestions that fit the user.

The tables come from the notebooks' saved files (`load_agent_data`); a tool whose table is missing is
simply not offered (`agent_tools`). The same tools serve a local Ollama model (llm.run_tools), the
CrewAI agents and the app.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

from .ingredients import normalize_ingredient
from .llm import Tool, safety_tool
from .safety import UserProfile, check_recipe

__all__ = [
    "agent_tools",
    "calories_tool",
    "load_agent_data",
    "recommend_tool",
    "substitutions_tool",
    "where_to_buy_tool",
]

MAX_RESULTS = 5


def load_agent_data(root: str | Path = ".") -> dict[str, Any]:
    """Load the tables the tools use from the project folder (missing files are skipped).

    Returns:
        A dict with any of: "recipes" (notebook 01's splits), "usda" (USDA matches, notebook 01),
        "portions" (USDA household weights), "substitutions" (notebook 04), "products" and
        "places" (notebook 03).
    """
    root = Path(root)
    processed = root / "data" / "processed"
    data: dict[str, Any] = {}
    splits = [processed / f"recipes_{s}.parquet" for s in ("train", "val", "test")]
    if all(p.exists() for p in splits):
        data["recipes"] = pd.concat([pd.read_parquet(p) for p in splits], ignore_index=True)
    if (processed / "usda_ingredient_nutrition.csv").exists():
        data["usda"] = pd.read_csv(processed / "usda_ingredient_nutrition.csv")
        usda_dir = root / "data" / "raw" / "usda_fdc"
        if any(usda_dir.glob("*sr_legacy*")):
            from .calories import (
                usda_portions,  # reads the SR Legacy file: only when it is there
            )
            data["portions"] = usda_portions(usda_dir)
    for key, name in [("substitutions", "ingredient_substitutions"), ("products", "ingredient_products"),
                      ("places", "places")]:
        if (processed / f"{name}.parquet").exists():
            data[key] = pd.read_parquet(processed / f"{name}.parquet")
    return data


def _fits(items: list[str], profile: UserProfile) -> dict:
    """The safety gate on single ingredients: {"passed", "problems" (rule and words, per item)}."""
    report = check_recipe(items, "", profile)
    return {"passed": report["passed"],
            "problems": [{"item": p["line"], "rule": p["rule"], "matched": p["matched"]} for p in report["problems"]]}


def recommend_tool(recipes: pd.DataFrame, profile: UserProfile, max_results: int = MAX_RESULTS) -> Tool:
    """Recipe ideas that already fit the profile (recommend.baseline_recommend, then the gate again)."""
    from .recommend import baseline_recommend

    families = sorted(str(f) for f in recipes["cuisine_family"].dropna().unique())

    def run(cuisine: object = None, calories: object = None, how_many: object = 3, **_ignored: object) -> list[dict]:
        target = float(str(calories)) if calories not in (None, "") else (profile.calories_per_meal or 500.0)
        family = None if str(cuisine or "").strip().lower() in ("", "any", "none") else str(cuisine)
        count = max(1, min(int(float(str(how_many or 3))), max_results))
        found = baseline_recommend(recipes, cuisine_family=family, calorie_target=target,
                                   vegetarian_only=profile.vegetarian, vegan_only=profile.vegan,
                                   avoid=profile.avoid, diets=profile.diets, top_n=count)
        ideas: list[dict[str, Any]] = [{"name": str(r["recipe_name"]), "cuisine": str(r["cuisine_family"]),
                  "calories": round(float(r["calories_per_serving"])),
                  "ingredients": [str(i) for i in list(r["ingredient_list"])[:15]]} for _, r in found.iterrows()]
        return [i for i in ideas if check_recipe(i["ingredients"], i["name"], profile)["passed"]]

    return Tool(
        name="recommend_recipes",
        description="Find recipes that already fit the user's food restrictions. Returns name, cuisine, "
                    "calories per serving and ingredients.",
        parameters={"type": "object", "properties": {
            "cuisine": {"type": "string", "enum": ["any", *families], "description": "Cuisine family, or any"},
            "calories": {"type": "number", "description": "Target calories per serving"},
            "how_many": {"type": "integer", "description": f"How many recipes, 1 to {max_results}"}}},
        run=run,
    )


def calories_tool(usda: pd.DataFrame, portions: Mapping[int, Mapping[str, float]], profile: UserProfile) -> Tool:
    """Calories per serving of ingredient lines (calories.recipe_calories), against the user's budget."""
    from .calories import recipe_calories

    rows = usda.dropna(subset=["fdc_id", "kcal_100g"])
    fdc_of = dict(zip(rows["ingredient"], rows["fdc_id"].astype(int)))
    kcal_of = dict(zip(rows["fdc_id"].astype(int), rows["kcal_100g"].astype(float)))

    def run(ingredient_lines: object = (), servings: object = None, **_ignored: object) -> dict:
        if isinstance(ingredient_lines, str):
            lines = ingredient_lines.splitlines()
        elif isinstance(ingredient_lines, (list, tuple)):
            lines = [str(x) for x in ingredient_lines]
        else:
            raise TypeError("ingredient_lines must be a list of strings")
        if not lines:
            raise ValueError("ingredient_lines is empty")
        count = float(str(servings)) if servings not in (None, "", 0) else None
        result = recipe_calories(lines, count, fdc_of, kcal_of, portions)
        per_serving = result["kcal_per_serving"]
        budget = profile.calories_per_meal
        return {"kcal_per_serving": None if per_serving is None else round(per_serving),
                "kcal_total": round(result["kcal_total"]),
                "share_of_lines_counted": round(result["counted_share"], 2),
                "not_counted": [str(t) for t in result["not_counted"]["text"]][:10]
                if hasattr(result["not_counted"], "columns") else list(result["not_counted"])[:10],
                "budget_per_meal": budget,
                "over_budget_by": None if per_serving is None or budget is None or per_serving <= budget
                else round(per_serving - budget),
                "note": "Lines not counted add calories that are missing from the total."}

    return Tool(
        name="count_calories",
        description="Count the calories of a recipe from its ingredient lines with amounts (USDA data), "
                    "and compare one serving with the user's calorie budget.",
        parameters={"type": "object", "required": ["ingredient_lines"], "properties": {
            "ingredient_lines": {"type": "array", "items": {"type": "string"},
                                 "description": "One ingredient per item, with amounts ('2 cups rice')"},
            "servings": {"type": "number", "description": "How many servings the recipe makes"}}},
        run=run,
    )


def where_to_buy_tool(products: pd.DataFrame, places: pd.DataFrame, profile: UserProfile) -> Tool:
    """Brands from the dish's home country and stores to try (stores.suggest_where_to_buy), with a
    warning when the ingredient itself breaks the user's rules."""
    from .stores import suggest_where_to_buy

    def run(ingredient: object = "", origin_country: object = "", **_ignored: object) -> dict:
        names = normalize_ingredient(ingredient)
        if not names:
            raise ValueError(f"not an ingredient: {ingredient!r}")
        found = suggest_where_to_buy(names[0], str(origin_country or ""), products, places, n=MAX_RESULTS)
        return {**found, "fits_user": _fits([str(ingredient)], profile)}

    return Tool(
        name="where_to_buy",
        description="Find brands of an ingredient from a dish's home country and nearby grocery stores that may "
                    "carry them (not verified: suggest calling first).",
        parameters={"type": "object", "required": ["ingredient"], "properties": {
            "ingredient": {"type": "string", "description": "One ingredient, for example 'fish sauce'"},
            "origin_country": {"type": "string", "description": "The dish's home country, for example 'Thailand'"}}},
        run=run,
    )


def substitutions_tool(substitutions: pd.DataFrame, profile: UserProfile) -> Tool:
    """Swaps home cooks reported for an ingredient (notebook 04), keeping only swaps that fit the user."""
    def run(ingredient: object = "", **_ignored: object) -> dict:
        names = normalize_ingredient(ingredient)
        if not names:
            raise ValueError(f"not an ingredient: {ingredient!r}")
        rows = substitutions[substitutions["original"] == names[0]].sort_values("n_reviews", ascending=False)
        swaps, left_out = [], []
        for row in rows.itertuples():
            check = _fits([str(row.substitute)], profile)
            if not check["passed"]:
                left_out.append(str(row.substitute))
                continue
            swaps.append({"substitute": str(row.substitute), "reviews": int(float(str(row.n_reviews or 0))),
                          "removes": str(row.flags_removed or ""), "adds": str(row.flags_added or ""),
                          "source": str(row.source)})
            if len(swaps) == MAX_RESULTS:
                break
        return {"ingredient": names[0], "swaps": swaps, "left_out_for_this_user": left_out[:MAX_RESULTS],
                "note": "Swaps home cooks reported in reviews; taste and texture can change."}

    return Tool(
        name="find_substitutions",
        description="Find substitutes for an ingredient that home cooks used, keeping only those that fit the "
                    "user's food restrictions.",
        parameters={"type": "object", "required": ["ingredient"], "properties": {
            "ingredient": {"type": "string", "description": "The ingredient to replace, for example 'butter'"}}},
        run=run,
    )


def agent_tools(data: Mapping[str, Any], profile: UserProfile) -> list[Tool]:
    """Every tool whose tables are in `data` (from load_agent_data), plus the safety gate, for one user."""
    tools = [safety_tool(profile)]
    if "recipes" in data:
        tools.append(recommend_tool(data["recipes"], profile))
    if "usda" in data and "portions" in data:
        tools.append(calories_tool(data["usda"], data["portions"], profile))
    if "products" in data and "places" in data:
        tools.append(where_to_buy_tool(data["products"], data["places"], profile))
    if "substitutions" in data:
        tools.append(substitutions_tool(data["substitutions"], profile))
    return tools
