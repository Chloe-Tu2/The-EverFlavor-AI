"""The recipe quality audit: what each recipe has and lacks (name, ingredients, steps, servings, time, nutrition,
country, photo, link), by source, and the duplicates. Counts only; it changes no recipe.

    python scripts/knowledge/recipe_quality_audit.py   # docs/audits/recipe_quality.md, data/knowledge/recipe_quality.json

The limits used (a day of cooking, 50 servings, 40 ingredients, 3,000 kcal a serving) are only where a person
should look; nothing is removed by them.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

COLS = ["recipe_id", "source", "recipe_name", "dish_name", "ingredient_list", "instructions", "servings", "minutes",
        "minutes_source", "calories_per_serving", "has_nutrition", "nutrition_plausible", "origin_country",
        "cuisine_labeled", "image_url", "photo_ok", "url"]
NAMES = {"foodcom": "Food.com", "culinarydb": "CulinaryDB", "huggingface": "Hugging Face", "themealdb": "TheMealDB"}


def checks(df: pd.DataFrame) -> dict[str, pd.Series]:
    n_ing = df.ingredient_list.map(lambda v: len(v) if v is not None and not isinstance(v, float) else 0)
    steps = df.instructions.fillna("").astype(str).str.strip()
    servings = df.servings.fillna(df.servings_listed)
    minutes = df.minutes.fillna(df.total_minutes)
    own_photo = df.image_url.notna() & (df.image_url.astype(str).str.strip() != "") & (
        df.photo_ok.astype("boolean").fillna(True))
    name = df.recipe_name.fillna("").astype(str).str.strip()
    key = df.dish_name.fillna("").astype(str).str.lower() + "|" + df.ingredient_list.map(
        lambda v: "|".join(sorted(map(str, v))) if v is not None and not isinstance(v, float) else "")
    return {
        "name missing or under 3 letters": name.str.len() < 3,
        "name in capitals only": name.str.isupper() & (name.str.len() > 3),
        "no ingredients": n_ing == 0,
        "one ingredient": n_ing == 1,
        "over 40 ingredients": n_ing > 40,
        "no steps": steps == "",
        "steps under 40 characters": (steps != "") & (steps.str.len() < 40),
        "no servings": servings.isna() | (servings <= 0),
        "over 50 servings": servings > 50,
        "no time given (an estimate is shown)": minutes.isna(),
        "over a day of time": minutes > 1440,
        "no nutrition": ~df.has_nutrition.fillna(False).astype(bool),
        "nutrition not plausible": df.has_nutrition.fillna(False).astype(bool) & ~df.nutrition_plausible.fillna(False).astype(bool),
        "over 3,000 kcal a serving": df.calories_per_serving > 3000,
        "no country": df.origin_country.isna() | (df.origin_country == "Unknown"),
        "no photo of its own": ~own_photo,
        "no photo at all (neither its own nor its dish's)": ~own_photo & ~df.has_dish_photo,
        "own photo checked and rejected": df.photo_ok.astype("boolean").fillna(True) == False,
        "no source link": df.url.isna() | (df.url.astype(str).str.strip() == ""),
        "same dish name and ingredients as another": key.duplicated(keep=False) & (n_ing > 0),
    }


def main() -> None:
    data = ROOT / "data" / "processed"
    df = pd.concat([pd.read_parquet(data / f"recipes_{s}.parquet", columns=COLS) for s in ("train", "val", "test")],
                   ignore_index=True)
    # what the app adds when it loads the recipes (app.load_recipes): Food.com's own servings, times and photos,
    # and the free photos of the dish in general for recipes without one
    details = pd.read_parquet(data / "foodcom_details.parquet", columns=["recipe_id", "servings_listed", "total_minutes"])
    df = df.merge(details, on="recipe_id", how="left")
    photos = pd.read_parquet(data / "foodcom_photos.parquet", columns=["recipe_id", "image_url", "photo_ok"])
    df = df.merge(photos.rename(columns={"image_url": "fc_url", "photo_ok": "fc_ok"}), on="recipe_id", how="left")
    fill = df.image_url.isna() & df.fc_url.notna()
    df.loc[fill, "image_url"], df.loc[fill, "photo_ok"] = df.loc[fill, "fc_url"], df.loc[fill, "fc_ok"]
    dish_photo = set(pd.read_parquet(data / "dish_photos.parquet", columns=["recipe_id"]).recipe_id)
    df["has_dish_photo"] = df.recipe_id.isin(dish_photo)
    found = checks(df)
    sources = [s for s in NAMES if s in set(df.source)]
    table = {c: {"all": int(m.sum()), **{s: int(m[df.source == s].sum()) for s in sources}} for c, m in found.items()}
    sizes = {"all": len(df), **{s: int((df.source == s).sum()) for s in sources}}
    complete = ~pd.concat([found[c] for c in ("no ingredients", "no steps", "no servings", "no nutrition")], axis=1).any(axis=1)
    out = {"built_on": date.today().isoformat(), "by": "scripts/knowledge/recipe_quality_audit.py", "recipes": sizes,
           "checks": table, "complete": {"all": int(complete.sum()), **{s: int(complete[df.source == s].sum()) for s in sources}}}
    (ROOT / "data" / "knowledge" / "recipe_quality.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

    def cell(c: str, s: str) -> str:
        n = table[c][s]
        return f"{n:,} ({n / sizes[s]:.0%})" if sizes[s] else "0"

    lines = [f"# Recipe quality (audit, {out['built_on']})", "",
             ("What each recipe has and lacks, by source. Counts only: no recipe was changed or removed. Built by "
             "`scripts/knowledge/recipe_quality_audit.py`; the numbers are in `data/knowledge/recipe_quality.json`. "
             "The limits (a day of time, 50 servings, 40 ingredients, 3,000 kcal a serving) only say where a person "
             "should look."), "",
             "| Check | All | " + " | ".join(NAMES[s] for s in sources) + " |",
             "|---|" + "---:|" * (len(sources) + 1),
             "| Recipes | " + " | ".join(f"{sizes[s]:,}" for s in ["all", *sources]) + " |"]
    lines += [f"| {c} | " + " | ".join(cell(c, s) for s in ["all", *sources]) + " |" for c in table]
    lines += ["| **complete: ingredients, steps, servings and nutrition** | "
              + " | ".join(f"{out['complete'][s]:,} ({out['complete'][s] / sizes[s]:.0%})" for s in ["all", *sources]) + " |",
              "", "## What it means", ""]
    worst = sorted(((table[c]["all"], c) for c in table), reverse=True)[:5]
    lines += [f"- The most common gaps: {', '.join(f'{c} ({n:,})' for n, c in worst)}."]
    lines += [("- A recipe without steps or servings can still be recommended (its flags come from its ingredients), "
              "but its page has less to show; the planner's recipe page work should show what is missing, not hide it."),
              ("- Steps, servings and a source link are missing for whole sources (CulinaryDB and the Hugging Face set "
               "come without steps in our tables, Food.com without links), not for single recipes: filling them means "
               "a source that has them, never writing them."),
              ("- Recipes with the same cleaned dish name and the same ingredients: most are within one source "
               f"(Food.com {table['same dish name and ingredients as another'].get('foodcom', 0):,}); whether they "
               "are the same recipe, and merging them, is for a person to check."), ""]
    with (ROOT / "docs" / "audits" / "recipe_quality.md").open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print(json.dumps(out["complete"]), {c: v["all"] for c, v in table.items()})


if __name__ == "__main__":
    main()
