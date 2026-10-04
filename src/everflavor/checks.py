"""Input checks shared by the other modules: fail early, with a message that says what to fix."""
from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

__all__ = [
    "require_columns",
]


def require_columns(df: pd.DataFrame, columns: Iterable[str], where: str) -> None:
    """Check that a dataframe has the columns a function needs.

    Args:
        df: The dataframe passed to the function.
        columns: The columns it needs.
        where: The function's name, used in the message.

    Raises:
        ValueError: Naming every missing column, instead of a KeyError deep inside the function.
    """
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"{where}() needs the column(s) {missing}, which are missing. "
                         f"Available columns: {list(df.columns)}")
