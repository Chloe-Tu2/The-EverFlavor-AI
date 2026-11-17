"""The two waiters, Walter and Nathalie, from the team's character sheets (originals/waiters/, 13 expressions and a
full figure each).

The sheets are concept art, so only the faces that fit a moment in the app are kept (MOODS): neutral, happy, excited,
wink, laughing, surprised, thinking (while the waiter works out an answer), concerned (allergy warnings) and proud.
Sad, angry, blushing and tired are left out. Each face is cut from the cell above its label, the white around it
becomes transparent (the chef importer's cut, which keeps white clothes), and it is placed on the app's waiter box.
The full figure is used from the waist up only ("half of the body").

    python design/pixel-art/waiter_sprites.py

Writes design/pixel-art/assets/<walter|nathalie>_<mood>.png, <name>_half.png and previews/waiters.png.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
from import_team_chefs import body, cut_out
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
SHEETS = {"walter": "waiter_male_sheet.jpg", "nathalie": "waiter_female_sheet.jpg"}
# Per row: the top of its labels and the centre of each label (pixels on the 1536 x 1024 sheet)
GRIDS = {
    "walter": [(383, [425, 663, 903, 1145, 1390]), (666, [421, 661, 905, 1144, 1390]), (950, [516, 838, 1162])],
    "nathalie": [(385, [452, 683, 913, 1144, 1383]), (668, [450, 683, 915, 1144, 1383]), (953, [548, 866, 1188])],
}
FIGURE = {"walter": (0, 20, 320, 1010), "nathalie": (30, 20, 340, 1010)}   # the full figure, left of the faces
MOODS = {"neutral": 1, "happy": 2, "excited": 3, "wink": 4, "laugh": 5, "surprised": 6, "thinking": 7,
         "worried": 8, "proud": 13}
SIZE = (128, 144)          # the app's waiter box (the corner button and his panel)
HALF = (192, 256)          # the half figure (setup window)


def cells(sheet: Image.Image, name: str) -> list[Image.Image]:
    """The 13 expression cells, numbered as on the sheet: the face above each label, below the row above."""
    return [sheet.crop((x - 118, top - 236, x + 118, top)) for top, xs in GRIDS[name] for x in xs]


def figure_only(image: Image.Image) -> Image.Image:
    """Only the figure and the marks beside it: pieces that touch the top edge (the bottom of a label or the
    title above the cell) are removed, then the rest is cropped."""
    rgba = np.asarray(image).copy()
    labels = ndimage.label(rgba[:, :, 3] > 0)[0]
    for index in np.unique(labels[0]):
        if index:
            piece = labels == index
            if piece.sum() < 0.2 * (rgba[:, :, 3] > 0).sum():   # a strip, not the figure itself
                rgba[piece, 3] = 0
    out = Image.fromarray(rgba, "RGBA")
    return out.crop(out.getbbox())


def cut(image: Image.Image) -> Image.Image:
    """The white around the figure made transparent, by the chef importer's cut (it works on a file)."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "cell.png"
        image.save(path)
        return figure_only(cut_out(path))


def fit(image: Image.Image, size: tuple[int, int], scale: float) -> Image.Image:
    """Scaled by `scale`, centred on the figure, standing on the bottom edge (what is larger is cut off)."""
    small = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))),
                         Image.Resampling.LANCZOS)
    left, _top, right, bottom = body(small)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.paste(small, (size[0] // 2 - (left + right) // 2, size[1] - bottom), small)
    return canvas


def main() -> None:
    preview = Image.new("RGBA", (SIZE[0] * (len(MOODS) + 2), SIZE[1] * 2), (238, 246, 234, 255))
    for row, (name, sheet_name) in enumerate(SHEETS.items()):
        sheet = Image.open(HERE / "originals" / "waiters" / sheet_name).convert("RGB")
        faces = [cut(c) for c in cells(sheet, name)]
        # One scale for all faces (the sheet draws them alike): the neutral face fills 90% of the box
        left, top, right, bottom = body(faces[0])
        scale = 0.9 * min(SIZE[0] / (right - left), SIZE[1] / (bottom - top))   # a margin for hair and marks
        for col, (mood, number) in enumerate(MOODS.items()):
            sprite = fit(faces[number - 1], SIZE, scale)
            sprite.save(HERE / "assets" / f"{name}_{mood}.png", optimize=True)
            preview.paste(sprite, (col * SIZE[0], row * SIZE[1]), sprite)
        whole = cut(sheet.crop(FIGURE[name]))
        half = whole.crop((0, 0, whole.width, whole.height // 2))     # head to waist
        h_left, h_top, h_right, h_bottom = body(half)
        half_sprite = fit(half, HALF, min(HALF[0] / (h_right - h_left), HALF[1] / (h_bottom - h_top)))
        half_sprite.save(HERE / "assets" / f"{name}_half.png", optimize=True)
        small = half_sprite.resize((SIZE[0] * 2 * 3 // 4, SIZE[1]), Image.Resampling.LANCZOS)
        preview.paste(small, (len(MOODS) * SIZE[0], row * SIZE[1]), small)
        print(name, len(MOODS), "faces and a half figure")
    preview.save(HERE / "previews" / "waiters.png", optimize=True)


if __name__ == "__main__":
    main()
