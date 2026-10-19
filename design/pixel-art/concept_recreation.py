"""Recreate the team's concept kitchens (2026-10-18 concept sheet) in code, as close to 1:1 as possible.

Each kitchen is drawn on its own (no interactive pieces yet), at the concept's proportions: 280 x 268 art pixels,
the kitchen part of the concept sheet at half size. Positions were measured on the concept, colors read from it.
Every shape gets pixel-art shading (light from the top left, a dark outline, highlights), so objects have volume
like the concept instead of flat color.

    python design/pixel-art/concept_recreation.py   ->   design/pixel-art/drafts/concept-recreation/
"""
from __future__ import annotations

import math
import random
from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageDraw

W, H = 280, 268
OUT = Path(__file__).resolve().parent / "drafts" / "concept-recreation"
RGB = tuple[int, int, int]


def rgb(color: str | RGB) -> RGB:
    if isinstance(color, tuple):
        return color
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def tone(color: str | RGB, f: float) -> RGB:
    """Lighter (f > 1, toward white) or darker (f < 1) version of a color."""
    r, g, b = rgb(color)
    if f >= 1:
        t = f - 1
        return int(r + (255 - r) * t), int(g + (255 - g) * t), int(b + (255 - b) * t)
    return int(r * f), int(g * f), int(b * f)


class Art:
    """A pixel canvas with the shading tools every kitchen uses."""

    def __init__(self, background: str, seed: int = 1):
        self.img = Image.new("RGB", (W, H), rgb(background))
        self.px = self.img.load()
        self.rand = random.Random(seed)

    # ---- single pixels and boxes
    def put(self, x: int, y: int, color: str | RGB) -> None:
        if 0 <= x < W and 0 <= y < H:
            self.px[x, y] = rgb(color)

    def box(self, x: int, y: int, w: int, h: int, color: str | RGB) -> None:
        for yy in range(max(0, y), min(H, y + h)):
            for xx in range(max(0, x), min(W, x + w)):
                self.px[xx, yy] = rgb(color)

    def line(self, points: list[tuple[int, int]], color: str | RGB, width: int = 1) -> None:
        ImageDraw.Draw(self.img).line(points, fill=rgb(color), width=width)

    # ---- any shape, filled with pixel-art shading
    def shape(self, draw: Callable[[ImageDraw.ImageDraw], None], base: str | RGB, mode: str = "cyl",
              outline: float = 0.42, highlight: bool = True) -> tuple[int, int, int, int] | None:
        """Fill a shape (drawn in white on a mask by `draw`) with shading. mode: 'cyl' (lit from the left, like a
        bottle), 'sphere' (lit from the top left, like a pot), 'flat' (a lit top edge), 'plain'."""
        mask = Image.new("L", (W, H), 0)
        draw(ImageDraw.Draw(mask))
        box = mask.getbbox()
        if not box:
            return None
        m = mask.load()
        x0, y0, x1, y1 = box
        w, h = max(1, x1 - x0 - 1), max(1, y1 - y0 - 1)
        cx, cy = (x0 + x1 - 1) / 2, (y0 + y1 - 1) / 2
        for y in range(y0, y1):
            for x in range(x0, x1):
                if not m[x, y]:
                    continue
                edge = any(not (0 <= x + dx < W and 0 <= y + dy < H and m[x + dx, y + dy])
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if edge and outline:
                    self.px[x, y] = tone(base, outline)
                    continue
                if mode == "cyl":
                    t = (x - x0) / w
                    f = 1.18 if (highlight and 0.16 < t < 0.26) else 1.06 if t < 0.4 else 0.8 if t > 0.8 else 0.9 if t > 0.62 else 1.0
                elif mode == "sphere":
                    nx, ny = (x - cx) / (w / 2), (y - cy) / (h / 2)
                    lit = -(0.55 * nx + 0.83 * ny)
                    f = 1.22 if (highlight and lit > 0.7 and abs(nx + 0.35) < 0.25) else 1.08 if lit > 0.25 else 1.0 if lit > -0.3 else 0.82
                elif mode == "flat":
                    f = 1.12 if y <= y0 + 1 else 0.86 if y >= y1 - 2 else 1.0
                else:
                    f = 1.0
                self.px[x, y] = tone(base, f)
        return box

    def rect(self, x: int, y: int, w: int, h: int, base: str | RGB, mode: str = "flat", outline: float = 0.42) -> None:
        self.shape(lambda d: d.rectangle([x, y, x + w - 1, y + h - 1], fill=255), base, mode, outline)

    def ellipse(self, x: int, y: int, w: int, h: int, base: str | RGB, mode: str = "sphere", outline: float = 0.42) -> None:
        self.shape(lambda d: d.ellipse([x, y, x + w - 1, y + h - 1], fill=255), base, mode, outline)

    def poly(self, points: list[tuple[int, int]], base: str | RGB, mode: str = "cyl", outline: float = 0.42) -> None:
        self.shape(lambda d: d.polygon(points, fill=255), base, mode, outline)

    # ---- materials
    def wood(self, x: int, y: int, w: int, h: int, base: str, vertical: bool = False, outline: bool = True) -> None:
        """A plank or a post: grain streaks, a lit edge and a shadowed edge."""
        self.box(x, y, w, h, base)
        for _ in range(max(1, w * h // 22)):
            gx, gy = x + self.rand.randrange(w), y + self.rand.randrange(h)
            length = self.rand.randint(3, 9)
            for k in range(length):
                xx, yy = (gx, gy + k) if vertical else (gx + k, gy)
                if x <= xx < x + w and y <= yy < y + h:
                    self.put(xx, yy, tone(base, 0.88))
        if vertical:
            self.box(x, y, 1, h, tone(base, 1.12))
            self.box(x + w - 2, y, 2, h, tone(base, 0.78))
        else:
            self.box(x, y, w, 1, tone(base, 1.14))
            self.box(x, y + h - 2, w, 2, tone(base, 0.76))
        if outline:
            for xx in range(x, x + w):
                self.put(xx, y - 1 if not vertical else y, tone(base, 0.55)) if not vertical else None
            if not vertical:
                self.box(x, y + h, w, 1, tone(base, 0.5))

    def plaster(self, x: int, y: int, w: int, h: int, base: str, cracks: int = 0) -> None:
        """A wall: soft speckles and, if asked, a few cracks with a lit lower edge."""
        self.box(x, y, w, h, base)
        for _ in range(w * h // 9):
            self.put(x + self.rand.randrange(w), y + self.rand.randrange(h),
                     tone(base, self.rand.choice((0.96, 0.97, 1.03, 1.04))))
        for _ in range(cracks):
            cx, cy = x + self.rand.randrange(w), y + self.rand.randrange(h)
            for _ in range(self.rand.randint(6, 14)):
                self.put(cx, cy, tone(base, 0.8))
                self.put(cx, cy + 1, tone(base, 1.06))
                cx += self.rand.choice((1, 1, 0, -1))
                cy += self.rand.choice((0, 1, 1, -1))

    def shadow(self, x: int, y: int, w: int, h: int = 2, f: float = 0.84) -> None:
        """Darken what is already there (the shadow under a shelf or an object)."""
        for yy in range(max(0, y), min(H, y + h)):
            for xx in range(max(0, x), min(W, x + w)):
                self.px[xx, yy] = tone(self.px[xx, yy], f)

    def jar(self, x: int, top: int, w: int, bottom: int, contents: str, lid: str = "#B77F54", fill_from: float = 0.3,
            speckle: str | None = None, leaf: bool = False) -> None:
        """A glass jar with a cork or wooden lid, its contents showing through, and a highlight on the glass."""
        glass, edge = "#E4ECEA", "#5D6866"
        self.shape(lambda d: d.rounded_rectangle([x, top + 3, x + w - 1, bottom - 1], 3, fill=255), glass, "plain", 0)
        level = top + 3 + int((bottom - top - 3) * fill_from)
        self.shape(lambda d: d.rounded_rectangle([x + 1, level, x + w - 2, bottom - 2], 2, fill=255), contents, "cyl", 0)
        if speckle:
            for _ in range(w * (bottom - level) // 4):
                self.put(x + 2 + self.rand.randrange(max(1, w - 4)), level + 1 + self.rand.randrange(max(1, bottom - level - 3)),
                         speckle)
        if leaf:
            self.ellipse(x + w // 2 - 5, level + 3, 10, 12, "#4F7F33", "sphere", 0.5)
            self.line([(x + w // 2, level + 4), (x + w // 2, level + 13)], "#2F5A1E")
        for k in range(top + 4, bottom - 3):                         # glass highlight
            self.put(x + 2, k, "#FFFFFF")
        self.shape(lambda d: d.rounded_rectangle([x, top + 3, x + w - 1, bottom - 1], 3, outline=255), edge, "plain", 0)
        self.rect(x + 2, top, w - 4, 4, lid, "cyl", 0.45)
        self.box(x + 1, top + 4, w - 2, 1, tone(edge, 1.3))

    def stones(self, x: int, y: int, w: int, h: int, base: str, mortar: str) -> None:
        """A rough stone wall: rows of rounded, shaded stones of different sizes, with dark mortar between."""
        self.box(x, y, w, h, mortar)
        row_y, row = y, 0
        while row_y < y + h:
            rh = self.rand.randint(8, 11)
            sx = x - (self.rand.randint(4, 10) if row % 2 else 0)
            while sx < x + w:
                sw = self.rand.randint(13, 22)
                shade = self.rand.choice((0.92, 1.0, 1.06))
                self.shape(lambda d, sx=sx, sw=sw, rh=rh, ry=row_y: d.rounded_rectangle(
                    [sx + 1, ry + 1, sx + sw - 1, ry + rh - 1], 3, fill=255), tone(base, shade), "sphere", 0.62)
                sx += sw
            row_y += rh
            row += 1

    def text(self, x: int, y: int, word: str, color: str | RGB) -> None:
        """A tiny 3 x 5 pixel font for labels."""
        font = {"R": ["11.", "1.1", "11.", "1.1", "1.1"], "I": ["111", ".1.", ".1.", ".1.", "111"],
                "C": [".11", "1..", "1..", "1..", ".11"], "E": ["111", "1..", "11.", "1..", "111"]}
        for k, ch in enumerate(word):
            for dy, row in enumerate(font[ch]):
                for dx, bit in enumerate(row):
                    if bit == "1":
                        self.put(x + k * 4 + dx, y + dy, color)

    def save(self, name: str) -> Image.Image:
        OUT.mkdir(parents=True, exist_ok=True)
        self.img.save(OUT / f"{name}.png")
        self.img.resize((W * 4, H * 4), Image.NEAREST).save(OUT / f"{name}_x4.png")
        return self.img


# ======================================================================================= Japanese
def japanese() -> Image.Image:
    a = Art("#C5A380", seed=7)
    beam, wall, shelf_c = "#5A312A", "#C3A17E", "#936348"
    paper, frame = "#FFF3D9", "#A0724F"

    # Walls and the timber frame
    a.plaster(0, 0, W, H, wall)
    a.wood(0, 0, W, 4, beam)
    a.wood(0, 35, W, 10, beam)
    a.wood(127, 0, 9, 200, beam, vertical=True)

    # Shoji doors on the right: two panels, a grid of paper squares
    for px0, px1 in ((137, 216), (219, 280)):
        a.box(px0, 45, px1 - px0, 103, frame)
        for cy in range(47, 146, 14):
            for cx in range(px0 + 3, px1 - 2, 17):
                a.box(cx, cy, 14, 12, paper)
                a.box(cx, cy + 11, 14, 1, tone(paper, 0.93))     # a soft shade at each square's foot
        a.box(px0, 45, 2, 103, tone(frame, 0.7))
    a.box(216, 45, 3, 103, tone(beam, 1.0))                       # where the two doors meet
    a.wood(136, 147, W - 136, 6, beam)                            # the rail under the doors

    # Shelves with their brackets and shadows
    for sy in (81, 122):
        a.wood(0, sy, 125, 6, shelf_c)
        a.shadow(0, sy + 7, 125, 3)
        a.rect(106, sy + 6, 6, 9, tone(shelf_c, 0.75))

    # Upper shelf: two soy sauce bottles, a green sake bottle, two white tokkuri, stacked bowls
    def bottle(x: int, w: int, top: int, body: str, cap: str, label: str | None, base: int = 81) -> None:
        neck = max(3, w // 3)
        a.poly([(x, base), (x, top + 12), (x + (w - neck) // 2, top + 6), (x + (w - neck) // 2, top + 3),
                (x + (w + neck) // 2, top + 3), (x + (w + neck) // 2, top + 6), (x + w, top + 12), (x + w, base)], body)
        a.rect(x + (w - neck) // 2 - 1, top, neck + 2, 4, cap, "cyl")
        if label:
            a.rect(x + 2, top + 16, w - 3, (base - top) // 3, label, "flat", 0.6)
    bottle(1, 13, 54, "#3B2423", "#CF3B35", None)
    a.rect(4, 70, 8, 6, "#2A1716", "plain", 0)                    # soy seen through the glass
    bottle(20, 13, 56, "#3B2423", "#CF3B35", "#E2B23A")
    a.rect(24, 74, 5, 3, "#3B2423", "plain", 0)
    bottle(38, 14, 50, "#8E9D5B", "#5C3C2A", "#F1E7CF")
    for k, (gx, gy) in enumerate([(42, 69), (45, 69), (43, 72)]):
        a.put(gx, gy, "#3B2A25")
    for tx, mark in ((60, "drop"), (78, "wave")):                 # tokkuri: round white flasks with blue marks
        a.shape(lambda d, tx=tx: (d.ellipse([tx, 64, tx + 14, 81], fill=255), d.rectangle([tx + 5, 56, tx + 9, 66], fill=255),
                                  d.rectangle([tx + 4, 55, tx + 10, 57], fill=255)), "#F3F1EC", "cyl", 0.5)
        if mark == "drop":
            a.box(tx + 5, 70, 4, 4, "#3E6CA8")
            a.box(tx + 6, 68, 2, 2, "#3E6CA8")
        else:
            a.box(tx + 4, 70, 7, 1, "#3E6CA8")
            a.box(tx + 4, 72, 2, 3, "#3E6CA8")
            a.box(tx + 9, 72, 2, 3, "#3E6CA8")
        a.box(tx + 2, 78, 11, 1, "#6E8FB5")
    for bx, by in ((98, 74), (98, 68)):                          # two stacks of small white bowls
        for k in range(2):
            y = by + k * 3
            a.poly([(bx, y), (bx + 18, y), (bx + 15, y + 6), (bx + 3, y + 6)], "#ECEDEB", "cyl", 0.5)
            a.box(bx + 1, y, 17, 1, "#FFFFFF")

    # Lower shelf: a rice bag, a box of rice, a donabe clay pot, an orange casserole
    a.poly([(3, 122), (3, 99), (6, 94), (24, 94), (27, 99), (27, 122)], "#E1C29B", "cyl", 0.5)
    a.rect(9, 102, 12, 14, "#F7EEDD", "flat", 0.6)
    a.ellipse(13, 104, 4, 4, "#CF3B35", "plain", 0)
    a.box(12, 110, 6, 1, "#3B2A25")
    a.box(14, 111, 2, 3, "#3B2A25")
    a.rect(23, 106, 16, 16, "#EFE3CC", "flat", 0.5)
    for _ in range(26):
        a.put(25 + a.rand.randrange(12), 108 + a.rand.randrange(12), "#FFFFFF")
    a.ellipse(46, 98, 32, 24, "#7A4533")                          # donabe body
    a.ellipse(48, 94, 28, 9, "#6B3A2B")                           # its lid
    a.rect(59, 91, 6, 4, "#5C3224", "cyl")
    for hx in (43, 76):
        a.ellipse(hx, 101, 5, 5, "#6B3A2B")
    a.ellipse(84, 104, 38, 18, "#B4572F")                         # orange casserole
    a.ellipse(86, 97, 34, 11, "#C5643A")
    a.rect(100, 94, 6, 4, "#9C4826", "cyl")

    # The stove, a pot, the wok over a blue flame, steam
    a.plaster(0, 153, 127, 43, "#C7A485")
    a.rect(0, 178, 50, 18, "#B8B4B4", "flat")
    a.box(0, 178, 50, 2, "#D6D3D2")
    a.ellipse(38, 184, 8, 8, "#5A5858")
    a.rect(0, 163, 15, 15, "#C9C6C5", "cyl")
    a.box(0, 162, 17, 2, "#8C8888")
    a.line([(46, 168), (73, 176)], "#5A2E1C", 5)                  # the wok's long wooden handle
    a.line([(47, 167), (72, 175)], "#B5562E", 3)
    a.line([(48, 166), (70, 173)], "#D9773F", 1)
    a.shape(lambda d: d.chord([70, 150, 128, 196], 0, 180, fill=255), "#4F4D50", "sphere", 0.38)
    a.box(71, 172, 57, 2, "#77747A")                              # the wok's rim
    a.box(84, 190, 2, 6, "#2E2E30")                               # the burner's stand
    a.box(112, 190, 2, 6, "#2E2E30")
    for fx in range(86, 112, 3):                                  # the blue flame
        a.put(fx, 193, "#4F86C6")
        a.put(fx + 1, 194, "#7FB2E5")
    a.box(84, 194, 30, 2, "#2E2E30")
    for k, sx in enumerate((84, 96, 108)):                        # three thick wisps of steam
        for t in range(30):
            wx = sx + round(3.5 * math.sin(t / 4.5 + k * 1.3))
            for dx in range(2 if t > 4 else 1):
                a.put(wx + dx, 166 - t, "#F7F0E4")
            a.put(wx + 2, 166 - t, "#E3D3BC")

    # Under the shoji: rice sack, a bowl of rice, a paper bag of rice, the bonsai
    a.plaster(136, 153, W - 136, 43, "#C8A485")
    a.poly([(148, 196), (147, 172), (151, 165), (170, 165), (175, 172), (174, 196)], "#C9A06A", "cyl", 0.45)
    a.ellipse(150, 162, 23, 8, "#F7F3EA", "sphere", 0.55)
    a.rect(152, 178, 19, 10, "#E8D3A8", "flat", 0.55)
    a.text(154, 180, "RICE", "#5A3A22")
    a.rect(186, 167, 25, 29, "#D9B98C", "cyl", 0.5)
    a.rect(190, 173, 16, 15, "#F4EBDA", "flat", 0.6)
    for mx, my in [(198, 176), (196, 178), (200, 178), (198, 180), (196, 183), (200, 183), (198, 185)]:
        a.put(mx, my, "#5A3A22")                                   # the character for rice, in brief
    a.ellipse(175, 181, 17, 14, "#7E9A62", "sphere", 0.45)        # a green bowl heaped with rice
    a.ellipse(177, 176, 13, 8, "#FBF8F1", "sphere", 0.6)
    a.rect(235, 182, 37, 13, "#4A3F78", "flat")                   # the bonsai: navy pot, trunk, cloud foliage
    a.box(240, 195, 4, 2, "#2F2850")
    a.box(263, 195, 4, 2, "#2F2850")
    a.line([(252, 183), (247, 172), (255, 162), (248, 150), (254, 140)], "#5A3524", 7)
    a.line([(252, 183), (247, 172), (255, 162), (248, 150), (254, 140)], "#7D523B", 5)
    a.line([(251, 180), (246, 172), (253, 162)], "#9A6A4C", 1)
    a.line([(255, 162), (270, 158)], "#7D523B", 3)
    a.line([(249, 152), (236, 150)], "#7D523B", 3)
    for fx, fy, fw, fh in [(222, 138, 30, 15), (240, 126, 30, 15), (258, 144, 24, 13), (226, 154, 22, 11),
                           (262, 156, 20, 10)]:
        a.ellipse(fx, fy, fw, fh, "#6B9938", "sphere", 0.45)
        for _ in range(fw):
            a.put(fx + 2 + a.rand.randrange(max(1, fw - 4)), fy + fh - 2 - a.rand.randrange(3), "#4C7A2A")
            a.put(fx + 3 + a.rand.randrange(max(1, fw - 6)), fy + 2 + a.rand.randrange(2), "#8DBE52")

    # The counter and the shoji-style doors under it
    a.wood(0, 196, W, 10, "#8A5339")
    a.box(0, 196, W, 2, "#A86E4C")
    a.box(0, 206, W, H - 206, "#5A3A2C")
    for dx in range(4, W, 46):
        a.box(dx, 210, 42, 54, "#8C5A3E")
        for cy in range(212, 262, 12):
            for cx in range(dx + 2, dx + 41, 10):
                a.box(cx, cy, 8, 10, "#EDE0CC")
                a.box(cx, cy + 9, 8, 1, "#D6C6AE")
    return a.save("japanese")


# ======================================================================================= Mediterranean
def mediterranean() -> Image.Image:
    a = Art("#CDBBA2", seed=11)
    plaster, beam = "#CDBBA2", "#5A3A2C"
    a.plaster(0, 0, W, H, plaster, cracks=16)
    for _ in range(16):                                           # big stones showing through the plaster
        sx, sy = a.rand.randrange(-10, W), a.rand.randrange(30, 190)
        sw, sh = a.rand.randint(18, 34), a.rand.randint(10, 16)
        a.shape(lambda d, sx=sx, sy=sy, sw=sw, sh=sh: d.rounded_rectangle([sx, sy, sx + sw, sy + sh], 4, fill=255),
                "#C3AF95", "plain", 0)
        a.shape(lambda d, sx=sx, sy=sy, sw=sw, sh=sh: d.rounded_rectangle([sx, sy, sx + sw, sy + sh], 4, outline=255),
                "#A8937A", "plain", 0)
        a.box(sx + 2, sy + sh + 1, sw - 3, 1, "#DDCDB6")

    # Timber: two short posts at the top, the long beam, the post beside the shelves
    a.wood(49, 0, 15, 16, beam, vertical=True)
    a.wood(222, 0, 15, 16, beam, vertical=True)
    a.wood(0, 15, W, 13, beam)
    a.wood(135, 28, 15, 168, beam, vertical=True)

    # Shelves
    for sy in (80, 120):
        a.wood(0, sy, 118, 6, "#7B4B35")
        a.shadow(0, sy + 7, 118, 3)
        for bx in (8, 106):
            a.rect(bx, sy + 6, 5, 8, "#5E3828")

    # Upper shelf: three olive oil bottles, three jars with cork lids
    def oil(x: int, w: int, top: int, body: str) -> None:
        neck = 4
        a.poly([(x, 80), (x, top + 14), (x + (w - neck) // 2, top + 7), (x + (w - neck) // 2, top + 2),
                (x + (w + neck) // 2, top + 2), (x + (w + neck) // 2, top + 7), (x + w, top + 14), (x + w, 80)], body)
        a.rect(x + (w - neck) // 2 - 1, top - 2, neck + 2, 5, "#5C3C2A", "cyl")
        a.rect(x + 2, top + 18, w - 3, (80 - top) // 3, "#E9DFA5", "flat", 0.55)
        a.ellipse(x + w // 2 - 2, top + 20, 4, 5, "#6E7A2A", "plain", 0)
    oil(5, 12, 45, "#6F7A2A")
    oil(20, 10, 47, "#7E8A33")
    oil(32, 10, 56, "#A3A243")
    for jx, contents, speck in ((49, "#D9C48F", "#B79E63"), (69, "#6E9B3E", "#4F7F2E"), (89, "#9C6B4E", "#6E4532")):
        a.jar(jx, 55, 17, 80, contents, speckle=speck, fill_from=0.25)

    # Lower shelf: four big jars (lentils, basil, peas, beans)
    for jx, contents, speck, leaf in ((11, "#B79566", "#8E6E45", False), (36, "#E6DCC0", None, True),
                                      (61, "#8FA05A", "#5E7A33", False), (85, "#D9BC8C", "#B8935F", False)):
        a.jar(jx, 95, 19, 120, contents, speckle=speck, fill_from=0.2, leaf=leaf)

    # Garlic braid on its hook
    a.rect(140, 58, 3, 6, "#A88A4A", "cyl")
    a.line([(141, 64), (141, 120)], "#B9A06A", 2)
    for k, gy in enumerate(range(70, 120, 8)):
        for gx in (133, 142):
            a.ellipse(gx + (k % 2), gy, 9, 9, "#F1EADC", "sphere", 0.5)

    # The window: lintel, frame, sky with a cloud, hills, a field, two cypresses; herbs on the sill
    a.wood(156, 45, 91, 10, beam)
    a.box(169, 55, 66, 87, "#523128")
    for (x0, x1) in ((174, 201), (205, 230)):
        for (y0, y1) in ((60, 96), (101, 137)):
            for yy in range(y0, y1):                               # sky above, land below
                t = (yy - 60) / 77
                a.box(x0, yy, x1 - x0, 1, tone("#9FD6F2", 1 + 0.25 * t) if yy < 112 else "#8DB357")
            if y0 == 101:
                a.shape(lambda d, x0=x0, x1=x1: d.polygon([(x0, 118), (x1, 112), (x1, 137), (x0, 137)], fill=255), "#7BA448", "plain", 0)
                a.shape(lambda d, x0=x0, x1=x1: d.polygon([(x0, 126), (x1, 121), (x1, 137), (x0, 137)], fill=255), "#C27F4E", "plain", 0)
                for fy in range(124, 137, 3):
                    a.box(x0, fy, x1 - x0, 1, "#A8663C")
    a.ellipse(178, 66, 14, 5, "#FFFFFF", "plain", 0)
    a.ellipse(184, 63, 9, 5, "#FFFFFF", "plain", 0)
    for cx in (178, 185):
        a.ellipse(cx, 104, 5, 16, "#4F6B33", "cyl", 0.6)
    a.box(201, 55, 4, 87, "#523128")
    a.box(169, 96, 66, 5, "#523128")
    a.wood(156, 141, 85, 7, "#6B4030")
    a.poly([(211, 141), (213, 124), (233, 124), (235, 141)], "#B5562F", "cyl")
    for _ in range(26):
        fx, fy = 209 + a.rand.randrange(26), 101 + a.rand.randrange(24)
        a.ellipse(fx, fy, 6, 5, a.rand.choice(("#5E8A3A", "#6FA046", "#4C7A2E")), "sphere", 0.55)

    # Hanging pans under the lower shelf, the stove, a steel stockpot, a copper pot and saucepan
    a.line([(15, 126), (15, 140)], "#6B6765", 2)
    a.ellipse(4, 138, 22, 22, "#7D7976", "sphere")
    a.line([(49, 126), (49, 140)], "#8A4A2E", 2)
    a.ellipse(37, 139, 25, 25, "#BC6C49", "sphere")
    a.ellipse(43, 145, 13, 13, "#D4825A", "plain", 0)
    a.line([(101, 126), (101, 136)], "#8A4A2E", 2)
    a.ellipse(89, 135, 25, 25, "#BC6C49", "sphere")
    a.ellipse(97, 158, 9, 6, "#8A4A2E", "plain", 0)
    a.rect(0, 185, 39, 11, "#4A4644", "flat")
    a.rect(0, 161, 33, 24, "#B9B5B2", "cyl")
    a.box(0, 160, 35, 2, "#8E8A88")
    a.rect(33, 166, 6, 3, "#8E8A88")
    a.box(57, 193, 76, 3, "#2E2B2A")
    a.rect(58, 172, 42, 21, "#BC6C49", "cyl")                    # the copper pot: straight sides, a domed lid
    a.box(58, 190, 42, 3, "#8A4A2E")
    a.ellipse(56, 165, 46, 11, "#C97A55", "sphere")
    a.rect(75, 160, 8, 6, "#3B2A25", "cyl")
    for hx in (51, 100):
        a.rect(hx, 174, 7, 4, "#3B2A25")
    a.rect(104, 181, 26, 13, "#C3714D", "cyl")                    # the saucepan and its long handle
    a.line([(129, 183), (146, 177)], "#3B2A25", 3)

    # On the counter beside the post: three jars, then rosemary in a terracotta pot
    a.jar(164, 172, 16, 194, "#7A5236", speckle="#4E3220", fill_from=0.25)
    a.jar(180, 175, 20, 194, "#D9B45E", speckle="#B9913E", fill_from=0.3)
    a.jar(201, 164, 15, 194, "#8FA548", speckle="#6E8A33", fill_from=0.25)
    a.poly([(241, 171), (271, 171), (267, 195), (245, 195)], "#B5562F", "cyl")
    a.box(239, 171, 34, 4, "#9C4826")
    for _ in range(26):                                           # rosemary: a bushy mound of upright sprigs
        rx = 236 + a.rand.randrange(42)
        top = 132 + a.rand.randrange(18)
        a.line([(rx, 172), (rx + a.rand.choice((-3, -1, 1, 3)), top)], "#3F5A26", 1)
    for _ in range(320):
        rx, ry = 234 + a.rand.randrange(46), 132 + a.rand.randrange(40)
        if abs(rx - 257) * 0.7 + max(0, 150 - ry) * 0.9 < 24:
            a.put(rx, ry, a.rand.choice(("#4C7A2E", "#6E9B3E", "#3F6B26", "#86B455")))

    # The counter and the stone base below it
    a.wood(0, 196, W, 9, "#744A3D")
    a.stones(0, 205, W, H - 205, "#6F6157", "#2E2622")
    return a.save("mediterranean")


# ======================================================================================= Mexican
def talavera(a: Art, x: int, y: int, size: int, k: int) -> None:
    """One painted talavera tile: a white ground, a coloured flower, corner motifs; the colours turn with k."""
    sets = [("#F4C542", "#2F6DB5", "#D8433A"), ("#2F6DB5", "#D8433A", "#4FA65B"), ("#D8433A", "#F4C542", "#2F6DB5"),
            ("#4FA65B", "#2F6DB5", "#F4C542")]
    ground, (c1, c2, c3) = "#F6EEDF", sets[k % len(sets)]
    a.box(x, y, size, size, ground)
    m = size // 2
    a.shape(lambda d: d.ellipse([x + 1, y + 1, x + size - 2, y + size - 2], fill=255), tone(c2, 1.25), "plain", 0)
    a.shape(lambda d: d.ellipse([x + 1, y + 1, x + size - 2, y + size - 2], outline=255), c2, "plain", 0)
    a.box(x, y, size, 1, "#C9BDA6")
    a.box(x, y, 1, size, "#C9BDA6")
    for dx, dy in ((0, 0), (size - 3, 0), (0, size - 3), (size - 3, size - 3)):   # corner quarter-flowers
        a.box(x + dx, y + dy, 3, 3, c2)
    a.shape(lambda d: d.polygon([(x + m, y + 2), (x + size - 3, y + m), (x + m, y + size - 3), (x + 2, y + m)], fill=255), c1, "plain", 0)
    a.shape(lambda d: d.ellipse([x + m - 3, y + m - 3, x + m + 2, y + m + 2], fill=255), c3, "plain", 0)
    a.put(x + m - 1, y + m - 1, "#FFFFFF")
    for dx, dy in ((m, 1), (1, m), (size - 2, m), (m, size - 2)):
        a.put(x + dx, y + dy, c3)


def mexican() -> Image.Image:
    a = Art("#F4A546", seed=23)
    wall = "#F2A243"
    a.plaster(0, 0, W, H, wall, cracks=6)
    for _ in range(40):                                           # sun-faded patches in the stucco
        fx, fy = a.rand.randrange(W), a.rand.randrange(140)
        a.ellipse(fx, fy, a.rand.randint(6, 16), a.rand.randint(3, 6), "#F7B762", "plain", 0)

    # Red banners hanging along the top
    for bx in (12, 71, 125, 187, 244):
        a.rect(bx, 0, 23, 14, "#B8403C", "cyl", 0.45)
        for sx in range(bx + 1, bx + 22, 4):
            a.put(sx + 1, 14, "#8E2E2B")

    # Blue shelves with their ollas, baskets and a sack of beans
    for sy in (75, 122):
        a.rect(0, sy, 156, 5, "#2F7FC1", "flat", 0.45)
        a.shadow(0, sy + 5, 156, 3, 0.86)
        for bx in (8, 140):
            a.rect(bx, sy + 5, 4, 8, "#245F91")

    def olla(x: int, top: int, w: int, base: int, band: str, band2: str, zigzag: bool = False) -> None:
        h = base - top
        a.ellipse(x, top + h // 4, w, h - h // 4, "#B75F3B")       # the round clay body
        a.ellipse(x + w // 6, top + 2, w - w // 3, h // 3, "#A9542F")   # the lid
        a.rect(x + w // 2 - 3, top - 2, 6, 5, "#8E4426", "cyl")
        for hx in (x - 3, x + w - 3):                              # loop handles
            a.shape(lambda d, hx=hx: d.ellipse([hx, top + h // 3, hx + 6, top + h // 3 + 8], outline=255, width=2),
                    "#8E4426", "plain", 0)
        by = top + h // 2 + 2
        a.box(x + 3, by, w - 6, 2, band)
        for kx in range(x + 4, x + w - 4, 4):
            a.put(kx, by + 3, band2)
            if zigzag:
                a.box(kx, by + 4 + (kx // 4) % 2, 2, 2, band2)
    olla(6, 37, 43, 75, "#F1D9A8", "#3A8C8C")
    olla(51, 49, 30, 75, "#3A8C8C", "#F1D9A8")
    olla(87, 54, 28, 75, "#F1D9A8", "#E7B83C")
    olla(118, 51, 36, 75, "#4F8F3A", "#E7B83C")
    olla(7, 89, 32, 122, "#E7B83C", "#C73A35", zigzag=True)

    def basket(x: int, w: int, top: int, base: int) -> None:
        a.poly([(x, top), (x + w, top), (x + w - 3, base), (x + 3, base)], "#C38244", "cyl")
        for wy in range(top + 2, base, 3):                        # the weave
            for wx in range(x + 2 + (wy % 2) * 2, x + w - 2, 4):
                a.put(wx, wy, "#9A5E2C")
    basket(44, 36, 104, 122)
    for cx in (47, 55, 63, 71):                                   # corn: yellow cobs with green husks
        a.ellipse(cx, 89, 8, 18, "#F2C531", "cyl", 0.45)
        for ky in range(91, 105, 2):
            a.put(cx + 3, ky, "#D9A51E")
        a.poly([(cx - 1, 106), (cx + 2, 94), (cx + 4, 106)], "#5E9B3A", "cyl", 0.5)
        a.poly([(cx + 5, 106), (cx + 8, 95), (cx + 9, 106)], "#4C8A30", "cyl", 0.5)
    basket(84, 36, 108, 122)
    for _ in range(16):                                           # big glossy chilies, stems up
        cx, cy = 85 + a.rand.randrange(28), 94 + a.rand.randrange(12)
        if a.rand.random() < 0.5:
            a.ellipse(cx, cy, 13, 5, "#D62E2A", "sphere", 0.45)
        else:
            a.ellipse(cx + 3, cy - 4, 5, 13, "#C7261F", "sphere", 0.45)
        a.box(cx, cy, 2, 2, "#3E8A2E")
    a.poly([(124, 122), (125, 100), (129, 94), (148, 94), (152, 100), (153, 122)], "#BE9170", "cyl")   # the sack
    a.ellipse(127, 90, 24, 9, "#5C3324", "sphere", 0.5)
    for _ in range(14):
        a.put(129 + a.rand.randrange(20), 91 + a.rand.randrange(5), "#7A4632")
    for fx, fy in ((134, 106), (143, 106), (138, 113)):
        a.ellipse(fx, fy, 4, 3, "#8E6648", "plain", 0)

    # The window: a blue border with coloured dots, open red shutters with painted panels, the desert outside
    a.rect(175, 41, 87, 107, "#3698C7", "flat", 0.45)
    for dy in range(44, 146, 6):
        a.put(177, dy, "#F4C542"); a.put(259, dy, "#D8433A")
    for dx in range(179, 258, 6):
        a.put(dx, 43, "#4FA65B"); a.put(dx, 146, "#F4C542")
    for yy in range(48, 146):                                     # sky to sand
        t = (yy - 48) / 97
        a.box(182, yy, 73, 1, tone("#8ED3F0", 1 + 0.3 * t) if yy < 110 else "#E2C27E")
    a.ellipse(205, 60, 20, 6, "#FFFFFF", "plain", 0)
    a.ellipse(215, 56, 12, 6, "#FFFFFF", "plain", 0)
    a.poly([(182, 112), (198, 100), (214, 108), (232, 98), (255, 110), (255, 116), (182, 116)], "#C99A5B", "plain", 0)
    a.poly([(208, 146), (214, 116), (222, 116), (230, 146)], "#B89058", "plain", 0)      # the path
    for bx, by in ((190, 120), (238, 122), (246, 112)):
        a.ellipse(bx, by, 10, 7, "#6E9B4A", "sphere", 0.55)
    for sx, w in ((182, 18), (237, 18)):                          # the open shutters
        a.rect(sx, 50, w, 95, "#C53731", "cyl", 0.45)
        a.rect(sx + 3, 54, w - 6, 26, "#E7B83C", "flat", 0.5)
        a.rect(sx + 3, 84, w - 6, 26, "#4FA65B", "flat", 0.5)
        a.rect(sx + 3, 114, w - 6, 26, "#2F6DB5", "flat", 0.5)
        for py in (66, 96, 126):
            a.ellipse(sx + w // 2 - 3, py - 3, 6, 6, "#D8433A", "plain", 0)
    a.rect(170, 143, 62, 5, "#2F7FC1", "flat", 0.45)              # the blue sill

    # Talavera backsplash, the stove, sacks and a basket of beans, the cactus
    k = 0
    for ty in range(138, 184, 15):
        for tx in range(0, W, 15):
            if not (170 <= tx < 262 and ty < 148):
                talavera(a, tx, ty, 15, k)
            k += 1
    a.rect(0, 155, 25, 25, "#C9C6C5", "cyl")
    a.box(0, 153, 27, 3, "#8C8888")
    a.rect(0, 180, 82, 6, "#3E3A3D", "flat")
    a.rect(0, 186, 82, 82, "#8F8C8E", "flat")
    for kx in (8, 24, 40, 56, 70):
        a.ellipse(kx, 193, 9, 9, "#3E3A3D", "sphere", 0.5)
    a.rect(4, 208, 74, 56, "#6E6B6E", "flat")
    a.rect(10, 212, 62, 4, "#B9B5B2", "cyl")
    for sx, sw, beans in ((99, 26, "#6F9A3A"), (126, 34, "#8E2A2A")):
        a.poly([(sx, 184), (sx + 1, 162), (sx + 5, 155), (sx + sw - 5, 155), (sx + sw - 1, 162), (sx + sw, 184)], "#BE9170", "cyl")
        a.ellipse(sx + 2, 151, sw - 4, 9, beans, "sphere", 0.5)
        for _ in range(sw):
            a.put(sx + 4 + a.rand.randrange(sw - 8), 152 + a.rand.randrange(5), tone(beans, 1.3))
    a.ellipse(165, 167, 42, 10, "#9E2A26", "sphere", 0.5)
    for _ in range(30):
        a.put(168 + a.rand.randrange(36), 168 + a.rand.randrange(6), "#D9443A")
    a.poly([(165, 172), (207, 172), (202, 184), (170, 184)], "#C38244", "cyl")
    a.poly([(233, 162), (269, 162), (265, 184), (237, 184)], "#E85A2E", "cyl")   # the cactus's painted pot
    a.box(236, 168, 30, 3, "#F4C542")
    for dx in range(238, 264, 5):
        a.box(dx, 174, 3, 3, "#2F6DB5")
    pads = [(241, 132, 16, 30), (229, 140, 13, 22), (256, 136, 14, 26), (236, 122, 12, 18), (251, 118, 12, 20),
            (262, 126, 11, 16)]                                    # a prickly pear: oval pads on pads
    for px, py, pw, ph in pads:
        a.ellipse(px, py, pw, ph, "#3E8E5A", "sphere", 0.45)
        for _ in range(pw // 2):
            a.put(px + 2 + a.rand.randrange(pw - 4), py + 2 + a.rand.randrange(ph - 4), "#DDE8C8")
    for fx, fy, col in ((238, 118, "#E86FA8"), (252, 113, "#F28A3C"), (263, 122, "#E86FA8"), (228, 136, "#F28A3C"),
                        (246, 128, "#E86FA8")):
        a.ellipse(fx, fy, 7, 6, col, "sphere", 0.5)
        a.put(fx + 3, fy + 2, "#F4C542")

    # The counter and the red painted cabinets with talavera panels
    a.wood(82, 184, W - 82, 9, "#C7794A")
    a.rect(82, 193, W - 82, 75, "#D9452F", "flat", 0.45)
    for dx in (90, 140, 190, 230):
        a.rect(dx, 199, 36, 64, "#C53A2A", "flat", 0.45)
        a.rect(dx + 5, 205, 26, 52, "#2F6DB5", "flat", 0.5)
        a.shape(lambda d, dx=dx: d.polygon([(dx + 18, 210), (dx + 28, 231), (dx + 18, 252), (dx + 8, 231)], fill=255), "#4FA65B", "plain", 0)
        a.ellipse(dx + 14, 227, 8, 8, "#F4C542", "plain", 0)
        a.rect(dx + 31, 226, 3, 9, "#F4C542", "cyl")
    return a.save("mexican")


# ======================================================================================= Middle Eastern
def arch_points(x0: int, x1: int, spring: int, apex: int, bottom: int, onion: float = 0.0) -> list[tuple[int, int]]:
    """An arch outline: straight sides from `bottom` up to `spring`, then a pointed (onion > 0: bulging) top."""
    xc = (x0 + x1) / 2
    left, right = [], []
    for k in range(25):
        t = k / 24
        bulge = onion * math.sin(math.pi * min(1.0, t * 1.4)) * (x1 - x0) / 2
        x = x0 - bulge + (xc - x0 + bulge) * t ** 1.7
        y = spring - (spring - apex) * math.sin(t * math.pi / 2)
        left.append((round(x), round(y)))
        right.append((round(2 * xc - x), round(y)))
    return [(x0, bottom), *left, *reversed(right), (x1, bottom)]


def arabesque(a: Art, x: int, y: int, w: int, h: int) -> None:
    """Carved and painted arabesque: interlaced rings in teal and orange on cream, repeated every 12 pixels."""
    a.box(x, y, w, h, "#E9D2AE")
    for ty in range(y, y + h, 12):
        for tx in range(x, x + w, 12):
            a.shape(lambda d, tx=tx, ty=ty: d.ellipse([tx + 1, ty + 1, tx + 11, ty + 11], outline=255, width=2), "#D9883E", "plain", 0)
            a.shape(lambda d, tx=tx, ty=ty: d.ellipse([tx + 4, ty + 4, tx + 8, ty + 8], fill=255), "#4E8C8C", "plain", 0)
            a.put(tx, ty, "#4E8C8C")


def zellige_star(a: Art, x: int, y: int, size: int) -> None:
    """A zellige tile: an eight-pointed star in orange on teal, with a cream centre."""
    a.box(x, y, size, size, "#3F7F86")
    m = size // 2
    star = [(x + m, y + 1), (x + m + 2, y + m - 2), (x + size - 2, y + m), (x + m + 2, y + m + 2), (x + m, y + size - 2),
            (x + m - 2, y + m + 2), (x + 1, y + m), (x + m - 2, y + m - 2)]
    a.shape(lambda d: d.polygon(star, fill=255), "#D9883E", "plain", 0)
    a.box(x + m - 1, y + m - 1, 3, 3, "#F2E2C2")
    a.box(x, y, size, 1, "#2E6066")


def middle_eastern() -> Image.Image:
    a = Art("#E6C796", seed=31)
    plaster = "#EBD3AA"
    arabesque(a, 0, 0, W, 196)                                    # pattern everywhere; the arches are cut out of it

    # Two big arches of cream plaster, with carved frames
    for x0, x1, spring, apex in ((-34, 120, 52, 14), (118, 300, 46, 6)):
        pts = arch_points(x0, x1, spring, apex, 196)
        a.shape(lambda d, pts=pts: d.polygon(pts, fill=255), plaster, "plain", 0)
        a.shape(lambda d, pts=pts: d.line(pts, fill=255, width=4), "#C9A27A", "plain", 0)
        a.shape(lambda d, pts=pts: d.line(pts, fill=255, width=1), "#8E6A44", "plain", 0)
    a.plaster(0, 60, 117, 136, plaster)
    a.plaster(131, 56, 126, 140, plaster)
    for px0, px1 in ((117, 131), (257, 280)):                     # zellige pillars
        for ty in range(80, 196, 12):
            zellige_star(a, px0, ty, px1 - px0 if px1 - px0 < 14 else 12)
            if px1 - px0 > 14:
                zellige_star(a, px0 + 12, ty, 12)

    # Spice jars on the upper shelf; a rice sack and three brass dallah on the lower one
    for sy in (75, 121):
        a.wood(2, sy, 110, 6, "#5E3A28")
        a.shadow(2, sy + 7, 110, 3)
        for bx in (8, 100):
            a.rect(bx, sy + 6, 5, 8, "#4A2C1E")
    for jx, contents, speck in ((7, "#D6452B", "#A82E1C"), (25, "#8A9A4A", "#6E7E35"), (42, "#E8A21E", "#C98410"),
                                (59, "#5E2E24", "#3E1C16"), (77, "#7E7A3A", "#5E5A28"), (94, "#C49A6C", "#A47A4C")):
        a.jar(jx, 50, 15, 75, contents, lid="#8E6A44", speckle=speck, fill_from=0.3)
    a.poly([(7, 121), (6, 104), (10, 97), (31, 97), (35, 104), (34, 121)], "#C59066", "cyl")
    a.ellipse(9, 93, 24, 9, "#F4EBDA", "sphere", 0.55)
    a.shape(lambda d: d.ellipse([16, 107, 25, 115], outline=255), "#7A5232", "plain", 0)

    def dallah(x: int, top: int, base: int, w: int) -> None:
        """A brass coffee pot: round belly, waist, tall lid with a finial, beaked spout, curved handle."""
        h = base - top
        a.ellipse(x, top + h // 2, w, h // 2, "#DFAA46")                       # belly
        a.poly([(x + w // 4, top + h // 2 + 2), (x + w // 3, top + h // 3), (x + 2 * w // 3, top + h // 3),
                (x + 3 * w // 4, top + h // 2 + 2)], "#DFAA46", "cyl")         # waist
        a.poly([(x + w // 3, top + h // 3), (x + w // 2, top + 4), (x + 2 * w // 3, top + h // 3)], "#E8BC5A", "cyl")
        a.rect(x + w // 2 - 1, top, 3, 5, "#B8862E", "cyl")
        a.line([(x + 2, top + h // 2 + 3), (x - 6, top + h // 4), (x - 9, top + h // 4 - 2)], "#B8862E", 3)
        a.line([(x + 2, top + h // 2 + 2), (x - 6, top + h // 4 - 1)], "#F2D27A", 1)
        a.shape(lambda d: d.arc([x + w - 6, top + h // 3, x + w + 6, top + 3 * h // 4], -90, 90, fill=255, width=2),
                "#B8862E", "plain", 0)
        a.box(x + w // 4, top + h // 2 + h // 4, 2, 4, "#F6D98A")
    dallah(44, 86, 121, 22)
    dallah(72, 94, 121, 15)
    dallah(90, 88, 121, 19)

    # The onion-arch window onto a city at sunset
    pts = arch_points(164, 232, 82, 24, 151, onion=0.42)
    a.shape(lambda d: d.polygon(pts, fill=255), "#764231", "cyl", 0.5)
    inner = arch_points(170, 226, 84, 32, 148, onion=0.42)
    mask_sky = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask_sky).polygon(inner, fill=255)
    ms = mask_sky.load()
    for yy in range(30, 150):
        t = (yy - 37) / 111
        col = tone("#F9C66A", 1 + 0.35 * t) if t < 0.6 else tone("#F2B36D", 1 + 0.1 * t)
        for xx in range(166, 231):
            if ms[xx, yy]:
                a.put(xx, yy, col)
    for bx, bw, bh, col in ((172, 12, 26, "#E7A365"), (184, 9, 40, "#D9925A"), (193, 20, 22, "#E7A365"),
                            (212, 12, 34, "#CC7F53"), (200, 6, 52, "#D9925A")):
        for yy in range(148 - bh, 148):
            for xx in range(bx, bx + bw):
                if ms[xx, yy]:
                    a.put(xx, yy, col)
    for dx, dy, dw in ((196, 92, 14), (174, 118, 10), (213, 110, 10)):          # domes
        a.shape(lambda d, dx=dx, dy=dy, dw=dw: d.chord([dx, dy, dx + dw, dy + dw], 180, 360, fill=255), "#CC7F53", "plain", 0)
    a.ellipse(186, 52, 18, 5, "#FFF3D9", "plain", 0)
    a.wood(160, 150, 76, 5, "#7A4B2C")

    # Tiled backsplash, then the things on the counter
    for ty in range(155, 184, 10):
        for tx in range(0, W, 10):
            zellige_star(a, tx, ty, 10)
    a.poly([(2, 184), (3, 156), (8, 148), (32, 148), (37, 156), (37, 184)], "#B98A60", "cyl")      # grain sacks
    a.ellipse(5, 143, 30, 11, "#E3C48A", "sphere", 0.5)
    for _ in range(40):
        a.put(8 + a.rand.randrange(24), 145 + a.rand.randrange(6), "#C9A46B")
    a.poly([(34, 184), (35, 163), (40, 158), (56, 158), (60, 163), (60, 184)], "#B98A60", "cyl")
    a.ellipse(37, 154, 21, 8, "#C9A06A", "sphere", 0.5)
    a.shape(lambda d: d.ellipse([42, 168, 52, 177], outline=255), "#7A5232", "plain", 0)
    dallah(76, 144, 184, 16)
    for k, y in enumerate(range(176, 158, -4)):                   # folded flatbread, stacked
        a.ellipse(84 + (k % 2), y, 40, 8, "#B89670", "sphere", 0.45)
    for k, y in enumerate(range(178, 156, -3)):                   # round flatbread, stacked high
        a.ellipse(132, y, 42, 8, "#E2B47A", "sphere", 0.45)
    a.ellipse(178, 180, 44, 5, "#F2E8D8", "plain", 0)             # a plate
    for k, y in enumerate(range(176, 160, -3)):
        a.ellipse(181, y, 38, 7, "#E8C08A", "sphere", 0.45)

    # The palm in a patterned brass pot
    a.poly([(236, 165), (266, 165), (262, 184), (240, 184)], "#BF6327", "cyl")
    for dx in range(239, 263, 5):
        a.ellipse(dx, 170, 4, 4, "#F2C14E", "plain", 0)
    a.rect(245, 130, 11, 36, "#B86C3C", "cyl")
    for ty in range(132, 164, 4):
        a.box(245, ty, 11, 1, "#8E4F28")
    for angle, length in ((200, 40), (225, 36), (250, 30), (290, 30), (315, 36), (340, 40), (180, 30), (0, 30)):
        # a drooping frond: a curved rib with leaflets on both sides
        rad = math.radians(angle)
        prev = (250, 130)
        for k in range(1, length):
            t = k / length
            x = 250 + math.cos(rad) * k
            y = 130 - math.sin(rad) * k * 0.55 + 18 * t * t           # gravity bends it down
            point = (round(x), round(y))
            a.line([prev, point], "#3F6B26", 2)
            if k % 2 == 0:
                for side in (-1, 1):
                    a.line([point, (point[0] + side * 2, point[1] + 5)], "#5E9B3A" if side < 0 else "#4C8A30", 1)
            prev = point

    # The counter, a tiled border, carved cabinets with arched niches
    a.wood(0, 184, W, 9, "#C9A27A")
    for tx in range(0, W, 6):
        a.box(tx, 193, 6, 6, ("#4E8C8C", "#D9883E", "#F2E2C2")[(tx // 6) % 3])
    a.box(0, 199, W, H - 199, "#C9A27A")
    for k in range(0, W, 8):
        a.box(k, 199, 1, H - 199, "#B8905F")
    for nx0, nx1 in ((12, 50), (226, 265), (64, 102), (174, 212)):
        pts = arch_points(nx0, nx1, 222, 206, 259, onion=0.12)
        a.shape(lambda d, pts=pts: d.polygon(pts, fill=255), "#6B4027", "cyl", 0.5)
        a.shape(lambda d, pts=pts: d.line(pts, fill=255, width=2), "#E1AC76", "plain", 0)
    return a.save("middle_eastern")


# ======================================================================================= The chefs
CW = CH = 64   # chef portraits: head and shoulders, on a transparent background


class Portrait(Art):
    """A 64 x 64 canvas for a chef (the same shading tools, a transparent background)."""

    def __init__(self, seed: int = 3):
        self.img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        self.px = self.img.load()
        self.rand = random.Random(seed)

    def put(self, x: int, y: int, color: str | RGB) -> None:
        if 0 <= x < CW and 0 <= y < CH:
            self.px[x, y] = (*rgb(color), 255)

    def box(self, x: int, y: int, w: int, h: int, color: str | RGB) -> None:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, color)

    def save(self, name: str) -> Image.Image:
        OUT.mkdir(parents=True, exist_ok=True)
        self.img.save(OUT / f"{name}.png")
        self.img.resize((CW * 4, CH * 4), Image.NEAREST).save(OUT / f"{name}_x4.png")
        return self.img

    def shape(self, draw: Callable[[ImageDraw.ImageDraw], None], base: str | RGB, mode: str = "cyl",
              outline: float = 0.42, highlight: bool = True) -> tuple[int, int, int, int] | None:
        # Same as Art.shape, on the portrait's own size and with opaque pixels
        mask = Image.new("L", (CW, CH), 0)
        draw(ImageDraw.Draw(mask))
        box = mask.getbbox()
        if not box:
            return None
        m = mask.load()
        x0, y0, x1, y1 = box
        w, h = max(1, x1 - x0 - 1), max(1, y1 - y0 - 1)
        cx, cy = (x0 + x1 - 1) / 2, (y0 + y1 - 1) / 2
        for y in range(y0, y1):
            for x in range(x0, x1):
                if not m[x, y]:
                    continue
                edge = any(not (0 <= x + dx < CW and 0 <= y + dy < CH and m[x + dx, y + dy])
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if edge and outline:
                    self.put(x, y, tone(base, outline))
                    continue
                if mode == "cyl":
                    t = (x - x0) / w
                    f = 1.15 if (highlight and 0.16 < t < 0.26) else 1.05 if t < 0.4 else 0.82 if t > 0.82 else 0.92 if t > 0.64 else 1.0
                elif mode == "sphere":
                    nx, ny = (x - cx) / (w / 2), (y - cy) / (h / 2)
                    lit = -(0.55 * nx + 0.83 * ny)
                    f = 1.1 if lit > 0.35 else 1.0 if lit > -0.35 else 0.86
                else:
                    f = 1.0
                self.put(x, y, tone(base, f))
        return box


SKIN, INK_DARK = "#C98B5E", "#3B2418"


def face(p: Portrait, beard: bool = False, mustache: bool = False) -> None:
    """The shared happy face (proportions of the concept): closed smiling eyes, rosy cheeks, an open smile."""
    p.box(28, 40, 9, 7, tone(SKIN, 0.82))                         # the neck in shade
    for ex in (15, 45):
        p.ellipse(ex, 23, 5, 8, SKIN)                              # ears
    p.ellipse(18, 11, 29, 32, SKIN)                               # the head (round and wide, as in the concept)
    for ex in (23, 36):                                           # happy closed eyes and the brows
        p.line([(ex, 27), (ex + 2, 25), (ex + 4, 25), (ex + 5, 27)], INK_DARK, 1)
        p.line([(ex, 22), (ex + 5, 21)], tone(INK_DARK, 1.25), 1)
    for cx in (20, 40):
        p.ellipse(cx, 28, 5, 3, "#E58A7A", "plain", 0)
    p.put(32, 29, tone(SKIN, 0.78))
    p.put(31, 30, tone(SKIN, 0.78))
    p.shape(lambda d: d.chord([27, 29, 38, 39], 0, 180, fill=255), "#7A2222", "plain", 0.6)
    p.box(29, 34, 8, 2, "#FFFFFF")                                 # teeth
    p.box(30, 37, 5, 1, "#C9474A")
    if mustache:
        p.shape(lambda d: d.polygon([(25, 34), (28, 31), (32, 33), (36, 31), (40, 34), (37, 35), (32, 34), (28, 35)],
                                    fill=255), "#2B1A14", "plain", 0)
    if beard:
        p.shape(lambda d: d.polygon([(24, 35), (27, 40), (32, 44), (37, 40), (41, 35), (38, 38), (32, 41), (27, 38)],
                                    fill=255), "#2B1A14", "plain", 0)
        p.shape(lambda d: d.polygon([(26, 32), (32, 31), (38, 32), (35, 33), (29, 33)], fill=255), "#2B1A14", "plain", 0)


def shoulders(p: Portrait, color: str) -> None:
    p.poly([(5, 63), (7, 53), (19, 46), (45, 46), (57, 53), (59, 63)], color, "cyl", 0.42)


def chef_classic() -> Image.Image:
    p = Portrait()
    shoulders(p, "#F4F2EE")
    for by in (52, 57):
        p.ellipse(39, by, 3, 3, "#8E8A86", "plain", 0)
    p.poly([(20, 46), (32, 54), (44, 46), (40, 45), (32, 50), (24, 45)], "#D63A30", "cyl")     # neckerchief and knot
    p.poly([(28, 51), (31, 60), (34, 52), (37, 60), (36, 51)], "#C2302A", "cyl")
    face(p, mustache=True)
    p.box(20, 15, 4, 6, "#2B1A14")                                 # hair at the temples
    p.box(41, 15, 4, 6, "#2B1A14")
    for bx, by, bw, bh in ((16, 2, 14, 13), (25, 0, 15, 13), (35, 2, 14, 13), (19, 5, 27, 12)):   # the tall toque
        p.ellipse(bx, by, bw, bh, "#FBFAF7", "sphere", 0.5)
    p.rect(20, 13, 25, 5, "#F2F0EB", "flat", 0.5)
    for gx in (25, 31, 37):
        p.line([(gx, 6), (gx, 13)], "#D9D6D0", 1)
    return p.save("chef_classic")


def chef_japanese() -> Image.Image:
    p = Portrait()
    shoulders(p, "#2C3E6B")
    p.poly([(27, 46), (32, 55), (37, 46)], "#F4F2EE", "cyl")      # white undershirt in the collar's V
    p.line([(21, 46), (32, 62)], "#1E2B4E", 2)
    p.line([(43, 46), (32, 62)], "#1E2B4E", 2)
    face(p)
    p.shape(lambda d: d.chord([19, 6, 46, 30], 180, 360, fill=255), "#4A2E22", "sphere", 0.5)   # hair
    p.rect(18, 14, 29, 5, "#F4F2EE", "flat", 0.5)                 # the twisted headband
    for tx in range(19, 46, 3):
        p.line([(tx, 18), (tx + 2, 15)], "#2C3E6B", 1)
    p.ellipse(11, 12, 9, 7, "#F4F2EE", "sphere", 0.5)            # its knot and tails
    p.line([(11, 16), (6, 20)], "#F4F2EE", 2)
    p.line([(12, 13), (7, 10)], "#F4F2EE", 2)
    return p.save("chef_japanese")


def chef_mexican() -> Image.Image:
    p = Portrait()
    shoulders(p, "#F6F1E6")
    for fx, fy, col in ((10, 54, "#D8433A"), (15, 58, "#4FA65B"), (49, 54, "#2F6DB5"), (52, 58, "#F4C542"),
                        (12, 59, "#E86FA8"), (46, 59, "#D8433A"), (20, 56, "#F4C542"), (43, 56, "#4FA65B")):
        p.ellipse(fx, fy, 4, 4, col, "plain", 0)
        p.put(fx + 1, fy + 1, "#FFFFFF")
    p.poly([(20, 46), (32, 54), (44, 46), (40, 45), (32, 50), (24, 45)], "#E8532E", "cyl")
    p.poly([(28, 51), (31, 60), (34, 52), (37, 60), (36, 51)], "#D8432A", "cyl")
    face(p)
    p.shape(lambda d: d.chord([19, 5, 46, 30], 180, 360, fill=255), "#1F1A1A", "sphere", 0.5)   # black hair
    p.rect(18, 13, 29, 5, "#1F1A1A", "flat", 0.6)                 # the embroidered headband
    for k, bx in enumerate(range(20, 45, 3)):
        p.ellipse(bx, 14, 3, 3, ("#D8433A", "#4FA65B", "#F4C542")[k % 3], "plain", 0)
    p.line([(18, 17), (12, 25)], "#1F1A1A", 3)                    # its tie
    return p.save("chef_mexican")


def chef_middle_eastern() -> Image.Image:
    p = Portrait()
    shoulders(p, "#F4F2EE")
    p.poly([(5, 63), (7, 53), (17, 47), (25, 63)], "#6B3E24", "cyl")    # the brown vest with gold trim
    p.poly([(59, 63), (57, 53), (47, 47), (39, 63)], "#6B3E24", "cyl")
    p.line([(18, 48), (25, 62)], "#E2B33C", 1)
    p.line([(46, 48), (39, 62)], "#E2B33C", 1)
    face(p, beard=True)
    cloth = [(13, 52), (13, 20), (19, 8), (32, 4), (45, 8), (51, 20), (51, 52), (45, 52), (44, 24), (39, 17), (25, 17),
             (20, 24), (19, 52)]
    mask = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(mask).polygon(cloth, fill=255)
    p.shape(lambda d: d.polygon(cloth, fill=255), "#F4F2EE", "plain", 0.5)
    mk = mask.load()
    for yy in range(CH):                                          # red checks, only on the cloth
        for xx in range(CW):
            if mk[xx, yy] and ((xx // 2) + (yy // 2)) % 2 == 0:
                p.put(xx, yy, "#C8323A")
    p.rect(17, 11, 31, 3, "#1A1A1A", "plain", 0)                  # the agal, two black rings
    p.rect(17, 15, 31, 2, "#1A1A1A", "plain", 0)
    return p.save("chef_middle_eastern")


CHEFS = {"chef_classic": chef_classic, "chef_japanese": chef_japanese, "chef_mexican": chef_mexican,
         "chef_middle_eastern": chef_middle_eastern}
KITCHENS = {"japanese": japanese, "mediterranean": mediterranean, "mexican": mexican, "middle_eastern": middle_eastern,
            **CHEFS}


def main() -> None:
    for name, draw in KITCHENS.items():
        draw()
        print("drew", name)


if __name__ == "__main__":
    main()
