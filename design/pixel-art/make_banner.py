"""Draw the README banner and the logo from the app's own pixel art (0.6.3).

The banner is the Classic kitchen's colours with three kitchen chefs and Walter standing on a tiled floor and the
title in the app's pixel fonts; the logo is the classic chef on a cream tile. Both are drawn on a grid of 4 screen
pixels per art pixel, like the app.

The fonts are the app's Google Fonts (SIL Open Font Licence), not kept in the repo; download them first:
    https://github.com/google/fonts/raw/main/ofl/jersey10/Jersey10-Regular.ttf
    https://github.com/google/fonts/raw/main/ofl/vt323/VT323-Regular.ttf

    python design/pixel-art/make_banner.py --fonts <folder with the two .ttf files>
writes docs/art/banner.png (1280x320) and docs/art/logo.png (256x256).
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
OUT = HERE.parents[1] / "docs" / "art"
SCALE = 4
# The Classic theme (app/themes.py)
PANEL, BORDER, TEXT, HEADING, BUTTON, SHADOW = "#FFF8E7", "#8B4513", "#4A2C2A", "#8B4513", "#FFB6C1", "#D9A679"
FLOOR = ("#C98B5A", "#B57446")
# The kitchens' chefs as the app draws them (traced from the team's art, already at screen size) and Walter
CHEFS = ["chef_ref_classic_happy", "chef_ref_chinese_woman_happy", "chef_ref_middle_eastern_happy", "walter_happy"]


def sprite(name: str, scale: int = SCALE) -> Image.Image:
    art = Image.open(ASSETS / f"{name}.png").convert("RGBA")
    return art.resize((art.width * scale, art.height * scale), Image.Resampling.NEAREST)


def pixel_box(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, border: str = BORDER) -> None:
    """A panel like the app's: a 1-art-pixel border and a drop shadow below and to the right."""
    x0, y0, x1, y1 = box
    draw.rectangle((x0 + SCALE, y0 + SCALE, x1 + SCALE, y1 + SCALE), fill=SHADOW)
    draw.rectangle(box, fill=fill, outline=border, width=SCALE)


def banner(title_font: Path, text_font: Path) -> Image.Image:
    width, height = 320 * SCALE, 80 * SCALE
    img = Image.new("RGBA", (width, height), PANEL)
    draw = ImageDraw.Draw(img)
    tile = 8 * SCALE   # the floor: two rows of checked tiles
    floor_top = height - 2 * tile
    for row in range(2):
        for col in range(width // tile + 1):
            draw.rectangle((col * tile, floor_top + row * tile, (col + 1) * tile - 1, floor_top + (row + 1) * tile - 1),
                           fill=FLOOR[(row + col) % 2])
    draw.rectangle((0, floor_top - SCALE, width, floor_top - 1), fill=BORDER)
    # The chefs and Walter standing on the floor, right half (native size: they are drawn at screen scale)
    people = [sprite(name, 1) for name in CHEFS]
    x = width - sum(p.width for p in people) - 4 * SCALE
    for person in people:
        img.alpha_composite(person, (x, floor_top - person.height + 4 * SCALE))
        x += person.width
    # Title, beta badge and tagline, left
    big = ImageFont.truetype(str(title_font), 30 * SCALE)
    small = ImageFont.truetype(str(text_font), 9 * SCALE)
    badge = ImageFont.truetype(str(title_font), 9 * SCALE)
    left, top = 8 * SCALE, 6 * SCALE
    draw.text((left + SCALE, top + SCALE), "EverFlavor", font=big, fill=SHADOW)
    draw.text((left, top), "EverFlavor", font=big, fill=HEADING)
    title_right = left + int(draw.textlength("EverFlavor", font=big))
    bx = title_right + 4 * SCALE
    label_w = int(draw.textlength("BETA", font=badge))
    pixel_box(draw, (bx, top + 6 * SCALE, bx + label_w + 6 * SCALE, top + 17 * SCALE), BUTTON)
    draw.text((bx + 3 * SCALE, top + 6 * SCALE), "BETA", font=badge, fill=TEXT)
    draw.text((left, top + 32 * SCALE), "Recipes that fit what you can eat,", font=small, fill=TEXT)
    draw.text((left, top + 40 * SCALE), "checked ingredient by ingredient.", font=small, fill=TEXT)
    draw.rectangle((0, 0, width - 1, height - 1), outline=BORDER, width=SCALE)
    return img


def logo() -> Image.Image:
    size = 64 * SCALE
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pixel_box(draw, (2 * SCALE, 2 * SCALE, size - 4 * SCALE, size - 4 * SCALE), PANEL)
    chef = sprite("chef_happy", 2 * SCALE)   # 24 art pixels at 8x: 192 screen pixels
    img.alpha_composite(chef, ((size - chef.width) // 2 - SCALE, (size - chef.height) // 2 - SCALE))
    return img


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fonts", required=True, help="folder with Jersey10-Regular.ttf and VT323-Regular.ttf")
    args = parser.parse_args()
    fonts = Path(args.fonts)
    OUT.mkdir(parents=True, exist_ok=True)
    banner(fonts / "Jersey10-Regular.ttf", fonts / "VT323-Regular.ttf").save(OUT / "banner.png", optimize=True)
    logo().save(OUT / "logo.png", optimize=True)
    print(f"wrote {OUT / 'banner.png'} and {OUT / 'logo.png'}")


if __name__ == "__main__":
    main()
