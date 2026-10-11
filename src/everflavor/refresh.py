"""Keep the saved data in step with the rules (2026-10-10).

The saved recipe tables hold flags and nutrition worked out with the rules of the day notebook 01 ran.
When a rule changes in the code (a new pork word, a USDA hand-check), the tables are out of date until
they are rebuilt. This module:

- **fingerprints the rules** (`rules_fingerprint`): notebook 01 saves it in `dataset_info.json`;
- **checks the saved data** (`data_freshness`): "current", "old" or "unknown", with what to do;
- **refreshes the flags in about 20-25 minutes** (`refresh_saved_data`), instead of rerunning notebook 01
  (about an hour): only the flags and diet profiles are worked out again (`pipeline.refresh_flags`).
  A change to the ingredient names or the USDA matches still needs notebook 01.

From the project folder (VS Code / Antigravity terminal):

    python -m everflavor.refresh            (with src on the path: set PYTHONPATH=src first)

Safety never depends on this: the agents check every recipe with the current rules before showing it.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .diets import DIET_PROFILES, NUTRITION_DIETS
from .flags import (
    ANIMAL_EXCEPTIONS,
    ANIMAL_KEYWORDS,
    COMPOUND_INGREDIENTS,
    FLAG_RULES,
    FOOD_EMOJI,
    FOREIGN_FOOD_WORDS,
    GLUTEN_FREE_NAME,
    HF_FREE_LABELS,
    LOOK_ALIKE_LETTERS,
    MEAT_EXCEPTIONS,
    MEAT_KEYWORDS,
)
from .ingredients import INGREDIENT_SYNONYMS
from .nutrition import (
    BOUGHT_DRY,
    FORM_WORDS,
    INGREDIENT_USDA,
    NO_USDA_MATCH,
    PROCESSING_WORDS,
)
from .pipeline import (
    FOR_PEOPLE_NAME,
    PET_FOOD_NAME,
    POISONOUS_TO_PETS,
    refresh_flags,
    split_tables,
)

__all__ = [
    "FLAG_LOGIC_VERSION",
    "PIPELINE_LOGIC_VERSION",
    "data_freshness",
    "refresh_saved_data",
    "rules_fingerprint",
]

# Raise by one when the CODE that works out the flags changes in a way the rule lists do not show
# (a new step in add_keyword_flags, say); the rule lists themselves are fingerprinted automatically.
FLAG_LOGIC_VERSION = 2   # 2: the flags read a decoded copy of every text (reveal_hidden_words)
# The same for the rest of notebook 01 (ingredient names, USDA matching): needs a full rerun.
PIPELINE_LOGIC_VERSION = 2   # 2: Hugging Face names keep the word that matters ("groundnut oil")

DATASET_INFO = Path("data/processed/dataset_info.json")
ALL_RECIPES = Path("data/interim/recipes_all.parquet")
SPLITS = {name: Path(f"data/processed/recipes_{name}.parquet") for name in ("train", "val", "test")}
# Later notebooks that read the flags and should be rerun after a refresh (about 10 minutes together)
READS_THE_FLAGS = ["02_cooking_methods_and_fats", "04_ingredient_knowledge", "06_dish_variants"]


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=sorted).encode("utf-8")).hexdigest()[:16]


def rules_fingerprint() -> dict[str, str]:
    """Short fingerprints of the rules: "flags" (refreshable without notebook 01) and "pipeline" (notebook 01)."""
    flags = {"version": FLAG_LOGIC_VERSION,
             "rules": {column: [sorted(keywords), sorted(exceptions)] for column, (keywords, exceptions)
                       in FLAG_RULES.items()},
             "meat": [sorted(MEAT_KEYWORDS), sorted(MEAT_EXCEPTIONS)],
             "animal": [sorted(ANIMAL_KEYWORDS), sorted(ANIMAL_EXCEPTIONS)],
             "compounds": COMPOUND_INGREDIENTS, "hf_labels": HF_FREE_LABELS, "gluten_free_name": GLUTEN_FREE_NAME,
             "diets": DIET_PROFILES, "nutrition_diets": NUTRITION_DIETS,
             "pets": [PET_FOOD_NAME, POISONOUS_TO_PETS, FOR_PEOPLE_NAME],
             "decoding": [FOREIGN_FOOD_WORDS, FOOD_EMOJI, LOOK_ALIKE_LETTERS]}
    pipeline = {"version": PIPELINE_LOGIC_VERSION, "usda": INGREDIENT_USDA, "no_match": sorted(NO_USDA_MATCH),
                "words": [sorted(PROCESSING_WORDS), sorted(FORM_WORDS), sorted(BOUGHT_DRY)],
                "synonyms": INGREDIENT_SYNONYMS}
    return {"flags": _digest(flags), "pipeline": _digest(pipeline)}


def data_freshness(root: str | Path = ".") -> dict[str, str]:
    """Compare the saved data's rules with the code's.

    Returns:
        {"flags", "pipeline": "current", "old" or "unknown" (saved before fingerprints existed or
        no data), "message": what to do, "" when everything is current}.
    """
    info_file = Path(root) / DATASET_INFO
    saved = {}
    if info_file.exists():
        saved = json.loads(info_file.read_text(encoding="utf-8")).get("rules", {})
    now = rules_fingerprint()
    status = {part: ("unknown" if part not in saved else "current" if saved[part] == now[part] else "old")
              for part in ("flags", "pipeline")}
    if not info_file.exists():
        message = ("No dataset_info.json, so the rules the data was built with are unknown: run notebook 01 "
                   "(it writes the file).")
    elif "unknown" in status.values():
        message = ("The data was saved before rule fingerprints existed: run notebook 01 once (30-45 minutes); "
                   "later rule changes then need only `python -m everflavor.refresh`.")
    elif status["pipeline"] != "current":
        message = ("The ingredient names or USDA rules changed since notebook 01 last ran: rerun notebook 01 "
                   "(30-45 minutes), then " + ", ".join(READS_THE_FLAGS) + ".")
    elif status["flags"] != "current":
        message = ("The flag or diet rules changed since the data was saved: run `python -m everflavor.refresh` "
                   "(about 20-25 minutes), then rerun " + ", ".join(READS_THE_FLAGS) + ".")
    else:
        message = ""
    return {**status, "message": message}


def refresh_saved_data(root: str | Path = ".", verbose: bool = True) -> pd.DataFrame:
    """Work out the flags and diet profiles of the saved tables again with the current rules.

    Rewrites `data/interim/recipes_all.parquet` and the three split files, and records the new flag
    fingerprint and the date in `dataset_info.json`. Nutrition, origin and the splits stay as they were.

    Returns:
        One row per flag or diet column that changed ("now true", "now false"); empty when none did.

    Raises:
        FileNotFoundError: If notebook 01 has not saved the tables yet.
        ValueError: If the tables were saved before the refresh columns existed (rerun notebook 01 once).
    """
    root = Path(root)
    recipes = pd.read_parquet(root / ALL_RECIPES)
    refreshed, changes = refresh_flags(recipes)
    refreshed.to_parquet(root / ALL_RECIPES, index=False)
    for (name, path), table in zip(SPLITS.items(), split_tables(refreshed)):
        table.to_parquet(root / path, index=False)
    info_file = root / DATASET_INFO
    info = json.loads(info_file.read_text(encoding="utf-8")) if info_file.exists() else {}
    info.setdefault("rules", {})["flags"] = rules_fingerprint()["flags"]
    info["flags_refreshed"] = datetime.date.today().isoformat()
    info.setdefault("rows", {}).update({"all": len(refreshed), **{n: int((refreshed["split"] == n).sum())
                                                                   for n in SPLITS}})
    info_file.write_text(json.dumps(info, indent=2, default=str), encoding="utf-8")
    if verbose:
        print(f"Refreshed the flags of {len(refreshed):,} recipes.")
        print(changes.to_string() if len(changes) else "No flag or diet changed.")
    return changes


def main() -> None:
    """Command line: show whether the saved data is current, and refresh the flags if they are old."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--force", action="store_true", help="refresh even if the flags look current")
    parser.add_argument("--root", default=".", help="the project folder (default: here)")
    args = parser.parse_args()
    status = data_freshness(args.root)
    print(f"Flags: {status['flags']}. Ingredient names and USDA matches: {status['pipeline']}.")
    if status["pipeline"] != "current":   # also data saved before fingerprints existed
        print(status["message"])
        return
    if status["flags"] == "current" and not args.force:
        print("Nothing to refresh.")
        return
    refresh_saved_data(args.root)
    print("Now rerun: " + ", ".join(READS_THE_FLAGS) + " (they read the flags).")


if __name__ == "__main__":
    main()
