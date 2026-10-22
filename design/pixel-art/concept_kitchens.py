"""The team's four full kitchens (2026-10-21 originals), recreated in code as close to 1:1 as possible.

Chinese ("The Jade Wok"), Mediterranean ("The Golden Hearth"), Mexican ("The Joyful Kitchen") and Middle Eastern
("The Saffron Market"): whole rooms, 16:9, drawn at 418 x 235 art pixels (the originals at a quarter size). Positions
were measured on the originals (design/pixel-art/references/concepts/*.jpg), colours read from them. The sign is drawn
empty: the page writes "EverFlavor Kitchen" on its own, so the title stays visible when a phone crops the picture.

    python design/pixel-art/concept_kitchens.py   ->   design/pixel-art/drafts/concept-kitchens/
"""
from __future__ import annotations

import math

import concept_recreation as cr
from concept_recreation import Art, tone
from PIL import Image, ImageDraw

FW, FH = 418, 235
OUT = cr.OUT.parent / "concept-kitchens"


def canvas(background: str, seed: int) -> Art:
    return Art(background, seed=seed, size=(FW, FH))


def finish(a: Art, warmth: float = 0.08, edge: float = 0.28) -> None:
    """Warm the whole picture a little and let the light fall off toward the edges (in bands, like pixel art)."""
    for y in range(a.h):
        for x in range(a.w):
            r, g, b = a.px[x, y]
            r, g, b = min(255, int(r * (1 + warmth))), int(g * (1 + warmth / 3)), int(b * (1 - warmth))
            d = math.hypot((x - a.w / 2) / (a.w / 2), (y - a.h * 0.45) / (a.h * 0.62))
            f = 1 - edge * round(max(0.0, d - 0.55) ** 1.4 * 8) / 8
            a.px[x, y] = (int(r * f), int(g * f), int(b * f))


def save(a: Art, name: str) -> Image.Image:
    finish(a)
    OUT.mkdir(parents=True, exist_ok=True)
    a.img.save(OUT / f"{name}.png")
    a.img.resize((FW * 4, FH * 4), Image.NEAREST).save(OUT / f"{name}_x4.png")
    return a.img


# ----------------------------------------------------------------------------------------------- shared pieces
def glow(a: Art, cx: int, cy: int, r: int, color: str, strength: float = 0.45) -> None:
    """Warm light around a lamp: blend a colour into what is there, fading with distance (in steps, like pixel art)."""
    col = cr.rgb(color)
    for y in range(max(0, cy - r), min(a.h, cy + r)):
        for x in range(max(0, cx - r), min(a.w, cx + r)):
            d = math.hypot(x - cx, y - cy) / r
            if d < 1:
                t = strength * (1 - d) ** 2.2
                t = round(t * 14) / 14                                # finely banded, like dithered light
                p = a.px[x, y]
                a.px[x, y] = tuple(int(p[k] + (col[k] - p[k]) * t) for k in range(3))


def planks(a: Art, x0: int, y0: int, x1: int, y1: int, base: str, horizontal: bool = True) -> None:
    """Wooden boards with seams, grain and a little variation from board to board."""
    a.box(x0, y0, x1 - x0, y1 - y0, base)
    if horizontal:
        for k, y in enumerate(range(y0, y1, 6)):
            shade = (1.0, 0.94, 1.04, 0.97)[k % 4]
            a.box(x0, y, x1 - x0, 5, tone(base, shade))
            a.box(x0, y + 5, x1 - x0, 1, tone(base, 0.72))
            for x in range(x0 + (k * 37) % 60, x1, 60):
                a.box(x, y, 1, 5, tone(base, 0.72))
    else:
        for k, x in enumerate(range(x0, x1, 9)):
            a.box(x, y0, 8, y1 - y0, tone(base, (1.0, 0.93, 1.05)[k % 3]))
            a.box(x + 8, y0, 1, y1 - y0, tone(base, 0.7))
    for _ in range((x1 - x0) * (y1 - y0) // 30):
        gx, gy = a.rand.randrange(x0, x1), a.rand.randrange(y0, y1)
        a.box(gx, gy, a.rand.randint(2, 6) if horizontal else 1, 1 if horizontal else a.rand.randint(2, 6), tone(base, 0.86))


def rug(a: Art, top: tuple[int, int], bottom: tuple[int, int], y0: int, y1: int, base: str, border: str, motif: str,
        fringe: bool = False) -> None:
    """A floor rug in perspective (narrower at the back), with a border band and a diamond medallion."""
    def edge(y: int) -> tuple[int, int]:
        t = (y - y0) / max(1, y1 - y0)
        return round(top[0] + (bottom[0] - top[0]) * t), round(top[1] + (bottom[1] - top[1]) * t)
    for y in range(y0, y1):
        lx, rx = edge(y)
        a.box(lx, y, rx - lx, 1, base)
        a.box(lx, y, 3, 1, border)
        a.box(rx - 3, y, 3, 1, border)
    for y in (y0, y0 + 1, y0 + 2, y1 - 3, y1 - 2, y1 - 1):
        lx, rx = edge(y)
        a.box(lx, y, rx - lx, 1, border)
    for y in (y0 + 4, y1 - 5):                                       # a thin inner line with a dotted pattern
        lx, rx = edge(y)
        for x in range(lx + 5, rx - 5, 3):
            a.put(x, y, motif)
    cx, cy = (top[0] + top[1] + bottom[0] + bottom[1]) // 4, (y0 + y1) // 2
    hw, hh = (bottom[1] - bottom[0]) // 6, (y1 - y0) // 2 - 4
    for k, scale in enumerate((1.0, 0.7, 0.4)):
        pts = [(cx, cy - int(hh * scale)), (cx + int(hw * scale), cy), (cx, cy + int(hh * scale)), (cx - int(hw * scale), cy)]
        a.shape(lambda d, pts=pts: d.polygon(pts, outline=255), motif if k != 1 else border, "plain", 0)
    for sx in (-1, 1):                                                # side diamonds
        for k in range(1, 3):
            dx = cx + sx * k * hw * 1.4
            pts = [(dx, cy - hh // 2), (dx + hw // 3, cy), (dx, cy + hh // 2), (dx - hw // 3, cy)]
            a.shape(lambda d, pts=pts: d.polygon(pts, fill=255), motif, "plain", 0)
    if fringe:
        for y in (y0 - 1, y1):
            lx, rx = edge(min(max(y, y0), y1 - 1))
            for x in range(lx, rx, 2):
                a.put(x, y, "#F1E6CF")


def leaves(a: Art, cx: int, cy: int, w: int, h: int, greens: tuple[str, ...] = ("#3F7A2E", "#5E9B3A", "#7DB84A"),
           count: int = 40, leaf: tuple[int, int] = (7, 4)) -> None:
    """A leafy bush: many small pointed leaves at random angles, darker below and lighter on top."""
    for _ in range(int(count * 1.8)):
        ang = a.rand.uniform(0, math.pi * 2)
        rr = a.rand.random() ** 0.6
        x, y = cx + math.cos(ang) * w / 2 * rr, cy + math.sin(ang) * h / 2 * rr
        shade = greens[0] if y > cy + h / 6 else greens[-1] if y < cy - h / 6 else greens[len(greens) // 2]
        lw, lh = leaf
        tilt = a.rand.uniform(-1, 1)
        pts = [(x - lw / 2, y + tilt * 2), (x, y - lh / 2), (x + lw / 2, y - tilt * 2), (x, y + lh / 2)]
        a.shape(lambda d, pts=pts: d.polygon(pts, fill=255), shade, "plain", 0.62)


def vine(a: Art, x: int, y: int, length: int, sway: float = 3, greens: tuple[str, str] = ("#3F7A2E", "#6FA846")) -> None:
    """A trailing plant hanging down from a pot or a shelf."""
    for k in range(0, length, 3):
        vx = x + round(sway * math.sin(k / 6))
        a.put(vx, y + k, "#2F5A22")
        a.ellipse(vx - 3 + (k // 3) % 2 * 3, y + k - 1, 4, 3, greens[(k // 3) % 2], "plain", 0.6)


def porcelain(a: Art, x: int, y: int, w: int, h: int, body: str = "#F2F2EE", blue: str = "#2F55A0", mouth: bool = True) -> None:
    """A blue-and-white porcelain vase or pot: round body, a band of blue pattern, a lip."""
    a.ellipse(x, y + h // 5, w, h - h // 5, body, "sphere", 0.5)
    if mouth:
        a.rect(x + w // 4, y, w // 2, h // 4 + 1, body, "cyl", 0.5)
    for yy in (y + h // 3, y + h - h // 4):
        a.box(x + 2, yy, w - 4, 1, blue)
    for xx in range(x + 3, x + w - 3, 4):
        a.box(xx, y + h // 2, 2, 3, blue)


def red_lantern(a: Art, cx: int, top: int, w: int = 20, h: int = 24) -> None:
    """A glowing red paper lantern with gold caps and a tassel."""
    glow(a, cx, top + h // 2, w * 2, "#FF9A3C", 0.32)
    a.line([(cx, top - 10), (cx, top)], "#3B1A12")
    a.rect(cx - w // 4, top, w // 2, 3, "#D9A830", "cyl")
    a.ellipse(cx - w // 2, top + 2, w, h, "#D83A28", "sphere", 0.45)
    for k in range(-w // 2 + 4, w // 2 - 2, 4):                      # its ribs
        a.line([(cx + k, top + 4), (cx + k, top + h - 1)], "#B02A1E")
    a.ellipse(cx - w // 4, top + h // 3, w // 2, h // 3, "#FFD27A", "plain", 0)   # the light inside
    a.rect(cx - w // 4, top + h, w // 2, 3, "#D9A830", "cyl")
    a.line([(cx, top + h + 3), (cx, top + h + 10)], "#D83A28", 2)


def brass_lantern(a: Art, cx: int, top: int, w: int = 12, h: int = 22) -> None:
    """A wall lantern: a metal cage with a flame, on a curled bracket."""
    glow(a, cx, top + h // 2, w * 3, "#FFC76A", 0.55)
    a.rect(cx - w // 2, top, w, h, "#4A3220", "flat", 0.5)
    a.rect(cx - w // 2 + 2, top + 3, w - 4, h - 6, "#FFD27A", "plain", 0)
    a.ellipse(cx - 2, top + h // 2 - 3, 4, 6, "#FFF3C2", "plain", 0)
    a.poly([(cx - w // 2 - 1, top), (cx, top - 5), (cx + w // 2 + 1, top)], "#4A3220", "flat", 0.5)
    for gx in range(cx - w // 2 + 2, cx + w // 2 - 1, 3):
        a.box(gx, top + 3, 1, h - 6, "#4A3220")


def cabinets(a: Art, x0: int, x1: int, y0: int, y1: int, color: str, frame: str, door_w: int, handle: str = "#2B2B2B",
             drawers: bool = False) -> None:
    """A run of cupboard doors (or drawers) in frames, with handles."""
    a.box(x0, y0, x1 - x0, y1 - y0, frame)
    for dx in range(x0 + 2, x1 - 2, door_w):
        w = min(door_w - 3, x1 - 2 - dx)
        if w < 6:
            continue
        if drawers:
            for k, dy in enumerate(range(y0 + 2, y1 - 2, (y1 - y0) // 3)):
                h = (y1 - y0) // 3 - 3
                a.rect(dx, dy, w, h, color, "flat", 0.5)
                a.rect(dx + w // 2 - 4, dy + h // 2 - 1, 8, 2, handle, "plain", 0)
        else:
            a.rect(dx, y0 + 2, w, y1 - y0 - 4, color, "flat", 0.5)
            a.rect(dx + 3, y0 + 5, w - 6, y1 - y0 - 10, tone(color, 0.92), "flat", 0.6)
            a.rect(dx + w // 2 - 3, y0 + (y1 - y0) // 3, 2, 7, handle, "plain", 0)
            a.rect(dx + w // 2 + 1, y0 + (y1 - y0) // 3, 2, 7, handle, "plain", 0)


def stove(a: Art, x: int, y: int, w: int, h: int, knobs: int = 5) -> None:
    """A steel range: a cooktop with grates, a row of knobs, the oven door with its window and handle."""
    a.rect(x, y, w, 4, "#3A3A3E", "flat", 0.5)
    for gx in range(x + 3, x + w - 6, w // 4):
        a.box(gx, y - 1, w // 4 - 4, 1, "#1E1E22")
    a.rect(x, y + 4, w, h - 4, "#A9A9AF", "flat", 0.45)
    for k in range(knobs):
        kx = x + 5 + k * (w - 10) // max(1, knobs - 1) - 3
        a.ellipse(kx, y + 7, 6, 6, "#4A4A50", "sphere", 0.5)
    a.rect(x + 4, y + 16, w - 8, 3, "#D7D7DC", "cyl", 0.5)
    a.rect(x + 4, y + 21, w - 8, h - 25, "#2A2A30", "flat", 0.5)
    a.rect(x + 8, y + 24, w - 16, h - 31, "#3E3E46", "plain", 0)


def stool(a: Art, x: int, y: int, w: int, h: int, seat: str, wood: str = "#7A4A2A", pattern: str | None = None) -> None:
    a.rect(x - 1, y + 5, w + 2, 3, tone(wood, 0.9), "flat", 0.5)
    a.rect(x, y, w, 6, seat, "flat", 0.5)
    if pattern:
        for px in range(x + 2, x + w - 2, 3):
            a.put(px, y + 2, pattern)
    for lx in (x + 1, x + w - 6):
        a.rect(lx, y + 8, 5, h - 8, wood, "cyl", 0.5)
    a.box(x + 3, y + h - 6, w - 6, 2, tone(wood, 0.8))


def empty_sign(a: Art, x0: int, y0: int, x1: int, y1: int, frame: str, paper: str, corner: str | None = None) -> None:
    """The kitchen's sign, empty: a wooden frame and a lit paper panel (the page writes the title on its own)."""
    a.rect(x0, y0, x1 - x0, y1 - y0, frame, "flat", 0.45)
    a.rect(x0 + 4, y0 + 4, x1 - x0 - 8, y1 - y0 - 8, paper, "plain", 0.6)
    glow(a, (x0 + x1) // 2, (y0 + y1) // 2, (x1 - x0) // 3, "#FFE2A8", 0.18)
    if corner:
        for cx in (x0 + 5, x1 - 15):
            a.rect(cx, y0 + 5, 10, y1 - y0 - 10, corner, "flat", 0.55)


# ======================================================================================= Chinese: The Jade Wok
def chinese() -> Image.Image:
    a = canvas("#D78845", seed=101)
    beam, ceiling = "#7C2F15", "#5E1A19"

    # Ceiling: dark wood with heavy beams running back into the room
    a.box(0, 0, FW, 40, ceiling)
    for k in range(0, FW, 14):
        a.box(k, 0, 1, 40, tone(ceiling, 0.8))
    for x_top, x_bot in ((90, 110), (220, 232), (330, 318)):
        a.poly([(x_top - 10, 0), (x_top + 10, 0), (x_bot + 10, 40), (x_bot - 10, 40)], beam, "cyl", 0.5)
    a.poly([(0, 0), (60, 0), (130, 28), (130, 38), (0, 30)], tone(ceiling, 1.1), "flat", 0.5)
    a.wood(132, 36, 250, 5, beam)                                     # the lintel over the back wall

    # The back wall (warm plaster, lit by the lanterns) and the posts that frame it
    a.plaster(135, 41, 238, 113, "#D99050", cracks=4)
    a.wood(126, 22, 10, 135, "#6E2A18", vertical=True)
    a.wood(371, 22, 9, 135, "#6E2A18", vertical=True)

    # The big lattice window on the left, with a cherry tree, mountains and a pagoda outside
    a.box(0, 22, 126, 135, "#6E2A18")
    for yy in range(46, 152):                                         # sky
        t = (yy - 46) / 106
        a.box(30, yy, 86, 1, tone("#6FB2E8", 1 + 0.35 * t))
    a.ellipse(70, 66, 26, 8, "#FFFFFF", "plain", 0)
    a.ellipse(80, 62, 18, 7, "#FFFFFF", "plain", 0)
    a.poly([(30, 112), (52, 92), (72, 104), (94, 88), (116, 102), (116, 130), (30, 130)], "#6C8FC4", "flat", 0.6)
    a.poly([(30, 120), (60, 108), (90, 116), (116, 110), (116, 140), (30, 140)], "#7FA2CC", "plain", 0)
    leaves(a, 72, 136, 90, 22, ("#2F6A2A", "#3F7A2E", "#5E9B3A"), count=90, leaf=(7, 5))
    for k, (py, pw) in enumerate(((100, 10), (106, 16), (113, 22))):  # the pagoda: three red roofs
        a.poly([(85 - pw // 2 - 3, py + 6), (85, py), (85 + pw // 2 + 3, py + 6)], "#3E6B3A", "flat", 0.5)
        a.rect(85 - pw // 2 + 2, py + 6, pw - 4, 5, "#C8452E", "flat", 0.5)
    a.rect(78, 124, 14, 8, "#C8452E", "flat", 0.5)
    for _ in range(140):                                              # the cherry tree's blossoms
        bx, by = a.rand.randrange(26, 76), a.rand.randrange(44, 120)
        if (bx - 46) ** 2 / 900 + (by - 78) ** 2 / 1500 < 1:
            a.ellipse(bx, by, 4, 3, a.rand.choice(("#F4A6C0", "#F7C3D3", "#E07FA0")), "plain", 0)
    a.line([(40, 150), (44, 110), (52, 90)], "#5A2E22", 3)
    for lx in range(0, 126, 10):                                      # the red lattice over the top and sides
        for ly in range(24, 46, 8):
            a.shape(lambda d, lx=lx, ly=ly: d.rectangle([lx, ly, lx + 9, ly + 7], outline=255), "#8E2A1E", "plain", 0)
    for ly in range(46, 152, 8):
        for lx in (0, 10, 116):
            a.shape(lambda d, lx=lx, ly=ly: d.rectangle([lx, ly, lx + 9, ly + 7], outline=255), "#8E2A1E", "plain", 0)
    for gx in (28, 116):
        a.box(gx, 22, 3, 135, "#5A1E14")
    a.box(0, 140, 126, 4, "#6E2A18")
    for lx in range(2, 124, 6):                                       # the railing under the window
        a.box(lx, 144, 2, 12, "#7A2E1E")

    # Lanterns: one in the window, one on each side of the sign
    red_lantern(a, 8, 30, 18, 22)
    red_lantern(a, 146, 52, 20, 22)
    red_lantern(a, 320, 52, 20, 22)

    # The empty sign with blossoms around it
    empty_sign(a, 174, 50, 294, 74, "#7A3A1E", "#F2C98A", "#C8452E")
    for _ in range(46):
        side = a.rand.choice((0, 1))
        bx = a.rand.randrange(156, 180) if side == 0 else a.rand.randrange(290, 312)
        by = a.rand.randrange(40, 84)
        a.ellipse(bx, by, 4, 4, a.rand.choice(("#F4A6C0", "#E07FA0", "#F7C3D3")), "plain", 0)

    # Left shelf: sauce bottles; pans hanging below
    a.wood(141, 106, 63, 4, "#7A3A1E")
    for k, (bx, bh, body, cap, label) in enumerate([(145, 18, "#4A1E12", "#C8452E", "#E9C46A"),
                                                     (154, 20, "#3A1610", "#C8452E", "#E9C46A"),
                                                     (163, 18, "#2A1410", "#C8452E", "#E9C46A"),
                                                     (172, 13, "#4A1E12", "#C8452E", "#E9C46A"),
                                                     (181, 22, "#6E8A2E", "#C8452E", "#F4E7B0"),
                                                     (192, 16, "#C8742A", "#C8452E", "#E9C46A")]):
        a.poly([(bx, 106), (bx, 106 - bh + 6), (bx + 2, 106 - bh + 3), (bx + 2, 106 - bh), (bx + 5, 106 - bh),
                (bx + 5, 106 - bh + 3), (bx + 7, 106 - bh + 6), (bx + 7, 106)], body, "cyl", 0.45)
        a.box(bx + 2, 106 - bh - 1, 4, 2, cap)
        a.rect(bx + 1, 106 - bh // 2 - 1, 6, 6, label, "plain", 0.6)
        a.put(bx + 3, 106 - bh // 2 + 1, "#B02A1E")
    for bx in (147, 196):
        a.rect(bx, 110, 3, 6, "#5A2A16")
    a.line([(163, 112), (163, 120)], "#2B2B2B")
    a.ellipse(152, 120, 22, 24, "#2E2E32", "sphere")
    a.line([(186, 112), (186, 118)], "#8A4A2E")
    a.ellipse(177, 118, 20, 22, "#C8642E", "sphere")
    a.ellipse(181, 122, 12, 14, "#B0501E", "plain", 0)

    # Right shelf: a bowl of greens, four jars; garlic, chilies and a vine on the wall
    a.wood(207, 106, 98, 4, "#7A3A1E")
    for bx in (212, 296):
        a.rect(bx, 110, 3, 6, "#5A2A16")
    porcelain(a, 210, 96, 16, 10, mouth=False)
    leaves(a, 218, 92, 12, 10, count=14, leaf=(3, 6))
    for k, (jx, inside) in enumerate(((227, "#5A2A1A"), (243, "#E8D2A2"), (259, "#6FA046"), (275, "#C8402A"))):
        a.jar(jx, 89, 14, 106, inside, lid="#A06A3A", speckle=tone(inside, 0.75), fill_from=0.25)
    vine(a, 293, 96, 34)
    leaves(a, 296, 100, 16, 14, count=18)
    for k in range(9):                                                # the chili string
        a.ellipse(310 + (k % 2) * 4, 84 + k * 4, 5, 8, "#D62E2A", "sphere", 0.5)
    a.line([(314, 80), (314, 86)], "#2F5A22")
    a.rect(355, 80, 3, 6, "#6B4A2A")
    for k, gy in enumerate(range(86, 118, 7)):
        for gx in (352, 358):
            a.ellipse(gx - (k % 2), gy, 7, 7, "#F4EFE4", "sphere", 0.5)

    # Bamboo in a blue-and-white pot
    for k, bx in enumerate((326, 331, 336, 341)):
        top = 70 + (k * 7) % 14
        a.rect(bx, top, 3, 70 - (top - 70), "#6FA846", "cyl", 0.5)
        for ny in range(top + 6, 138, 10):
            a.box(bx, ny, 3, 1, "#3F7A2E")
    leaves(a, 334, 84, 36, 34, ("#3F7A2E", "#5E9B3A", "#86C45A"), count=38, leaf=(8, 3))
    porcelain(a, 322, 134, 28, 18)

    # The counter and what stands on it
    a.wood(115, 152, 275, 7, "#8A4A26")
    porcelain(a, 122, 140, 20, 12, mouth=False)
    leaves(a, 132, 132, 24, 16, count=22)
    a.rect(145, 138, 10, 14, "#C8964A", "cyl", 0.5)                  # utensil jar with spoons and chopsticks
    for ux in (147, 150, 153):
        a.line([(ux, 138), (ux - 1, 128)], "#8A5A2E", 1)
    a.ellipse(183, 145, 18, 8, "#C8402A", "sphere", 0.5)               # a red bowl
    for k, sy in enumerate((142, 136, 130)):                           # the bamboo steamer, three tiers and a lid
        a.rect(201, sy, 28, 7, "#E0B46A", "cyl", 0.5)
        a.box(202, sy + 3, 26, 1, "#B08446")
    a.ellipse(201, 126, 28, 6, "#D4A458", "sphere", 0.5)
    a.ellipse(230, 145, 14, 7, "#3A6EA8", "sphere", 0.5)
    a.ellipse(245, 136, 38, 14, "#2E2E32", "sphere", 0.45)             # the wok and its lid
    a.ellipse(253, 132, 22, 7, "#3A3A40", "sphere", 0.5)
    a.rect(262, 129, 4, 3, "#2E2E32")
    for hx in (243, 282):
        a.rect(hx, 138, 3, 3, "#1E1E22")
    a.rect(288, 138, 28, 13, "#C8302A", "cyl")                         # the red pot
    a.ellipse(287, 134, 30, 6, "#D83A30", "sphere", 0.5)
    a.rect(300, 131, 4, 3, "#2E2E32")

    # Baskets of vegetables on the right of the counter
    for bx, bw in ((348, 34), (384, 30)):
        a.poly([(bx, 140), (bx + bw, 140), (bx + bw - 3, 154), (bx + 3, 154)], "#C8964A", "cyl")
        for wy in range(142, 154, 3):
            a.box(bx + 2, wy, bw - 4, 1, "#9A6A32")
    a.ellipse(358, 128, 16, 14, "#B8D88A", "sphere", 0.5)              # cabbage, carrots, greens, tomatoes
    for cx in (373, 378):
        a.poly([(cx, 140), (cx + 3, 126), (cx + 5, 140)], "#E8862E", "cyl", 0.5)
        a.box(cx + 2, 124, 2, 3, "#3F7A2E")
    leaves(a, 352, 130, 10, 12, count=10)
    for tx in (387, 394, 401, 405):
        a.ellipse(tx, 134 + (tx % 3), 7, 7, "#D62E2A", "sphere", 0.5)

    # The range and the red cabinets
    stove(a, 242, 150, 49, 45)
    cabinets(a, 117, 149, 159, 195, "#8A5530", "#5A2A16", 31, drawers=True)
    cabinets(a, 149, 242, 159, 195, "#A82A1E", "#5A1E14", 31)
    cabinets(a, 291, 392, 159, 195, "#A82A1E", "#5A1E14", 34)
    a.box(115, 195, 277, 2, "#3A140E")

    # The shelves on the right wall: bowls, a plant, a framed red hanging
    a.box(375, 40, 43, 115, "#6E2A18")
    for sy in (68, 94, 120):
        a.wood(377, sy, 41, 4, "#8A4A26")
    a.rect(392, 46, 18, 22, "#C8302A", "flat", 0.5)
    a.rect(395, 49, 12, 16, "#D9A830", "plain", 0)
    a.box(400, 52, 2, 10, "#8E1E14")
    for k, by in enumerate((88, 114)):
        for bx in (379, 395):
            for s in range(2):
                a.ellipse(bx, by - s * 3, 14, 6, "#F2F2EE", "sphere", 0.5)
                a.box(bx + 2, by - s * 3 + 3, 10, 1, "#2F55A0")
    a.ellipse(392, 36, 22, 14, "#B08A5A", "sphere", 0.5)               # a basket on top, and a vine
    vine(a, 378, 44, 40)
    leaves(a, 382, 46, 18, 14, count=16)

    # The dining table and stools on the left, with fruit and flowers
    a.wood(0, 156, 100, 6, "#8A4A26")
    a.box(0, 162, 98, 4, "#5A2A16")
    for lx in (8, 86):
        a.rect(lx, 166, 5, 46, "#6E3A1E", "cyl", 0.5)
    a.rect(18, 156, 14, 38, "#B8302A", "flat", 0.5)                    # the red runner hanging off the table
    for ry in range(160, 192, 4):
        a.box(20, ry, 10, 1, "#D9A830")
    for sx in (34, 80):
        stool(a, sx, 172, 30, 40, "#C8302A", "#6E3A1E")
    stool(a, -6, 174, 24, 38, "#C8302A", "#6E3A1E")
    a.ellipse(16, 146, 22, 9, "#C8402A", "sphere", 0.5)                # bowl of oranges
    for ox in (19, 25, 31):
        a.ellipse(ox, 142, 7, 6, "#F08A2E", "sphere", 0.5)
    a.ellipse(51, 148, 16, 7, "#8A5A2E", "sphere", 0.5)
    porcelain(a, 37, 124, 12, 24)
    for _ in range(26):
        a.ellipse(a.rand.randrange(32, 54), a.rand.randrange(108, 126), 4, 4, a.rand.choice(("#F4A6C0", "#E07FA0")), "plain", 0)
    porcelain(a, 0, 136, 12, 18)
    leaves(a, 8, 116, 30, 40, ("#2F6A2A", "#3F7A2E", "#5E9B3A"), count=30, leaf=(10, 4))

    # The floor, the rug, a basket of greens and a potted plant on the right
    planks(a, 0, 195, FW, FH, "#C8642A")
    rug(a, (112, 360), (100, 372), 204, 224, "#B8302A", "#8E1E14", "#E0A23A")
    a.poly([(375, 172), (403, 172), (400, 206), (378, 206)], "#C8964A", "cyl")
    for wy in range(175, 206, 4):
        a.box(377, wy, 25, 1, "#9A6A32")
    leaves(a, 389, 168, 30, 14, count=26)
    a.poly([(404, 190), (418, 190), (418, 214), (406, 214)], "#C8742A", "cyl")
    leaves(a, 412, 176, 26, 30, count=26, leaf=(9, 4))
    return save(a, "chinese")


# ======================================================================================= Mediterranean: The Golden Hearth
def stones_light(a: Art, x0: int, y0: int, x1: int, y1: int, base: str = "#D9CDB8") -> None:
    """A light dressed-stone wall (the fireplace): rows of shaded blocks with thin mortar."""
    a.box(x0, y0, x1 - x0, y1 - y0, "#A89A84")
    for k, y in enumerate(range(y0, y1, 9)):
        off = 0 if k % 2 == 0 else 7
        for x in range(x0 - off, x1, 15):
            a.rect(max(x0, x + 1), y + 1, min(13, x1 - max(x0, x + 1)), 7, tone(base, a.rand.choice((0.94, 1.0, 1.05))),
                   "sphere", 0.7)


def fire(a: Art, cx: int, base: int, w: int, h: int) -> None:
    """Flames over glowing logs, with a warm glow on the stones around."""
    glow(a, cx, base - h // 2, w * 2, "#FF8A2A", 0.5)
    for lx, ly, lw in ((cx - w // 2, base - 4, w), (cx - w // 3, base - 7, w * 2 // 3)):
        a.rect(lx, ly, lw, 4, "#5A3220", "cyl", 0.5)
    for k, (col, scale) in enumerate((("#E0441C", 1.0), ("#F7902A", 0.72), ("#FFD45A", 0.42))):
        fw, fh = int(w * scale), int(h * scale)
        pts = [(cx - fw // 2, base - 5), (cx - fw // 3, base - fh // 2), (cx - fw // 6, base - fh * 3 // 4), (cx, base - fh),
               (cx + fw // 6, base - fh * 2 // 3), (cx + fw // 3, base - fh // 2 - 2), (cx + fw // 2, base - 5)]
        a.shape(lambda d, pts=pts: d.polygon(pts, fill=255), col, "plain", 0)
    for _ in range(10):
        a.put(cx + a.rand.randint(-w // 2, w // 2), base - a.rand.randint(h // 2, h + 6), "#FFD45A")


def sunflowers(a: Art, cx: int, top: int, n: int = 5) -> None:
    for k in range(n):
        fx, fy = cx - 12 + (k * 7) % 24, top + (k * 5) % 12
        a.line([(fx + 3, fy + 4), (cx, top + 28)], "#3F7A2E")
        for ang in range(0, 360, 45):
            px, py = fx + 3 + round(4 * math.cos(math.radians(ang))), fy + 3 + round(4 * math.sin(math.radians(ang)))
            a.ellipse(px - 1, py - 1, 3, 3, "#F2B81E", "plain", 0)
        a.ellipse(fx + 1, fy + 1, 5, 5, "#6B3A16", "plain", 0)


def golden_hearth() -> Image.Image:
    a = canvas("#E8C9A0", seed=202)
    timber = "#7A4A24"
    planks(a, 0, 0, FW, 28, "#8E5A2E", horizontal=False)              # the plank ceiling and its rafters
    for x_top, x_bot in ((60, 30), (150, 140), (230, 230), (310, 320), (390, 410)):
        a.poly([(x_top - 7, 0), (x_top + 7, 0), (x_bot + 8, 28), (x_bot - 8, 28)], timber, "cyl", 0.5)
    a.plaster(0, 28, FW, 167, "#DDB485", cracks=10)
    for _ in range(24):                                               # stone showing through the plaster
        sx, sy = a.rand.randrange(110, FW), a.rand.randrange(30, 150)
        a.shape(lambda d, sx=sx, sy=sy: d.rounded_rectangle([sx, sy, sx + 16, sy + 9], 3, outline=255), "#C9A87E", "plain", 0)
    a.wood(0, 37, FW, 5, timber)                                      # half-timbering
    for px in (105, 141, 322, 367):
        a.wood(px, 28, 6, 130, timber, vertical=True)
    a.wood(141, 75, 226, 4, timber)

    # The stone fireplace with its fire, the mantel with pots and vines, the log store below
    stones_light(a, 0, 40, 112, 195)
    a.shape(lambda d: d.polygon([(30, 152), (30, 120), (40, 108), (66, 102), (92, 108), (100, 120), (100, 152)], fill=255),
            "#2A1A14", "plain", 0)
    a.shape(lambda d: d.polygon([(30, 120), (40, 108), (66, 102), (92, 108), (100, 120)], outline=255), "#B9AD98", "plain", 0)
    fire(a, 65, 150, 30, 34)
    a.rect(38, 150, 56, 4, "#A89A84", "flat", 0.5)
    a.rect(55, 162, 42, 30, "#2A1A14", "plain", 0)
    for ly in (166, 174, 182):                                        # logs stacked in the store
        for lx in range(58, 92, 8):
            a.ellipse(lx, ly, 8, 7, "#8E5A2E", "sphere", 0.5)
    a.wood(8, 67, 100, 6, "#8E5A2E")
    for px, pw in ((14, 18), (48, 16), (82, 14)):                    # terracotta pots with plants on the mantel
        a.poly([(px, 56), (px + pw, 56), (px + pw - 2, 67), (px + 2, 67)], "#C26A3A", "cyl")
        leaves(a, px + pw // 2, 50, pw + 8, 12, count=12)
    porcelain(a, 70, 52, 10, 15)
    for vx in (16, 30, 92, 104):
        vine(a, vx, 72, 36)

    # The empty sign between two brass lanterns, vines around it
    brass_lantern(a, 153, 52)
    brass_lantern(a, 283, 52)
    empty_sign(a, 172, 52, 264, 72, "#7A4A24", "#F6DDB0")
    for vx in (166, 268):
        vine(a, vx, 52, 22)
        leaves(a, vx, 56, 10, 12, count=8)

    # Shelves: bottles, jars; pans and a chili string below and beside them
    a.wood(141, 102, 41, 4, "#8E5A2E")
    for k, bx in enumerate(range(143, 180, 7)):
        a.poly([(bx, 102), (bx, 90), (bx + 2, 87), (bx + 2, 84), (bx + 4, 84), (bx + 4, 87), (bx + 6, 90), (bx + 6, 102)],
               ("#3F6B2A", "#5E7D2E", "#4A3A1E", "#6E8A2E", "#5E7D2E")[k % 5], "cyl", 0.45)
        a.rect(bx + 1, 93, 5, 5, "#E9D6A0", "plain", 0.6)
        a.put(bx + 3, 95, "#B02A1E")
    a.line([(152, 106), (152, 112)], "#2B2B2B")
    a.ellipse(142, 112, 18, 18, "#2E2E32", "sphere")
    a.line([(152, 122), (148, 134)], "#2E2E32", 2)
    a.line([(172, 106), (172, 112)], "#8A4A2E")
    a.ellipse(163, 112, 18, 18, "#C8642E", "sphere")
    a.line([(172, 122), (170, 134)], "#8A4A2E", 2)
    for k in range(8):
        a.ellipse(125 + (k % 2) * 4, 94 + k * 4, 5, 8, "#A0306A", "sphere", 0.5)
    a.line([(129, 90), (129, 95)], "#3F7A2E")
    a.wood(181, 106, 69, 4, "#8E5A2E")
    for jx, inside in ((184, "#E8D9B8"), (195, "#7A2A22"), (206, "#B8A04A"), (217, "#5E8A3A"), (228, "#9A6A3A"), (239, "#B8302A")):
        a.jar(jx, 91, 10, 106, inside, lid="#B08A5A", speckle=tone(inside, 0.8), fill_from=0.25)

    # The window onto a hill town, garlic hanging beside it
    a.box(252, 85, 54, 58, "#5A3A22")
    for yy in range(88, 140):
        a.box(255, yy, 48, 1, tone("#7EC0EC", 1 + 0.3 * (yy - 88) / 52) if yy < 112 else "#6FA046")
    a.ellipse(262, 94, 14, 5, "#FFFFFF", "plain", 0)
    a.poly([(255, 116), (270, 106), (288, 112), (303, 104), (303, 120), (255, 120)], "#4F8A3A", "plain", 0)
    for hx, hw, roof in ((266, 8, "#C8642E"), (276, 10, "#D9774A"), (288, 7, "#C8642E")):
        a.rect(hx, 120, hw, 8, "#F2E2C2", "flat", 0.6)
        a.box(hx - 1, 118, hw + 2, 2, roof)
    a.rect(280, 108, 4, 12, "#E8D2A8", "flat", 0.6)                   # the church tower
    a.box(279, 106, 6, 2, "#C8642E")
    leaves(a, 262, 128, 14, 10, count=10)
    a.box(278, 85, 2, 58, "#5A3A22")
    a.box(252, 113, 54, 2, "#5A3A22")
    a.wood(250, 141, 58, 4, "#8E5A2E")
    for k, gy in enumerate(range(82, 102, 6)):
        for gx in (300, 306):
            a.ellipse(gx - (k % 2), gy, 6, 6, "#F4EFE4", "sphere", 0.5)
    vine(a, 300, 62, 40)
    leaves(a, 305, 66, 26, 22, count=26)
    a.rect(341, 82, 16, 25, "#8E5A2E", "flat", 0.5)                   # a framed botanical picture
    a.rect(343, 84, 12, 21, "#F2E6CF", "plain", 0)
    a.line([(349, 102), (349, 88)], "#3F7A2E")
    a.ellipse(346, 86, 6, 6, "#C8402A", "plain", 0)

    # The range with two copper pots, the counter and what is on it
    a.wood(122, 154, 268, 6, "#9A5A2E")
    stove(a, 166, 150, 55, 45, knobs=5)
    for px in (171, 196):
        a.rect(px, 133, 22, 17, "#C8642E", "cyl")
        a.ellipse(px - 1, 130, 24, 6, "#D9774A", "sphere", 0.5)
        a.rect(px + 9, 127, 4, 3, "#3B2A25")
    a.rect(128, 150, 26, 4, "#C9A87E", "flat", 0.5)                   # a board with bread and cheese, a candle
    a.ellipse(132, 146, 10, 5, "#D9A86B", "sphere", 0.5)
    a.rect(146, 140, 4, 9, "#F4EFE4", "cyl", 0.5)
    glow(a, 148, 138, 10, "#FFC76A", 0.4)
    a.put(148, 137, "#FFD45A")
    a.rect(229, 122, 18, 30, "#B08A5A", "flat", 0.5)                  # a cutting board leaning on the wall
    a.ellipse(234, 118, 8, 6, "#B08A5A", "plain", 0.5)
    a.ellipse(227, 146, 16, 9, "#9A9AA0", "sphere", 0.5)              # mortar and pestle
    a.line([(238, 145), (244, 137)], "#7A7A80", 3)
    a.rect(246, 148, 14, 6, "#C8642E", "cyl")
    a.line([(259, 149), (266, 146)], "#3B2A25", 2)
    for tx in range(221, 327, 4):                                     # the tiled worktop with a checked cloth
        a.box(tx, 154, 2, 2, "#C8402A")
    a.rect(291, 157, 18, 28, "#F4EFE4", "flat", 0.55)
    for ty in range(160, 184, 5):
        a.box(292, ty, 16, 1, "#C8402A")
    a.poly([(304, 140), (322, 140), (319, 154), (307, 154)], "#C26A3A", "cyl")
    leaves(a, 313, 133, 22, 16, count=18, leaf=(4, 6))
    porcelain(a, 333, 132, 18, 22)
    sunflowers(a, 342, 108)
    leaves(a, 342, 122, 22, 14, count=12)
    a.ellipse(350, 146, 24, 8, "#9A6A3A", "sphere", 0.5)
    for tx in (353, 359, 365):
        a.ellipse(tx, 142, 7, 6, "#D62E2A", "sphere", 0.5)
    cabinets(a, 122, 166, 160, 195, "#8E5A2E", "#5A3218", 22, handle="#3A3A3A", drawers=True)
    cabinets(a, 221, 390, 160, 195, "#8E5A2E", "#5A3218", 34, handle="#3A3A3A")

    # Plate shelves and jars on the right, hanging plants, a big potted plant
    a.box(372, 82, 46, 73, "#7A4A24")
    for sy in (108, 130, 152):
        a.wood(374, sy, 44, 3, "#9A5A2E")
    for k in range(4):
        a.ellipse(376, 124 - k * 3, 18, 5, "#F4F2EE", "sphere", 0.5)
    a.jar(398, 116, 9, 130, "#8E1E2A", fill_from=0.1)
    a.jar(406, 118, 9, 130, "#8E1E2A", fill_from=0.1)
    a.poly([(388, 95), (402, 95), (400, 106), (390, 106)], "#C26A3A", "cyl")
    leaves(a, 395, 90, 22, 14, count=14)
    for vx in (395, 410):
        vine(a, vx, 28, 52)
    leaves(a, 402, 34, 30, 26, count=28)
    porcelain(a, 392, 182, 26, 28)
    leaves(a, 405, 160, 34, 38, ("#2F6A2A", "#3F7A2E", "#5E9B3A"), count=26, leaf=(10, 4))

    # The table, a stool, a bread basket, sunflowers in a blue vase
    a.wood(0, 155, 58, 6, "#8E5A2E")
    for lx in (4, 50):
        a.rect(lx, 161, 5, 34, "#6E3A1E", "cyl", 0.5)
    a.ellipse(26, 147, 22, 8, "#C26A3A", "sphere", 0.5)
    for tx in (29, 35, 41):
        a.ellipse(tx, 143, 6, 6, "#D62E2A", "sphere", 0.5)
    porcelain(a, 2, 132, 14, 22)
    sunflowers(a, 9, 108)
    leaves(a, 9, 124, 18, 12, count=10)
    stool(a, 2, 182, 30, 40, "#C8302A", "#6E3A1E")
    a.poly([(92, 172), (118, 172), (115, 192), (95, 192)], "#C8964A", "cyl")
    for wy in range(175, 192, 3):
        a.box(94, wy, 22, 1, "#9A6A32")
    for bx, by in ((95, 166), (103, 164)):
        a.ellipse(bx, by, 14, 8, "#D9A86B", "sphere", 0.5)
    a.rect(110, 150, 10, 20, "#9A6A3A", "cyl")
    leaves(a, 115, 144, 14, 12, count=10, leaf=(3, 6))

    # The floor and the rug
    planks(a, 0, 195, FW, FH, "#B8662E")
    rug(a, (86, 352), (77, 360), 200, 229, "#B83A22", "#8E2414", "#E8A23A")
    return save(a, "mediterranean")


# ======================================================================================= Mexican: The Joyful Kitchen
def joyful_kitchen() -> Image.Image:
    a = canvas("#F2A93B", seed=303)
    a.plaster(0, 0, FW, 195, "#F2A93B", cracks=6)
    for k, x in enumerate(range(0, FW, 22)):                         # red beams across the ceiling
        a.poly([(x - 2, 0), (x + 14, 0), (x + 16, 26), (x, 26)], "#C8452E", "cyl", 0.5)
    a.box(0, 26, FW, 3, "#9A3020")

    # The arched blue doorway onto the village, with bougainvillea
    arch = cr.arch_points(14, 82, 50, 26, 150, onion=0.0)
    a.shape(lambda d: d.polygon(arch, fill=255), "#2F6DB5", "flat", 0.5)
    inner = cr.arch_points(20, 76, 54, 32, 150)
    mask = Image.new("L", (FW, FH), 0)
    ImageDraw.Draw(mask).polygon(inner, fill=255)
    mk = mask.load()
    for y in range(30, 150):
        for x in range(18, 80):
            if mk[x, y]:
                a.put(x, y, tone("#7EC8F0", 1 + 0.25 * (y - 30) / 120) if y < 96 else "#D9A86B")
    for hx, hy, hw, hh in ((24, 108, 22, 22), (50, 100, 24, 30)):     # adobe houses
        for y in range(hy, hy + hh):
            for x in range(hx, hx + hw):
                if mk[x, y]:
                    a.put(x, y, "#E8B080" if x < hx + hw - 4 else "#C98A5A")
        a.rect(hx + hw // 3, hy + hh - 10, 6, 10, "#8E5A3A", "plain", 0)
    for _ in range(120):
        bx, by = a.rand.randrange(16, 44), a.rand.randrange(36, 120)
        if mk[bx, by]:
            a.ellipse(bx, by, 4, 4, a.rand.choice(("#E8418A", "#F06AA8", "#C8306E")), "plain", 0)
    a.ellipse(56, 84, 6, 18, "#3F6B2A", "cyl", 0.6)
    leaves(a, 30, 120, 22, 30, count=24)
    a.box(80, 96, 4, 54, "#C8452E")

    # Lanterns, the hanging basket, a plate on the wall
    brass_lantern(a, 8, 20, 10, 30)
    brass_lantern(a, 132, 38)
    brass_lantern(a, 278, 38)
    a.line([(101, 26), (101, 40)], "#5A3220")
    a.ellipse(88, 40, 26, 22, "#9A6A32", "sphere", 0.5)
    leaves(a, 101, 42, 34, 26, count=24)
    vine(a, 92, 52, 26)
    a.ellipse(91, 86, 19, 17, "#F4EFE4", "sphere", 0.5)
    a.shape(lambda d: d.ellipse([94, 89, 107, 100], outline=255), "#2F6DB5", "plain", 0)
    a.ellipse(97, 91, 7, 7, "#E8432F", "plain", 0)

    # The empty sign with talavera corners, vines around it
    empty_sign(a, 140, 35, 270, 54, "#8E4A22", "#F7E3B8", "#2F6DB5")
    for vx in (142, 266):
        vine(a, vx, 34, 22)
    a.rect(300, 37, 17, 17, "#F4EFE4", "flat", 0.55)
    cr.talavera(a, 302, 39, 13, 2)

    # Blue shelves: ollas above, a pot, corn, chilies and beans below
    for sy in (87, 112):
        a.rect(122, sy, 106, 4, "#2F8FA8", "flat", 0.45)
        a.shadow(122, sy + 4, 106, 2)
    def olla(x: int, top: int, w: int, base: int) -> None:
        h = base - top
        a.ellipse(x, top + h // 4, w, h - h // 4, "#B85A2E")
        a.ellipse(x + w // 6, top + 2, w - w // 3, h // 3, "#A84E26")
        a.rect(x + w // 2 - 2, top, 4, 3, "#8E4426", "cyl")
        a.box(x + 3, top + h // 2 + 1, w - 6, 2, "#3A8C8C")
        for kx in range(x + 4, x + w - 4, 3):
            a.put(kx, top + h // 2 + 4, "#F2D9A8")
    for ox in (124, 152, 180, 205):
        olla(ox, 69, 24, 87)
    olla(124, 94, 22, 112)
    a.poly([(147, 100), (172, 100), (170, 112), (149, 112)], "#C8964A", "cyl")
    for cx in (149, 155, 161, 167):
        a.ellipse(cx, 92, 6, 12, "#F2C531", "cyl", 0.45)
        a.poly([(cx - 1, 104), (cx + 2, 96), (cx + 4, 104)], "#4C8A30", "cyl", 0.5)
    a.poly([(175, 102), (200, 102), (198, 112), (177, 112)], "#C8964A", "cyl")
    for _ in range(14):
        a.ellipse(a.rand.randrange(176, 196), a.rand.randrange(94, 102), 8, 4, "#D62E2A", "sphere", 0.5)
    a.poly([(202, 112), (203, 99), (207, 94), (220, 94), (224, 99), (225, 112)], "#C9A06A", "cyl")
    a.ellipse(204, 92, 20, 7, "#5A2E22", "sphere", 0.5)

    # The painted window with open shutters onto the village and its church
    a.rect(235, 64, 80, 66, "#2F8FC8", "flat", 0.45)
    for yy in range(70, 124):
        a.box(254, yy, 42, 1, tone("#7EC8F0", 1 + 0.3 * (yy - 70) / 54) if yy < 96 else "#8DB357")
    a.poly([(254, 98), (270, 88), (284, 94), (296, 86), (296, 100), (254, 100)], "#6E9B4A", "plain", 0)
    a.rect(272, 84, 7, 22, "#F2E2C2", "flat", 0.55)
    a.ellipse(271, 78, 9, 8, "#E8783A", "sphere", 0.5)
    for hx in (258, 284):
        a.rect(hx, 106, 10, 10, "#E8B080", "flat", 0.6)
        a.box(hx - 1, 104, 12, 2, "#C8642E")
    leaves(a, 274, 116, 40, 10, count=18)
    for sx in (237, 297):
        a.rect(sx, 68, 17, 58, "#C8392A", "cyl", 0.45)
        for py in (72, 90, 108):
            a.rect(sx + 3, py, 11, 14, "#E8B83C", "flat", 0.55)
            a.ellipse(sx + 6, py + 4, 5, 6, "#2F6DB5", "plain", 0)
    a.rect(232, 128, 86, 4, "#2F8FC8", "flat", 0.45)
    for k in range(8):                                                # the chili string
        a.ellipse(322 + (k % 2) * 4, 62 + k * 4, 5, 8, "#D62E2A", "sphere", 0.5)

    # Talavera backsplash, the range, the counter and what is on it
    for k, ty in enumerate(range(116, 146, 15)):
        for j, tx in enumerate(range(82, FW, 15)):
            if not (232 <= tx <= 318 and ty < 132):
                cr.talavera(a, tx, ty, 15, k + j)
    stove(a, 114, 140, 66, 55, knobs=6)
    a.rect(124, 126, 26, 16, "#C9C6C5", "cyl")
    a.ellipse(123, 122, 28, 6, "#D7D4D2", "sphere", 0.5)
    a.wood(180, 144, 238, 7, "#C8783A")
    for bx, bw, fill in ((185, 26, "#5EAA3A"), (244, 34, "#D62E2A")):
        a.poly([(bx, 132), (bx + bw, 132), (bx + bw - 3, 144), (bx + 3, 144)], "#C8964A", "cyl")
        for _ in range(bw // 2):
            a.ellipse(bx + 2 + a.rand.randrange(bw - 8), 127 + a.rand.randrange(5), 6, 6, fill, "sphere", 0.5)
    a.poly([(213, 144), (214, 130), (218, 125), (236, 125), (239, 130), (240, 144)], "#C9A06A", "cyl")
    a.ellipse(215, 121, 24, 8, "#5A2E22", "sphere", 0.5)
    for _ in range(16):
        a.put(217 + a.rand.randrange(20), 122 + a.rand.randrange(5), "#7A3A2A")
    a.poly([(298, 126), (330, 126), (326, 144), (302, 144)], "#E85A2E", "cyl")    # the cactus in a painted pot
    a.box(300, 131, 28, 3, "#F4C542")
    for px, py, pw, ph in ((306, 96, 14, 30), (296, 106, 11, 22), (319, 100, 12, 26), (309, 86, 10, 14)):
        a.ellipse(px, py, pw, ph, "#3E8E5A", "sphere", 0.45)
        for _ in range(pw // 2):
            a.put(px + 2 + a.rand.randrange(pw - 4), py + 2 + a.rand.randrange(ph - 4), "#DDE8C8")
    for fx, fy in ((308, 84), (318, 96), (296, 104)):
        a.ellipse(fx, fy, 6, 5, "#E86FA8", "sphere", 0.5)
    a.ellipse(355, 138, 26, 9, "#2F6DB5", "sphere", 0.5)
    for lx in (358, 365, 372):
        a.ellipse(lx, 133, 7, 6, "#F2C531", "sphere", 0.5)
    a.rect(358, 145, 60, 15, "#F4F2EE", "flat", 0.5)                 # the white sink and its tap
    a.rect(366, 147, 44, 8, "#C9CDD4", "flat", 0.5)
    a.line([(404, 145), (404, 132), (396, 132), (396, 136)], "#3A3A3E", 2)
    a.rect(370, 116, 12, 28, "#B08A5A", "flat", 0.5)

    # Shelves with pottery on the right, vines
    for sy in (84, 108):
        a.wood(360, sy, 58, 4, "#8E5A2E")
    for k, (px, col) in enumerate(((364, "#F4F2EE"), (380, "#C26A3A"), (396, "#F4F2EE"), (370, "#2F6DB5"), (392, "#C26A3A"))):
        porcelain(a, px, 66 if k < 3 else 90, 12, 18, body=col if col != "#2F6DB5" else "#F4F2EE",
                  blue="#2F6DB5" if col != "#C26A3A" else "#F2D9A8")
    for vx in (362, 410):
        vine(a, vx, 30, 70)
    leaves(a, 380, 40, 50, 30, count=34)

    # Painted cabinets with talavera panels, the cushioned stools, the table and its runner
    a.rect(180, 151, 128, 39, "#C8432F", "flat", 0.45)
    for dx in (184, 226, 268):
        a.rect(dx, 154, 38, 33, "#B83A2A", "flat", 0.45)
        a.rect(dx + 4, 157, 30, 27, "#3FA34D", "flat", 0.5)
        a.shape(lambda d, dx=dx: d.polygon([(dx + 19, 160), (dx + 30, 170), (dx + 19, 181), (dx + 8, 170)], fill=255), "#F4C542", "plain", 0)
        a.ellipse(dx + 15, 166, 8, 8, "#E8432F", "plain", 0)
    a.rect(335, 160, 83, 52, "#C8432F", "flat", 0.45)
    for dx in (338, 378):
        a.rect(dx, 164, 36, 44, "#B83A2A", "flat", 0.45)
        a.rect(dx + 4, 168, 28, 36, "#2F6DB5", "flat", 0.5)
        a.ellipse(dx + 12, 180, 12, 12, "#F4C542", "plain", 0)
    stool(a, 307, 162, 22, 34, "#8E5A2E", "#7A4A2A")
    planks(a, 0, 190, FW, FH, "#B85A35")                               # terracotta floor tiles
    for x in range(0, FW, 18):
        a.box(x, 190, 1, FH - 190, "#8E4228")
    rug(a, (198, 350), (192, 356), 202, 227, "#C8392A", "#8E2414", "#3FA34D", fringe=True)
    a.wood(0, 165, 150, 7, "#9A5A2E")                                 # the big wooden table
    a.box(0, 172, 148, 4, "#6E3A1E")
    for lx in (10, 138):
        a.rect(lx, 176, 6, 54, "#7A4A2A", "cyl", 0.5)
    a.rect(90, 165, 38, 60, "#2F6DB5", "flat", 0.5)                   # the striped runner
    for k, ry in enumerate(range(167, 224, 4)):
        a.box(91, ry, 36, 2, ("#E8432F", "#F4C542", "#3FA34D", "#F4EFE4")[k % 4])
    for sx, sy, sw in ((0, 205, 42), (140, 184, 34)):
        stool(a, sx, sy, sw, 40, "#2F6DB5", "#7A4A2A", pattern="#F4C542")
    a.ellipse(66, 158, 26, 12, "#3A3A3E", "sphere", 0.5)              # the molcajete
    a.rect(76, 150, 5, 12, "#F4EFE4", "cyl", 0.5)
    a.rect(64, 148, 12, 18, "#C8964A", "cyl", 0.5)
    for ux in (67, 70, 73):
        a.line([(ux, 148), (ux - 1, 138)], "#8A5A2E")
    a.ellipse(36, 160, 24, 9, "#C26A3A", "sphere", 0.5)
    for fx in (40, 46, 51):
        a.ellipse(fx, 156, 6, 6, a.rand.choice(("#D62E2A", "#F2C531")), "sphere", 0.5)
    a.poly([(4, 152), (30, 152), (27, 166), (7, 166)], "#C26A3A", "cyl")
    leaves(a, 17, 146, 32, 18, count=24)
    for _ in range(8):
        a.ellipse(a.rand.randrange(6, 28), a.rand.randrange(138, 152), 4, 4, "#E86FA8", "plain", 0)
    porcelain(a, 0, 132, 16, 26)
    leaves(a, 8, 104, 30, 56, ("#2F6A2A", "#3F7A2E", "#5E9B3A"), count=30, leaf=(10, 4))
    a.poly([(374, 200), (412, 200), (406, 235), (380, 235)], "#C26A3A", "cyl")
    leaves(a, 394, 186, 48, 34, ("#2F6A2A", "#3F7A2E", "#5E9B3A"), count=34, leaf=(10, 4))
    return save(a, "mexican")


# ======================================================================================= Middle Eastern: The Saffron Market
def saffron_market() -> Image.Image:
    a = canvas("#E8C08A", seed=404)
    cr.arabesque(a, 0, 0, FW, 110)
    for x0, x1, apex in ((-20, 104, 14), (96, 330, 2), (322, 438, 14)):  # the big arches
        pts = cr.arch_points(x0, x1, 60, apex, 200)
        a.shape(lambda d, pts=pts: d.polygon(pts, fill=255), "#E8C08A", "plain", 0)
        a.shape(lambda d, pts=pts: d.line(pts, fill=255, width=5), "#F2D9A8", "plain", 0)
        a.shape(lambda d, pts=pts: d.line(pts, fill=255, width=1), "#3F8F8C", "plain", 0)
    a.plaster(0, 60, FW, 135, "#E8C08A")
    for px0 in (85, 315):                                             # tiled pillars
        for ty in range(48, 146, 10):
            cr.zellige_star(a, px0, ty, 9)
            cr.zellige_star(a, px0 + 9, ty, 9)
        a.rect(px0 - 2, 44, 22, 5, "#F2D9A8", "flat", 0.5)

    # The doorway to the bazaar, the big ornate lantern, wall lanterns, the empty sign
    a.rect(0, 50, 46, 95, "#7A4A24", "flat", 0.5)
    for y in range(56, 145):
        for x in range(3, 42):
            a.put(x, y, "#E8A46A" if y < 90 else "#C9805A")
    for k, (sx, sy, sw, col) in enumerate(((4, 70, 14, "#C8402A"), (20, 64, 18, "#2F8F8C"), (6, 96, 12, "#F2C14E"), (24, 92, 14, "#C8402A"))):
        a.rect(sx, sy, sw, 26, col, "flat", 0.6)
        a.box(sx, sy, sw, 3, "#F4EFE4")
    a.ellipse(8, 112, 30, 22, "#9A6A42", "plain", 0)
    brass_lantern(a, 64, 40, 18, 40)
    brass_lantern(a, 119, 22, 12, 26)
    brass_lantern(a, 297, 22, 12, 26)
    empty_sign(a, 136, 17, 282, 45, "#7A4A24", "#F7E0B4", "#2F6DB5")
    for vx in (138, 278):
        vine(a, vx, 16, 26)

    # The shelf: six spice jars and three brass dallah
    a.wood(102, 86, 154, 5, "#7A4A24")
    for bx in (110, 246):
        a.rect(bx, 91, 4, 7, "#5A3218")
    for jx, inside in ((108, "#D6452B"), (123, "#8A9A4A"), (138, "#E8A21E"), (153, "#5E2E24"), (168, "#E8B85A"), (183, "#C8402A")):
        a.jar(jx, 62, 13, 86, inside, lid="#C9A06A", speckle=tone(inside, 0.75), fill_from=0.3)

    def dallah(x: int, top: int, base: int, w: int) -> None:
        h = base - top
        a.ellipse(x, top + h // 2, w, h // 2, "#E0AE3E")
        a.poly([(x + w // 4, top + h // 2 + 2), (x + w // 3, top + h // 3), (x + 2 * w // 3, top + h // 3),
                (x + 3 * w // 4, top + h // 2 + 2)], "#E0AE3E", "cyl")
        a.poly([(x + w // 3, top + h // 3), (x + w // 2, top + 3), (x + 2 * w // 3, top + h // 3)], "#F0C45A", "cyl")
        a.line([(x + 2, top + h // 2 + 3), (x - 6, top + h // 4), (x - 8, top + h // 4 - 2)], "#B8862E", 2)
        a.shape(lambda d: d.arc([x + w - 5, top + h // 3, x + w + 6, top + 3 * h // 4], -90, 90, fill=255, width=2), "#B8862E", "plain", 0)
    for dx, dt, dw in ((206, 70, 12), (222, 58, 16), (242, 64, 13)):
        dallah(dx, dt, 86, dw)

    # The onion-arch window at sunset, porcelain on the right shelves, the palm
    pts = cr.arch_points(260, 314, 96, 50, 132, onion=0.28)
    a.shape(lambda d: d.polygon(pts, fill=255), "#9A5A2E", "cyl", 0.5)
    inner = cr.arch_points(265, 309, 98, 57, 130, onion=0.28)
    mask = Image.new("L", (FW, FH), 0)
    ImageDraw.Draw(mask).polygon(inner, fill=255)
    mk = mask.load()
    for y in range(56, 131):
        for x in range(258, 316):
            if mk[x, y]:
                t = (y - 60) / 70
                a.put(x, y, tone("#F28A3C", 1 + 0.4 * t) if y < 112 else "#C96A3A")
    a.ellipse(282, 98, 14, 14, "#FFE08A", "plain", 0)
    a.shape(lambda d: d.chord([272, 84, 300, 112], 180, 360, fill=255), "#D9784A", "plain", 0)   # the dome
    for bx, bw, bh in ((264, 10, 26), (296, 12, 22), (276, 22, 14)):
        for y in range(130 - bh, 130):
            for x in range(bx, bx + bw):
                if mk[x, y]:
                    a.put(x, y, "#B8603A")
    leaves(a, 290, 122, 40, 10, ("#3F6B2A", "#4F7A33", "#6E8A3A"), count=16)
    for sy in (72, 104):
        a.wood(352, sy, 66, 4, "#7A4A24")
    for px, py, pw, ph in ((364, 48, 16, 24), (384, 50, 14, 22), (356, 84, 14, 20), (380, 82, 18, 22), (402, 86, 12, 18)):
        porcelain(a, px, py, pw, ph)
    vine(a, 354, 44, 50)
    leaves(a, 360, 50, 22, 22, count=16)
    a.poly([(320, 128), (346, 128), (342, 148), (324, 148)], "#D9A830", "cyl")
    a.rect(330, 96, 7, 32, "#9A6A3A", "cyl", 0.5)
    for ty in range(98, 128, 4):
        a.box(330, ty, 7, 1, "#6E4A2A")
    for ang, length in ((200, 34), (225, 30), (250, 24), (290, 24), (315, 30), (340, 34), (175, 26), (5, 26)):
        rad = math.radians(ang)
        prev = (333, 96)
        for k in range(1, length):
            t = k / length
            point = (round(333 + math.cos(rad) * k), round(96 - math.sin(rad) * k * 0.55 + 14 * t * t))
            a.line([prev, point], "#3F6B26", 2)
            if k % 2 == 0:
                for side in (-1, 1):
                    a.line([point, (point[0] + side * 2, point[1] + 5)], "#5E9B3A" if side < 0 else "#4C8A30", 1)
            prev = point

    # Tiled wainscot, the long counter with sacks, a dallah, flatbread and dates; the carved base below
    for ty in range(107, 145, 10):
        for tx in range(100, 335, 10):
            cr.zellige_star(a, tx, ty, 10)
    a.wood(55, 144, 280, 7, "#8E5A2E")
    a.poly([(56, 128), (80, 128), (77, 144), (59, 144)], "#D9A830", "cyl")
    leaves(a, 68, 116, 30, 26, count=22, leaf=(9, 4))
    a.ellipse(84, 137, 18, 8, "#F2E6CF", "sphere", 0.5)
    for dx in (87, 92, 97):
        a.ellipse(dx, 134, 5, 4, "#7A2A22", "sphere", 0.5)
    for sx, sw, top, grain in ((105, 40, 116, "#F4EFE6"), (140, 36, 124, "#E8B83A")):
        a.poly([(sx, 144), (sx + 1, top + 8), (sx + 6, top), (sx + sw - 6, top), (sx + sw - 1, top + 8), (sx + sw, 144)], "#C9A06A", "cyl")
        a.ellipse(sx + 3, top - 4, sw - 6, 9, grain, "sphere", 0.5)
    a.ellipse(150, 106, 22, 8, "#C8402A", "sphere", 0.5)
    a.poly([(148, 112), (172, 112), (170, 118), (150, 118)], "#C9A06A", "cyl")
    dallah(178, 104, 144, 18)
    for k, y in enumerate(range(140, 114, -3)):                       # two stacks of flatbread
        a.ellipse(198, y, 38, 8, "#E8C08A", "sphere", 0.45)
    for k, y in enumerate(range(140, 120, -3)):
        a.ellipse(237, y, 38, 8, "#E2B47A", "sphere", 0.45)
    a.ellipse(276, 137, 20, 8, "#4A4A4E", "sphere", 0.5)
    for dx in (279, 284, 289):
        a.ellipse(dx, 134, 5, 4, "#7A2A22", "sphere", 0.5)
    a.box(67, 151, 270, 46, "#F2D9A8")
    for nx in range(70, 334, 44):                                     # carved arches with tile between them
        cr.zellige_star(a, nx, 155, 8)
        cr.zellige_star(a, nx, 165, 8)
        cr.zellige_star(a, nx, 175, 8)
        pts = cr.arch_points(nx + 11, nx + 41, 170, 158, 196, onion=0.15)
        a.shape(lambda d, pts=pts: d.polygon(pts, fill=255), "#8E5A3A", "cyl", 0.5)
        a.shape(lambda d, pts=pts: d.line(pts, fill=255, width=2), "#D9A86B", "plain", 0)

    # The low carved table with a brass tea set, stools with tiled cushions, the side table, lantern, plants
    a.wood(0, 172, 85, 6, "#8E5A2E")
    a.rect(4, 178, 77, 52, "#7A4A24", "flat", 0.5)
    for k in range(4):
        a.shape(lambda d, k=k: d.arc([8 + k * 18, 182, 24 + k * 18, 200], 180, 360, fill=255, width=2), "#D9A86B", "plain", 0)
    dallah(12, 140, 172, 18)
    for cx in (34, 48, 60):
        a.rect(cx, 164, 9, 8, "#E0AE3E", "cyl")
        a.ellipse(cx - 1, 162, 11, 4, "#F0C45A", "plain", 0.5)
    a.poly([(0, 150), (16, 150), (14, 170), (2, 170)], "#C26A3A", "cyl")
    leaves(a, 8, 140, 22, 24, count=18)
    stool(a, 75, 184, 42, 40, "#2F6DB5", "#7A4A24", pattern="#E8A21E")
    a.ellipse(86, 179, 20, 7, "#F4EFE6", "sphere", 0.5)
    a.wood(335, 148, 83, 6, "#8E5A2E")
    a.rect(340, 154, 70, 56, "#7A4A24", "flat", 0.5)
    brass_lantern(a, 381, 120, 16, 30)
    for bx in (390, 404):
        a.ellipse(bx, 172 + (bx % 4), 14, 10, "#C8964A", "sphere", 0.5)
    stool(a, 362, 180, 30, 44, "#2F6DB5", "#7A4A24", pattern="#E8A21E")
    a.ellipse(366, 175, 22, 7, "#F4EFE6", "sphere", 0.5)
    a.poly([(398, 138), (418, 138), (418, 150), (400, 150)], "#C26A3A", "cyl")
    leaves(a, 410, 128, 26, 22, count=18)
    a.poly([(402, 200), (418, 200), (418, 234), (404, 234)], "#C26A3A", "cyl")
    leaves(a, 412, 188, 22, 28, count=18)

    # The stone floor and the rug
    a.box(0, 197, FW, FH - 197, "#C97A4A")
    for k, y in enumerate(range(197, FH, 9)):
        a.box(0, y, FW, 1, "#A35C34")
        for x in range((k % 2) * 14, FW, 28):
            a.box(x, y, 1, 9, "#A35C34")
    rug(a, (112, 350), (107, 355), 201, 231, "#C8392A", "#2F4F8C", "#F2C14E", fringe=True)
    return save(a, "middle_eastern")


KITCHENS = {"chinese": chinese, "mediterranean": golden_hearth, "mexican": joyful_kitchen, "middle_eastern": saffron_market}


def main() -> None:
    for name, draw in KITCHENS.items():
        draw()
        print("drew", name)


if __name__ == "__main__":
    main()
