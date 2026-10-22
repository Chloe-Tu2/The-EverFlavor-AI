"""v6 (future work): the team's second, colorful Saffron Market traced with the v5 tracer.

Its settings live here so the v5 script (design/pixel-art/trace_kitchens.py) stays as approved: the kitchen above
the sheet's pieces, no extra outline (the art has its own), half the lighting (its glow is painted in), and the most
common colour per block. Judged too pixelated for now (2026-10-22); kept for the v6 pass.

    python design/pixel-art/future-works/v6/trace_v6.py   ->   design/pixel-art/future-works/v6/traced/middle_eastern_v2/
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))          # design/pixel-art, where trace_kitchens.py lives
import trace_kitchens as t

t.REF, t.OUT = HERE / "concepts", HERE / "traced"
t.OBJECTS["middle_eastern_v2"] = {
    "lantern_niche": (380, 85, 440, 215), "lantern_1": (495, 0, 560, 135), "lantern_2": (620, 60, 670, 165),
    "lantern_3": (690, 0, 750, 130), "lantern_4": (765, 95, 820, 235),
    "pots_shelf_top": (480, 140, 750, 200), "pots_shelf_mid": (480, 225, 750, 275),
    "jars_niche_left": (860, 130, 1000, 280), "jars_niche_mid": (1350, 95, 1450, 280),
    "jars_niche_right": (1510, 60, 1615, 290), "plant_hanging_mid": (555, 140, 620, 305),
    "plant_hanging_right": (760, 60, 850, 190), "plant_hanging_far": (1430, 60, 1500, 225),
    "plant_niche": (410, 300, 460, 360), "pan_rail": (1095, 230, 1305, 335), "pots_counter": (530, 340, 700, 385),
    "copper_teapot": (960, 310, 1110, 390), "red_pot": (1120, 345, 1200, 390), "vases_counter": (1310, 330, 1610, 400),
    "fruit_bowls": (670, 345, 1000, 425), "ewer": (780, 325, 840, 415), "tree_left": (0, 215, 140, 470),
    "pot_left": (0, 440, 95, 560), "sofa": (60, 360, 440, 530), "cushions": (130, 365, 350, 435),
    "teapot_table": (120, 440, 170, 480), "side_table": (95, 470, 200, 560), "stove": (1100, 375, 1310, 560),
    "island": (535, 400, 1000, 615), "stool_1": (470, 470, 600, 580), "stool_2": (605, 480, 755, 600),
    "plant_corner_left": (0, 500, 230, 624), "plant_right": (1480, 480, 1672, 624),
}
t.SOURCES["middle_eastern_v2"] = ("middle_eastern_v2_colorful.png", (0, 0, 1672, 624))
t.LIGHTS["middle_eastern_v2"] = [(200, 180, 330, 0.7, 0), (1200, 220, 160, 0.4, 0)]   # the window, under the hood
t.OUTLINE["middle_eastern_v2"] = None
t.LIGHTING["middle_eastern_v2"] = 0.5
t.MODE_SHRINK.add("middle_eastern_v2")

if __name__ == "__main__":
    t.trace("middle_eastern_v2")
