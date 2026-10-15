"""Draw EverFlavor's concept pixel art: the kitchen scene (one per color theme) and the chef guide.

Everything is drawn from code, pixel by pixel, so the art can be changed and redrawn by anyone:
edit a palette or a sprite below and run, from the project folder,

    python design/pixel-art/make_pixel_art.py

It writes small native-size PNGs to design/pixel-art/concept/ (the app scales them up with sharp
pixels) and 4x previews to design/pixel-art/concept/preview/ for looking at them.
Needs only Pillow (already in config/requirements.txt).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageColor, ImageDraw

OUT = Path(__file__).resolve().parent / "concept"
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


def kitchen(theme: str) -> Image.Image:
    """The kitchen: window, shelves with jars, hanging pans, stove with a steaming pot, cutting board, plant."""
    p = THEMES[theme]
    img = Image.new("RGB", (W, H), p["wall"])
    d = ImageDraw.Draw(img)
    o = p["outline"]

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
    for px in (wx - 2, wx + ww - 10):                                          # curtains
        rect(d, px, wy - 2, 12, wh + 6, p["accent"])
        for k in range(0, wh + 6, 4):
            d.point((px + 6, wy - 2 + k), fill=p["accent_dark"])

    # Two shelves with jars and pots
    jar_colors = ["#D9483B", "#F2C14E", "#5E9B4A", "#C8743C", "#E8E1D5", "#8E5A9B"]
    for row, sy in enumerate((26, 50)):
        rect(d, 14, sy, 104, 3, p["wood"], o)
        x = 18
        for j in range(7):
            jh = 9 + (j * 3 + row * 2) % 6
            jw = 8 + (j + row) % 3 * 2
            color = jar_colors[(j + row * 3) % len(jar_colors)]
            rect(d, x, sy - jh, jw, jh, color, o)
            rect(d, x + 1, sy - jh - 2, jw - 2, 2, p["wood_light"], o)          # lid
            d.line([x + 2, sy - jh + 3, x + 2, sy - 3], fill="#FFFFFF")          # glint
            x += jw + 5
            if x > 108:
                break

    # Pans hanging from a rail between the shelves and the window
    rect(d, 124, 14, 22, 2, p["steel_dark"])
    for k, (px, r) in enumerate([(127, 5), (136, 4), (144, 3)]):
        d.line([px, 16, px, 22 + k * 2], fill=p["steel_dark"])
        d.ellipse([px - r, 22 + k * 2, px + r, 22 + k * 2 + 2 * r], fill=p["steel"], outline=o)

    # Hanging lamp; at night it lights a cone on the wall
    if p["light"]:
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        g = ImageDraw.Draw(glow)
        g.polygon([(122, 30), (86, 96), (160, 96)], fill=p["light"] + "38")
        img.paste(glow, (0, 0), glow)
        d = ImageDraw.Draw(img)
    d.line([123, 0, 123, 22], fill=o)
    rect(d, 117, 22, 13, 5, p["accent_dark"], o)
    d.point((123, 28), fill=p["light"] or "#FFF3B0")

    # Counter and cabinets
    rect(d, 0, 96, W, 5, p["counter"], o)
    rect(d, 0, 101, W, H - 101, p["wood"])
    for cx in range(4, W, 40):
        rect(d, cx, 105, 34, 26, p["wood_light"], p["wood_dark"])
        rect(d, cx + 15, 116, 4, 2, p["steel"], o)                             # handle

    # Stove with a pot and steam
    rect(d, 24, 88, 48, 8, p["steel_dark"], o)
    for bx in (30, 54):
        rect(d, bx, 86, 12, 2, "#2B2B2B")
    rect(d, 27, 74, 20, 12, p["accent"], o)                                    # pot
    rect(d, 25, 74, 24, 3, p["accent_dark"], o)                                # lid
    rect(d, 35, 71, 4, 3, p["accent_dark"], o)
    for k, (sx, sy) in enumerate([(31, 66), (36, 61), (41, 64), (34, 56), (40, 53)]):
        d.point((sx, sy), fill="#FFFFFF" if theme != "classic" else "#D8CFC8")
        d.point((sx + 1, sy - 1), fill="#FFFFFF" if theme != "classic" else "#D8CFC8")

    # Cutting board with a tomato, a carrot and basil
    rect(d, 92, 91, 40, 5, p["wood_light"], o)
    d.ellipse([97, 84, 105, 92], fill="#D9483B", outline=o)                    # tomato
    rect(d, 100, 83, 3, 2, "#5E9B4A")
    d.polygon([(110, 90), (124, 87), (124, 89)], fill="#E8862E", outline=o)    # carrot
    rect(d, 124, 86, 3, 2, "#5E9B4A")
    for lx, ly in [(116, 84), (119, 82), (113, 82)]:                           # basil leaves
        d.ellipse([lx, ly, lx + 4, ly + 3], fill="#5E9B4A", outline=o)

    # Plant in a pot on the counter's right
    rect(d, 214, 84, 14, 12, "#C8743C", o)
    for lx, ly in [(212, 76), (218, 70), (224, 75), (215, 66), (226, 66), (220, 62)]:
        d.ellipse([lx, ly, lx + 6, ly + 9], fill="#5E9B4A", outline=o)
    return img


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


def chef(mood: str) -> Image.Image:
    rows = CHEF_BODY + CHEF_FACES[mood] + CHEF_TORSO
    assert len(rows) == 24 and all(len(r) == 24 for r in rows), mood
    img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), ImageColor.getrgb(CHEF_COLORS[ch]) + (255,))
    return img


def main() -> None:
    (OUT / "preview").mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        scene = kitchen(theme)
        scene.save(OUT / f"kitchen_{theme}.png")
        scene.resize((W * 4, H * 4), Image.NEAREST).save(OUT / "preview" / f"kitchen_{theme}_x4.png")
    for mood in CHEF_FACES:
        sprite = chef(mood)
        sprite.save(OUT / f"chef_{mood}.png")
        sprite.resize((24 * 8, 24 * 8), Image.NEAREST).save(OUT / "preview" / f"chef_{mood}_x8.png")
    print(f"Saved {len(THEMES)} kitchens and {len(CHEF_FACES)} chefs in {OUT}")


if __name__ == "__main__":
    main()
