"""Bring the team's chef expression packs into the app (0.6.3).

The packs (13 expressions per chef, 896 x 1200 PNG on white) are drawn in a pixel style but enlarged and smoothed,
with no exact pixel grid, so they are used as drawn: the white around the figure becomes transparent (a flood fill
from the edges, stopped by the black outline, so the white hat stays), the figure is cropped, and it is scaled to
the app's chef size, standing on the bottom edge.

    python design/pixel-art/import_team_chefs.py <folder with the unpacked packs>

The folder holds one sub-folder per pack (classic_man, classic_woman, chinese_man, chinese_woman), each with
PNG/01_..._neutral.png to 13_..._worried.png. Writes design/pixel-art/assets/chef_ref_<kitchen>[_woman]_<mood>.png
(the four moods the app uses: happy, alert, thinking, wink) and design/pixel-art/originals/chefs/<pack>/<mood>.png
(all 13, for later), plus previews/team_chefs.png.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PACKS = {"classic_man": "chef_ref_classic_", "classic_woman": "chef_ref_classic_woman_",
         "chinese_man": "chef_ref_chinese_", "chinese_woman": "chef_ref_chinese_woman_"}
MOODS = ["neutral", "happy", "laughing", "wink", "surprised", "thinking", "sad", "angry", "shy", "love", "sleepy",
         "smug", "worried"]
APP_MOODS = {"happy": "happy", "wink": "wink", "thinking": "thinking", "alert": "worried"}   # app name: pack mood
SIZE = (170, 223)     # the app's chef box (the classic chef's size before)
KEEP = (224, 300)     # the size kept in originals/ for later use


def cut_out(path: Path, white: int = 236) -> Image.Image:
    """The figure on a transparent background: near-white pixels joined to the image's edge are removed."""
    rgb = np.asarray(Image.open(path).convert("RGB"))
    # Light pixels as one colour, everything else another, then a fast fill from points along the edges
    mask = Image.fromarray(np.where(rgb.min(axis=2) >= white, 255, 0).astype(np.uint8), "L").copy()
    w, _h = mask.size
    # The coat is cut off without an outline above a white strip: close it along the figure's lowest rows
    dark = rgb.min(axis=2) < white - 60
    rows = np.where(dark.any(axis=1))[0]
    bottom = int(rows[-1])
    for y in range(max(0, bottom - 3), bottom + 1):
        xs = np.where(dark[y])[0]
        if xs.size:
            ImageDraw.Draw(mask).line([(int(xs[0]), y), (int(xs[-1]), y)], fill=0)
    for x, y in [(x, 0) for x in range(0, w, 16)] + [(x, _h - 1) for x in range(0, w, 16)]:
        if mask.getpixel((x, y)) == 255:
            ImageDraw.floodfill(mask, (x, y), 128)
    outside = np.asarray(mask) == 128
    rgba = np.dstack([rgb, np.where(outside, 0, 255).astype(np.uint8)])
    image = Image.fromarray(rgba, "RGBA")
    return image.crop(image.getbbox())


def fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Scaled to fit `size`, centred, standing on the bottom edge."""
    scale = min(size[0] / image.width, size[1] / image.height)
    small = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.paste(small, ((size[0] - small.width) // 2, size[1] - small.height), small)
    return canvas


def main(source: Path) -> None:
    sheet = Image.new("RGBA", (KEEP[0] * len(MOODS) // 2, KEEP[1] * len(PACKS) // 2), (96, 140, 170, 255))  # blue shows holes
    for row, (pack, prefix) in enumerate(PACKS.items()):
        files = sorted((source / pack / "PNG").glob("*.png"))
        by_mood = {mood: next(f for f in files if f.stem.endswith("_" + mood)) for mood in MOODS}
        keep_dir = HERE / "originals" / "chefs" / pack
        keep_dir.mkdir(parents=True, exist_ok=True)
        for col, mood in enumerate(MOODS):
            figure = cut_out(by_mood[mood])
            kept = fit(figure, KEEP)
            kept.save(keep_dir / f"{mood}.png", optimize=True)
            thumb = kept.resize((KEEP[0] // 2, KEEP[1] // 2), Image.LANCZOS)
            sheet.paste(thumb, (col * KEEP[0] // 2, row * KEEP[1] // 2), thumb)
        for app_mood, mood in APP_MOODS.items():
            fit(cut_out(by_mood[mood]), SIZE).save(HERE / "assets" / f"{prefix}{app_mood}.png", optimize=True)
        print(pack, "done")
    sheet.save(HERE / "previews" / "team_chefs.png", optimize=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
