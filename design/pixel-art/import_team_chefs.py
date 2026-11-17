"""Bring the team's chef expression packs into the app (0.6.3).

The packs (13 expressions per chef, PNG on white) are drawn in a pixel style but enlarged and smoothed, with no
exact pixel grid, so they are used as drawn: the white around the figure becomes transparent (a flood fill from the
edges, stopped by the black outline, so the white hat stays), the figure is cropped and scaled to the app's chef
size, standing on the bottom edge.

Some faces in a pack were framed larger or smaller than the rest. To even them out, every face in a pack is scaled
so its hat (the widest row of the top seventh of the figure) has the same width.

    python design/pixel-art/import_team_chefs.py <folder with the unpacked packs>

The folder holds one sub-folder per pack (see PACKS), each with PNG files named ..._01_neutral.png to
..._13_worried.png, at any depth. Writes design/pixel-art/assets/chef_ref_<kitchen>[_woman]_<mood>.png (the four
moods the app uses: happy, alert, thinking, wink) and design/pixel-art/originals/chefs/<pack>/<mood>.png (all 13,
for later), plus previews/team_chefs.png.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
PACKS = {"classic_man": "chef_ref_classic_", "classic_woman": "chef_ref_classic_woman_",
         "chinese_man": "chef_ref_chinese_", "chinese_woman": "chef_ref_chinese_woman_",
         "moroccan_male": "chef_ref_moroccan_", "moroccan_female": "chef_ref_moroccan_woman_",
         "mexican_male": "chef_ref_mexican_", "mexican_female": "chef_ref_mexican_woman_",
         "middle_eastern_male": "chef_ref_middle_eastern_", "middle_eastern_female": "chef_ref_middle_eastern_woman_"}
APP_MOODS = {"happy": 2, "wink": 4, "thinking": 6, "alert": 13}   # app name: number of the pack's expression
# Faces that stand in for a broken frame: moroccan_female 02 (happy) was cut off its sheet with the figure's right
# side missing, so her laughing face (03) is used until the team re-exports it
SWAPS = {"moroccan_female": {"happy": 3}}
# Same-size frames that are still drawn at different scales (chinese_woman 11-13 are closer up): evened out
EVEN_OUT = {"chinese_woman"}
SIZE = (170, 223)     # the app's chef box (the classic chef's size before)
KEEP = (224, 300)     # the size kept in originals/ for later use
NUMBERED = re.compile(r"(?:^|_)(\d\d)_(?:.*_)?([a-z]+)$")   # 01_classic_chef_neutral, mexican_male_01_neutral


def cut_out(path: Path, white: int = 236, crop: bool = True) -> Image.Image:
    """The figure on a transparent background: near-white pixels joined to the image's edge are removed (packs
    that already come on a transparent background are cleaned and cropped)."""
    source = Image.open(path).convert("RGBA")
    if see_through(source):
        # Some frames were cut a little off their sheet and carry a thin slice of the next frame along an edge:
        # clear any flat or narrow piece near the edge
        rgba = np.asarray(source).copy()
        labels = ndimage.label(rgba[:, :, 3] > 0)[0]
        h, w = labels.shape
        for index, found in enumerate(ndimage.find_objects(labels), start=1):
            if found is None:
                continue
            ys, xs = found
            tall, wide = ys.stop - ys.start, xs.stop - xs.start
            near_edge = min(ys.start, xs.start, h - ys.stop, w - xs.stop) <= 24
            if near_edge and ((tall <= 30 and wide >= 3 * tall) or (wide <= 30 and tall >= 3 * wide)):
                rgba[labels == index, 3] = 0
        # A slice touching the hat: wide rows at the top that suddenly narrow where the hat's tip begins
        counts = (rgba[:, :, 3] > 0).sum(axis=1)
        rows = np.where(counts > 0)[0]
        for k in range(1, min(16, rows.size)):
            if counts[rows[:k]].min() >= 120 and counts[rows[k]] < 0.4 * counts[rows[:k]].min():
                rgba[rows[0]:rows[k], :, 3] = 0
                break
        image = Image.fromarray(rgba, "RGBA")
        return image.crop(image.getbbox())
    rgb = np.asarray(source.convert("RGB"))
    # Light pixels as one colour, everything else another, then a fast fill from points along the edges
    mask = Image.fromarray(np.where(rgb.min(axis=2) >= white, 255, 0).astype(np.uint8), "L").copy()
    w, h = mask.size
    # The coat is cut off without an outline above a white strip: close it along the figure's lowest rows
    dark = rgb.min(axis=2) < white - 60
    rows = np.where(dark.any(axis=1))[0]
    bottom = int(rows[-1])
    for y in range(max(0, bottom - 3), bottom + 1):
        xs = np.where(dark[y])[0]
        if xs.size:
            ImageDraw.Draw(mask).line([(int(xs[0]), y), (int(xs[-1]), y)], fill=0)
    for x, y in [(x, 0) for x in range(0, w, 16)] + [(x, h - 1) for x in range(0, w, 16)]:
        if mask.getpixel((x, y)) == 255:
            ImageDraw.floodfill(mask, (x, y), 128)
    outside = np.asarray(mask) == 128
    rgba = np.dstack([rgb, np.where(outside, 0, 255).astype(np.uint8)])
    image = Image.fromarray(rgba, "RGBA")
    return image.crop(image.getbbox()) if crop else image


def body(image: Image.Image) -> tuple[int, int, int, int]:
    """The box around the figure's big pieces (hat, head, body), leaving out small loose marks (a sleepy "zzz",
    sparkles, hearts)."""
    labels, count = ndimage.label(np.asarray(image)[:, :, 3] > 0)
    if count <= 1:
        return image.getbbox() or (0, 0, image.width, image.height)
    sizes = ndimage.sum_labels(np.ones_like(labels), labels, range(1, count + 1))
    ys, xs = np.where(np.isin(labels, np.where(sizes >= 0.05 * sizes.max())[0] + 1))
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def head_width(image: Image.Image) -> int:
    """How wide the head is: the longest unbroken run of the figure in a row of its top seventh (a "zzz" or a heart
    beside the hat is not counted)."""
    left, top, right, bottom = body(image)
    # The hat band only (hands, hearts and tears near the face would widen anything lower)
    alpha = np.asarray(image)[top:top + (bottom - top) // 7, left:right, 3] > 0
    widths = [longest_run(row) for row in alpha]
    return max(widths, default=0) or right - left


def longest_run(row: np.ndarray) -> int:
    """The length of the longest stretch of True in a row."""
    edges = np.diff(np.concatenate(([0], row.astype(np.int8), [0])))
    starts, ends = np.where(edges == 1)[0], np.where(edges == -1)[0]
    return int((ends - starts).max()) if starts.size else 0


def place(image: Image.Image, scale: float, size: tuple[int, int]) -> Image.Image:
    """Scaled by `scale`, centred on the figure, its lowest row on the bottom edge (anything larger is cut off)."""
    small = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))),
                         Image.Resampling.LANCZOS)
    box = body(small)    # left, top, right, bottom
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.paste(small, (size[0] // 2 - (box[0] + box[2]) // 2, size[1] - box[3]), small)
    return canvas


def pack_scales(figures: list[Image.Image], size: tuple[int, int]) -> list[float]:
    """One scale per face so every head is as wide as in the pack's typical face, which fits `size`."""
    heads = [head_width(f) for f in figures]
    fits = [min(size[0] / (b[2] - b[0]), size[1] / (b[3] - b[1])) for b in map(body, figures)]
    target = float(np.median([fit * head for fit, head in zip(fits, heads)]))
    return [target / head for head in heads]


def see_through(image: Image.Image) -> bool:
    """True for art that already comes on a transparent background."""
    return bool((np.asarray(image)[:, :, 3] == 0).mean() > 0.2)


def same_frames(paths: list[Path]) -> bool:
    """True for a pack whose faces are whole frames of one size on white, drawn at one scale (the 896x1200 packs):
    those need no evening out, only the same cut from every frame."""
    images = [Image.open(p) for p in paths]
    return len({im.size for im in images}) == 1 and not any(see_through(im.convert("RGBA")) for im in images[:1])


def render_frames(frames: list[Image.Image], size: tuple[int, int]) -> list[Image.Image]:
    """The same box cut from every frame and scaled alike, so a face with a raised arm keeps the others' scale
    (the arm is cut at the box's edge). The box is the first face's figure, widened to the app's shape."""
    left, top, right, bottom = body(frames[0])
    height = bottom - top
    width = height * size[0] / size[1]
    middle = (left + right) / 2
    box = (round(middle - width / 2), top, round(middle + width / 2), bottom)
    return [f.crop(box).resize(size, Image.Resampling.LANCZOS) for f in frames]


def render(figures: list[Image.Image], size: tuple[int, int]) -> list[Image.Image]:
    """The pack's faces at `size`, evened out face by face (pack_scales)."""
    return [place(f, s, size) for f, s in zip(figures, pack_scales(figures, size))]


def load(folder: Path) -> dict[int, tuple[str, Path]]:
    """The pack's faces by number: {1: ("neutral", path), ...}."""
    faces = {}
    for path in sorted(folder.rglob("*.png")):   # the PNG copies (some packs also hold JPGs)
        found = NUMBERED.search(path.stem)
        if found:
            faces[int(found.group(1))] = (found.group(2), path)
    return faces


def main(source: Path) -> None:
    packs = [(pack, prefix, source / pack) for pack, prefix in PACKS.items() if (source / pack).is_dir()]
    sheet = Image.new("RGBA", (KEEP[0] * 13 // 2, KEEP[1] * len(packs) // 2), (96, 140, 170, 255))  # blue shows holes
    for row, (pack, prefix, folder) in enumerate(packs):
        faces = load(folder)
        numbers = sorted(faces)
        paths = [faces[n][1] for n in numbers]
        uniform = pack not in EVEN_OUT and same_frames(paths)
        figures = [cut_out(p, crop=not uniform) for p in paths]
        draw = render_frames if uniform else render
        keep_dir = HERE / "originals" / "chefs" / pack
        keep_dir.mkdir(parents=True, exist_ok=True)
        for col, (number, kept) in enumerate(zip(numbers, draw(figures, KEEP))):
            kept.save(keep_dir / f"{faces[number][0]}.png", optimize=True)
            thumb = kept.resize((KEEP[0] // 2, KEEP[1] // 2), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (col * KEEP[0] // 2, row * KEEP[1] // 2), thumb)
        in_app = dict(zip(numbers, draw(figures, SIZE)))
        for app_mood, number in {**APP_MOODS, **SWAPS.get(pack, {})}.items():
            in_app[number].save(HERE / "assets" / f"{prefix}{app_mood}.png", optimize=True)
        print(pack, len(numbers), "faces", "(same cut)" if uniform else "(evened out)")
    sheet.save(HERE / "previews" / "team_chefs.png", optimize=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
