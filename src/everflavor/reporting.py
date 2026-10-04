"""Small helpers for tables, run records and the completion checklist."""
from __future__ import annotations

import os
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import pandas as pd

from .charts import SOURCE_LABELS

__all__ = [
    "by_source",
    "hf_revision",
    "package_version",
    "print_checklist",
    "saved_rows",
    "to_json",
]


def by_source(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Count recipes per source (rows) and value of `column` (columns), with totals."""
    return pd.crosstab(df["source"].map(SOURCE_LABELS), df[column], margins=True, margins_name="total")


def package_version(name: str) -> str | None:
    """Return the installed version of a package, or None if it is not installed."""
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def hf_revision(repo_id: str) -> str | None:
    """Return the exact Hugging Face dataset revision (commit), or None if offline."""
    try:
        from huggingface_hub import HfApi
        return HfApi().dataset_info(repo_id).sha
    except Exception:  # noqa: BLE001 - offline, not installed, or Hub error: record no revision
        return None


def to_json(value: object) -> object:
    """Turn numpy numbers into plain Python ones (the `default` for json.dump)."""
    return value.item() if hasattr(value, "item") else str(value)


def saved_rows(csv_path: str | Path) -> pd.DataFrame:
    """Return a saved CSV as a dataframe, or an empty one if the file is missing."""
    return pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()


def print_checklist(checklist: Sequence[tuple[str, str, str | None]]) -> tuple[int, int]:
    """Print a completion checklist grouped by week.

    Args:
        checklist: (week, item, file that proves it is done, or None for manual items).

    Returns:
        (items done, total items). An item with a file is done only if the file exists.
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
