"""One chart style for the whole project, and the helpers every chart uses."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.container import BarContainer
from matplotlib.figure import Figure

FIGURE_DIR = Path("data/processed/figures")

SOURCE_LABELS = {"foodcom": "Food.com", "huggingface": "Hugging Face",
                 "culinarydb": "CulinaryDB", "themealdb": "TheMealDB"}
FAMILY_ORDER = ["African", "Middle Eastern", "Latin American", "Asian", "European", "Other"]
# Same color for each cuisine family in every chart
FAMILY_COLORS = dict(zip(FAMILY_ORDER, sns.color_palette("muted", 5) + [(0.7, 0.7, 0.7)]))


def set_chart_style() -> None:
    """Apply the project chart style: bold titles, no box around the plot, a light grid."""
    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams.update({
        "figure.dpi": 110,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlepad": 12,
        "axes.labelsize": 11,
        "axes.spines.top": False,     # no box around the plot
        "axes.spines.right": False,
        "legend.frameon": False,
        "grid.alpha": 0.5,
    })


def show_figure(fig: Figure, name: str, folder: str | Path = FIGURE_DIR) -> None:
    """Tidy a chart, save it as a PNG and display it.

    Args:
        fig: The finished chart.
        name: File name without extension, for example "08_combining_sources".
        folder: Where to save the PNG (created if missing).
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(folder / f"{name}.png", bbox_inches="tight", dpi=110)
    plt.show()


def thousands(ax: Axes, axis: str = "y") -> None:
    """Show 12,000 instead of 12000 on a count axis ("y" or "x")."""
    formatter = plt.FuncFormatter(lambda v, _: f"{v:,.0f}")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(formatter)


def label_bars(ax: Axes, fmt: str = "{:,.0f}", **kwargs) -> None:
    """Write each bar's value on top of it, formatted with `fmt` (extra kwargs go to `bar_label`)."""
    for container in ax.containers:
        if not isinstance(container, BarContainer):
            continue   # other chart elements (error bars, lines) have no bar values
        ax.bar_label(container, labels=[fmt.format(v) for v in container.datavalues],  # type: ignore[union-attr]  # matplotlib's stubs allow None; bars always have values
                     padding=2, fontsize=9, **kwargs)
