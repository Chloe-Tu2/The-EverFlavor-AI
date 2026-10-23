"""The regional chefs from the team's references (references/chefs/): the background cut away (the light card and the
checkerboard some of them have painted in), saved as assets/chef_ref_<region>_<mood>.png for the app's chef.

Each reference is one portrait for now, so every mood uses it (the app makes the chef hop when tapped). The woman
cook of each region and the regions without a reference (Mexican, Moroccan) are still to come (planner, 0.5.2).

    python design/pixel-art/make_chefs.py
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
# reference -> (region, its background: a painted "checker" board or a warm "card")
REGIONS = {"chef1_asian_headband": ("japanese", "checker"), "chef3_asian_scarf": ("chinese", "checker"),
           "chef2_classic_white_hat": ("classic", "card"), "chef4_middle_eastern": ("middle_eastern", "card")}
MARGIN = 8                       # the background is found from this band along the edge (some have a frame line)
MOODS = ("happy", "alert", "thinking", "wink")


def cut(img: np.ndarray, kind: str) -> np.ndarray:
    """RGBA with the background transparent: the background's pixels (light neutral greys for a checkerboard, light
    warm cream for a card, so a white chef's coat stays) connected to the band along the edge."""
    rgb = img[..., :3].astype(int)
    spread, warm = rgb.max(axis=2) - rgb.min(axis=2), rgb[..., 0] - rgb[..., 2]
    if kind == "checker":
        light = (rgb.min(axis=2) > 140) & (spread < 30)
    else:
        light = (rgb.min(axis=2) > 200) & (warm > 8)
    _, labels = cv2.connectedComponents(light.astype(np.uint8), connectivity=4)
    band = np.concatenate([labels[:MARGIN].ravel(), labels[-MARGIN:].ravel(),
                           labels[:, :MARGIN].ravel(), labels[:, -MARGIN:].ravel()])
    edge = set(np.unique(band)) - {0}
    background = np.isin(labels, list(edge)) & light
    if kind == "checker":                               # and the thin grey frame line some boards have
        frame = np.zeros(light.shape, bool)
        frame[:4], frame[-4:], frame[:, :4], frame[:, -4:] = True, True, True, True
        background |= frame & (spread < 30) & (rgb.min(axis=2) > 90)
    alpha = np.where(background, 0, 255).astype(np.uint8)
    return np.dstack([img[..., :3], alpha])


def main() -> None:
    for ref, (region, kind) in REGIONS.items():
        img = np.array(Image.open(HERE / "references" / "chefs" / f"{ref}.png").convert("RGBA"))
        out = cut(img, kind)
        ys, xs = np.nonzero(out[..., 3])
        out = out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        for mood in MOODS:
            Image.fromarray(out, "RGBA").save(HERE / "assets" / f"chef_ref_{region}_{mood}.png", optimize=True)
        print(region, out.shape[1], "x", out.shape[0])


if __name__ == "__main__":
    main()
