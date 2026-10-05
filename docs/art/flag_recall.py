"""Chart for the README: how many real cases each allergen flag catches in review round 4.

Round 4 was labeled by hand by a team member and scored before any fix, then the
misses it found were fixed. The chart shows both, so the README shows the honest
first measure next to the current one:

    python docs/art/flag_recall.py    # saves docs/art/flag_recall.svg

Numbers come from notebook 01, section 5.12 (recall on 200 recipes). Update
ROUND4 when a new round is scored.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Flag -> (recall before the fixes, recall after), in percent
ROUND4 = {
    "Pork": (100, 100), "Alcohol": (100, 100), "Gluten": (94.2, 94.2), "Dairy": (94.6, 94.6),
    "Egg": (100, 100), "Peanut": (100, 100), "Tree nuts": (94.7, 100), "Fish": (92.9, 100),
    "Shellfish": (100, 100), "Soy": (100, 100), "Sesame": (100, 100),
}
OUT = Path(__file__).with_name("flag_recall.svg")
AFTER, BEFORE, TEXT, GRID = "#2E7D32", "#C62828", "#555555", "#DDDDDD"


def draw() -> Path:
    """Draw a dot chart (before -> after) of round 4 recall per allergen and save it as SVG."""
    names = list(ROUND4)[::-1]                      # first flag at the top
    fig, ax = plt.subplots(figsize=(7.5, 4.9))
    for y, name in enumerate(names):
        before, after = ROUND4[name]
        if before != after:
            ax.annotate("", xy=(after, y), xytext=(before, y),
                        arrowprops={"arrowstyle": "->", "color": AFTER, "lw": 1.6})
            ax.plot(before, y, "o", ms=8, mfc="white", mec=BEFORE, mew=1.8)
        ax.plot(after, y, "o", ms=9, color=AFTER)
        ax.text(101.2, y, f"{after:.0f}%", va="center", fontsize=9, color=TEXT)
    ax.set_yticks(range(len(names)), names, fontsize=10)
    ax.set_xlim(90, 103)
    ax.set_xticks([90, 92, 94, 96, 98, 100], ["90%", "92%", "94%", "96%", "98%", "100%"], fontsize=9, color=TEXT)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0)
    ax.plot([], [], "o", mfc="white", mec=BEFORE, mew=1.8, ls="", label="first measure (hand-labeled)")
    ax.plot([], [], "o", color=AFTER, ls="", label="after the round 4 fixes")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=9)
    ax.set_title("Real cases each allergen flag catches (review round 4, 200 recipes)",
                 fontsize=11, loc="left", color="#222222", pad=26)
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    fig.savefig(OUT, format="svg", facecolor="white")
    plt.close(fig)
    return OUT


if __name__ == "__main__":
    print("Saved", draw())
