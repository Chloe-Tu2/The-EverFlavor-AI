"""Cut the pieces out of a team concept sheet (the part under the kitchen: chefs, the title sign, props).

The sheets have a painted light-grey checkerboard instead of real transparency. Each piece is cut from its box:
the light, grey pixels that touch the box's edge are the background and become transparent; everything else is the
piece. Design work only (needs OpenCV).

    python design/pixel-art/cut_sheet.py   ->   design/pixel-art/drafts/team-sheets/<sheet>/<piece>.png and sheet.png
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REF = HERE / "references" / "concepts"
OUT = HERE / "drafts" / "team-sheets"

# Boxes (x0, y0, x1, y1) on the 1672 x 941 sheet
SHEETS = {
    "middle_eastern_v2": ("middle_eastern_v2_colorful.png", {
        "chef_woman_dish": (35, 650, 150, 932), "chef_woman_spoon": (170, 650, 312, 932),
        "chef_man_pot": (318, 645, 442, 932), "chef_man_arms_crossed": (452, 645, 578, 932),
        "title_sign": (580, 640, 976, 885), "valance": (985, 650, 1338, 735), "shelf": (1360, 668, 1510, 728),
        "chalkboard": (1522, 648, 1652, 803), "plant_bowl": (985, 738, 1112, 858), "plant_flowers": (1132, 738, 1252, 855),
        "pan_rail": (1288, 752, 1512, 852), "basket_fruit": (938, 855, 1052, 935), "bowl_lemons": (1058, 855, 1168, 935),
        "tagine": (1172, 825, 1282, 935), "spice_jars": (1288, 852, 1528, 935), "ewer": (1528, 812, 1608, 935),
        "spoon_jar": (1608, 835, 1672, 935),
    }),
}


def cut(sheet: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = box
    crop = sheet[y0:y1, x0:x1, :3].astype(np.int32)
    light = (crop.min(axis=2) > 205) & (crop.max(axis=2) - crop.min(axis=2) < 20)     # the checkerboard
    n, labels = cv2.connectedComponents(light.astype(np.uint8), connectivity=4)
    edge = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))) - {0}
    background = np.isin(labels, list(edge)) & light
    alpha = np.where(background, 0, 255).astype(np.uint8)
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))       # drop stray specks
    n, parts, stats, _ = cv2.connectedComponentsWithStats((alpha > 0).astype(np.uint8))
    if n > 2:                                     # keep the piece's parts, drop bits of the neighbouring pieces
        areas = stats[1:, cv2.CC_STAT_AREA]
        keep = [k + 1 for k, area in enumerate(areas) if area >= 0.15 * areas.max()]
        alpha = np.where(np.isin(parts, keep), alpha, 0).astype(np.uint8)
    rgba = np.dstack([crop.astype(np.uint8), alpha])
    ys, xs = np.nonzero(alpha)
    return rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(ys) else rgba


def main() -> None:
    for name, (file, boxes) in SHEETS.items():
        sheet = np.array(Image.open(REF / file).convert("RGB"))
        out = OUT / name
        out.mkdir(parents=True, exist_ok=True)
        pieces = {piece: cut(sheet, box) for piece, box in boxes.items()}
        for piece, rgba in pieces.items():
            Image.fromarray(rgba, "RGBA").save(out / f"{piece}.png")
        # an overview on a dark background, so the cut edges show
        width = sum(p.shape[1] + 12 for p in pieces.values())
        rows, row, x, height = [], [], 0, 0
        for piece in pieces.values():
            if x + piece.shape[1] > 1400 and row:
                rows.append((row, height))
                row, x, height = [], 0, 0
            row.append((x, piece))
            x += piece.shape[1] + 12
            height = max(height, piece.shape[0])
        rows.append((row, height))
        view = Image.new("RGBA", (1400, sum(h + 12 for _, h in rows)), (40, 30, 26, 255))
        y = 0
        for row, h in rows:
            for x, piece in row:
                img = Image.fromarray(piece, "RGBA")
                view.alpha_composite(img, (x, y + h - piece.shape[0]))
            y += h + 12
        view.save(out / "sheet.png")
        print(f"{name}: {len(pieces)} pieces cut ({width} px of pieces), written to {out}")


if __name__ == "__main__":
    main()
