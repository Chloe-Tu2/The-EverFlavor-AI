"""The Middle Eastern woman cook in more detail: drawn on an 80 x 92 grid (twice the other cooks'), with three tones
per material (light from the top left), the hijab's folds and pin, the chef jacket's collar and buttons, the apron
and its neck strap, and a face with brows, nose and lips. After the reference photos in references/chefs/women/
(a chef with her hijab tucked into the collar of her white jacket, a black apron).

    python design/pixel-art/make_chef_hd.py   ->   assets/chef_ref_middle_eastern_woman_<mood>.png,
                                                   previews/middle_eastern_woman_hd.png (every hijab color)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
W, H, TOP, SCALE = 80, 92, 4, 2
INK = (58, 36, 40)
SKIN = (214, 152, 112)
JACKET, BUTTON = (250, 248, 242), (176, 176, 184)
EYE, BROW, LASH = (52, 34, 34), (70, 44, 38), (40, 26, 28)
LIP, TEETH, CHEEK, SHINE = (176, 74, 78), (255, 255, 255), (226, 128, 112), (255, 255, 255)
MOODS = ("happy", "alert", "thinking", "wink")
HIJABS = {                                    # hijab, apron
    "white": ((236, 232, 222), (46, 44, 52)),
    "black": ((44, 40, 48), (110, 70, 44)),
    "navy": ((44, 58, 104), (46, 44, 52)),
    "rose": ((200, 132, 140), (110, 70, 44)),
}
DEFAULT = "white"


def shade(rgb: np.ndarray, mask: np.ndarray, color: tuple[int, int, int], depth: int = 4) -> None:
    """Fill a shape in three tones: lighter along its top left edge, darker along its bottom right."""
    base = np.array(color, np.float32)
    rgb[mask] = base
    up = np.zeros_like(mask)
    up[depth:, depth:] = mask[:-depth, :-depth]                 # the shape moved down right: where it is not, light
    down = np.zeros_like(mask)
    down[:-depth, :-depth] = mask[depth:, depth:]
    rgb[mask & ~up] = np.minimum(base * 1.12 + 10, 255)
    rgb[mask & ~down] = base * 0.78


def cook(mood: str, hijab: tuple[int, int, int], apron: tuple[int, int, int]) -> np.ndarray:
    rgb = np.zeros((H, W, 3), np.float32)
    inside = np.zeros((H, W), bool)
    lines = np.zeros((H, W), bool)                              # dark lines where one shape lies over another

    def shape(color: tuple[int, int, int], draw, depth: int = 4) -> np.ndarray:
        img = Image.new("1", (W, H), 0)
        draw(ImageDraw.Draw(img))
        m = np.array(img, bool)
        edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
        lines[m] = False
        lines[edge & inside] = True                              # its edge, where it covers something
        shade(rgb, m, color, depth)
        inside[m] = True
        return m

    shape(hijab, lambda d: (d.ellipse((17, 9, 63, 66), fill=1),            # the hijab behind the head and neck
                            d.polygon([(16, 50), (64, 50), (60, 72), (20, 72)], fill=1)))
    shape(JACKET, lambda d: d.rounded_rectangle((5, 66, 75, H + 8), radius=14, fill=1), 5)
    shape(hijab, lambda d: d.polygon([(28, 64), (52, 64), (40, 84)], fill=1))     # tucked into the collar
    shape(JACKET, lambda d: (d.line([(27, 64), (40, 86)], fill=1, width=4),      # the collar's two sides
                             d.line([(53, 64), (40, 86)], fill=1, width=4)), 2)
    shape(apron, lambda d: (d.rectangle((27, 86, 53, H), fill=1),                # the apron's bib
                            d.line([(29, 86), (33, 68)], fill=1, width=2),       # and its neck strap
                            d.line([(51, 86), (47, 68)], fill=1, width=2)), 3)
    shape(BUTTON, lambda d: [d.ellipse((x, y, x + 2, y + 2), fill=1) for x in (17, 61) for y in (78, 85)], 1)
    shape(SKIN, lambda d: d.ellipse((25, 21, 55, 61), fill=1), 4)               # the face
    shape(hijab, lambda d: (d.ellipse((20, 12, 60, 64), fill=1),                 # the hijab's oval around the face,
                            d.ellipse((26, 24, 54, 62), fill=0)), 3)             # low on the forehead
    fold = tuple(int(c * 0.72) for c in hijab)
    img = Image.new("1", (W, H), 0)
    d = ImageDraw.Draw(img)
    d.arc((13, 14, 37, 70), 120, 200, fill=1)                                    # folds of the hijab
    d.arc((43, 14, 67, 70), 340, 60, fill=1)
    d.line([(34, 66), (40, 80)], fill=1)
    rgb[np.array(img, bool) & inside] = fold
    rgb[lines] *= 0.55
    face(rgb, mood)
    rgb[44:46, 56:58] = (236, 210, 140)                                          # a pin at the side

    rgb = np.pad(rgb, ((TOP, 0), (0, 0), (0, 0)))
    inside = np.pad(inside, ((TOP, 0), (0, 0)))
    out = np.dstack([np.clip(rgb, 0, 255), inside * 255]).astype(np.uint8)
    near = np.zeros(inside.shape, bool)                                          # the outline around the figure
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        near |= np.roll(np.roll(inside, dy, axis=0), dx, axis=1)
    near[0] = False
    near[-1] = False
    out[near & ~inside] = (*INK, 255)
    return out


def face(rgb: np.ndarray, mood: str) -> None:
    """Brows, eyes, nose, cheeks and mouth for a mood (face centre x 40, eyes on row 38)."""
    def px(points, color) -> None:
        for x, y in points:
            rgb[y, x] = color

    def closed(x: int) -> None:                                # a smiling closed eye with a lash
        px([(x, 39), (x + 1, 38), (x + 2, 37), (x + 3, 37), (x + 4, 38), (x + 5, 39)], EYE)
        px([(x + 5 if x > 40 else x - 1, 38)], LASH)

    def opened(x: int, up: bool = False) -> None:              # an open eye with a shine and a lash
        y = 36 if up else 37
        px([(x + i, y + j) for i in range(1, 5) for j in range(3)], EYE)
        px([(x + 2, y), (x + 1, y + 1)], SHINE)
        px([(x + 5 if x > 40 else x, y - 1)], LASH)

    left, right = 31, 44
    px([(x, 33) for x in range(left, left + 6)] + [(x, 33) for x in range(right, right + 6)], BROW)
    if mood == "thinking":                                     # one brow raised
        px([(x, 32) for x in range(right + 1, right + 5)], BROW)
    if mood == "happy":
        closed(left)
        closed(right)
    elif mood == "wink":
        opened(left)
        closed(right)
    else:
        opened(left, mood == "thinking")
        opened(right, mood == "thinking")
    px([(40, 43), (41, 44)], tuple(int(c * 0.8) for c in SKIN))                  # the nose's shadow
    px([(x, y) for x in (30, 31, 32, 48, 49, 50) for y in (45, 46)], CHEEK)
    if mood in ("happy", "wink"):                              # a wide smile with teeth and a lower lip
        px([(x, 48) for x in range(35, 46)], LIP)
        px([(x, 49) for x in range(36, 45)], TEETH)
        px([(x, 50) for x in range(37, 44)], LIP)
        px([(34, 47), (46, 47)], LIP)
    elif mood == "alert":                                      # a round "oh"
        px([(39, 48), (40, 48), (41, 48), (38, 49), (42, 49), (38, 50), (42, 50), (39, 51), (40, 51), (41, 51)], LIP)
    else:                                                      # thinking: a small mouth to one side
        px([(x, 49) for x in range(39, 45)], LIP)


def big(arr: np.ndarray) -> Image.Image:
    img = Image.fromarray(arr, "RGBA")
    return img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST)


def main() -> None:
    hijab, apron = HIJABS[DEFAULT]
    for mood in MOODS:
        big(cook(mood, hijab, apron)).save(HERE / "assets" / f"chef_ref_middle_eastern_woman_{mood}.png", optimize=True)
    rows = [np.concatenate([np.array(big(cook(mood, h, a))) for mood in ("happy", "wink", "alert")], axis=1)
            for h, a in HIJABS.values()]
    sheet = Image.fromarray(np.concatenate(rows, axis=0))
    back = Image.new("RGBA", sheet.size, (236, 226, 208, 255))
    Image.alpha_composite(back, sheet).save(HERE / "previews" / "middle_eastern_woman_hd.png")


if __name__ == "__main__":
    main()
