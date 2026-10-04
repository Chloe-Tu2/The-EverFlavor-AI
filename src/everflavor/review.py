"""Blind hand-check samples for the restriction flags (5.12): drawing them and scoring the flags."""
from pathlib import Path

import numpy as np
import pandas as pd

REVIEW_DIR = Path("docs/flag_review")
REVIEW_PER_SOURCE = 50
ANSWERS = {"1": 1, "0": 0, "yes": 1, "no": 0, "y": 1, "n": 0, "true": 1, "false": 0,
           "1.0": 1, "0.0": 0}
DISAGREEMENT_COLUMNS = ["recipe_id", "recipe_name", "ingredients", "flag", "answer", "pipeline_flag", "team_check"]


def sample_file(round_no, folder=REVIEW_DIR):
    return Path(folder) / f"flag_review_sample_round{round_no}.csv"


def labeled_file(round_no, folder=REVIEW_DIR):
    return Path(folder) / f"flag_review_labeled_round{round_no}.csv"


def disagreement_file(round_no, folder=REVIEW_DIR):
    return Path(folder) / f"flag_review_disagreements_round{round_no}.csv"


def make_review_samples(df_all, rounds, flag_columns, folder=REVIEW_DIR, per_source=REVIEW_PER_SOURCE):
    """Write a blind sample for every round that does not have one yet (never overwritten).

    `rounds` maps round number -> random seed. No recipe appears in two rounds, and
    each sample has the same number of recipes from each source (fewer if a source is small).
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


def score_flags(labeled_path, df_all, flag_columns):
    """Recall and precision of each flag against one labeled file (blank answers are skipped).

    Also returns the disagreements: one row per recipe and flag where the
    answer and our flag differ, for the team to spot-check.
    """
    labeled = pd.read_csv(labeled_path, dtype={"recipe_id": str}).merge(
        df_all[["recipe_id"] + flag_columns], on="recipe_id", suffixes=("_true", "_ours"))
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


def save_disagreements(disagreements, round_no, folder=REVIEW_DIR):
    """Save the disagreements to spot-check, unless a reviewer has started filling in team_check."""
    path = disagreement_file(round_no, folder)
    started = path.exists() and pd.read_csv(path)["team_check"].notna().any()
    if not started:
        disagreements.to_csv(path, index=False)
    return path
