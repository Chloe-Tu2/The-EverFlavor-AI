"""The Middle Eastern woman cook made from the team's own Middle Eastern chef (references/chefs/chef4_middle_eastern.png),
so she is in exactly their style: same face, eyes, smile, outline and palette. His headdress already frames the face
the way a hijab does; on her:
  - the black cord (agal) on top becomes part of the scarf;
  - the beard goes: a rounded chin, and the scarf wraps close under it;
  - brows a little finer, lashes at the eyes' outer corners, color on the lower lip;
  - the vest and robe become a white chef jacket with buttons, the scarf tucked into its collar, and an apron.
Every change is made in blocks of 4 pixels, the size of the reference's own pixels.

    python design/pixel-art/make_chef_from_ref.py   ->   assets/chef_ref_middle_eastern_woman_<mood>.png,
                                                         previews/middle_eastern_woman_from_ref.png
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
B = 4                                                   # the block every change is drawn in
INK = (58, 36, 40)
SCARF = {"white": (236, 230, 222), "rose": (201, 157, 146), "black": (60, 52, 58), "navy": (52, 64, 108)}
APRON = (54, 50, 58)
JACKET = [(196, 192, 186), (226, 222, 214), (250, 248, 242)]       # dark, mid, light
LIP, LASH, BUTTON = (184, 92, 92), (52, 34, 34), (170, 170, 178)


def blocks(draw_fn, shape: tuple[int, int]) -> np.ndarray:
    """A mask drawn on the 4-pixel grid, then enlarged to the picture."""
    h, w = shape
    img = Image.new("1", (w // B + 1, h // B + 1), 0)
    draw_fn(ImageDraw.Draw(img))
    return np.kron(np.array(img, np.uint8), np.ones((B, B), np.uint8))[:h, :w].astype(bool)


def outline(mask: np.ndarray) -> np.ndarray:
    """The mask's own edge, one block wide."""
    inner = mask.copy()
    for dy, dx in ((B, 0), (-B, 0), (0, B), (0, -B)):
        inner &= np.roll(np.roll(mask, dy, 0), dx, 1)
    return mask & ~inner


def woman(man: np.ndarray, scarf: tuple[int, int, int]) -> np.ndarray:
    img = man.copy()
    rgb = img[..., :3].astype(np.float32)
    alpha = img[..., 3] > 0
    h, w = alpha.shape
    lum = rgb.mean(axis=2)
    pinkish = (rgb[..., 0] > rgb[..., 2] + 10) & (lum > 110) & (lum < 215)    # the headdress' rose tones
    # the scarf: his rose headdress, in her color (keeping its light and shade)
    head = alpha & (pinkish | ((lum > 60) & (lum < 130))) & (np.arange(h)[:, None] < 150)
    head &= ~((np.abs(np.arange(w)[None, :] - 90) < 34) & (np.arange(h)[:, None] > 52))   # not the face
    tone = (lum / np.median(lum[head]))[..., None]
    # the black cord on top becomes scarf too
    edge = np.zeros_like(alpha)
    for dy, dx in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        edge |= ~np.roll(np.roll(alpha, dy, 0), dx, 1)
    cord = alpha & ~edge & (lum < 75) & (np.arange(h)[:, None] < 50)
    # chin and scarf under it, in place of the beard
    beard_zone = blocks(lambda d: d.rectangle((10, 23, 35, 38), fill=1), (h, w))
    beard = alpha & beard_zone & (lum < 95)
    mouth = blocks(lambda d: d.rectangle((17, 26, 27, 29), fill=1), (h, w))
    chin = blocks(lambda d: d.ellipse((14, 14, 31, 35), fill=1), (h, w))
    skin = np.array((217, 154, 119), np.float32)

    out = rgb.copy()
    scarf_c = np.array(scarf, np.float32)
    out[head] = np.clip(scarf_c * tone[head], 0, 255)
    out[cord] = scarf_c * 0.86
    out[beard & chin & ~mouth] = skin
    out[beard & ~chin & ~mouth] = scarf_c * 0.9
    jaw = outline(chin) & beard_zone & ~mouth & (np.arange(h)[:, None] > 100)
    out[jaw & alpha] = INK
    # finer brows (the lower block of each goes), lashes, a colored lower lip
    brows = blocks(lambda d: (d.rectangle((13, 16, 18, 16), fill=1), d.rectangle((26, 16, 31, 16), fill=1)), (h, w))
    out[brows & (lum < 80)] = skin
    lash = blocks(lambda d: (d.point((13, 19), fill=1), d.point((31, 19), fill=1)), (h, w))
    out[lash] = LASH
    lip = blocks(lambda d: d.rectangle((19, 30, 25, 30), fill=1), (h, w))
    out[lip & alpha] = LIP

    # the jacket: the shoulders repainted white, lit from the left, inside the picture's own outline
    rim = np.zeros_like(alpha)
    for dy, dx in ((B, 0), (-B, 0), (0, B), (0, -B)):
        rim |= ~np.roll(np.roll(alpha, dy, 0), dx, 1)
    body = alpha & (np.arange(h)[:, None] >= 146) & ~blocks(lambda d: d.ellipse((14, 14, 31, 35), fill=1), (h, w))
    xs = np.broadcast_to(np.arange(w)[None, :], (h, w))
    out[body] = JACKET[1]
    out[body & (xs < w * 0.3)] = JACKET[2]
    out[body & (xs > w * 0.75)] = JACKET[0]
    out[body & rim] = INK
    # the scarf tucked into the collar, the apron and its strap, buttons
    tuck = blocks(lambda d: d.polygon([(15, 35), (29, 35), (22, 43)], fill=1), (h, w)) & alpha
    out[tuck] = scarf_c * 0.95
    out[outline(tuck) & (np.arange(h)[:, None] > 145)] = INK
    apron = blocks(lambda d: (d.rectangle((16, 43, 28, 52), fill=1),
                              d.line([(17, 43), (19, 37)], fill=1), d.line([(27, 43), (25, 37)], fill=1)), (h, w)) & alpha
    out[apron] = APRON
    out[outline(apron) & (np.arange(h)[:, None] > 170)] = INK
    buttons = blocks(lambda d: [d.point((x, y), fill=1) for x in (10, 34) for y in (43, 47)], (h, w)) & alpha
    out[buttons] = BUTTON
    return np.dstack([np.clip(out, 0, 255), img[..., 3]]).astype(np.uint8)


def main() -> None:
    man = np.array(Image.open(HERE / "assets" / "chef_ref_middle_eastern_happy.png").convert("RGBA"))
    sheet = []
    for name, color in SCARF.items():
        her = woman(man, color)
        if name == "white":
            for mood in ("happy", "alert", "thinking", "wink"):
                Image.fromarray(her, "RGBA").save(HERE / "assets" / f"chef_ref_middle_eastern_woman_{mood}.png")
        sheet.append(her)
    row = np.concatenate([man] + sheet, axis=1)
    back = Image.new("RGBA", (row.shape[1], row.shape[0]), (236, 226, 208, 255))
    Image.alpha_composite(back, Image.fromarray(row, "RGBA")).save(HERE / "previews" / "middle_eastern_woman_from_ref.png")


if __name__ == "__main__":
    main()
