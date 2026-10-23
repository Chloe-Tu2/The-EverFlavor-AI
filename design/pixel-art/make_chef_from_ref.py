"""The Middle Eastern woman cook made from the team's own Middle Eastern chef (references/chefs/chef4_middle_eastern.png),
so she is in exactly their style: same face, eyes, smile, outline and palette. His headdress already frames the face
the way a hijab does; on her:
  - the black cord (agal) on top becomes part of the scarf;
  - the beard goes: a rounded chin, and the scarf wraps close under it;
  - brows a little finer, lashes at the eyes' outer corners, color on the lower lip;
  - the vest and robe become a white chef jacket with buttons, the scarf tucked into its collar, and an apron.
Every change is made in blocks of 4 pixels, the size of the reference's own pixels.

    python design/pixel-art/make_chef_from_ref.py   ->   assets/chef_ref_middle_eastern_woman_<mood>.png,
                                                         previews/middle_eastern_woman.png
"""
from __future__ import annotations

from pathlib import Path

import cv2
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
    ys = np.broadcast_to(np.arange(h)[:, None], (h, w))
    # her face: his skin with the eyes, brows and mouth inside it, widened to a rounded chin where the beard was.
    # The hijab is never painted inside it, and a dark line one block wide frames it.
    skinlike = alpha & (rgb[..., 0] - rgb[..., 2] > 75) & (rgb[..., 0] > 170)
    closed = cv2.morphologyEx(skinlike.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    filled = closed.copy()
    flood = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(filled, flood, (0, 0), 1)
    face = (closed | (1 - filled)).astype(bool)
    chin = blocks(lambda d: d.ellipse((11, 13, 34, 36), fill=1), (h, w))
    face = (face | chin) & (ys >= 52) & (ys < 150)
    # the scarf: his headdress (everything around the face above the shoulders), in her color with its shading
    head = alpha & ~face & (ys < 150) & (lum > 60)
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
    skin = np.array((217, 154, 119), np.float32)

    out = rgb.copy()
    scarf_c = np.array(scarf, np.float32)
    out[head] = np.clip(scarf_c * tone[head], 0, 255)
    out[cord] = scarf_c * 0.86
    out[beard & face & ~mouth] = skin
    out[beard & ~face & ~mouth] = scarf_c * 0.9
    # leftover specks inside the face (the beard's edge, the headdress' shadow) become skin; the eyes, brows,
    # nose and mouth stay
    nose = blocks(lambda d: d.rectangle((19, 24, 25, 25), fill=1), (h, w))
    speck = face & ~skinlike & ~mouth & ~nose & (((ys < 100) & (lum >= 80)) | (ys >= 100))
    out[speck] = skin
    out[outline(face) & alpha & ~mouth] = INK
    # finer brows (the lower block of each goes), lashes, a colored lower lip
    brows = blocks(lambda d: (d.rectangle((13, 16, 18, 16), fill=1), d.rectangle((26, 16, 31, 16), fill=1)), (h, w))
    out[brows & (lum < 80)] = skin
    lash = blocks(lambda d: (d.point((13, 19), fill=1), d.point((31, 19), fill=1)), (h, w))
    out[lash] = LASH
    lip = blocks(lambda d: d.rectangle((19, 30, 25, 30), fill=1), (h, w))
    out[lip & alpha] = LIP

    return redraw(out, face, scarf_c)


def redraw(out: np.ndarray, face: np.ndarray, scarf: np.ndarray) -> np.ndarray:
    """Her hijab and jacket drawn again on the reference's 4-pixel grid, after the photos of women chefs in a hijab
    (references/chefs/women/): the hijab rounded close around the head (not his peaked headdress and cape), wrapped
    under the chin and falling into the jacket's stand collar; a double-breasted chef jacket and an apron. Flat
    tones lit from the top left and a dark line between every part, as in the team's chefs. The face is his."""
    h, w = face.shape
    gh, gw = -(-h // B), -(-w // B)

    def grid(draw_fn) -> np.ndarray:
        img = Image.new("1", (gw, gh), 0)
        draw_fn(ImageDraw.Draw(img))
        return np.array(img, bool)

    def shift(m: np.ndarray, dy: int, dx: int) -> np.ndarray:
        r = np.zeros_like(m)
        r[max(dy, 0):gh + min(dy, 0), max(dx, 0):gw + min(dx, 0)] = m[max(-dy, 0):gh - max(dy, 0), max(-dx, 0):gw - max(dx, 0)]
        return r

    face_g = face[B // 2::B, B // 2::B][:gh, :gw]
    face_g = np.pad(face_g, ((0, gh - face_g.shape[0]), (0, gw - face_g.shape[1])))
    hijab = grid(lambda d: (d.ellipse((7, 1, 37, 42), fill=1),
                            d.polygon([(10, 33), (35, 33), (30, 42), (22, 46), (15, 42)], fill=1))) & ~face_g
    body = grid(lambda d: d.rounded_rectangle((1, 38, gw - 2, gh + 4), radius=6, fill=1)) & ~hijab & ~face_g
    collar = grid(lambda d: (d.polygon([(13, 37), (17, 37), (21, 45)], fill=1),
                             d.polygon([(32, 37), (28, 37), (24, 45)], fill=1))) & body
    apron = grid(lambda d: (d.rectangle((16, 45, 29, gh), fill=1),
                            d.line([(17, 45), (19, 39)], fill=1), d.line([(28, 45), (26, 39)], fill=1))) & body
    buttons = grid(lambda d: [d.point((x, y), fill=1) for x in (9, 12, 33, 36) for y in (44, 48)]) & body & ~apron

    canvas = np.zeros((gh, gw, 3), np.float32)
    label = np.zeros((gh, gw), int)
    xs = np.broadcast_to(np.arange(gw)[None, :], (gh, gw))
    canvas[body] = JACKET[1]
    canvas[body & (xs < gw * 0.3)] = JACKET[2]
    canvas[body & (xs > gw * 0.72)] = JACKET[0]
    label[body] = 1
    canvas[collar] = JACKET[2]
    label[collar] = 2
    canvas[hijab] = scarf
    canvas[hijab & ~shift(hijab, 2, 2)] = np.minimum(scarf * 1.1 + 12, 255)          # light along the top left
    canvas[hijab & ~shift(hijab, -2, -2)] = scarf * 0.8                               # shade along the bottom right
    folds = grid(lambda d: (d.arc((4, 12, 20, 52), 120, 200, fill=1), d.arc((25, 12, 41, 52), 340, 60, fill=1),
                            d.line([(22, 40), (22, 45)], fill=1))) & hijab
    canvas[folds] = scarf * 0.84
    label[hijab] = 3
    canvas[apron] = APRON
    label[apron] = 4
    canvas[buttons] = BUTTON
    solid = label > 0
    ink = np.zeros_like(solid)
    for dy, dx in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        ink |= shift(solid | face_g, dy, dx)
    ink &= ~solid & ~face_g                                                           # the outline around her
    ink |= solid & ((label != shift(label, 1, 0)) | (label != shift(label, 0, 1))) & shift(solid, 1, 0) & shift(solid, 0, 1)
    face_edge = face_g & ~(shift(face_g, 1, 0) & shift(face_g, -1, 0) & shift(face_g, 0, 1) & shift(face_g, 0, -1))
    canvas[ink] = INK

    def up(m: np.ndarray) -> np.ndarray:
        return m.repeat(B, axis=0).repeat(B, axis=1)[:h, :w]

    rgb = up(canvas)
    face_px = up(face_g)                                                              # the face, on the same grid
    rgb[face_px] = out[face_px]
    rgb[up(face_edge)] = INK
    alpha = up(solid | ink) | face_px
    return np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)


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
    Image.alpha_composite(back, Image.fromarray(row, "RGBA")).save(HERE / "previews" / "middle_eastern_woman.png")


if __name__ == "__main__":
    main()
