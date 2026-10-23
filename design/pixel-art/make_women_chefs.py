"""The woman cook of each region, drawn in the style of the team's chef references (references/chefs/): a round
face with closed, smiling eyes, a dark outline and light from the top left. Each is drawn on a 40 x 46 grid and
saved four times larger as assets/chef_ref_<region>_woman_<mood>.png, one face per mood.

What each one wears (sources in references/chefs/README.md):
  - japanese: a white kappogi (the cooking smock first taught at the Akahori Kappo school in 1902) over an indigo
    kimono collar, hair in a bun under a white tenugui headband
  - chinese: a white jacket with a mandarin collar and red frog buttons, as on samfoo work clothes, hair in a bun
  - classic: a white toque, a double-breasted white jacket and a red neckerchief, like the classic chef reference
  - middle_eastern: drawn by make_chef_from_ref.py from the team's own Middle Eastern chef, to match his style

    python design/pixel-art/make_women_chefs.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
W, H, SCALE = 40, 46, 4
TOP = 3                                                       # empty rows added above the drawing, for the outline
INK, WHITE, CHEEK, MOUTH, TEETH = (64, 39, 42), (252, 250, 244), (236, 140, 130), (150, 50, 56), (255, 255, 255)
MOODS = ("happy", "alert", "thinking", "wink")

LOOKS = {
    "japanese": {"skin": (238, 192, 152), "hair": (46, 34, 34), "cloth": WHITE, "accent": (44, 58, 104)},
    "chinese": {"skin": (232, 182, 138), "hair": (36, 28, 30), "cloth": (246, 242, 230), "accent": (186, 40, 40)},
    "classic": {"skin": (240, 198, 162), "hair": (110, 66, 40), "cloth": WHITE, "accent": (196, 44, 44)},
    "middle_eastern": {"skin": (214, 152, 112), "hair": (40, 30, 30), "cloth": WHITE,
                       "accent": (236, 232, 222), "apron": (46, 44, 52)},
}
# The Middle Eastern cook's choices: a plain hijab in one color with the white chef jacket, and the apron's color
HIJABS = {
    "white": {"accent": (236, 232, 222), "apron": (46, 44, 52)},
    "black": {"accent": (44, 40, 48), "apron": (110, 70, 44)},
    "navy": {"accent": (44, 58, 104), "apron": (46, 44, 52)},
    "rose": {"accent": (200, 132, 140), "apron": (110, 70, 44)},
}


def figure(region: str, mood: str, look: dict | None = None) -> np.ndarray:
    """The cook drawn in layers, each over the last, then shaded and outlined; returns RGBA. look overrides the
    region's colors (the hijab variations)."""
    look = {**LOOKS[region], **(look or {})}
    layers: list[tuple[tuple[int, int, int], Image.Image]] = []

    def layer(color: tuple[int, int, int]) -> ImageDraw.ImageDraw:
        mask = Image.new("1", (W, H), 0)
        layers.append((color, mask))
        return ImageDraw.Draw(mask)

    if region == "middle_eastern":                           # the scarf behind the head, falling to the shoulders
        d = layer(look["accent"])
        d.ellipse((8, 5, 31, 33), fill=1)
        d.rectangle((7, 26, 32, 40), fill=1)
    d = layer(look["cloth"])                                 # shoulders
    d.rounded_rectangle((3, 34, 36, H + 4), radius=7, fill=1)
    if region == "middle_eastern":
        d = layer(look["accent"])                            # the hijab over the shoulders
        d.polygon([(9, 30), (30, 30), (32, 37), (7, 37)], fill=1)
    d = layer(look["skin"])                                  # neck, ears and face
    if region != "middle_eastern":
        d.rectangle((16, 28, 23, 35), fill=1)
        d.ellipse((9, 18, 12, 24), fill=1)
        d.ellipse((27, 18, 30, 24), fill=1)
    d.ellipse((11, 10, 28, 31), fill=1)
    if region in ("japanese", "chinese"):
        d = layer(look["hair"])
        d.ellipse((10, 7, 29, 17), fill=1)                   # hair over the top of the head
        d.ellipse((15, 1, 24, 9), fill=1)                    # the bun
        d.rectangle((10, 12, 12, 23), fill=1)
        d.rectangle((27, 12, 29, 23), fill=1)
        d = layer(look["skin"])                              # the forehead under the parted hair
        d.polygon([(13, 17), (20, 12), (27, 17)], fill=1)
        if region == "japanese":
            d = layer(WHITE)                                 # the tenugui headband, knotted at the side
            d.rectangle((10, 12, 29, 14), fill=1)
            d.rectangle((29, 11, 32, 13), fill=1)
    elif region == "classic":
        d = layer(look["hair"])                              # hair at the sides, under the hat
        d.rectangle((10, 12, 13, 24), fill=1)
        d.rectangle((26, 12, 29, 24), fill=1)
        d = layer(WHITE)                                     # the toque: a puffed crown on a band
        d.ellipse((8, 0, 31, 11), fill=1)
        d.rectangle((11, 8, 28, 14), fill=1)
    else:
        d = layer(look["accent"])                            # the scarf framing the face
        d.ellipse((10, 7, 29, 17), fill=1)
        d.rectangle((10, 12, 12, 30), fill=1)
        d.rectangle((27, 12, 29, 30), fill=1)

    if region == "japanese":                                 # the kimono collar crossing at the neck
        d = layer(look["accent"])
        d.line([(15, 34), (20, 41)], fill=1, width=2)
        d.line([(25, 34), (20, 41)], fill=1, width=2)
    elif region == "chinese":
        d = layer(look["cloth"])                             # the mandarin collar
        d.rectangle((15, 33, 24, 35), fill=1)
        d = layer(look["accent"])                            # frog buttons down the side opening
        for x, y in ((22, 38), (24, 41), (26, 44)):
            d.rectangle((x, y, x + 2, y), fill=1)
    elif region == "classic":
        d = layer(look["accent"])                            # the neckerchief
        d.polygon([(14, 33), (26, 33), (20, 40)], fill=1)
        d = layer((190, 190, 196))                           # two rows of buttons
        for y in (40, 43):
            d.point((15, y), fill=1)
            d.point((25, y), fill=1)
    else:
        d = layer(look["apron"])                             # the apron's bib, over the chef jacket
        d.rectangle((13, 40, 26, H), fill=1)
        d = layer((190, 190, 196))                           # the jacket's buttons, either side of the bib
        for y in (39, 42, 45):
            d.point((10, y), fill=1)
            d.point((29, y), fill=1)

    rgb = np.zeros((H, W, 3), np.float32)
    z = np.full((H, W), -1)
    for i, (color, mask) in enumerate(layers):
        m = np.array(mask, bool)
        rgb[m] = color
        z[m] = i
    inside = z >= 0
    for i in range(len(layers)):                             # light from the top left: lower right edges darker
        m = z == i
        edge = m & ~(np.roll(m, -1, axis=1) & np.roll(m, -1, axis=0))
        rgb[edge] *= 0.86
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):        # a dark line where a shape lies over another
        nz = np.roll(np.roll(z, dy, axis=0), dx, axis=1)
        rgb[inside & (nz > z) & (nz >= 0)] *= 0.62
    face(rgb, mood)
    rgb, inside = np.pad(rgb, ((TOP, 0), (0, 0), (0, 0))), np.pad(inside, ((TOP, 0), (0, 0)))   # room above the head
    out = np.dstack([np.clip(rgb, 0, 255), inside * 255]).astype(np.uint8)
    near = np.zeros(inside.shape, bool)                            # the outline: every empty pixel next to the figure
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        near |= np.roll(np.roll(inside, dy, axis=0), dx, axis=1)
    near[0] = False                                          # (the roll wraps the bottom row to the top)
    out[near & ~inside] = (*INK, 255)
    return out


def face(rgb: np.ndarray, mood: str) -> None:
    """Eyes, cheeks and mouth for a mood (eyes on row 20, mouth from row 25)."""
    def px(x: int, y: int, color: tuple[int, int, int]) -> None:
        rgb[y, x] = color

    def closed(x: int) -> None:                              # a happy closed eye
        for dx, dy in ((0, 1), (1, 0), (2, 0), (3, 1)):
            px(x + dx, 20 + dy, INK)

    def opened(x: int, look_up: bool = False) -> None:       # an open eye with a shine
        y = 19 if look_up else 20
        for dx in (1, 2):
            px(x + dx, y, INK)
            px(x + dx, y + 1, INK)
        px(x + 1, y, WHITE)

    left, right = 14, 22
    if mood == "happy":
        closed(left)
        closed(right)
    elif mood == "wink":
        opened(left)
        closed(right)
    else:
        opened(left, mood == "thinking")
        opened(right, mood == "thinking")
    for x in (13, 14, 25, 26):                               # cheeks
        px(x, 24, CHEEK)
    if mood in ("happy", "wink"):                            # a wide smile with teeth
        for x in range(17, 23):
            px(x, 25, MOUTH)
            px(x, 26, TEETH)
        for x in range(18, 22):
            px(x, 27, MOUTH)
    elif mood == "alert":                                    # a small round "oh"
        for x, y in ((19, 25), (20, 25), (18, 26), (21, 26), (19, 27), (20, 27)):
            px(x, y, MOUTH)
    else:                                                    # thinking: a little sideways mouth
        for x in range(19, 23):
            px(x, 26, MOUTH)


def variations() -> None:
    """previews/middle_eastern_woman_variations.png: each hijab color, happy and wink."""
    rows = []
    for colors in HIJABS.values():
        faces = [Image.fromarray(figure("middle_eastern", mood, colors), "RGBA")
                 .resize((W * SCALE, (H + TOP) * SCALE), Image.NEAREST) for mood in ("happy", "wink")]
        rows.append(np.concatenate([np.array(f) for f in faces], axis=1))
    sheet = Image.fromarray(np.concatenate(rows, axis=1))
    back = Image.new("RGBA", sheet.size, (236, 226, 208, 255))
    Image.alpha_composite(back, sheet).save(HERE / "previews" / "middle_eastern_woman_variations.png")


def main() -> None:
    rows = []
    for region in (r for r in LOOKS if r != "middle_eastern"):   # she comes from make_chef_from_ref.py
        row = []
        for mood in MOODS:
            img = Image.fromarray(figure(region, mood), "RGBA").resize((W * SCALE, (H + TOP) * SCALE), Image.NEAREST)
            img.save(HERE / "assets" / f"chef_ref_{region}_woman_{mood}.png", optimize=True)
            row.append(np.array(img))
        rows.append(np.concatenate(row, axis=1))
    sheet = Image.fromarray(np.concatenate(rows, axis=0))
    back = Image.new("RGBA", sheet.size, (236, 226, 208, 255))
    Image.alpha_composite(back, sheet).save(HERE / "previews" / "women_chefs.png")


if __name__ == "__main__":
    main()
