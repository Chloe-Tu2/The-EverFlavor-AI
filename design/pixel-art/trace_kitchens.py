"""Trace the team's kitchens object by object, then assemble them as real pixel art.

For each object in a kitchen (listed below with a box around it on the original, 1672 x 941):
  1. isolate it: GrabCut (OpenCV) separates it from what is behind it, so its outline follows the original at its
     real angle (a window on the side wall stays on the side wall, a stool keeps its legs);
  2. take it out of the room: the backdrop is the original with every object's place filled in from around it;
  3. put both on the pixel grid (418 x 235, the original at a quarter size) with one limited palette per kitchen,
     and give every object a dark outline along its edge;
  4. assemble: backdrop, then the objects from the back to the front.

Each object is also saved on its own with its place (scene.json, the format of the app's interactive kitchen), so
it can move when tapped later. Needs OpenCV (design work only): pip install opencv-python-headless

    python design/pixel-art/trace_kitchens.py chinese   ->   design/pixel-art/drafts/traced-kitchens/chinese/
"""
from __future__ import annotations

import base64
import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REF = HERE / "references" / "concepts"
OUT = HERE / "drafts" / "traced-kitchens"
SCALE = 4                    # the original is 4x the pixel grid
COLORS = 56                  # one palette per kitchen

# Objects per kitchen: name -> box (x0, y0, x1, y1) on the original, listed from the back to the front
OBJECTS = {
    "chinese": {
        "lantern_window": (0, 110, 82, 262), "lantern_left": (538, 192, 636, 332), "lantern_right": (1228, 192, 1332, 332),
        "bottles": (562, 326, 818, 426), "bowl_greens": (832, 336, 902, 426), "jars": (902, 352, 1152, 426),
        "pan_black": (598, 442, 702, 584), "pan_copper": (702, 442, 794, 568), "vine": (1138, 356, 1222, 532),
        "chilies": (1228, 326, 1298, 508), "garlic": (1402, 316, 1478, 488), "bamboo": (1282, 256, 1412, 618),
        "basket_top": (1572, 96, 1668, 162), "vine_right": (1478, 156, 1562, 372),
        "bowl_plant": (482, 492, 582, 618), "utensils": (572, 530, 632, 618), "red_bowl": (728, 572, 808, 618),
        "steamer": (798, 512, 922, 618), "blue_bowl": (912, 572, 978, 618), "wok": (966, 526, 1148, 608),
        "red_pot": (1142, 536, 1278, 612), "veg_baskets": (1382, 496, 1664, 628),
        "plant_left": (0, 366, 134, 612), "vase_flowers": (132, 476, 208, 608), "oranges": (52, 582, 158, 648),
        "bowl_table": (192, 586, 278, 638),
        "stool_back": (0, 696, 78, 864), "stool_mid": (128, 686, 268, 864), "stool_front": (322, 686, 448, 864),
        "basket_greens": (1492, 676, 1628, 844), "plant_right": (1586, 586, 1672, 844),
    },
    "mediterranean": {
        "mantel_plants": (45, 140, 480, 440), "jug_mantel": (295, 205, 355, 272), "lantern_left": (580, 185, 700, 300),
        "lantern_right": (1040, 180, 1160, 330), "bottles": (570, 335, 725, 412), "jars": (725, 360, 1000, 430),
        "chilies": (490, 370, 545, 500), "pan_black": (560, 425, 640, 535), "pan_copper": (650, 425, 720, 535),
        "garlic_vine": (1180, 240, 1320, 460), "picture": (1360, 325, 1435, 440), "plant_shelf": (1465, 355, 1545, 440),
        "hanging_plant": (1545, 95, 1672, 420), "plates": (1475, 495, 1550, 540), "red_jars": (1540, 470, 1620, 545),
        "sunflowers_left": (0, 445, 115, 635), "fruit_bowl": (65, 590, 165, 640), "herb_pot": (435, 505, 520, 630),
        "barrel": (435, 620, 500, 760), "bread_basket": (360, 660, 480, 780), "candle_board": (510, 570, 665, 635),
        "copper_pots": (670, 510, 895, 610), "board_mortar": (905, 485, 990, 632), "small_pan": (980, 590, 1050, 632),
        "herbs": (1200, 505, 1300, 630), "towel": (1165, 615, 1255, 745), "vase_sunflowers": (1300, 430, 1410, 610),
        "tomatoes": (1400, 565, 1500, 628), "table": (0, 615, 235, 890), "stool_front": (0, 690, 130, 890),
        "plant_right": (1530, 580, 1672, 845),
    },
    "mexican": {
        "lamp_left": (0, 0, 60, 230), "lantern_mid": (495, 125, 560, 245), "lantern_right": (1095, 125, 1150, 245),
        "hanging_plant": (345, 60, 480, 330), "plate_wall": (360, 345, 445, 440), "tile_picture": (1195, 148, 1272, 232),
        "pots_top": (495, 262, 900, 350), "pots_mid": (495, 375, 900, 450), "chilies": (1280, 235, 1340, 400),
        "shelf_plants": (1345, 110, 1672, 420), "jars_shelf": (1450, 310, 1660, 425), "clay_vase": (1385, 405, 1465, 500),
        "cactus": (1190, 385, 1340, 580), "tomato_basket": (975, 515, 1120, 580), "sacks": (800, 495, 970, 580),
        "limes": (740, 500, 850, 580), "steel_pot": (488, 495, 615, 560), "spoons": (400, 475, 460, 585),
        "flower_vase": (345, 485, 410, 585), "plant_counter": (185, 500, 300, 600), "flowers": (290, 485, 350, 585),
        "fruit_bowl": (1420, 535, 1530, 590), "board": (1500, 490, 1545, 585), "tap": (1565, 525, 1620, 600),
        "plant_left": (0, 320, 140, 600), "tomatoes_left": (60, 560, 150, 610), "plant_table": (15, 605, 165, 740),
        "chili_bowl": (145, 665, 255, 720), "utensil_pot": (255, 580, 325, 680), "mortar": (265, 630, 375, 725),
        "runner": (365, 665, 560, 895), "stool_mid": (555, 730, 705, 920), "stool_right": (1230, 650, 1350, 790),
        "plant_right": (1480, 665, 1672, 920), "stool_front": (0, 815, 180, 941),
    },
    "middle_eastern": {
        "vine_left": (0, 70, 90, 360), "lantern_hanging": (210, 130, 305, 370), "lantern_left": (445, 70, 525, 220),
        "lantern_right": (1155, 70, 1240, 220), "vine_sign_left": (520, 50, 620, 235),
        "vine_sign_right": (1060, 45, 1150, 215), "jars": (428, 245, 805, 345), "ewers_shelf": (805, 220, 1030, 348),
        "vases_top": (1420, 110, 1580, 220), "vine_shelf": (1365, 105, 1460, 320), "vine_right": (1575, 140, 1672, 390),
        "vases_mid": (1455, 280, 1610, 372), "palm": (1255, 320, 1515, 600), "lantern_floor": (1485, 445, 1570, 610),
        "plant_counter_right": (1575, 450, 1672, 590), "plant_counter_left": (215, 360, 355, 585),
        "dates_left": (330, 535, 415, 585), "dates_right": (1100, 530, 1190, 585), "sacks": (420, 415, 700, 580),
        "ewer_gold": (690, 420, 800, 580), "bread": (790, 465, 1100, 585), "table": (0, 690, 335, 905),
        "plant_left": (0, 560, 135, 705), "tea_set": (55, 565, 300, 712), "stool_mid": (300, 725, 470, 900),
        "basket": (1555, 685, 1650, 760), "stool_right": (1450, 720, 1600, 900), "pot_right": (1600, 720, 1672, 900),
    },
}


def isolate(img: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    """The object's mask inside its box: GrabCut, then the biggest connected piece, smoothed a little."""
    x0, y0, x1, y1 = box
    pad = 6                                                          # GrabCut needs some background around the box
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(img.shape[1], x1 + pad), min(img.shape[0], y1 + pad)
    crop = img[Y0:Y1, X0:X1]
    mask = np.zeros(crop.shape[:2], np.uint8)
    rect = (x0 - X0 + 1, y0 - Y0 + 1, max(2, x1 - x0 - 2), max(2, y1 - y0 - 2))
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(crop, mask, rect, bg, fg, 6, cv2.GC_INIT_WITH_RECT)
    obj = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    obj = cv2.morphologyEx(obj, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(obj)
    if n > 1:                                                         # keep the pieces that matter (not specks)
        keep = [k for k in range(1, n) if stats[k, cv2.CC_STAT_AREA] > 0.08 * stats[1:, cv2.CC_STAT_AREA].max()]
        obj = np.isin(labels, keep).astype(np.uint8) * 255
    full = np.zeros(img.shape[:2], np.uint8)
    full[Y0:Y1, X0:X1] = obj
    return full


def palette_of(img: np.ndarray, k: int) -> np.ndarray:
    data = img.reshape(-1, 3).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, _, centers = cv2.kmeans(data, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    return centers.astype(np.uint8)


def to_palette(img: np.ndarray, pal: np.ndarray) -> np.ndarray:
    flat = img.reshape(-1, 1, 3).astype(np.int32)
    idx = ((flat - pal.reshape(1, -1, 3).astype(np.int32)) ** 2).sum(axis=2).argmin(axis=1)
    return pal[idx].reshape(img.shape)


def png_uri(rgba: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def trace(name: str) -> None:
    img = cv2.cvtColor(cv2.imread(str(REF / f"{name}.jpg")), cv2.COLOR_BGR2RGB)
    h, w = img.shape[0] // SCALE, img.shape[1] // SCALE
    out = OUT / name
    (out / "sprites").mkdir(parents=True, exist_ok=True)

    masks = {obj: isolate(img, box) for obj, box in OBJECTS[name].items()}
    everything = np.zeros(img.shape[:2], np.uint8)
    for m in masks.values():
        everything = np.maximum(everything, m)
    grown = cv2.dilate(everything, np.ones((9, 9), np.uint8))
    backdrop_full = cv2.inpaint(img, grown, 9, cv2.INPAINT_TELEA)     # the empty room

    small = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
    pal = palette_of(small, COLORS)
    backdrop = to_palette(cv2.resize(backdrop_full, (w, h), interpolation=cv2.INTER_AREA), pal)
    final = backdrop.copy()
    pieces = {}
    for obj, m in masks.items():
        msmall = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA) > 110
        if not msmall.any():
            continue
        ys, xs = np.nonzero(msmall)
        x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
        colours = to_palette(small[y0:y1, x0:x1], pal)
        sub = msmall[y0:y1, x0:x1]
        edge = sub & ~cv2.erode(sub.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        dark = (colours.astype(np.int32) * 55 // 100).astype(np.uint8)    # a dark outline in the object's own hue
        colours = np.where(edge[..., None], to_palette(dark, pal), colours)
        rgba = np.dstack([colours, sub.astype(np.uint8) * 255])
        Image.fromarray(rgba, "RGBA").save(out / "sprites" / f"{obj}.png")
        final[y0:y1, x0:x1] = np.where(sub[..., None], colours, final[y0:y1, x0:x1])
        pieces[obj] = {"png": png_uri(rgba), "x": int(x0), "y": int(y0), "w": int(x1 - x0), "h": int(y1 - y0)}

    Image.fromarray(backdrop).save(out / "backdrop.png")
    Image.fromarray(final).save(out / f"{name}.png")
    Image.fromarray(final).resize((w * 4, h * 4), Image.NEAREST).save(out / f"{name}_x4.png")
    bd = np.dstack([backdrop, np.full(backdrop.shape[:2], 255, np.uint8)])
    (out / "scene.json").write_text(json.dumps({"size": [w, h], "backdrop": png_uri(bd), "pieces": pieces}), encoding="utf-8")

    orig = Image.fromarray(img).resize((w * 2, h * 2), Image.LANCZOS)
    mine = Image.fromarray(final).resize((w * 2, h * 2), Image.NEAREST)
    sheet = Image.new("RGB", (w * 4 + 8, h * 2), "white")
    sheet.paste(orig, (0, 0))
    sheet.paste(mine, (w * 2 + 8, 0))
    sheet.save(out / "compare.png")
    print(f"{name}: {len(pieces)} objects traced, palette of {COLORS}, written to {out}")


if __name__ == "__main__":
    for kitchen in sys.argv[1:] or list(OBJECTS):
        trace(kitchen)
