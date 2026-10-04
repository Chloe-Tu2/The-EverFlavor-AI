"""Small helpers for tables, run records and the completion checklist."""
import os
from importlib.metadata import PackageNotFoundError, version

import pandas as pd

from .charts import SOURCE_LABELS


def by_source(df, column):
    """Recipes per source (rows) and value of `column` (columns), with totals."""
    return pd.crosstab(df["source"].map(SOURCE_LABELS), df[column], margins=True, margins_name="total")


def package_version(name):
    """Installed version of a package, or None."""
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def hf_revision(repo_id):
    """The exact Hugging Face dataset revision (commit), or None if offline."""
    try:
        from huggingface_hub import HfApi
        return HfApi().dataset_info(repo_id).sha
    except Exception:  # noqa: BLE001 - offline, not installed, or Hub error: record no revision
        return None


def to_json(value):
    """Turn numpy numbers into plain Python ones for JSON."""
    return value.item() if hasattr(value, "item") else str(value)


def saved_rows(csv_path):
    """Return a saved CSV as a dataframe, or an empty one if it is missing."""
    return pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()


def print_checklist(checklist):
    """Print (week, item, proof path) items; an item with a path is done only if the path exists.

    Returns (items done, total).
    """
    current_week = None
    completed = 0
    for week, item, proof_path in checklist:
        if week != current_week:
            print(f"\n{'=' * 55}")
            print(f"  {week}")
            print(f"{'=' * 55}")
            current_week = week
        done = proof_path is None or os.path.exists(proof_path)
        completed += done
        note = "" if done else f"  (missing: {proof_path})"
        print(f"  [{'x' if done else ' '}] {item}{note}")
    print(f"\nTotal items completed: {completed} / {len(checklist)}")
    return completed, len(checklist)
