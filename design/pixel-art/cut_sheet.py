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


TOP = 640                                   # the pieces start under the kitchen


def foreground(part: np.ndarray) -> np.ndarray:
    """Everything that is not the checkerboard. The checkerboard is light and grey: the light grey areas that touch
    the edge, or are too big to be a highlight, are background. Then the light fringe the background left on the
    pieces' edges is peeled off."""
    rgb = part.astype(np.int32)
    light = (rgb.min(axis=2) > 205) & (rgb.max(axis=2) - rgb.min(axis=2) < 20)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(light.astype(np.uint8), connectivity=4)
    edge = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))) - {0}
    big = {k for k in range(1, n) if stats[k, cv2.CC_STAT_AREA] > 150}
    solid = ~np.isin(labels, list(edge | big))
    fringe = (rgb.min(axis=2) > 170) & (rgb.max(axis=2) - rgb.min(axis=2) < 35)
    for _ in range(2):                                                # peel the light fringe, a pixel at a time
        near = cv2.dilate((~solid).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        solid &= ~(near & fringe)
    return cv2.morphologyEx(solid.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)).astype(bool)


def cut_all(sheet: np.ndarray, boxes: dict[str, tuple[int, int, int, int]]) -> dict[str, np.ndarray]:
    """Each piece is every blob of the foreground whose centre is in the piece's box, so a piece that reaches past
    its box is not cut off, and bits of a neighbour that reach into the box are left out."""
    part = sheet[TOP:, :, :3]
    solid = foreground(part)
    near = cv2.dilate(solid.astype(np.uint8), np.ones((5, 5), np.uint8))   # parts a few pixels apart stay together
    n, blobs, stats, centres = cv2.connectedComponentsWithStats(near)
    pieces = {}
    for piece, (x0, y0, x1, y1) in boxes.items():
        mine = [k for k in range(1, n) if x0 <= centres[k][0] < x1 and y0 - TOP <= centres[k][1] < y1 - TOP
                and stats[k, cv2.CC_STAT_AREA] > 60]
        mask = np.isin(blobs, mine) & solid
        ys, xs = np.nonzero(mask)
        if not len(ys):
            continue
        sl = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
        pieces[piece] = np.dstack([part[sl], mask[sl].astype(np.uint8) * 255])
    return pieces


def main() -> None:
    for name, (file, boxes) in SHEETS.items():
        sheet = np.array(Image.open(REF / file).convert("RGB"))
        out = OUT / name
        out.mkdir(parents=True, exist_ok=True)
        pieces = cut_all(sheet, boxes)
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
