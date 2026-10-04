"""Parse lists and labels stored as text in the raw datasets."""
from __future__ import annotations

import ast
import json

import numpy as np

__all__ = [
    "parse_label_list",
    "parse_list_string",
]


def parse_list_string(raw: object) -> list:
    """Parse a list stored as text, in JSON ('["a"]') or Python ("['a']") form.

    Args:
        raw: Text, a list or an array.

    Returns:
        The items, or [] if the value is not a list.
    """
    if isinstance(raw, (list, tuple, np.ndarray)):
        return list(raw)
    if not isinstance(raw, str):
        return []
    for parser in (json.loads, ast.literal_eval):
        try:
            items = parser(raw)
        except (ValueError, SyntaxError):
            continue
        return list(items) if isinstance(items, (list, tuple)) else []
    return []


def parse_label_list(raw: object) -> list[str]:
    """Turn a label value into a list of lowercase labels.

    Handles list strings ('["asian", "indian"]'), real lists, and single labels
    such as 'Middle East'.
    """
    if isinstance(raw, str) and not raw.strip().startswith("["):
        items = [raw]
    else:
        items = parse_list_string(raw)
    return [str(i).strip().lower() for i in items]
