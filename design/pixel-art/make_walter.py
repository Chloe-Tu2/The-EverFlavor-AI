"""Walter, the AI waiter (0.6.3): PLACEHOLDER pixel art from Claude's concept sketch A ("Classic": black vest, red bow
tie, towel over the arm), until the team's concept art replaces it (docs: the waiter plan).

Drawn in code on a 32x36 grid with a black outline, saved 4x (nearest neighbour) as assets/walter_<mood>.png.

    python design/pixel-art/make_walter.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

W, H = 32, 36
PAL = {"K": (43, 29, 26), "S": (232, 180, 138), "s": (201, 142, 102), "H": (59, 42, 32), "h": (96, 66, 48),
       "W": (246, 243, 236), "w": (206, 200, 188), "V": (47, 47, 58), "v": (30, 30, 38), "B": (179, 38, 46),
       "b": (122, 26, 32), "E": (26, 18, 16), "e": (255, 255, 255), "M": (142, 74, 58), "G": (224, 176, 64),
       "T": (90, 130, 190), "A": (122, 36, 48), "a": (92, 26, 36), "Y": (250, 236, 180), "y": (190, 170, 120),
       "R": (180, 180, 186), "r": (130, 130, 138), "C": (36, 98, 96), "c": (24, 70, 68), "P": (120, 90, 60),
       "N": (224, 150, 130)}


def blank():
    return np.full((H, W), "", dtype=object)


def fill(g, pts, col):
    for x, y in pts:
        if 0 <= x < W and 0 <= y < H:
            g[y, x] = col


def ellipse(cx, cy, rx, ry):
    return [(x, y) for y in range(H) for x in range(W) if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1]


def rect(x0, y0, x1, y1):
    return [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]


def body(g, vest, vest_dark, apron=None):
    for y in range(26, H):
        hw = min(8 + (y - 26) * 0.9, 13)
        for x in range(W):
            d = abs(x + .5 - 16)
            if d <= hw:
                col = "W"
                if vest and d > (36 - y) * 0.35 + 0.5 and d < hw - 2.5:
                    col = vest_dark if d > hw - 4 else vest
                if d >= hw - 1:
                    col = "w"
                g[y, x] = col
    if apron:
        fill(g, rect(9, 31, 22, 35), apron[0])
        fill(g, rect(9, 31, 22, 31), apron[1])


def head(g, hair, hair_hi, style):
    fill(g, rect(14, 22, 17, 26), "s")                                   # neck
    fill(g, ellipse(9, 17, 1.6, 2.2) + ellipse(23, 17, 1.6, 2.2), "S")   # ears
    fill(g, ellipse(16, 15.5, 6.6, 7.6), "S")
    fill(g, [(x, 22) for x in range(13, 19)], "s")                       # jaw shade
    if style == "slick":       # side part, swept back
        fill(g, ellipse(16, 10, 7.2, 4.6), hair)
        fill(g, rect(9, 10, 10, 15) + rect(22, 10, 23, 14), hair)
        fill(g, [(x, 8) for x in range(12, 20)], hair_hi)
        fill(g, [(12, 9), (13, 9)], "S")                                 # the part
    elif style == "messy":
        fill(g, ellipse(16, 10, 7.6, 5.2), hair)
        fill(g, rect(9, 10, 10, 16) + rect(22, 10, 23, 15), hair)
        fill(g, [(10, 13), (13, 12), (16, 13), (19, 12), (21, 13)], hair)  # fringe tufts
        fill(g, [(11, 7), (15, 6), (19, 7), (14, 8), (18, 8)], hair_hi)
    elif style == "grey":
        fill(g, ellipse(16, 10.5, 7.0, 4.2), hair)
        fill(g, rect(9, 11, 10, 17) + rect(22, 11, 23, 17), hair)
        fill(g, rect(12, 8, 19, 9), "S")                                 # receding top
        fill(g, [(x, 10) for x in range(11, 21)], hair_hi)


def face(g, mood, brow="H", stache=None):
    if mood == "wink":
        fill(g, [(12, 16), (13, 16), (13, 17), (12, 17)], "E")
        fill(g, [(12, 16)], "e")
        fill(g, [(18, 17), (19, 16), (20, 16), (21, 17)], "E")
    elif mood == "thinking":
        fill(g, [(13, 15), (14, 15), (13, 16), (14, 16), (20, 15), (21, 15), (20, 16), (21, 16)], "E")
        fill(g, [(13, 15), (20, 15)], "e")
    elif mood == "laugh":
        fill(g, [(11, 17), (12, 16), (13, 16), (14, 17), (18, 17), (19, 16), (20, 16), (21, 17)], "E")
    elif mood == "surprised":
        fill(g, [(12, 15), (13, 15), (12, 16), (13, 16), (12, 17), (13, 17), (19, 15), (20, 15), (19, 16), (20, 16),
                 (19, 17), (20, 17)], "E")
        fill(g, [(12, 15), (19, 15)], "e")
    else:
        fill(g, [(12, 16), (13, 16), (12, 17), (13, 17), (19, 16), (20, 16), (19, 17), (20, 17)], "E")
        fill(g, [(12, 16), (19, 16)], "e")
    browy = 13 if mood in ("thinking", "surprised") else 14
    if mood == "worried":     # brows up in the middle
        fill(g, [(11, 14), (12, 13), (13, 13), (19, 13), (20, 13), (21, 14)], brow)
    else:
        fill(g, [(11, browy), (12, browy), (13, browy), (19, browy), (20, browy), (21, browy)], brow)
    if mood == "thinking":
        fill(g, [(21, browy - 1)], brow)
    fill(g, [(16, 18), (16, 19)], "s")                                   # nose
    fill(g, [(11, 19), (21, 19)], "N")                                   # cheeks
    if stache:
        fill(g, [(x, 20) for x in range(12, 21)] + [(11, 21), (21, 21), (13, 19), (14, 19), (18, 19), (19, 19)],
             stache)
    mouths = {"happy": [(14, 20), (15, 21), (16, 21), (17, 21), (18, 20)],
              "neutral": [(14, 21), (15, 21), (16, 21), (17, 21)],
              "wink": [(14, 20), (15, 21), (16, 21), (17, 21), (18, 20)],
              "thinking": [(16, 21), (17, 21), (18, 20)],
              "laugh": [(14, 20), (15, 20), (16, 20), (17, 20), (18, 20), (15, 21), (16, 21), (17, 21)],
              "surprised": [(15, 20), (16, 20), (15, 21), (16, 21)],
              "worried": [(14, 21), (15, 20), (16, 20), (17, 20), (18, 21)]}
    fill(g, mouths[mood], "M")
    if mood == "laugh":
        fill(g, [(15, 20), (16, 20), (17, 20)], "e")


def bowtie(g, col, dark):
    fill(g, [(13, 26), (13, 27), (13, 28), (14, 27), (18, 27), (19, 26), (19, 27), (19, 28), (14, 26), (14, 28),
             (18, 26), (18, 28)], col)
    fill(g, [(15, 27), (16, 27), (17, 27)], dark)


def outline(g):
    out = g.copy()
    for y in range(H):
        for x in range(W):
            if g[y, x] == "" and any(0 <= x + dx < W and 0 <= y + dy < H and g[y + dy, x + dx] != ""
                                      for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y, x] = "K"
    return out


def walter(concept, mood="happy"):
    g = blank()
    if concept == "A":      # Classic: black vest, red bow tie, towel over the arm
        body(g, "V", "v")
        head(g, "H", "h", "slick")
        face(g, mood)
        bowtie(g, "B", "b")
        fill(g, [(12, 31), (12, 33), (19, 31), (19, 33)], "G")           # vest buttons
        fill(g, rect(24, 28, 27, 35), "W")                               # towel
        fill(g, [(x, 31) for x in range(24, 28)] + [(x, 33) for x in range(24, 28)], "T")
        if mood == "thinking":
            fill(g, rect(17, 22, 19, 24) + [(18, 25), (18, 26)], "S")   # hand at the chin
            fill(g, [(17, 24), (19, 24)], "s")
    elif concept == "B":    # Bistro: young, apron, notepad and pencil
        body(g, None, None, apron=("A", "a"))
        head(g, "P", "h", "messy")
        face(g, mood, brow="P")
        bowtie(g, "E", "V")
        fill(g, rect(3, 29, 8, 34), "Y")
        fill(g, [(x, 31) for x in range(4, 8)] + [(x, 33) for x in range(4, 8)], "y")
        fill(g, rect(8, 31, 10, 33), "S")
        fill(g, [(27, 27), (26, 28), (25, 29), (24, 30)], "G")           # pencil
        fill(g, [(23, 31)], "E")
    else:                   # Maitre d: grey hair, mustache, teal vest, watch chain
        body(g, "C", "c")
        head(g, "R", "r", "grey")
        face(g, mood, brow="r", stache="R")
        bowtie(g, "E", "V")
        fill(g, [(11, 31), (12, 32), (13, 33), (14, 33)], "G")           # watch chain
        fill(g, [(19, 31), (19, 33)], "G")
    return outline(g)


def img(g, scale=8):
    a = np.zeros((H, W, 4), np.uint8)
    for y in range(H):
        for x in range(W):
            if g[y, x]:
                a[y, x] = (*PAL[g[y, x]], 255)
    return Image.fromarray(a, "RGBA").resize((W * scale, H * scale), Image.NEAREST)



MOODS = ("neutral", "happy", "laugh", "wink", "thinking", "surprised", "worried")
SCALE = 4


def main() -> None:
    assets = Path(__file__).resolve().parent / "assets"
    for mood in MOODS:
        img(walter("A", mood), SCALE).save(assets / f"walter_{mood}.png", optimize=True)
    print(f"{len(MOODS)} moods -> {assets}/walter_<mood>.png ({W * SCALE}x{H * SCALE})")


if __name__ == "__main__":
    main()
