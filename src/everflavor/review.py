"""Blind hand-check samples for the restriction flags (5.12): drawing them and scoring the flags."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

REVIEW_DIR = Path("docs/flag_review")
REVIEW_PER_SOURCE = 50
ANSWERS = {"1": 1, "0": 0, "yes": 1, "no": 0, "y": 1, "n": 0, "true": 1, "false": 0,
           "1.0": 1, "0.0": 0}
DISAGREEMENT_COLUMNS = ["recipe_id", "recipe_name", "ingredients", "flag", "answer", "pipeline_flag", "team_check"]


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
    already_sampled = set()
    for round_no, seed in rounds.items():
        path = sample_file(round_no, folder)
        if path.exists():
            already_sampled |= set(pd.read_csv(path, usecols=["recipe_id"], dtype=str)["recipe_id"])
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
