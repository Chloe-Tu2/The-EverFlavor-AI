"""Draw EverFlavor's pixel art: the kitchen scenes (one per theme), the chef guides and the icons.

Everything is drawn from code, pixel by pixel, so the art can be changed and redrawn by anyone:
edit a palette or a sprite below and run, from the project folder,

    python design/pixel-art/make_pixel_art.py

It writes small native-size PNGs and the interactive scene files to design/pixel-art/assets/ (the app scales
them up with sharp pixels) and enlarged previews to design/pixel-art/previews/ for looking at them.
Needs only Pillow (already in config/requirements.txt).
"""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw

OUT = Path(__file__).resolve().parent / "assets"
PREVIEW = Path(__file__).resolve().parent / "previews"
# The team's own art (the detailed concept style): originals/<scene>.png replaces that scene's drawing, and
# originals/<scene>.hotspots.json lists the objects that move when tapped: [{"name", "x", "y", "w", "h"}, ...]
# in the picture's pixels. originals/chef_<variant>.png (variant: classic, japanese, mexican, middle_eastern)
# replaces that chef in every mood. See originals/README.md.
ORIGINALS = Path(__file__).resolve().parent / "originals"


def original_parts(name: str) -> tuple[Image.Image, dict[str, tuple[Image.Image, int, int]]] | None:
    """The team's picture for one scene and its tappable objects, or None when there is no picture yet."""
    picture = ORIGINALS / f"{name}.png"
    if not picture.exists():
        return None
    img = Image.open(picture).convert("RGBA")
    spots = ORIGINALS / f"{name}.hotspots.json"
    pieces = {}
    for spot in json.loads(spots.read_text(encoding="utf-8")) if spots.exists() else []:
        x, y, w, h = (int(spot[k]) for k in ("x", "y", "w", "h"))
        pieces[spot["name"]] = (img.crop((x, y, x + w, y + h)), x, y)   # drawn again over itself, so it can move
    return img, pieces


def original_chef(variant: str) -> Image.Image | None:
    picture = ORIGINALS / f"chef_{variant}.png"
    return Image.open(picture).convert("RGBA") if picture.exists() else None
W, H = 240, 135   # 16:9; the app scales it to the window

# One palette per theme. "classic" is Eva's cream, brown and pink (the default).
THEMES = {
    "classic": {   # Eva's cooking-game colors, daytime
        "wall": "#FFF1E6", "tile": "#FCE3D3", "tile_line": "#F3D2BE", "sky": ["#BFE6FF", "#DDF2FF"],
        "wood": "#A0522D", "wood_dark": "#8B4513", "wood_light": "#D9A679", "counter": "#F6D7B8",
        "accent": "#FFB6C1", "accent_dark": "#E68AA0", "steel": "#C9C2BC", "steel_dark": "#8F8780",
        "outline": "#4A2C2A", "light": None, "sun": "#FFF3B0",
    },
    "morning": {   # sunrise through the window, butter and peach
        "wall": "#FFF4D6", "tile": "#FBE7B5", "tile_line": "#F1D592", "sky": ["#FF9F7A", "#FFD39A"],
        "wood": "#B9773E", "wood_dark": "#8A5427", "wood_light": "#E6B77C", "counter": "#FCE2B0",
        "accent": "#F2C14E", "accent_dark": "#D9A030", "steel": "#D8D1C4", "steel_dark": "#9A9283",
        "outline": "#4A3122", "light": None, "sun": "#FFE680",
    },
    "night": {   # lamplight, moon in the window
        "wall": "#3A2E4A", "tile": "#433556", "tile_line": "#2F2540", "sky": ["#0F1633", "#1C2752"],
        "wood": "#6E4128", "wood_dark": "#4E2D1C", "wood_light": "#946446", "counter": "#5A4660",
        "accent": "#FF8FAB", "accent_dark": "#D9668A", "steel": "#8E8AA0", "steel_dark": "#5E5A70",
        "outline": "#1A1424", "light": "#FFD98A", "sun": "#F4F1D0",
    },
    "basil": {   # fresh greens, herb garden
        "wall": "#EEF5E6", "tile": "#DDEBCF", "tile_line": "#C8DDB6", "sky": ["#AEE3F0", "#D8F2F7"],
        "wood": "#8C6A43", "wood_dark": "#6A4E30", "wood_light": "#C4A278", "counter": "#E2EBD3",
        "accent": "#5E9B4A", "accent_dark": "#457536", "steel": "#C5CBC0", "steel_dark": "#8B9286",
        "outline": "#2F3A26", "light": None, "sun": "#FFF3B0",
    },
}


def rect(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, fill: str, outline: str | None = None) -> None:
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=fill, outline=outline)


def kitchen_parts(theme: str) -> tuple[Image.Image, dict[str, tuple[Image.Image, int, int]]]:
    """The kitchen as a backdrop plus the pieces that can move (for the interactive scene in the app).

    Returns the backdrop (wall, window, shelves, counter, stove, board) and {name: (sprite, x, y)} for each
    piece: the curtains, every jar, the pans, the lamp, the pot and its lid, the tomato, the herbs, the plant.
    """
    p = THEMES[theme]
    img = Image.new("RGBA", (W, H), p["wall"])
    d = ImageDraw.Draw(img)
    o = p["outline"]
    pieces: dict[str, tuple[Image.Image, int, int]] = {}

    def piece(name: str, draw) -> None:
        """Draw one movable piece on its own transparent layer and keep the part that has pixels."""
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw(ImageDraw.Draw(layer))
        box = layer.getbbox()
        if box:
            pieces[name] = (layer.crop(box), box[0], box[1])

    # Tiled backsplash behind the counter
    for y in range(70, 96, 6):
        for x in range(0, W, 8):
            rect(d, x + (4 if (y // 6) % 2 else 0), y, 8, 6, p["tile"], p["tile_line"])

    # Window with sky (sun, moon or clouds by theme)
    wx, wy, ww, wh = 152, 12, 54, 44
    top, bottom = p["sky"]
    for i in range(wh):
        t = i / (wh - 1)
        c = tuple(int(int(top[k:k + 2], 16) * (1 - t) + int(bottom[k:k + 2], 16) * t) for k in (1, 3, 5))
        d.line([wx, wy + i, wx + ww - 1, wy + i], fill=c)
    if theme == "night":
        d.ellipse([wx + 34, wy + 6, wx + 44, wy + 16], fill=p["sun"])          # moon
        d.ellipse([wx + 37, wy + 5, wx + 47, wy + 15], fill=top)               # its shadow: a crescent
        for sx, sy in [(6, 6), (14, 20), (24, 9), (9, 30), (28, 26), (44, 34), (20, 36)]:
            d.point((wx + sx, wy + sy), fill="#FFFFFF")
    elif theme == "morning":
        d.ellipse([wx + 18, wy + 28, wx + 36, wy + 46], fill=p["sun"])         # rising sun, cut by the sill
    else:
        d.ellipse([wx + 36, wy + 5, wx + 46, wy + 15], fill=p["sun"])
        for cx, cy in [(8, 22), (26, 30)]:                                      # two clouds
            rect(d, wx + cx, wy + cy, 14, 4, "#FFFFFF")
            rect(d, wx + cx + 3, wy + cy - 3, 8, 3, "#FFFFFF")
    rect(d, wx - 3, wy - 3, ww + 6, 3, p["wood_dark"])                         # frame
    rect(d, wx - 3, wy + wh, ww + 6, 4, p["wood_dark"])
    rect(d, wx - 3, wy, 3, wh, p["wood_dark"])
    rect(d, wx + ww, wy, 3, wh, p["wood_dark"])
    rect(d, wx + ww // 2 - 1, wy, 2, wh, p["wood_dark"])                       # cross bars
    rect(d, wx, wy + wh // 2 - 1, ww, 2, p["wood_dark"])
    rect(d, wx - 6, wy + wh + 4, ww + 12, 3, p["wood_light"])                  # sill

    def curtain(px: int):
        def draw(c: ImageDraw.ImageDraw) -> None:
            rect(c, px, wy - 2, 12, wh + 6, p["accent"])
            for k in range(0, wh + 6, 4):
                c.point((px + 6, wy - 2 + k), fill=p["accent_dark"])
        return draw
    piece("curtain_left", curtain(wx - 2))
    piece("curtain_right", curtain(wx + ww - 10))

    # Two shelves with jars
    jar_colors = ["#D9483B", "#F2C14E", "#5E9B4A", "#C8743C", "#E8E1D5", "#8E5A9B"]
    for row, sy in enumerate((26, 50)):
        rect(d, 14, sy, 104, 3, p["wood"], o)
        x = 18
        for j in range(7):
            jh = 9 + (j * 3 + row * 2) % 6
            jw = 8 + (j + row) % 3 * 2
            color = jar_colors[(j + row * 3) % len(jar_colors)]

            def jar(c: ImageDraw.ImageDraw, x=x, jh=jh, jw=jw, color=color, sy=sy) -> None:
                rect(c, x, sy - jh, jw, jh, color, o)
                rect(c, x + 1, sy - jh - 2, jw - 2, 2, p["wood_light"], o)      # lid
                c.line([x + 2, sy - jh + 3, x + 2, sy - 3], fill="#FFFFFF")      # glint
            piece(f"jar_{row}_{j}", jar)
            x += jw + 5
            if x > 108:
                break

    # Pans hanging from a rail between the shelves and the window
    rect(d, 124, 14, 22, 2, p["steel_dark"])
    for k, (px, r) in enumerate([(127, 5), (136, 4), (144, 3)]):
        def pan(c: ImageDraw.ImageDraw, k=k, px=px, r=r) -> None:
            c.line([px, 16, px, 22 + k * 2], fill=p["steel_dark"])
            c.ellipse([px - r, 22 + k * 2, px + r, 22 + k * 2 + 2 * r], fill=p["steel"], outline=o)
        piece(f"pan_{k}", pan)

    # Hanging lamp; at night it lights a cone on the wall
    if p["light"]:
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).polygon([(122, 30), (86, 96), (160, 96)], fill=p["light"] + "38")
        img.alpha_composite(glow)
        d = ImageDraw.Draw(img)

    def lamp(c: ImageDraw.ImageDraw) -> None:
        c.line([123, 0, 123, 22], fill=o)
        rect(c, 117, 22, 13, 5, p["accent_dark"], o)
        c.point((123, 28), fill=p["light"] or "#FFF3B0")
    piece("lamp", lamp)

    # Counter and cabinets
    rect(d, 0, 96, W, 5, p["counter"], o)
    rect(d, 0, 101, W, H - 101, p["wood"])
    for cx in range(4, W, 40):
        rect(d, cx, 105, 34, 26, p["wood_light"], p["wood_dark"])
        rect(d, cx + 15, 116, 4, 2, p["steel"], o)                             # handle

    # Stove with a pot, its lid and steam
    rect(d, 24, 88, 48, 8, p["steel_dark"], o)
    for bx in (30, 54):
        rect(d, bx, 86, 12, 2, "#2B2B2B")
    steam = "#FFFFFF" if theme != "classic" else "#D8CFC8"
    for sx, sy in [(31, 66), (36, 61), (41, 64), (34, 56), (40, 53)]:
        d.point([(sx, sy), (sx + 1, sy - 1)], fill=steam)
    piece("pot", lambda c: rect(c, 27, 74, 20, 12, p["accent"], o))

    def lid(c: ImageDraw.ImageDraw) -> None:
        rect(c, 25, 74, 24, 3, p["accent_dark"], o)
        rect(c, 35, 71, 4, 3, p["accent_dark"], o)
    piece("lid", lid)

    # Cutting board with a tomato, a carrot and basil
    rect(d, 92, 91, 40, 5, p["wood_light"], o)

    def tomato(c: ImageDraw.ImageDraw) -> None:
        c.ellipse([97, 84, 105, 92], fill="#D9483B", outline=o)
        rect(c, 100, 83, 3, 2, "#5E9B4A")
    piece("tomato", tomato)

    def herbs(c: ImageDraw.ImageDraw) -> None:
        c.polygon([(110, 90), (124, 87), (124, 89)], fill="#E8862E", outline=o)    # carrot
        rect(c, 124, 86, 3, 2, "#5E9B4A")
        for lx, ly in [(116, 84), (119, 82), (113, 82)]:                           # basil leaves
            c.ellipse([lx, ly, lx + 4, ly + 3], fill="#5E9B4A", outline=o)
    piece("herbs", herbs)

    # Plant in a pot on the counter's right
    def plant(c: ImageDraw.ImageDraw) -> None:
        rect(c, 214, 84, 14, 12, "#C8743C", o)
        for lx, ly in [(212, 76), (218, 70), (224, 75), (215, 66), (226, 66), (220, 62)]:
            c.ellipse([lx, ly, lx + 6, ly + 9], fill="#5E9B4A", outline=o)
    piece("plant", plant)
    return img, pieces


def kitchen(theme: str) -> Image.Image:
    """The whole kitchen in one picture: the backdrop with every piece in its place."""
    img, pieces = kitchen_parts(theme)
    for sprite, x, y in pieces.values():
        img.alpha_composite(sprite, (x, y))
    return img.convert("RGB")


# The chef, 24 x 24. K outline, W white, w shade, S skin, s cheek, M mustache, R neckerchief,
# B button, E eye shine. Rows 9-15 change with the mood.
CHEF_BODY = [
    "........KKKKKKKK........",
    "......KKWWWWWWWWKK......",
    ".....KWWWWWWWWWWWWK.....",
    "....KWWWWWWWWWWWWWWK....",
    "....KWWWWWWWWWWWWwWK....",
    ".....KWWWWWWWWWWwWK.....",
    ".....KwwwwwwwwwwwwK.....",
    ".....KKKKKKKKKKKKKK.....",
    ".....KSSSSSSSSSSSSK.....",
]
CHEF_FACES = {
    "happy": [
        "....KSSSSSSSSSSSSSSK....",
        "....KSSKKSSSSSSKKSSK....",
        "....KSSKESSSSSSKESSK....",
        "....KssSSSSSSSSSSssK....",
        "....KSSSMMMMMMMMSSSK....",
        ".....KSKMMSSSSMMKSK.....",
        ".....KSSSSKKKKSSSSK.....",
    ],
    "wink": [   # pressed: a wink and a smile (an easter egg)
        "....KSSSSSSSSSSSSSSK....",
        "....KSSKKSSSSSSSSSSK....",
        "....KSSKESSSSSSKKKSK....",
        "....KssSSSSSSSSSSssK....",
        "....KSSSMMMMMMMMSSSK....",
        ".....KSKMMSSSSMMKSK.....",
        ".....KSSSSKKKKSSSSK.....",
    ],
    "alert": [   # eyebrows up, mouth open: "watch out"
        "....KSSKKSSSSSSKKSSK....",
        "....KSSSSSSSSSSSSSSK....",
        "....KSSKKSSSSSSKKSSK....",
        "....KSSKESSSSSSKESSK....",
        "....KSSSMMMMMMMMSSSK....",
        ".....KSSMMSKKSMMSSK.....",
        ".....KSSSSSKKSSSSSK.....",
    ],
    "thinking": [   # eyes to the side, flat mouth
        "....KSSSSSSSSSSSSSSK....",
        "....KSSSKKSSSSSSKKSK....",
        "....KSSSKESSSSSSKESK....",
        "....KSSSSSSSSSSSSSSK....",
        "....KSSSMMMMMMMMSSSK....",
        ".....KSSMMSSSSMMSSK.....",
        ".....KSSSSSSKKKSSSK.....",
    ],
}
CHEF_TORSO = [
    "......KKSSSSSSSSKK......",
    "....KKKKRRRRRRRRKKKK....",
    "...KWWWWKRRRRRRKWWWWK...",
    "..KWWWWWWKRRRRKWWWWWWK..",
    "..KWWWWWWWKRRKWWWWWWWK..",
    "..KWWwWWWWWBWWWWWwWWWK..",
    "..KWWwWWWWWWWWWWWwWWWK..",
    "..KKKKKKKKKBKKKKKKKKKK..",
]
CHEF_COLORS = {"K": "#3B2A25", "W": "#FFFFFF", "w": "#E6E1DA", "S": "#F2C29B", "s": "#E8A07E",
               "M": "#5A3A2A", "R": "#D9483B", "B": "#3B2A25", "E": "#FFFFFF"}


def chef(mood: str, rows: list[str] | None = None) -> Image.Image:
    """The chef in one mood; `rows` draws another kitchen's chef (cuisine_kitchens.chef_rows)."""
    rows = rows or CHEF_BODY + CHEF_FACES[mood] + CHEF_TORSO
    assert len(rows) == 24 and all(len(r) == 24 for r in rows), mood
    img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), ImageColor.getrgb(CHEF_COLORS[ch]) + (255,))
    return img


# ---------- Icons (20 x 20), drawn shape by shape; the app shows them at 2x ----------
INK, PLATE, PLATE_SHADE = "#3B2A25", "#FFFFFF", "#E3D9CC"
RED, RED_DARK, GREEN, GREEN_DARK = "#D9483B", "#A8322A", "#5E9B4A", "#3F7A33"
ORANGE, YELLOW, CREAM, SKIN, STEEL, STEEL_DARK = "#E8862E", "#F2C14E", "#F6D7B8", "#F2C29B", "#B8B2AC", "#7E7770"


def _canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def icon_find() -> Image.Image:
    """Find recipes: a spread seen from above, a soup bowl, a salad plate, a tomato and a carrot."""
    img, d = _canvas()
    d.ellipse([6, 5, 19, 18], fill=PLATE, outline=INK)                  # big plate
    d.ellipse([8, 7, 17, 16], fill=PLATE_SHADE)                         # its well
    d.ellipse([9, 8, 14, 12], fill=GREEN)                               # salad
    d.ellipse([12, 10, 16, 14], fill=GREEN_DARK)
    d.point([(10, 9), (13, 12), (11, 11)], fill=RED)                    # cherry tomatoes
    d.point([(15, 11), (12, 9)], fill=YELLOW)                           # corn
    d.ellipse([0, 1, 8, 8], fill=PLATE, outline=INK)                    # soup bowl
    d.ellipse([2, 3, 6, 6], fill=ORANGE)
    d.point([(3, 4), (5, 5)], fill=CREAM)
    d.ellipse([0, 13, 5, 18], fill=RED, outline=INK)                    # tomato
    d.point([(2, 13), (3, 12)], fill=GREEN)
    d.point((1, 15), fill="#F28B7E")                                    # its shine
    d.line([(15, 1), (19, 4)], fill=ORANGE, width=2)                    # carrot
    d.point([(14, 0), (14, 1)], fill=GREEN)
    return img


def icon_check() -> Image.Image:
    """Check my recipe: the chef handing a plate over, a green check rising from it."""
    img, d = _canvas()
    d.ellipse([1, 1, 8, 6], fill=PLATE, outline=INK)                    # toque
    d.rectangle([2, 5, 7, 7], fill=PLATE, outline=INK)
    d.rectangle([2, 8, 7, 12], fill=SKIN, outline=INK)                  # face
    d.point([(4, 10), (6, 10)], fill=INK)
    d.line([(3, 12), (6, 12)], fill="#5A3A2A")                          # mustache
    d.rectangle([1, 13, 8, 19], fill=PLATE, outline=INK)                # jacket
    d.point([(4, 13), (5, 13)], fill=RED)                               # neckerchief
    d.rectangle([8, 13, 13, 14], fill=PLATE, outline=INK)               # arm held out
    d.rectangle([13, 13, 14, 14], fill=SKIN)                            # hand
    d.ellipse([10, 10, 19, 13], fill=PLATE, outline=INK)                # plate on the hand
    d.ellipse([12, 7, 17, 12], fill=STEEL, outline=INK)                 # cloche over the dish
    d.point((14, 6), fill=INK)                                          # its knob
    d.line([(15, 2), (16, 3), (19, 0)], fill=GREEN_DARK)                # check mark above
    d.line([(15, 3), (16, 4), (19, 1)], fill=GREEN)
    return img


def icon_settings() -> Image.Image:
    """Settings: an oven knob instead of a gear."""
    img, d = _canvas()
    d.ellipse([2, 2, 17, 17], fill=STEEL, outline=INK)
    d.ellipse([5, 5, 14, 14], fill=PLATE_SHADE, outline=INK)
    d.rectangle([9, 3, 10, 9], fill=RED)                                # the pointer
    for x, y in [(1, 9), (18, 9), (9, 0), (9, 18), (3, 3), (15, 3)]:   # the dial's marks
        d.point((x, y), fill=INK)
    return img


def icon_timer() -> Image.Image:
    """Minutes: a tomato kitchen timer."""
    img, d = _canvas()
    d.ellipse([2, 4, 17, 18], fill=RED, outline=INK)
    d.rectangle([7, 1, 12, 4], fill=GREEN, outline=INK)                 # stem
    d.line([(3, 11), (16, 11)], fill=RED_DARK)                          # the twist line
    d.line([(9, 6), (9, 10)], fill=PLATE)                               # the arrow
    d.point([(5, 8), (14, 8)], fill="#F28B7E")
    return img


def icon_flame() -> Image.Image:
    """Calories: a stove flame under a pan."""
    img, d = _canvas()
    d.rectangle([1, 3, 15, 6], fill=STEEL_DARK, outline=INK)            # pan
    d.rectangle([15, 4, 19, 5], fill=INK)                               # handle
    d.polygon([(4, 18), (6, 9), (8, 13), (10, 8), (12, 13), (14, 9), (16, 18)], fill=ORANGE, outline=INK)
    d.polygon([(7, 18), (9, 13), (10, 15), (11, 12), (13, 18)], fill=YELLOW)
    return img


def icon_protein() -> Image.Image:
    """Protein: a fried egg in a pan."""
    img, d = _canvas()
    d.ellipse([1, 3, 16, 18], fill=STEEL_DARK, outline=INK)
    d.rectangle([15, 9, 19, 11], fill=INK)
    d.ellipse([3, 6, 13, 15], fill=PLATE)
    d.ellipse([6, 8, 10, 12], fill=YELLOW, outline=ORANGE)
    return img


def icon_safe() -> Image.Image:
    """Safe recipe: a steaming bowl with a basil leaf."""
    img, d = _canvas()
    d.pieslice([2, 2, 17, 19], 0, 180, fill=PLATE, outline=INK)
    d.line([(2, 10), (17, 10)], fill=INK)
    d.ellipse([4, 8, 15, 12], fill=CREAM)
    d.ellipse([10, 7, 15, 10], fill=GREEN, outline=GREEN_DARK)
    for x in (6, 9, 12):
        d.point([(x, 5), (x + 1, 3), (x, 1)], fill=STEEL)
    return img


def icon_alert() -> Image.Image:
    """A problem found: a pot boiling over."""
    img, d = _canvas()
    d.rectangle([3, 8, 16, 18], fill=STEEL, outline=INK)
    d.rectangle([1, 9, 3, 11], fill=INK)
    d.rectangle([16, 9, 18, 11], fill=INK)
    d.rectangle([2, 6, 17, 8], fill=RED, outline=INK)                   # lid knocked up
    for x, y in [(4, 4), (8, 2), (12, 3), (15, 5), (6, 9), (14, 10)]:   # foam spilling
        d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=PLATE, outline=STEEL_DARK)
    return img


def icon_empty() -> Image.Image:
    """Nothing found: an empty plate with crumbs."""
    img, d = _canvas()
    d.ellipse([1, 4, 18, 17], fill=PLATE, outline=INK)
    d.ellipse([4, 7, 15, 14], fill=PLATE_SHADE)
    d.point([(7, 9), (11, 12), (13, 9)], fill=CREAM)
    d.point([(8, 12)], fill="#C8743C")
    return img


def icon_bell() -> Image.Image:
    """What's new: the kitchen's service bell ("order up!"), rung when there is an update."""
    img, d = _canvas()
    d.rectangle([2, 15, 17, 17], fill=STEEL_DARK, outline=INK)          # the base
    d.pieslice([3, 6, 16, 24], 180, 360, fill=YELLOW, outline=INK)      # the brass dome
    d.line([(6, 11), (8, 9)], fill=PLATE)                               # its shine
    d.rectangle([9, 3, 10, 6], fill=STEEL_DARK, outline=INK)            # the plunger
    d.rectangle([7, 2, 12, 3], fill=STEEL, outline=INK)
    d.point([(2, 4), (17, 4), (1, 8), (18, 8)], fill=ORANGE)            # ring lines
    return img


def icon_cloche() -> Image.Image:
    """No photo yet: a covered dish, with a little steam, in the recipe card instead of a photo."""
    img, d = _canvas()
    d.rectangle([1, 15, 18, 17], fill=PLATE, outline=INK)               # the plate
    d.pieslice([3, 5, 16, 28], 180, 360, fill=STEEL, outline=INK)       # the cover
    d.line([(6, 12), (8, 9)], fill=PLATE)
    d.rectangle([9, 3, 10, 5], fill=STEEL_DARK, outline=INK)
    for x in (5, 10, 14):
        d.point([(x, 1), (x + 1, 0)], fill=STEEL)
    return img


ICONS = {"bell": icon_bell, "cloche": icon_cloche, "find": icon_find, "check": icon_check, "settings": icon_settings, "timer": icon_timer,
         "flame": icon_flame, "protein": icon_protein, "safe": icon_safe, "alert": icon_alert, "empty": icon_empty}


def _png(img: Image.Image) -> str:
    """A picture as a PNG data URI (for the scene files the app reads)."""
    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


def main() -> None:
    import cuisine_kitchens  # the four cuisine kitchens and their chefs (draft, 2026-10-18)

    PREVIEW.mkdir(parents=True, exist_ok=True)
    scenes = {theme: (lambda theme=theme: kitchen_parts(theme)) for theme in THEMES} | cuisine_kitchens.SCENES
    for name, parts in scenes.items():
        backdrop, pieces = original_parts(name) or parts()
        size = list(backdrop.size)
        scene = backdrop.copy()
        for sprite, x, y in pieces.values():
            scene.alpha_composite(sprite, (x, y))
        scene.convert("RGB").save(OUT / f"kitchen_{name}.png")
        # The interactive kitchen in the app: the backdrop and every movable piece with its place
        layers = {"size": size, "backdrop": _png(backdrop),
                  "pieces": {piece: {"png": _png(sprite), "x": x, "y": y, "w": sprite.width, "h": sprite.height}
                             for piece, (sprite, x, y) in pieces.items()}}
        (OUT / f"scene_{name}.json").write_text(json.dumps(layers), encoding="utf-8")
        big = scene if scene.width > W else scene.resize((W * 4, H * 4), Image.NEAREST)   # originals are big already
        big.convert("RGB").save(PREVIEW / f"kitchen_{name}_x4.png")
    CHEF_COLORS.update(cuisine_kitchens.CHEF_EXTRA_COLORS)
    for mood, face in CHEF_FACES.items():
        sprite = original_chef("classic") or chef(mood)
        sprite.save(OUT / f"chef_{mood}.png")
        (sprite if sprite.width > 24 else sprite.resize((24 * 8, 24 * 8), Image.NEAREST)).save(
            PREVIEW / f"chef_{mood}_x8.png")
        for variant in cuisine_kitchens.CHEF_VARIANTS:
            sprite = original_chef(variant) or chef(mood, cuisine_kitchens.chef_rows(variant, face))
            sprite.save(OUT / f"chef_{variant}_{mood}.png")
            (sprite if sprite.width > 24 else sprite.resize((24 * 8, 24 * 8), Image.NEAREST)).save(
                PREVIEW / f"chef_{variant}_{mood}_x8.png")
    sheet = Image.new("RGBA", (len(ICONS) * 24, 24), (0, 0, 0, 0))
    for k, (name, draw) in enumerate(ICONS.items()):
        icon = draw()
        icon.save(OUT / f"icon_{name}.png")
        icon.resize((20 * 8, 20 * 8), Image.NEAREST).save(PREVIEW / f"icon_{name}_x8.png")
        sheet.paste(icon, (k * 24 + 2, 2))
    sheet.resize((sheet.width * 6, sheet.height * 6), Image.NEAREST).save(PREVIEW / "icons_sheet_x6.png")
    print(f"Saved {len(scenes)} kitchens, {len(CHEF_FACES) * (1 + len(cuisine_kitchens.CHEF_VARIANTS))} chefs and "
          f"{len(ICONS)} icons in {OUT}")


if __name__ == "__main__":
    main()
