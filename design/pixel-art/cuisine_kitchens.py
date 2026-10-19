"""Draft: four cuisine kitchens and their chefs, recreated from the team's concept art (2026-10-18).

One kitchen per cuisine family in the recipe data: Japanese (Asian), Mediterranean (European), Mexican (Latin
American) and Middle Eastern. Every one keeps the app's own title, "EverFlavor Kitchen" (the concepts used other
names). Drawn shape by shape like make_pixel_art.py, which calls SCENES and CHEF_VARIANTS when it runs.
"""
from __future__ import annotations

from collections.abc import Callable

from PIL import Image, ImageDraw

W, H = 240, 135
INK = "#3B2A25"


class Scene:
    """A backdrop plus the pieces that move when tapped ({name: (sprite, x, y)}, as kitchen_parts returns)."""

    def __init__(self, wall: str):
        self.img = Image.new("RGBA", (W, H), wall)
        self.d = ImageDraw.Draw(self.img)
        self.pieces: dict[str, tuple[Image.Image, int, int]] = {}

    def piece(self, name: str, draw: Callable[[ImageDraw.ImageDraw], None]) -> None:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw(ImageDraw.Draw(layer))
        box = layer.getbbox()
        if box:
            self.pieces[name] = (layer.crop(box), box[0], box[1])

    def parts(self) -> tuple[Image.Image, dict[str, tuple[Image.Image, int, int]]]:
        return self.img, self.pieces


def box(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, fill: str, outline: str | None = INK) -> None:
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=fill, outline=outline)


def speckle(d: ImageDraw.ImageDraw, color: str, top: int = 0, bottom: int = 96, step: int = 7) -> None:
    """A little plaster texture: a regular scatter of dots (no randomness, so the art is the same every run)."""
    for y in range(top + 2, bottom, step):
        for x in range((y * 3) % 11, W, 13):
            d.point((x, y), fill=color)


def bottle(c: ImageDraw.ImageDraw, x: int, y_base: int, h: int, body: str, cap: str, label: str | None = None) -> None:
    box(c, x, y_base - h, 6, h, body)
    box(c, x + 2, y_base - h - 4, 2, 4, body)
    box(c, x + 1, y_base - h - 6, 4, 2, cap)
    if label:
        box(c, x + 1, y_base - h // 2 - 2, 4, 4, label, None)
    c.point((x + 1, y_base - h + 2), fill="#FFFFFF")


def jar(c: ImageDraw.ImageDraw, x: int, y_base: int, w: int, h: int, inside: str, lid: str = "#A9783F") -> None:
    box(c, x, y_base - h, w, h, "#EDE8DE")
    box(c, x + 1, y_base - h + 3, w - 2, h - 4, inside, None)
    box(c, x + 1, y_base - h - 2, w - 2, 2, lid)
    c.line([x + 1, y_base - h + 1, x + 1, y_base - 2], fill="#FFFFFF")


def japanese() -> tuple[Image.Image, dict]:
    wood, wood_light, paper, grid = "#5B3A29", "#8A6142", "#FBF3E2", "#9C7A57"
    s = Scene("#E8D5B0")
    d = s.d
    speckle(d, "#DCC7A0")
    box(d, 0, 0, W, 6, wood, None)
    for bx in (0, 118, 236):
        box(d, bx, 0, 4, 96, wood, None)
    sx, sy, sw, sh = 150, 14, 76, 58                                  # shoji window
    box(d, sx - 3, sy - 3, sw + 6, sh + 6, wood, None)
    box(d, sx, sy, sw, sh, paper, None)
    for gx in range(sx + 9, sx + sw, 9):
        d.line([gx, sy, gx, sy + sh - 1], fill=grid)
    for gy in range(sy + 10, sy + sh, 10):
        d.line([sx, gy, sx + sw - 1, gy], fill=grid)
    box(d, sx + sw // 2 - 1, sy, 3, sh, wood, None)
    for shelf_y in (36, 64):
        box(d, 10, shelf_y, 100, 3, wood_light)
    s.piece("soy_1", lambda c: bottle(c, 16, 36, 14, "#3A1F1A", "#C0392B", "#E9C46A"))
    s.piece("soy_2", lambda c: bottle(c, 27, 36, 12, "#4A2A1E", "#C0392B", "#F4F1E8"))
    s.piece("sake", lambda c: bottle(c, 39, 36, 15, "#F4F1E8", "#2E5E8C", "#2E5E8C"))
    s.piece("cups", lambda c: (box(c, 52, 30, 7, 6, "#F4F1E8"), box(c, 61, 30, 7, 6, "#F4F1E8")))

    def donabe(c: ImageDraw.ImageDraw) -> None:                       # clay pot with its lid
        c.pieslice([18, 48, 46, 72], 180, 360, fill="#7A4A2E", outline=INK)
        box(c, 18, 60, 29, 4, "#5E3822")
        box(c, 30, 46, 4, 3, "#5E3822")
    s.piece("donabe", donabe)
    s.piece("bowls", lambda c: (c.pieslice([56, 54, 72, 66], 0, 180, fill="#F4F1E8", outline=INK),
                                c.pieslice([58, 50, 70, 60], 0, 180, fill="#F4F1E8", outline=INK)))
    s.piece("tea_tin", lambda c: (box(c, 80, 50, 10, 14, "#B5462F"), box(c, 80, 48, 10, 2, "#5B3A29")))

    box(d, 0, 96, W, 5, "#C9A57A")                                    # counter and shoji-style doors
    box(d, 0, 101, W, H - 101, wood, None)
    for cx in range(4, W, 40):
        box(d, cx, 105, 34, 26, paper, wood_light)
        for gx in range(cx + 8, cx + 34, 9):
            d.line([gx, 106, gx, 129], fill=grid)
        d.line([cx + 1, 117, cx + 32, 117], fill=grid)
    box(d, 18, 88, 50, 8, "#8F8780")                                  # stove and wok
    for k, (wx, wy) in enumerate([(30, 70), (37, 64), (44, 69), (36, 58)]):
        d.point([(wx, wy), (wx + 1, wy - 1)], fill="#FFFFFF" if k % 2 else "#EDE6DA")

    def wok(c: ImageDraw.ImageDraw) -> None:
        c.pieslice([24, 72, 58, 96], 0, 180, fill="#2B2B2B", outline=INK)
        c.line([24, 84, 10, 80], fill="#6B4A2F", width=2)
    s.piece("wok", wok)

    def rice(c: ImageDraw.ImageDraw) -> None:
        box(c, 120, 76, 20, 20, "#EFE6D2")
        box(c, 125, 81, 10, 8, "#C0392B", None)
        box(c, 129, 83, 2, 4, "#FFFFFF", None)
        c.pieslice([144, 86, 158, 98], 180, 360, fill="#FFFFFF", outline=INK)
    s.piece("rice", rice)

    def bonsai(c: ImageDraw.ImageDraw) -> None:
        box(c, 196, 88, 26, 8, "#2C4A7A")
        c.line([209, 88, 206, 80, 212, 74, 208, 68], fill="#6B4A2F", width=2)
        for fx, fy, fw in [(194, 62, 18), (206, 56, 18), (214, 66, 14), (200, 72, 12)]:
            c.ellipse([fx, fy, fx + fw, fy + 8], fill="#3F7A33", outline=INK)
    s.piece("bonsai", bonsai)
    return s.parts()


def mediterranean() -> tuple[Image.Image, dict]:
    wood, stone, stone_line = "#6B4A2F", "#E7DCC8", "#CDBDA3"
    s = Scene(stone)
    d = s.d
    for row, y in enumerate(range(6, 96, 9)):                         # stone wall
        for x in range(-8 if row % 2 else 0, W, 18):
            d.rectangle([x, y, x + 17, y + 8], outline=stone_line)
    box(d, 0, 0, W, 6, wood, None)
    box(d, 136, 0, 5, 96, wood, None)
    wx, wy, ww, wh = 172, 18, 44, 42                                  # window on green hills
    box(d, wx, wy, ww, wh, "#9FD3F0", None)
    d.pieslice([wx - 10, wy + 22, wx + 30, wy + 60], 180, 360, fill="#7FA65A")
    d.pieslice([wx + 14, wy + 26, wx + 56, wy + 64], 180, 360, fill="#5E8A43")
    box(d, wx, wy + wh - 4, ww, 4, "#5E8A43", None)
    d.ellipse([wx + 30, wy + 14, wx + 34, wy + 30], fill="#3F6B2E")   # a cypress
    for bx, by, bw, bh in [(wx - 3, wy - 3, ww + 6, 3), (wx - 3, wy + wh, ww + 6, 4), (wx - 3, wy, 3, wh),
                           (wx + ww, wy, 3, wh), (wx + ww // 2 - 1, wy, 2, wh), (wx, wy + wh // 2 - 1, ww, 2)]:
        box(d, bx, by, bw, bh, wood, None)
    box(d, wx - 6, wy + wh + 4, ww + 12, 3, "#B08A5F", None)
    for shelf_y in (32, 58):
        box(d, 8, shelf_y, 112, 3, "#8A6142")
    for k, (x, h, body) in enumerate([(12, 18, "#5E7D2E"), (21, 15, "#7E9A3A"), (30, 12, "#A9B44A")]):
        s.piece(f"oil_{k}", lambda c, x=x, h=h, body=body: bottle(c, x, 32, h, body, "#2F2F2F", "#F2C14E"))
    for k, (x, inside) in enumerate([(44, "#D9C27A"), (58, "#6E9B3E"), (72, "#C8A27A"), (86, "#B5462F")]):
        s.piece(f"spice_{k}", lambda c, x=x, inside=inside: jar(c, x, 32, 11, 13, inside))
    for k, (x, inside) in enumerate([(12, "#C9B36B"), (32, "#5E8A43"), (52, "#8FA05A"), (72, "#D8C9A8")]):
        s.piece(f"herb_jar_{k}", lambda c, x=x, inside=inside: jar(c, x, 58, 15, 17, inside))

    def garlic(c: ImageDraw.ImageDraw) -> None:
        c.line([152, 4, 152, 52], fill="#B08A5F")
        for k, gy in enumerate(range(10, 52, 6)):
            gx = 148 + (k % 2) * 4
            c.ellipse([gx, gy, gx + 6, gy + 6], fill="#F4EFE6", outline=INK)
    s.piece("garlic", garlic)

    def copper_pan(c: ImageDraw.ImageDraw) -> None:
        c.line([104, 61, 104, 66], fill=INK)
        c.ellipse([96, 66, 112, 82], fill="#C46A2C", outline=INK)
        c.ellipse([99, 69, 109, 79], fill="#D98C4E")
    s.piece("copper_pan", copper_pan)

    box(d, 0, 96, W, 5, "#D8CBB2")                                    # counter on a stone base
    box(d, 0, 101, W, H - 101, "#8F8577", None)
    for row, y in enumerate(range(101, H, 8)):
        for x in range(-10 if row % 2 else 0, W, 20):
            d.rectangle([x, y, x + 19, y + 7], fill="#A79D8D", outline="#6E6658")
    box(d, 16, 88, 52, 8, "#8F8780")
    s.piece("copper_pot", lambda c: (box(c, 22, 72, 22, 16, "#C46A2C"), box(c, 20, 72, 26, 3, "#A85620"),
                                     c.line([25, 76, 25, 85], fill="#E8A26A")))
    s.piece("saucepan", lambda c: (box(c, 50, 78, 14, 10, "#C46A2C"), c.line([64, 80, 74, 78], fill=INK, width=2)))
    s.piece("tomatoes", lambda c: [c.ellipse([x, 88, x + 7, 95], fill="#D9483B", outline=INK) for x in (96, 103, 110)])

    def herbs(c: ImageDraw.ImageDraw) -> None:
        box(c, 206, 84, 16, 12, "#C8743C")
        for lx, ly in [(203, 72), (209, 66), (215, 70), (219, 64), (212, 60)]:
            c.ellipse([lx, ly, lx + 6, ly + 12], fill="#4F8A3A", outline=INK)
    s.piece("basil_pot", herbs)
    return s.parts()


def mexican() -> tuple[Image.Image, dict]:
    s = Scene("#EDA43F")
    d = s.d
    speckle(d, "#E39A35")
    flags = ["#D63B3B", "#2E86C1", "#3FA34D", "#E86FA8", "#F2C14E"]
    d.line([0, 3, W, 3], fill=INK)                                   # papel picado
    for k, x in enumerate(range(4, W, 22)):
        box(d, x, 3, 15, 11, flags[k % len(flags)], None)
        for hx in range(x + 3, x + 13, 4):
            d.point([(hx, 7), (hx + 1, 9)], fill="#EDA43F")
        for zx in range(x, x + 15, 3):
            d.point((zx, 13), fill="#EDA43F")
    for k in range(70, 96, 8):                                        # talavera tiles
        for x in range(0, W, 8):
            box(d, x, k, 8, 8, "#F4EFE4", "#C9C2B2")
            d.polygon([(x + 4, k + 1), (x + 7, k + 4), (x + 4, k + 7), (x + 1, k + 4)], fill="#1F5FA8")
            d.point((x + 4, k + 4), fill="#F2C14E")
    wx, wy, ww, wh = 168, 18, 48, 50                                  # painted window, shutters open
    box(d, wx, wy, ww, wh, "#8FD1F2", None)
    d.polygon([(wx, wy + 34), (wx + 18, wy + 26), (wx + 34, wy + 32), (wx + ww, wy + 24), (wx + ww, wy + wh),
               (wx, wy + wh)], fill="#C99A5B")
    box(d, wx, wy + 40, ww, 10, "#E6C27A", None)
    box(d, wx + 30, wy + 30, 4, 14, "#3FA34D", None)
    box(d, wx + 26, wy + 34, 4, 3, "#3FA34D", None)
    box(d, wx + 34, wy + 32, 4, 3, "#3FA34D", None)
    for bx, by, bw, bh, color in [(wx - 4, wy - 4, ww + 8, 4, "#2E86C1"), (wx - 4, wy + wh, ww + 8, 4, "#2E86C1"),
                                  (wx - 4, wy, 4, wh, "#D63B3B"), (wx + ww, wy, 4, wh, "#D63B3B")]:
        box(d, bx, by, bw, bh, color, None)
    for sx in (wx - 16, wx + ww + 4):                                 # the open shutters
        box(d, sx, wy, 12, wh, "#2E8B87")
        box(d, sx + 3, wy + 6, 6, 14, "#D63B3B", None)
        box(d, sx + 3, wy + 28, 6, 14, "#F2C14E", None)
    for shelf_y in (40, 66):
        box(d, 6, shelf_y, 112, 4, "#2E86C1")

    def olla(c: ImageDraw.ImageDraw, x: int, y_base: int, w: int) -> None:
        c.ellipse([x, y_base - w + 2, x + w, y_base], fill="#B5562B", outline=INK)
        box(c, x + w // 2 - 3, y_base - w, 6, 3, "#9C4422")
        c.line([x + 2, y_base - w // 2, x + w - 2, y_base - w // 2], fill="#F4EFE4")
        for px in range(x + 4, x + w - 2, 4):
            c.point((px, y_base - w // 2 + 2), fill="#2E8B87")
    for k, (x, w) in enumerate([(10, 20), (34, 18), (56, 16), (76, 18)]):
        s.piece(f"olla_{k}", lambda c, x=x, w=w: olla(c, x, 40, w))
    s.piece("olla_big", lambda c: olla(c, 10, 66, 22))

    def corn(c: ImageDraw.ImageDraw) -> None:
        box(c, 38, 56, 22, 10, "#B08A5F")
        for cx in (40, 46, 52):
            c.ellipse([cx, 46, cx + 6, 60], fill="#F2C14E", outline=INK)
            c.line([cx + 3, 58, cx + 6, 62], fill="#3FA34D")
    s.piece("corn", corn)

    def chilies(c: ImageDraw.ImageDraw) -> None:
        box(c, 64, 58, 20, 8, "#B08A5F")
        for cx in range(65, 82, 4):
            c.ellipse([cx, 52, cx + 4, 60], fill="#D63B3B", outline=INK)
    s.piece("chilies", chilies)
    s.piece("beans", lambda c: (box(c, 88, 52, 18, 14, "#C9A46B"),
                                [c.point((bx, 54), fill="#5A2E22") for bx in range(90, 104, 2)]))

    box(d, 0, 96, W, 5, "#D9C9A8")                                    # counter, painted cabinets, range
    box(d, 0, 101, W, H - 101, "#7A4A2E", None)
    for k, cx in enumerate(range(4, W, 40)):
        box(d, cx, 105, 34, 26, "#C8432F" if k % 2 else "#2E8B87", "#5A2E22")
        box(d, cx + 15, 116, 4, 2, "#F2C14E")
    box(d, 8, 84, 54, 12, "#8F8780")
    for kx in range(14, 58, 10):
        d.ellipse([kx, 98, kx + 5, 103], fill="#3B3B3B")
    s.piece("pot", lambda c: (box(c, 16, 70, 18, 14, "#B8B2AC"), box(c, 14, 70, 22, 3, "#8F8780")))
    s.piece("produce", lambda c: [c.ellipse([x, 86, x + 9, 95], fill=col, outline=INK)
                                  for x, col in [(96, "#3FA34D"), (106, "#D63B3B"), (116, "#8E3B5A")]])

    def cactus(c: ImageDraw.ImageDraw) -> None:
        box(c, 202, 84, 18, 12, "#F4EFE4")
        c.polygon([(206, 87), (211, 85), (216, 87), (211, 92)], fill="#1F5FA8")
        box(c, 208, 60, 6, 24, "#3FA34D")
        box(c, 202, 66, 4, 10, "#3FA34D")
        box(c, 216, 64, 4, 12, "#3FA34D")
        c.ellipse([208, 56, 213, 61], fill="#E86FA8", outline=INK)
    s.piece("cactus", cactus)
    return s.parts()


def middle_eastern() -> tuple[Image.Image, dict]:
    tile = ["#1E7A8C", "#D9822B", "#F4EFE4"]
    s = Scene("#EBCB97")
    d = s.d
    speckle(d, "#E2BD84")

    def tiles(x0: int, y0: int, w: int, h: int) -> None:
        for y in range(y0, y0 + h, 4):
            for x in range(x0, x0 + w, 4):
                box(d, x, y, 4, 4, tile[(x // 4 + y // 4) % 3], None)
    tiles(0, 0, W, 6)
    d.polygon([(8, 96), (8, 30), (40, 10), (66, 6), (92, 10), (124, 30), (124, 96)], fill="#E2BD84")   # alcove
    d.line([(8, 30), (40, 10), (66, 6), (92, 10), (124, 30)], fill="#1E7A8C", width=3)
    for shelf_y in (36, 62):
        box(d, 14, shelf_y, 104, 3, "#8A6142")
    for k, (x, inside) in enumerate([(18, "#C0392B"), (31, "#5E8A43"), (44, "#F2C14E"), (57, "#7A4A2E"),
                                     (70, "#D9822B"), (83, "#C8A27A")]):
        s.piece(f"spice_{k}", lambda c, x=x, inside=inside: jar(c, x, 36, 10, 14, inside))

    def dallah(c: ImageDraw.ImageDraw, x: int) -> None:            # brass coffee pot
        c.ellipse([x, 48, x + 14, 62], fill="#D9A830", outline=INK)
        box(c, x + 5, 42, 5, 7, "#D9A830")
        c.polygon([(x + 5, 42), (x + 7, 37), (x + 10, 42)], fill="#A87A1E", outline=INK)
        c.line([x + 1, 52, x - 6, 44], fill="#A87A1E", width=2)
        c.arc([x + 10, 46, x + 20, 58], -90, 90, fill=INK)
    for k, x in enumerate((30, 52, 74)):
        s.piece(f"dallah_{k}", lambda c, x=x: dallah(c, x))

    wx, wy, ww = 168, 22, 48                                          # arched window at sunset
    for i in range(54):
        t = i / 53
        color = tuple(int(a * (1 - t) + b * t) for a, b in zip((236, 132, 84), (246, 204, 140)))   # sunset, red-orange to gold
        d.line([wx, wy + i, wx + ww - 1, wy + i], fill=color)
    for bx, bw, bh in [(wx + 2, 10, 12), (wx + 14, 8, 20), (wx + 24, 14, 10), (wx + 38, 8, 16)]:
        box(d, bx, wy + 54 - bh, bw, bh, "#B8673A", None)
    d.pieslice([wx + 24, wy + 38, wx + 38, wy + 50], 180, 360, fill="#B8673A")
    box(d, wx + 16, wy + 26, 3, 8, "#B8673A", None)
    d.polygon([(wx - 4, wy + 6), (wx + ww // 2, wy - 20), (wx + ww + 4, wy + 6), (wx + ww + 4, wy - 22),
               (wx - 4, wy - 22)], fill="#EBCB97")                    # the pointed arch's top
    d.line([(wx - 4, wy + 6), (wx + ww // 2, wy - 20), (wx + ww + 4, wy + 6)], fill="#7A4B22", width=3)
    box(d, wx - 4, wy + 6, 4, 48, "#7A4B22", None)
    box(d, wx + ww, wy + 6, 4, 48, "#7A4B22", None)
    box(d, wx - 6, wy + 54, ww + 12, 4, "#C9A46B", None)
    tiles(132, 64, 30, 32)
    tiles(222, 64, 18, 32)

    box(d, 0, 96, W, 5, "#D8C29A")                                    # counter, tiled band, arched doors
    box(d, 0, 101, W, H - 101, "#7A4B22", None)
    tiles(0, 101, W, 4)
    for cx in range(4, W, 40):
        box(d, cx, 108, 34, 24, "#9A6230", "#5A3518")
        d.arc([cx + 8, 112, cx + 26, 130], 180, 360, fill="#D9A830")
    for k, (x, grain) in enumerate([(10, "#F4EFE6"), (32, "#E2B33C")]):
        s.piece(f"sack_{k}", lambda c, x=x, grain=grain: (box(c, x, 78, 18, 18, "#C9A46B"),
                                                          c.ellipse([x + 1, 74, x + 16, 82], fill=grain, outline=INK)))
    s.piece("flatbread", lambda c: [c.ellipse([96, y, 128, y + 6], fill="#E8C88F", outline=INK)
                                    for y in range(90, 76, -3)])

    def palm(c: ImageDraw.ImageDraw) -> None:
        c.ellipse([200, 82, 222, 96], fill="#D9A830", outline=INK)
        box(c, 210, 64, 3, 20, "#7A4B22", None)
        for ex, ey in [(196, 60), (226, 60), (200, 52), (222, 52), (211, 48)]:
            c.line([211, 64, ex, ey], fill="#3F7A33", width=3)
    s.piece("palm", palm)
    return s.parts()


SCENES = {"japanese": japanese, "mediterranean": mediterranean, "mexican": mexican, "middle_eastern": middle_eastern}

# ---------- The chefs: the same faces and moods as the classic chef, with each kitchen's headwear and clothes ----------
# Rows 0-8 are the head (replacing the toque), rows 16-23 the clothes; H hair, N/n navy, P red bandana, C/W keffiyeh,
# A agal (the black cord), U blue, G green, Y yellow thread.
CHEF_EXTRA_COLORS = {"H": "#2B2B33", "N": "#2C3E6B", "n": "#22305A", "P": "#C9302C", "C": "#B3262E", "A": "#1F1F1F",
                     "U": "#2E86C1", "G": "#3FA34D", "Y": "#F2C14E"}
HEADS = {
    "japanese": [   # hachimaki headband with a red mark and its knot
        "........................",
        "........................",
        "........................",
        "......KKKKKKKKKKKK......",
        ".....KHHHHHHHHHHHHK.....",
        "....KHHHHHHHHHHHHHHK....",
        "....KWWWWWWWWWWWWWWKRK..",
        "....KWWPWWWWWWWWWWWKKRK.",
        ".....KSSSSSSSSSSSSK.....",
    ],
    "mexican": [   # red bandana with white dots
        "........................",
        "........................",
        "........................",
        "......KKKKKKKKKKKK......",
        ".....KHHHHHHHHHHHHK.....",
        "....KPPPPPPPPPPPPPPK....",
        "....KPWPPPWPPPWPPPWKPK..",
        "....KPPPPPPPPPPPPPPKKPK.",
        ".....KSSSSSSSSSSSSK.....",
    ],
    "middle_eastern": [   # keffiyeh in red and white checks, held by the agal
        "........................",
        "........................",
        "......KKKKKKKKKKKK......",
        ".....KWCWCWCWCWCWCK.....",
        "....KAAAAAAAAAAAAAAK....",
        "...KCWCWCWCWCWCWCWCWK...",
        "...KWCWCWCWCWCWCWCWCK...",
        "...KCWKKKKKKKKKKKKWCK...",
        "...KWKSSSSSSSSSSSSKWK...",
    ],
}
TORSOS = {
    "japanese": [   # navy samue jacket with a white collar
        "......KKSSSSSSSSKK......",
        "....KKKKWNNNNNNWKKKK....",
        "...KNNNNKWNNNNWKNNNNK...",
        "..KNNNNNNKWNNWKNNNNNNK..",
        "..KNNNNNNNKWWKNNNNNNNK..",
        "..KNNnNNNNNWNNNNNnNNNK..",
        "..KNNnNNNNNNNNNNNnNNNK..",
        "..KKKKKKKKKKKKKKKKKKKK..",
    ],
    "mexican": [   # white shirt, embroidered band, red neckerchief
        "......KKSSSSSSSSKK......",
        "....KKKKRRRRRRRRKKKK....",
        "...KWWWWKRRRRRRKWWWWK...",
        "..KWWWWWWKRRRRKWWWWWWK..",
        "..KGYUPGYUKRRKUYGPUYGK..",
        "..KWWwWWWWWBWWWWWwWWWK..",
        "..KWWwWWWWWWWWWWWwWWWK..",
        "..KKKKKKKKKKKKKKKKKKKK..",
    ],
    "middle_eastern": [   # white thobe
        "......KKSSSSSSSSKK......",
        "....KKKKWWWWWWWWKKKK....",
        "...KWWWWKWWWWWWKWWWWK...",
        "..KWWWWWWKWWWWKWWWWWWK..",
        "..KWWWWWWWKWWKWWWWWWWK..",
        "..KWWwWWWWWBWWWWWwWWWK..",
        "..KWWwWWWWWWWWWWWwWWWK..",
        "..KKKKKKKKKKKKKKKKKKKK..",
    ],
}
NO_MUSTACHE = {"japanese", "mexican"}   # their concepts are clean-shaven


def chef_rows(variant: str, face: list[str]) -> list[str]:
    """The chef's 24 rows for one kitchen and one mood (the face rows come from make_pixel_art.CHEF_FACES)."""
    face = [row.replace("M", "S") for row in face] if variant in NO_MUSTACHE else face
    rows = HEADS[variant] + face + TORSOS[variant]
    if variant == "middle_eastern":   # the keffiyeh falls beside the face to the shoulders
        rows = [row if not 9 <= y <= 18 else
                row[:1] + "K" + ("CW" if y % 2 else "WC") + row[4:20] + ("WC" if y % 2 else "CW") + "K" + row[23:]
                for y, row in enumerate(rows)]
    assert len(rows) == 24 and all(len(r) == 24 for r in rows), variant
    return rows


CHEF_VARIANTS = list(HEADS)
