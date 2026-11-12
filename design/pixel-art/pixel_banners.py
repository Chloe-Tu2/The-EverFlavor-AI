"""The team's banners redrawn as pixel art for the app (0.6.3): 640 pixels wide, a small palette, and the text set
again in the app's pixel fonts with hard edges, one pixel bolder so it reads at this size.

How: the letters are found by colour inside each text box (dark letters on the banner, or light letters on a
ribbon) and filled from the colours around them, so sparkles and ribbons stay whole; the banner is brought down to
640 pixels and a palette (with a few key colours kept exact); the text is drawn back at that size.

    python design/pixel-art/pixel_banners.py --fonts <folder with Jersey10-Regular.ttf and VT323-Regular.ttf>

The fonts are Google Fonts (SIL Open Font Licence), downloaded when drawing and not kept here (see make_banner.py).
Reads originals/banners/; writes assets/banner_<name>.png and previews/pixel_banners.png.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ORIGINALS = HERE / "originals" / "banners"
WIDTH, COLOURS = 640, 64
KEEP = [(250, 196, 64), (255, 226, 120), (30, 13, 11), (200, 44, 40), (255, 252, 244)]   # gold, outline, red, white
TITLE, BODY = "Jersey10-Regular.ttf", "VT323-Regular.ttf"

# Each banner: its source, then its text blocks: (box in the source's pixels, light or dark letters, font, lines,
# and optionally {"align": "left"} to keep the old left edge, {"bold": False} to skip the extra pixel)
BANNERS: dict[str, tuple[str, list[tuple[Any, ...]]]] = {   # blocks have 4 or 5 parts, so typed loosely
    "meet_the_waiter": ("banner_meet_the_waiter_walter.png", [
        ((595, 28, 1165, 112), "dark", TITLE, ["Meet the Waiter!"]),
        ((610, 115, 1160, 198), "dark", BODY, ["Your new guide to the stories", "behind every dish."]),
    ]),
    "app_update": ("banner_app_update.png", [
        ((395, 30, 800, 100), "dark", TITLE, ["App Update"], {"align": "left"}),      # the icon is just left of it
        ((385, 105, 900, 190), "dark", TITLE, ["Improvements, new content,", "and a better cooking experience!"],
         {"bold": False}),                                     # Jersey is heavy enough; VT323 bolded smudges here
    ]),
    "new_chefs": ("banner_new_chefs.png", [
        ((700, 40, 1110, 115), "light", TITLE, ["New Chefs!"]),
        ((660, 118, 1170, 205), "dark", BODY, ["Say hello to our", "Moroccan and Mexican chefs!"]),
    ]),
    "whats_cooking": ("banner_whats_cooking.png", [
        ((580, 8, 1070, 88), "dark", TITLE, ["EverFlavor"]),
        ((500, 98, 1050, 190), "light", TITLE, ["What's Cooking?"]),
        ((455, 195, 1085, 250), "dark", BODY, ["New updates, chefs, and features!"]),
    ]),
}


def letters(art: np.ndarray, box: tuple[int, int, int, int], kind: str) -> np.ndarray:
    """Where the letters are inside `box`: very dark pixels, or very light ones (on a ribbon), widened by 2 px
    to take their soft edges too."""
    x0, y0, x1, y1 = box
    part = art[y0:y1, x0:x1]
    if kind == "dark":
        found = part.max(axis=2) < 140
    else:
        found = (part.min(axis=2) > 200) & (part.max(axis=2) - part.min(axis=2) < 60)
    # Only letter-sized pieces: no big dark shapes (a cloche, an outline) and no lone specks
    labels, count = ndimage.label(found)
    sizes = ndimage.sum_labels(np.ones_like(labels), labels, range(1, count + 1))
    boxes = ndimage.find_objects(labels)
    keep = np.zeros_like(found)
    for index, (size, piece) in enumerate(zip(sizes, boxes), start=1):
        tall = piece[0].stop - piece[0].start
        if 6 <= size and tall <= (y1 - y0):
            keep |= labels == index
    mask = np.zeros(art.shape[:2], bool)
    mask[y0:y1, x0:x1] = ndimage.binary_dilation(keep, iterations=2 if kind == "dark" else 4)
    return mask


def fill(art: np.ndarray, mask: np.ndarray) -> None:
    """Fill the masked pixels from their nearest unmasked neighbours, row by row (left and right blended)."""
    for y in np.where(mask.any(axis=1))[0]:
        row, hole = art[y], mask[y]
        xs = np.arange(row.shape[0])
        good = ~hole
        for c in range(3):
            row[hole, c] = np.interp(xs[hole], xs[good], row[good, c])


def text_lines(mask: np.ndarray, box: tuple[int, int, int, int]) -> list[tuple[int, int, int, int]]:
    """The box of each line of the original text (rows with letters, split at empty rows)."""
    x0, y0, x1, y1 = box
    part = mask[y0:y1, x0:x1]
    rows = np.where(part.any(axis=1))[0]
    groups: list[list[int]] = []
    for r in rows.tolist():   # plain ints, not numpy's
        if groups and r <= groups[-1][1] + 2:
            groups[-1][1] = r
        else:
            groups.append([r, r])
    out = []
    for top, bottom in groups:
        cols = np.where(part[top:bottom + 1].any(axis=0))[0]
        out.append((x0 + int(cols[0]), y0 + top, x0 + int(cols[-1]) + 1, y0 + bottom + 1))
    return out


def fitted(path: Path, texts: list[str], width: int, height: int) -> ImageFont.FreeTypeFont:
    """The largest size at which every line fits the width, and no taller than the old letters (plus a third)."""
    size = 6
    while size < 200:
        font = ImageFont.truetype(str(path), size + 1)
        too_wide = any(font.getbbox(t)[2] - font.getbbox(t)[0] > width for t in texts)
        too_tall = font.getbbox("Hg")[3] - font.getbbox("H")[1] > height * 1.35
        if too_wide or too_tall:
            break
        size += 1
    return ImageFont.truetype(str(path), size)


def ink(art: np.ndarray, mask: np.ndarray, kind: str) -> tuple[int, int, int]:
    """The letters' own colour: the darkest (or lightest) tenth of the masked pixels."""
    pixels = art[mask]
    order = pixels.sum(axis=1).argsort()
    tenth = max(1, len(order) // 10)
    picked = pixels[order[:tenth]] if kind == "dark" else pixels[order[-tenth:]]
    return tuple(int(v) for v in np.median(picked, axis=0))  # type: ignore[return-value]


def pixel_banner(name: str, fonts: Path) -> Image.Image:
    source, blocks = BANNERS[name]
    art = np.asarray(Image.open(ORIGINALS / source).convert("RGB")).astype(float)
    plan = []
    for box, kind, font_name, texts, *extra in blocks:
        mask = letters(art, box, kind)
        lines = text_lines(mask, box)
        colour = ink(art, mask, kind)
        plan.append((lines, colour, font_name, texts, extra[0] if extra else {}))
        fill(art, mask)
    image = Image.fromarray(art.clip(0, 255).astype(np.uint8))
    scale = WIDTH / image.width
    small = image.resize((WIDTH, round(image.height * scale)), Image.Resampling.BOX)
    base = small.quantize(COLOURS - len(KEEP), method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    flat = (base.getpalette() or [])[:3 * (COLOURS - len(KEEP))] + [c for rgb in KEEP for c in rgb]
    palette = Image.new("P", (1, 1))
    palette.putpalette(flat + [0] * (768 - len(flat)))
    small = small.quantize(palette=palette, dither=Image.Dither.NONE).convert("RGB")
    draw = ImageDraw.Draw(small)
    draw.fontmode = "1"                                          # hard pixel edges
    for lines, colour, font_name, texts, options in plan:
        if len(lines) != len(texts):                             # fall back to one block when lines were not found
            top = min(line[1] for line in lines)
            bottom = max(line[3] for line in lines)
            lines = [(min(line[0] for line in lines), top + i * (bottom - top) // len(texts),
                      max(line[2] for line in lines), top + (i + 1) * (bottom - top) // len(texts))
                     for i in range(len(texts))]
        width = max(line[2] - line[0] for line in lines) * scale * 1.06
        height = max(line[3] - line[1] for line in lines) * scale
        font = fitted(fonts / font_name, texts, round(width), round(height))
        for (x0, y0, x1, y1), text in zip(lines, texts):
            box = draw.textbbox((0, 0), text, font=font)
            centre_x = (x0 + x1) / 2 * scale
            centre_y = (y0 + y1) / 2 * scale
            x = round(x0 * scale - box[0] if options.get("align") == "left" else centre_x - (box[2] - box[0]) / 2 - box[0])
            y = round(centre_y - (box[3] - box[1]) / 2 - box[1])
            for dx in (0, 1) if options.get("bold", True) else (0,):   # one pixel bolder
                draw.text((x + dx, y), text, font=font, fill=colour)
    return small


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--fonts", required=True, type=Path)
    fonts = parser.parse_args().fonts
    made = []
    for name in BANNERS:
        banner = pixel_banner(name, fonts)
        banner.save(HERE / "assets" / f"banner_{name}.png", optimize=True)
        made.append(banner.resize((banner.width * 2, banner.height * 2), Image.Resampling.NEAREST))
        print(name, banner.size)
    sheet = Image.new("RGB", (max(m.width for m in made), sum(m.height + 8 for m in made)), "white")
    y = 0
    for m in made:
        sheet.paste(m, (0, y))
        y += m.height + 8
    sheet.save(HERE / "previews" / "pixel_banners.png", optimize=True)


if __name__ == "__main__":
    main()
