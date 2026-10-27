"""Drafts of the "no photo yet" picture (docs/plans/RECIPE_PHOTOS.md): four 32x32 options in the icons' palette,
saved side by side with their captions in previews/no_photo_drafts_x6.png for the team to pick one.
B was picked (2026-10-26); it now lives in make_pixel_art.no_photo.

Run: python design/pixel-art/no_photo_drafts.py
"""
from __future__ import annotations

from pathlib import Path

from make_pixel_art import (
    GREEN,
    INK,
    ORANGE,
    PLATE,
    PLATE_SHADE,
    PREVIEW,
    RED,
    STEEL,
    STEEL_DARK,
    YELLOW,
    no_photo,
)
from PIL import Image, ImageDraw

N = 32
WOOD, WOOD_DARK, PAN, PAN_DARK = "#C8874A", "#8E5A2E", "#4A4A52", "#2E2E34"


def _canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _pan(d: ImageDraw.ImageDraw, top: int = 14) -> None:
    """A frying pan seen from a little above, handle to the right."""
    d.rectangle([22, top + 5, 31, top + 7], fill=WOOD_DARK, outline=INK)    # the handle
    d.ellipse([1, top, 25, top + 14], fill=PAN, outline=INK)                # the rim
    d.ellipse([4, top + 2, 22, top + 12], fill=PAN_DARK)                    # the inside
    d.line([(6, top + 3), (10, top + 2)], fill=STEEL)                       # its shine


def _steam(d: ImageDraw.ImageDraw, xs: tuple[int, ...], top: int) -> None:
    for x in xs:
        d.point([(x, top + 4), (x + 1, top + 3), (x, top + 2), (x + 1, top + 1), (x, top)], fill=STEEL)


def crossed_utensils() -> Image.Image:
    """A: a spatula and a whisk crossed over a frying pan, like a kitchen crest."""
    img, d = _canvas()
    _pan(d, 16)
    d.line([(3, 2), (24, 23)], fill=WOOD_DARK, width=2)                     # the spatula's handle
    d.polygon([(1, 0), (6, 0), (6, 5), (1, 5)], fill=STEEL, outline=INK)    # its blade
    d.line([(2, 2), (5, 2)], fill=STEEL_DARK)
    d.line([(27, 3), (7, 23)], fill=STEEL_DARK, width=2)                    # the whisk's handle
    d.ellipse([23, 0, 31, 9], fill=None, outline=INK)                       # its wires: a balloon of loops
    d.line([(27, 0), (27, 9)], fill=STEEL)
    d.arc([24, 1, 30, 9], 200, 340, fill=STEEL)
    d.arc([25, 0, 29, 9], 90, 270, fill=STEEL)
    return img



def pan_with_egg() -> Image.Image:
    """C: an egg frying in the pan over a small flame."""
    img, d = _canvas()
    _steam(d, (9, 15), 2)
    _pan(d, 9)
    d.ellipse([7, 12, 18, 19], fill=PLATE, outline=PLATE_SHADE)             # the white
    d.ellipse([11, 14, 15, 17], fill=YELLOW, outline=ORANGE)                # the yolk
    d.point((12, 15), fill=PLATE)
    for x, h in ((7, 4), (11, 6), (15, 5), (19, 4)):                       # the flame
        d.line([(x, 31 - h), (x, 31)], fill=ORANGE, width=2)
        d.point((x, 31 - h + 2), fill=YELLOW)
    d.line([(4, 31), (22, 31)], fill=RED)
    return img


def cloche() -> Image.Image:
    """D: a covered dish with steam, the larger cousin of icon_cloche."""
    img, d = _canvas()
    _steam(d, (9, 15, 21), 0)
    d.rectangle([1, 25, 30, 28], fill=PLATE, outline=INK)                   # the plate
    d.pieslice([4, 9, 27, 41], 180, 360, fill=STEEL, outline=INK)           # the cover
    d.line([(9, 20), (12, 15)], fill=PLATE)
    d.rectangle([14, 6, 17, 9], fill=STEEL_DARK, outline=INK)               # the knob
    d.point([(3, 27), (28, 27)], fill=GREEN)                                # a garnish
    return img


DRAFTS = {"A": (crossed_utensils, "Cooking up a picture..."),
          "B": (no_photo, "Cooking up a picture... (picked)"),
          "C": (pan_with_egg, "Picture on the stove..."),
          "D": (cloche, "Photo coming soon")}


def main() -> None:
    scale, cell = 6, 64
    sheet = Image.new("RGB", (len(DRAFTS) * cell * scale // 2, N * scale + 50), "#FBF4EA")
    d = ImageDraw.Draw(sheet)
    for k, (key, (draw, caption)) in enumerate(DRAFTS.items()):
        art = draw()
        big = art.resize((N * scale, N * scale), Image.NEAREST)
        x = k * cell * scale // 2 + 2
        sheet.paste(big, (x, 10), big)
        d.text((x, N * scale + 22), f"{key}: {caption}", fill=INK)
    out = Path(PREVIEW) / "no_photo_drafts_x6.png"
    sheet.save(out)
    print("saved", out)


if __name__ == "__main__":
    main()
