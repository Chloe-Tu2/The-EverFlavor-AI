"""Day and night for the v5 kitchens: morning, evening and night versions of each traced kitchen.

Starts from the finished day kitchen (drafts/traced-kitchens/<name>/<name>.png, left as it is) and changes the
light, not the drawing:
  - the room takes the light of the hour (a tint and a brightness);
  - what is seen through the windows (sky, trees, town) gets the sky of the hour; at night, stars;
  - the lanterns (every traced object named lantern or lamp, from scene.json), the fire and candles keep the room
    lit around them: warm glows that fade out in dithered bands, the pixel-art way. They are off in the morning,
    half on in the evening, full at night;
  - each picture is put back on a palette of its own (64 colors), so it stays pixel art.

    python design/pixel-art/day_night.py   ->   drafts/traced-kitchens/<name>/<name>_<time>.png, compare_day_night.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
TRACED = HERE / "drafts" / "traced-kitchens"
SCALE = 4                                    # the traced kitchens are the originals at a quarter size
COLORS = 64
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16

# Window openings (x0, y0, x1, y1) on the original, 1672 x 941: what is inside and looks like outdoors gets the sky
WINDOWS = {
    "chinese": [(80, 110, 430, 570)],
    "mediterranean": [(1035, 365, 1215, 560)],
    "mexican": [(70, 110, 330, 560), (1025, 280, 1235, 495)],
    "middle_eastern": [(0, 250, 140, 620), (1065, 230, 1250, 510)],
}
# Lights that are no traced object: fire and candles (x, y, reach) on the original; lanterns come from scene.json
FLAMES = {"mediterranean": [(265, 530, 420), (583, 595, 110)]}
LANTERN_REACH = 230

# The hours: room tint (r, g, b multipliers), sky color and how much of it, lights (0 off to 1 full)
TIMES = {
    "morning": {"room": (1.04, 0.98, 0.92), "sky": (255, 214, 170), "sky_mix": 0.45, "lights": 0.0, "stars": False},
    "evening": {"room": (0.92, 0.74, 0.62), "sky": (240, 120, 90), "sky_mix": 0.6, "lights": 0.6, "stars": False},
    "night": {"room": (0.36, 0.40, 0.62), "sky": (22, 30, 70), "sky_mix": 0.85, "lights": 1.0, "stars": True},
}


def outdoors(img: np.ndarray, boxes: list[tuple[int, int, int, int]]) -> np.ndarray:
    """Inside the window boxes, the pixels that look like outdoors (sky, foliage, far walls): bluish, greenish or
    bright, not the brown wood of the frame."""
    h, w = img.shape[:2]
    rgb = img.astype(np.int32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    looks_out = (b > r * 0.9) | (g > r * 0.95) | (rgb.max(axis=2) > 225)
    mask = np.zeros((h, w), bool)
    for x0, y0, x1, y1 in boxes:
        mask[y0 // SCALE:y1 // SCALE, x0 // SCALE:x1 // SCALE] = True
    return mask & looks_out


def lights_of(name: str) -> list[tuple[float, float, float]]:
    """(x, y, reach) on the pixel grid: every lantern or lamp of the kitchen's scene, and its flames."""
    pieces = json.loads((TRACED / name / "scene.json").read_text(encoding="utf-8"))["pieces"]
    found = [(p["x"] + p["w"] / 2, p["y"] + p["h"] / 2, LANTERN_REACH / SCALE)
             for key, p in pieces.items() if "lantern" in key or "lamp" in key]
    found += [(x / SCALE, y / SCALE, r / SCALE) for x, y, r in FLAMES.get(name, [])]
    return found


def lamp_mask(name: str, shape: tuple[int, int]) -> np.ndarray:
    """The lanterns' own pixels, which stay as bright as by day."""
    pieces = json.loads((TRACED / name / "scene.json").read_text(encoding="utf-8"))["pieces"]
    mask = np.zeros(shape, bool)
    for key, p in pieces.items():
        if "lantern" in key or "lamp" in key:
            sprite = np.array(Image.open(TRACED / name / "sprites" / f"{key}.png").convert("RGBA"))[..., 3] > 0
            mask[p["y"]:p["y"] + p["h"], p["x"]:p["x"] + p["w"]] |= sprite
    return mask


def glow_of(lights: list[tuple[float, float, float]], shape: tuple[int, int]) -> np.ndarray:
    """How lit each pixel is by the lights, 0 to 1, in four dithered steps."""
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    glow = np.zeros(shape)
    for x, y, reach in lights:
        glow = np.maximum(glow, np.clip(1 - np.hypot(xx - x, yy - y) / reach, 0, 1) ** 1.3)
    dither = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w]
    return np.floor(glow * 4 + dither * 0.9) / 4                    # bands with dithered edges


def palette_of(img: np.ndarray, k: int) -> np.ndarray:
    data = img.reshape(-1, 3).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    cv2.setRNGSeed(7)
    _, labels, centers = cv2.kmeans(data, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    return centers.astype(np.uint8)[labels.ravel()].reshape(img.shape)


def hour(name: str, day: np.ndarray, time: str) -> np.ndarray:
    t = TIMES[time]
    h, w = day.shape[:2]
    img = day.astype(np.float32)
    room = np.clip(img * np.array(t["room"], np.float32), 0, 255)
    out_mask = outdoors(day, WINDOWS.get(name, []))
    sky = np.array(t["sky"], np.float32)
    shade = img.mean(axis=2, keepdims=True) / 255                      # keep the outdoor shapes readable
    outside = img * (1 - t["sky_mix"]) + sky * t["sky_mix"] * (0.55 + 0.9 * shade)
    if t["stars"]:
        rng = np.random.default_rng(len(name))
        stars = (rng.random((h, w)) < 0.012) & out_mask & (img.mean(axis=2) > 120)
        outside[stars] = (255, 246, 210)
    result = np.where(out_mask[..., None], outside, room)
    if t["lights"] > 0:                                                 # warm lamplight brings the day colors back
        glow = glow_of(lights_of(name), (h, w))[..., None] * t["lights"] * ~out_mask[..., None]
        warm = np.clip(img * np.array((1.12, 1.0, 0.82), np.float32), 0, 255)
        result = result * (1 - glow) + warm * glow
        result = np.where(lamp_mask(name, (h, w))[..., None], img, result)   # the lanterns stay bright
    return palette_of(np.clip(result, 0, 255).astype(np.uint8), COLORS)


def main(names: list[str]) -> None:
    rows = []
    for name in names:
        folder = TRACED / name
        day = np.array(Image.open(folder / f"{name}.png").convert("RGB"))
        versions = {"morning": hour(name, day, "morning"), "day": day,
                    "evening": hour(name, day, "evening"), "night": hour(name, day, "night")}
        for time, img in versions.items():
            if time == "day":
                continue
            Image.fromarray(img).save(folder / f"{name}_{time}.png")
            Image.fromarray(img).resize((img.shape[1] * 4, img.shape[0] * 4), Image.NEAREST).save(folder / f"{name}_{time}_x4.png")
        row = np.concatenate([np.pad(np.kron(v, np.ones((2, 2, 1), np.uint8)), ((0, 0), (0, 6), (0, 0)), constant_values=255)
                              for v in versions.values()], axis=1)
        rows.append(np.pad(row, ((0, 6), (0, 0), (0, 0)), constant_values=255))
        print(f"{name}: morning, evening, night written to {folder}")
    Image.fromarray(np.concatenate(rows, axis=0)).save(TRACED / "compare_day_night.png")


if __name__ == "__main__":
    main(sys.argv[1:] or list(WINDOWS))
