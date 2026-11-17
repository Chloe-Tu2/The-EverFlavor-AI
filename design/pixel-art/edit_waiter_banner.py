"""The team's "Meet the Waiter" banner, with its text fitted to Walter (0.6.3).

The banner came with the line "Your new guide for IT support and quick help." and a laptop and a gear in the
speech bubble. Walter tells the stories behind dishes, so this script keeps the team's art and only changes those
parts, in the banner's own style: the two lines are set again in the same colour, size and place, the laptop
becomes a steaming bowl and the gear a recipe book (drawn as blocky pixels, like the rest of the banner).

    python design/pixel-art/edit_waiter_banner.py

Reads originals/banners/banner_meet_the_waiter.png (the team's art, never changed) and writes
originals/banners/banner_meet_the_waiter_walter.png (cut_banners.py --app makes the app's copy from it).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "originals" / "banners" / "banner_meet_the_waiter.png"
TARGET = HERE / "originals" / "banners" / "banner_meet_the_waiter_walter.png"
LINES = ("Your new guide to the stories", "behind every dish.")
OLD_LINE = "Your new guide for IT support"    # its width in the art sets the font size
OLD_WIDTH = 1134 - 632 + 1                     # measured in the art: x 632 to 1134
TEXT_BOX = (624, 112, 1160, 198)               # where the old two lines are (x0, y0, x1, y1)
LINE_TOPS = (119, 157)                         # the top of each old line
CENTRE_X = 880
INK = (60, 11, 7)                              # the text colour in the art
FONTS = ["C:/Windows/Fonts/segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]

CELL = 4                                       # screen pixels per art pixel in the bubble drawings
OUTLINE, CREAM = (30, 13, 11), (254, 246, 233)
BOWL = ["....s..s..s.....",
        "...s..s..s......",
        "....s..s..s.....",
        "...s..s..s......",
        "................",
        "kkkkkkkkkkkkkkkk",
        "kyyyyyyyyyyyyyyk",
        "krrrrrrrrrrrrrrk",
        ".krrwrrrrrrrrrk.",
        ".krrrrrrrrrrrrk.",
        "..krrrrrrrrrrk..",
        "...kkrrrrrrkk...",
        ".....kkkkkk.....",
        "....kkkkkkkk...."]
BOOK = ["kkkkkkkkkkkkkkkkkkk.",
        "kdcccccccccccccccck.",
        "kdcllllllllllllllckk",
        "kdclddddddddddddlckp",
        "kdcllllllllllllllckp",
        "kdcccccccccccccccckp",
        "kdccccccyycccccccckp",
        "kdcccccyyyyccccccckp",
        "kdccccccyycccccccckp",
        "kdcccccccccccccccckp",
        "kdcccccccccccccccckp",
        "kdcccccccccccccccckp",
        "kdcccccccccccccccckp",
        "kdcccccccccccccccckp",
        "kdcccccccccccccccckp",
        "kdcccccccccccccccckp",
        "kkkkkkkkkkkkkkkkkkkp",
        ".kpppppppppppppppppk",
        "..kkkkkkkkkkkkkkkkkk"]
PALETTE = {"k": OUTLINE, "s": (150, 150, 160), "y": (232, 168, 56), "r": (196, 64, 48), "w": (236, 120, 96),
           "c": (168, 58, 44), "l": (250, 238, 214), "d": (120, 40, 30), "p": (250, 238, 214)}


def sprite(rows: list[str], cell: int = CELL) -> Image.Image:
    """A letter grid drawn as blocky pixels, `cell` screen pixels each."""
    small = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, letter in enumerate(row):
            if letter in PALETTE:
                small.putpixel((x, y), (*PALETTE[letter], 255))
    return small.resize((small.width * cell, small.height * cell), Image.Resampling.NEAREST)


def clear(art: np.ndarray, box: tuple[int, int, int, int]) -> None:
    """Paint over a box with the background on its left and right edges, blended across each row."""
    x0, y0, x1, y1 = box
    left = art[y0:y1, x0 - 6:x0].mean(axis=1)
    right = art[y0:y1, x1:x1 + 6].mean(axis=1)
    t = np.linspace(0, 1, x1 - x0)[None, :, None]
    art[y0:y1, x0:x1] = (left[:, None, :] * (1 - t) + right[:, None, :] * t).round()


def font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONTS:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    sys.exit("No bold font found: add one to FONTS")


def main() -> None:
    art = np.asarray(Image.open(SOURCE).convert("RGB")).astype(float)
    clear(art, TEXT_BOX)
    banner = Image.fromarray(art.astype(np.uint8), "RGB")
    draw = ImageDraw.Draw(banner)
    size = 40
    while font(size).getlength(OLD_LINE) > OLD_WIDTH:
        size -= 1
    face = font(size)
    for line, top in zip(LINES, LINE_TOPS):
        x0, y0, x1, _y1 = draw.textbbox((0, 0), line, font=face)
        draw.text((CENTRE_X - (x1 - x0) // 2 - x0, top - y0), line, font=face, fill=INK)
    # The bubble: the laptop becomes a steaming bowl, the gear a recipe book
    draw.rectangle((1234, 56, 1333, 131), fill=CREAM)
    bowl = sprite(BOWL, CELL + 1)
    banner.paste(bowl, (1284 - bowl.width // 2, 130 - bowl.height), bowl)
    book = sprite(BOOK)
    banner.paste(book, (1320, 204 - book.height), book)
    banner.save(TARGET, optimize=True)
    print("wrote", TARGET.relative_to(HERE), "font size", size)


if __name__ == "__main__":
    main()
