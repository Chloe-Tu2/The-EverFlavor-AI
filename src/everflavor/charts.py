"""One chart style for the whole project, and the helpers every chart uses."""
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

FIGURE_DIR = Path("data/processed/figures")

SOURCE_LABELS = {"foodcom": "Food.com", "huggingface": "Hugging Face",
                 "culinarydb": "CulinaryDB", "themealdb": "TheMealDB"}
FAMILY_ORDER = ["African", "Middle Eastern", "Latin American", "Asian", "European", "Other"]
# Same color for each cuisine family in every chart
FAMILY_COLORS = dict(zip(FAMILY_ORDER, sns.color_palette("muted", 5) + [(0.7, 0.7, 0.7)]))


def set_chart_style():
    """Bold titles, no box around the plot, light grid."""
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


def show_figure(fig, name, folder=FIGURE_DIR):
    """Tidy, save to data/processed/figures/<name>.png, and display a chart."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(folder / f"{name}.png", bbox_inches="tight", dpi=110)
    plt.show()


def thousands(ax, axis="y"):
    """Show 12,000 instead of 12000 on a count axis."""
    formatter = plt.FuncFormatter(lambda v, _: f"{v:,.0f}")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(formatter)


def label_bars(ax, fmt="{:,.0f}", **kwargs):
    """Write each bar's value on top of it."""
    for container in ax.containers:
        ax.bar_label(container, labels=[fmt.format(v) for v in container.datavalues],
                     padding=2, fontsize=9, **kwargs)
