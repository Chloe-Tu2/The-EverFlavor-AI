"""Blind hand-check samples for the restriction flags (5.12): drawing them and scoring the flags."""
from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from .checks import require_columns
from .flags import COMPOUND_INGREDIENTS, FLAG_RULES, explain_flag, make_flag
from .progress import progress_bar

__all__ = [
    "ANSWERS",
    "COMPOUND_HEADS",
    "COMPOUND_MIN_RECIPES",
    "DISAGREEMENT_COLUMNS",
    "EVIDENCE_COLUMNS",
    "EVIDENCE_MIN_PRODUCTS",
    "EVIDENCE_MIN_SHARE",
    "EVIDENCE_PAGE_SIZE",
    "OFF_ALLERGEN_FLAGS",
    "REVIEW_DIR",
    "REVIEW_PER_SOURCE",
    "compound_candidates",
    "compound_evidence",
    "declared_allergens",
    "disagreement_file",
    "labeled_file",
    "make_review_samples",
    "sample_file",
    "save_disagreements",
    "score_flags",
]


REVIEW_DIR = Path("docs/flag_review")
REVIEW_PER_SOURCE = 50
ANSWERS = {"1": 1, "0": 0, "yes": 1, "no": 0, "y": 1, "n": 0, "true": 1, "false": 0,
           "1.0": 1, "0.0": 0}
DISAGREEMENT_COLUMNS = ["recipe_id", "recipe_name", "ingredients", "flag", "answer", "pipeline_flag",
                        "why_flagged", "team_check"]


def sample_file(round_no: int, folder: str | Path = REVIEW_DIR) -> Path:
    """Return the blind sample file of a review round."""
    return Path(folder) / f"flag_review_sample_round{round_no}.csv"


def labeled_file(round_no: int, folder: str | Path = REVIEW_DIR) -> Path:
    """Return the labeled (answers) file of a review round."""
    return Path(folder) / f"flag_review_labeled_round{round_no}.csv"


def disagreement_file(round_no: int, folder: str | Path = REVIEW_DIR) -> Path:
    """Return the disagreements file of a review round."""
    return Path(folder) / f"flag_review_disagreements_round{round_no}.csv"


def make_review_samples(df_all: pd.DataFrame, rounds: Mapping[int, int], flag_columns: Sequence[str],
                        folder: str | Path = REVIEW_DIR, per_source: int = REVIEW_PER_SOURCE) -> None:
    """Write a blind sample for every review round that does not have one yet.

    Existing samples are never overwritten, no recipe appears in two rounds, and
    each sample has the same number of recipes from each source (fewer if a
    source is small). The flag columns are left empty for the reviewer.

    Args:
        df_all: The combined recipe table.
        rounds: Round number -> random seed.
        flag_columns: The flags the reviewer answers.
        folder: Where the review files live.
        per_source: Recipes per source in each sample.
    """
    Path(folder).mkdir(parents=True, exist_ok=True)
    # Every saved sample counts, also rounds left out of `rounds`, so a new round is always fresh
    already_sampled: set[str] = set()
    for saved in sorted(Path(folder).glob("flag_review_sample_round*.csv")):
        already_sampled |= set(pd.read_csv(saved, usecols=["recipe_id"], dtype=str)["recipe_id"])
    for round_no, seed in rounds.items():
        path = sample_file(round_no, folder)
        if path.exists():
            print(f"Round {round_no} sample already exists: {path}")
            continue
        pool = df_all[~df_all["recipe_id"].isin(already_sampled)]
        picked = [g.sample(min(len(g), per_source), random_state=seed).index
                  for _, g in pool.groupby("source")]
        sample = pool.loc[np.concatenate(picked)]
        sheet = pd.DataFrame({
            "recipe_id"  : sample["recipe_id"],
            "source"     : sample["source"],
            "recipe_name": sample["recipe_name"],
            "ingredients": sample["ingredient_list"].apply(lambda l: " | ".join(l)),
            "url"        : sample["url"],
        })
        for flag in flag_columns:
            sheet[flag] = ""          # reviewers fill 1 or 0
        sheet.to_csv(path, index=False)
        already_sampled |= set(sheet["recipe_id"])
        print(f"Saved {len(sheet)} recipes for review to {path}")


def score_flags(labeled_path: str | Path, df_all: pd.DataFrame,
                flag_columns: Sequence[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Score our flags against one labeled review round.

    Blank answers are skipped, and flags the round was labeled without are
    skipped too. For vegetarian and vegan, the risky case ("not vegetarian")
    is scored.

    Args:
        labeled_path: The labeled file of a round.
        df_all: The combined table with our flags.
        flag_columns: The flags to score.

    Returns:
        (scores, disagreements): recall and precision per flag, and one row per
        recipe and flag where the answer and our flag differ.

    Raises:
        ValueError: If the file has no answers yet.
    """
    labeled = pd.read_csv(labeled_path, dtype={"recipe_id": str}).merge(
        df_all[["recipe_id", *flag_columns]], on="recipe_id", suffixes=("_true", "_ours"))
    rows, disagreements = [], []
    for flag in flag_columns:
        if f"{flag}_true" not in labeled:
            continue   # this round was labeled before the flag existed
        true = labeled[f"{flag}_true"].astype(str).str.strip().str.lower().map(ANSWERS)
        ours = labeled[f"{flag}_ours"].astype(int)
        known = true.notna()
        if not known.any():
            continue   # nobody has reviewed this flag yet
        true, ours = true[known].astype(int), ours[known]
        for idx in true.index[true != ours]:
            disagreements.append({"recipe_id": labeled.at[idx, "recipe_id"], "recipe_name": labeled.at[idx, "recipe_name"],
                                  "ingredients": labeled.at[idx, "ingredients"], "flag": flag,
                                  "answer": int(true[idx]), "pipeline_flag": int(ours[idx]),
                                  "why_flagged": _why_flagged(f"{labeled.at[idx, 'ingredients']} | "
                                                              f"{labeled.at[idx, 'recipe_name']}", flag),
                                  "team_check": ""})   # reviewer: who is right? write "answer" or "pipeline"
        # For vegetarian / vegan the risky case is "not vegetarian", so score that side
        if flag in ("vegetarian", "vegan"):
            true, ours = 1 - true, 1 - ours
        tp = ((true == 1) & (ours == 1)).sum()
        positives, flagged = (true == 1).sum(), (ours == 1).sum()
        rows.append({"flag": flag if flag not in ("vegetarian", "vegan") else f"not {flag}",
                     "reviewed": int(known.sum()), "positives": int(positives),
                     # NaN when the sample has no such recipes, instead of a misleading 0
                     "recall": tp / positives if positives else np.nan,
                     "precision": tp / flagged if flagged else np.nan})
    if not rows:
        raise ValueError(f"{Path(labeled_path).name} has no answers yet; fill flag columns with 1 or 0.")
    return (pd.DataFrame(rows).set_index("flag").round(3),
            pd.DataFrame(disagreements, columns=DISAGREEMENT_COLUMNS))


def _why_flagged(text: object, flag: str) -> str:
    """Say what set (or ruled out) a flag, for the reviewer: the keywords, or where else it came from."""
    keywords = explain_flag(str(text).lower(), flag)
    if keywords:
        return "keyword: " + ", ".join(keywords)
    return "no keyword in the cleaned ingredients (raw ingredient text, or a Hugging Face label)"


# ------------------------------------------------------------------ compound ingredients (5.13)
# Open Food Facts allergen tag -> our flag column
OFF_ALLERGEN_FLAGS = {
    "en:gluten": "contains_gluten", "en:milk": "contains_dairy", "en:eggs": "contains_egg",
    "en:peanuts": "contains_peanut", "en:nuts": "contains_tree_nut", "en:fish": "contains_fish",
    "en:crustaceans": "contains_shellfish", "en:molluscs": "contains_shellfish",
    "en:soybeans": "contains_soy", "en:sesame-seeds": "contains_sesame",
}
# Last words that mark a ready-made product, whose allergens are hidden from the recipe
COMPOUND_HEADS = {"pudding", "sauce", "paste", "mix", "stock", "broth", "bouillon", "spread", "dressing",
                  "seasoning", "crumb", "cracker", "cookie", "wrapper", "pastry", "crust", "cake", "custard",
                  "ketchup", "relish", "chutney", "pesto", "gravy", "soup", "cereal", "granola", "candy",
                  "chocolate", "frosting", "icing", "marinade", "rub", "bar", "biscuit", "wafer", "chip",
                  "curry", "masala", "powder", "base", "cube", "concentrate", "glaze", "topping", "filling",
                  "batter", "noodle"}
COMPOUND_MIN_RECIPES = 100   # only ingredients used this often are looked up
EVIDENCE_PAGE_SIZE = 20      # products fetched per ingredient
EVIDENCE_MIN_PRODUCTS = 5    # fewer matching products is not enough evidence
EVIDENCE_MIN_SHARE = 0.6     # share of matching products that must declare the allergen
EVIDENCE_COLUMNS = ["ingredient", "recipes", "products", "rule_flags", "declared_shares",
                    "suggested_flags", "team_decision", "reviewed_by", "notes"]


def compound_candidates(df: pd.DataFrame, min_recipes: int = COMPOUND_MIN_RECIPES) -> pd.DataFrame:
    """List ready-made ingredients (COMPOUND_HEADS) used in at least `min_recipes` recipes.

    Args:
        df: Recipes with 'ingredient_list'.
        min_recipes: Minimum number of recipes.

    Returns:
        'ingredient' and 'recipes', most used first.

    Raises:
        ValueError: If 'ingredient_list' is missing.
    """
    require_columns(df, ["ingredient_list"], "compound_candidates")
    counts = df["ingredient_list"].explode().dropna().astype(str).value_counts()
    counts = counts[[name.split()[-1] in COMPOUND_HEADS if name.split() else False for name in counts.index]]
    counts = counts[counts >= min_recipes]
    return counts.rename_axis("ingredient").reset_index(name="recipes")


def _names_match(ingredient: str, product_name: str) -> bool:
    """True if every word of the ingredient appears in the product name (plural endings allowed)."""
    words = re.findall(r"[a-z]+", product_name.lower())
    found = set(words) | {w[:-1] for w in words if w.endswith("s")} | {w[:-2] for w in words if w.endswith("es")}
    return all(w in found for w in re.findall(r"[a-z]+", ingredient.lower()))


def declared_allergens(ingredient: str, products: Sequence[Mapping]) -> tuple[int, dict[str, float]]:
    """Summarize the allergens that Open Food Facts products declare for one ingredient.

    Only products whose name contains every word of the ingredient count, so a
    search for "ranch dressing" does not count a salad that comes with it.

    Args:
        ingredient: For example "ranch dressing".
        products: Raw Open Food Facts products (with 'product_name' and 'allergens_tags').

    Returns:
        (number of matching products, {flag column: share of them declaring it}).
    """
    matching = [p for p in products if _names_match(ingredient, str(p.get("product_name") or ""))]
    shares: dict[str, float] = {}
    for product in matching:
        flags = {OFF_ALLERGEN_FLAGS[t] for t in product.get("allergens_tags") or [] if t in OFF_ALLERGEN_FLAGS}
        for flag in flags:
            shares[flag] = shares.get(flag, 0) + 1 / len(matching)
    return len(matching), {f: round(s, 2) for f, s in sorted(shares.items())}


def _base_rule_flags(ingredient: str) -> list[str]:
    """Allergen flags the keyword rules give an ingredient, leaving out COMPOUND_INGREDIENTS.

    The compound entries are what this evidence is meant to check, so they must
    not count as "already flagged by the rules".
    """
    flags = []
    for flag in dict.fromkeys(OFF_ALLERGEN_FLAGS.values()):
        keywords, exceptions = FLAG_RULES[flag]
        if make_flag(ingredient, [k for k in keywords if k not in COMPOUND_INGREDIENTS], exceptions):
            flags.append(flag)
    return flags


def compound_evidence(candidates: pd.DataFrame, search: Callable[[str], list[dict]],
                      previous: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build the evidence table that the team reviews in 5.13.

    For each candidate it records which allergen flags our keyword rules give
    the ingredient on its own, which allergens Open Food Facts products declare,
    and the flags to add: declared by at least EVIDENCE_MIN_SHARE of at least
    EVIDENCE_MIN_PRODUCTS products, and not already given by the rules.

    Args:
        candidates: Output of compound_candidates.
        search: Returns Open Food Facts products for a search text (for example
            a cached search); an exception marks that ingredient as not looked up.
        previous: The last saved evidence table. The team's decisions in it are
            kept, and so is its Open Food Facts evidence (only new or failed
            ingredients are looked up), so the slow searches run only once.

    Returns:
        One row per candidate with EVIDENCE_COLUMNS.

    Raises:
        ValueError: If a needed column is missing.
    """
    require_columns(candidates, ["ingredient", "recipes"], "compound_evidence")
    kept: dict[str, dict] = {}
    if previous is not None and not previous.empty:
        kept = {str(k): v for k, v in previous.fillna("").set_index("ingredient").to_dict("index").items()}
    rows = []
    pairs = zip(candidates["ingredient"], candidates["recipes"])
    for ingredient, recipes in progress_bar(pairs, "Checking ready-made ingredients", total=len(candidates)):
        rule_flags = _base_rule_flags(ingredient)
        old = kept.get(ingredient, {})
        shares: Mapping[str, float | str]   # flag -> share, or "lookup_failed" -> the error
        if old and int(old.get("products", -1)) >= 0:
            n_products = int(old["products"])
            shares = dict(pair.split("=") for pair in str(old["declared_shares"]).split())
        else:
            try:
                n_products, shares = declared_allergens(ingredient, search(ingredient))
            except Exception as e:  # noqa: BLE001 - one failed lookup must not stop the others
                n_products, shares = -1, {"lookup_failed": type(e).__name__}
        suggested = sorted({f for f, s in shares.items() if f in OFF_ALLERGEN_FLAGS.values()
                            and n_products >= EVIDENCE_MIN_PRODUCTS and float(s) >= EVIDENCE_MIN_SHARE
                            and f not in rule_flags})
        rows.append({"ingredient": ingredient, "recipes": int(recipes), "products": n_products,
                     "rule_flags": " ".join(dict.fromkeys(rule_flags)),
                     "declared_shares": " ".join(f"{f}={s}" for f, s in shares.items()),
                     "suggested_flags": " ".join(suggested),
                     "team_decision": old.get("team_decision", ""),
                     "reviewed_by": old.get("reviewed_by", ""), "notes": old.get("notes", "")})
    return pd.DataFrame(rows, columns=EVIDENCE_COLUMNS).fillna("")


def save_disagreements(disagreements: pd.DataFrame, round_no: int, folder: str | Path = REVIEW_DIR) -> Path:
    """Save a round's disagreements, unless a reviewer has started filling in 'team_check'.

    Returns:
        The disagreements file.
    """
    path = disagreement_file(round_no, folder)
    started = path.exists() and pd.read_csv(path)["team_check"].notna().any()
    if not started:
        disagreements.to_csv(path, index=False)
    return path
