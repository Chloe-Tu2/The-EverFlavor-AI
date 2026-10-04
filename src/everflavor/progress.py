"""Progress bars that work the same in Google Colab, VS Code, Antigravity and a terminal."""
from __future__ import annotations

import importlib.util
import os
import sys
from collections.abc import Iterable
from typing import TypeVar

__all__ = [
    "MIN_ROWS",
    "MIN_SECONDS",
    "PROGRESS_ENV",
    "progress_bar",
]

T = TypeVar("T")

# Environment variable that picks the bar: unset or "auto" (widget in notebooks, text elsewhere),
# "text" (always the text bar, for an editor whose notebooks cannot draw widgets), "0" (no bars)
PROGRESS_ENV = "EVERFLAVOR_PROGRESS"
# Redraw at most once per second: keeps saved notebook outputs small
MIN_SECONDS = 1.0
# Tables smaller than this finish in a moment: functions show no bar for them
MIN_ROWS = 10_000


def _in_notebook() -> bool:
    """Return True inside a notebook kernel (Colab, VS Code, Antigravity, JupyterLab), not a terminal."""
    ipython = sys.modules.get("IPython")
    shell = ipython.get_ipython() if ipython is not None and hasattr(ipython, "get_ipython") else None
    return shell is not None and hasattr(shell, "kernel")


def progress_bar(items: Iterable[T], description: str = "", total: int | None = None,
                 show: bool = True) -> Iterable[T]:
    """Show a progress bar while a loop runs, without changing what the loop gets.

    In a notebook with ipywidgets (Colab always has it; locally it comes with
    config/requirements.txt) this is tqdm's widget bar, in Colab, VS Code and
    Antigravity alike. Elsewhere it is a text bar on standard output, so it does
    not look like an error. EVERFLAVOR_PROGRESS=text always uses the text bar (if
    an editor shows "HBox(...)" instead of a moving bar); without tqdm, or with
    EVERFLAVOR_PROGRESS=0, the items are returned unchanged.

    Args:
        items: What the loop runs over.
        description: Short text in front of the bar, for example "Matching USDA dishes".
        total: Number of items, when `items` has no length (for example a generator).
        show: False returns the items unchanged, for example for a small table (MIN_ROWS).

    Returns:
        An iterable over the same items, in the same order.
    """
    mode = os.environ.get(PROGRESS_ENV, "auto").strip().lower()
    if mode == "0" or not show:
        return items
    try:
        if mode != "text" and _in_notebook() and importlib.util.find_spec("ipywidgets") is not None:
            from tqdm.notebook import tqdm
            return tqdm(items, desc=description, total=total, mininterval=MIN_SECONDS)
        from tqdm import tqdm as text_tqdm
    except ImportError:
        return items
    # Text bar on stdout: notebooks show stderr in red, which looks like an error
    return text_tqdm(items, desc=description, total=total, mininterval=MIN_SECONDS, file=sys.stdout)
