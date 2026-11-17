"""Nutrition facts for the dish page, as the data has them (no app code, so tests can load it)."""
from __future__ import annotations

import pandas as pd


def as_number(value: object) -> float | None:
    """A number from the data, or None when it is missing."""
    try:
        out = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return out if pd.notna(out) else None


def nutrition_facts(row: pd.Series) -> dict:
    """The recipe's nutrition per serving, as the data has it: the numbers, whether they are the recipe's own
    ("listed") or an estimate from its ingredients, the estimate's range and the servings when known."""
    listed = str(row.get("nutrition_source")) == "listed" and bool(row.get("nutrition_plausible", True))
    facts = {label: as_number(row.get(column)) for label, column in
             (("Calories", "calories_per_serving"), ("Protein", "protein_g"), ("Fat", "fat_g"),
              ("Carbohydrates", "carbs_g"), ("Sodium", "sodium_mg"))}
    if listed:   # the recipe's own extra facts (Food.com, CC0 Kaggle set): only next to its own listed numbers
        facts.update({label: as_number(row.get(column)) for label, column in
                      (("Sugar", "sugar_g"), ("Fibre", "fiber_g"), ("Saturated fat", "saturated_fat_g"),
                       ("Cholesterol", "cholesterol_mg"))})
    low, high = as_number(row.get("calories_est_min")), as_number(row.get("calories_est_max"))
    servings = as_number(row.get("servings"))
    if servings is None:
        servings = as_number(row.get("servings_listed"))
    return {"facts": facts, "listed": listed, "range": (low, high) if low and high else None,
            "servings": int(servings) if servings and servings > 0 else None}


UNITS = {"Calories": "kcal", "Protein": "g", "Fat": "g", "Carbohydrates": "g", "Sodium": "mg", "Sugar": "g",
         "Fibre": "g", "Saturated fat": "g", "Cholesterol": "mg"}


def nutrition_line(info: dict) -> str:
    """One short line under the photo: calories, protein and servings, only the ones the data has."""
    facts = info["facts"]
    parts = [f"{facts['Calories']:.0f} kcal" if facts["Calories"] is not None else "",
             f"{facts['Protein']:.0f} g protein" if facts["Protein"] is not None else ""]
    parts = [p for p in parts if p]
    if not parts:
        return ""
    line = " · ".join(parts) + " per serving" + ("" if info["listed"] else " (estimated)")
    return line + (f" · serves {info['servings']}" if info["servings"] else "")


def dish_story(entry: dict | None, limit: int = 170) -> tuple[str, str] | None:
    """One line about what the dish is, for its card: the first sentence of Walter's sourced summary (Wikipedia,
    with its link for the credit), or None when there is no summary. Never written by a model."""
    summary = str((entry or {}).get("summary") or "").strip()
    if not summary:
        return None
    first = summary.split(". ")[0].rstrip(".") + "."
    if len(first) > limit:
        first = first[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    link = next((s.get("url", "") for s in (entry or {}).get("sources", [])
                 if str(s.get("name", "")).startswith("Wikipedia") and str(s.get("url", "")).startswith("https://")), "")
    return (first, link) if link else None   # no credit link, no line (Wikipedia text needs its credit)
