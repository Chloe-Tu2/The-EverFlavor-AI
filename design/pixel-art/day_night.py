"""Day and night for the v5 kitchens: morning, afternoon, evening and night versions of each traced kitchen.

Starts from the finished kitchen (drafts/traced-kitchens/<name>/<name>.png, left as it is) and changes the light,
not the drawing:
  - the room takes the light of the hour. Morning is fresh: shadows a little cooler, highlights golden, and beams of
    low sunlight slanting in from the windows. Evening is warm, with long orange beams. Night is dark blue;
  - what is seen through the windows (sky, trees, town) gets the sky of the hour; at night, stars;
  - a sun drawn in a window is moved to where the hour puts it (low on the left in the morning, high in the
    afternoon, low on the right in the evening) and becomes a moon at night, always behind the window's buildings;
  - the lanterns (every traced object named lantern or lamp, from scene.json), the fire and candles light the room
    around them: warm glows that fade out in dithered bands, the pixel-art way. Off in the morning and afternoon,
    half on in the evening, full at night;
  - each picture is put back on a palette of its own (64 colors), so it stays pixel art.

    python design/pixel-art/day_night.py   ->   drafts/traced-kitchens/<name>/<name>_<hour>.png, compare_day_night.png
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
# A sun drawn in a window: where it is (x, y on the pixel grid), its radius, and where each hour puts it
SUNS = {
    "middle_eastern": {"at": (277, 100), "radius": 6,
                       "morning": (275, 108), "afternoon": (289, 72), "evening": (301, 90), "night": (300, 70)},
}
# Lights that are no traced object: fire and candles (x, y, reach) on the original; lanterns come from scene.json
FLAMES = {"mediterranean": [(265, 530, 420), (583, 595, 110)]}
LANTERN_REACH = 230

# The hours. room: color multipliers; cool: how much the shadows turn blue; gold: how much the highlights turn
# golden; beams: color and strength of the sunlight slanting in (none at night); sky: its color and how much of it;
# sun: the sun's color (None leaves it as drawn); lights: the lanterns and flames, 0 off to 1 full.
TIMES: dict[str, dict] = {
    "morning": {"room": (1.08, 1.07, 1.04), "cool": 0.55, "gold": 0.3, "haze": 0.22, "beams": ((255, 240, 200), 0.5),
                "sky": (255, 222, 190), "sky_mix": 0.35, "sun": (255, 246, 214), "lights": 0.0, "stars": False},
    "afternoon": {"room": (1.0, 1.0, 1.0), "cool": 0.0, "gold": 0.0, "beams": None,
                  "sky": (150, 200, 245), "sky_mix": 0.0, "sun": (255, 250, 228), "lights": 0.0, "stars": False},
    "evening": {"room": (0.92, 0.76, 0.64), "cool": 0.0, "gold": 0.0, "beams": ((255, 150, 80), 0.28),
                "sky": (240, 120, 90), "sky_mix": 0.6, "sun": (255, 214, 130), "lights": 0.6, "stars": False},
    "night": {"room": (0.36, 0.40, 0.62), "cool": 0.0, "gold": 0.0, "beams": None,
              "sky": (22, 30, 70), "sky_mix": 0.85, "sun": (226, 232, 240), "lights": 1.0, "stars": True},
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


def move_sun(name: str, img: np.ndarray, time: str) -> np.ndarray:
    """Paint the window's sun out of the sky and draw it again where the hour puts it, in the hour's color. It is
    drawn only on sky (light pixels), so the buildings in front of it stay in front."""
    sun = SUNS.get(name)
    if not sun:
        return img
    (x, y), r = sun["at"], sun["radius"]
    disc = np.zeros(img.shape[:2], np.uint8)
    cv2.circle(disc, (x, y), r + 1, 255, -1)
    sky = cv2.inpaint(img, disc, 4, cv2.INPAINT_TELEA)                  # the sky without the sun
    nx, ny = sun[time]
    color = np.array(TIMES[time]["sun"], np.float32)
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    dist = np.hypot(xx - nx, yy - ny)
    is_sky = sky.mean(axis=2) > 150                                     # buildings are darker: they stay in front
    out = sky.astype(np.float32)
    halo = np.clip(1 - (dist - r) / (r * 1.6), 0, 1) * 0.35 * is_sky    # a soft ring of light around it
    out = out * (1 - halo[..., None]) + color * halo[..., None]
    core = (dist <= r) & is_sky
    out[core] = color
    if time == "night":                                                 # a crescent: a darker bite out of the moon
        out[(np.hypot(xx - nx - r * 0.6, yy - ny + r * 0.3) <= r * 0.85) & core] = sky[(np.hypot(
            xx - nx - r * 0.6, yy - ny + r * 0.3) <= r * 0.85) & core]
    return np.clip(out, 0, 255).astype(np.uint8)


def beams(boxes: list[tuple[int, int, int, int]], shape: tuple[int, int], sun_left: bool) -> np.ndarray:
    """Shafts of low sunlight: each window's opening slid down and across the room, the way a low sun throws it,
    strongest near the window and fading out, in dithered bands."""
    h, w = shape
    light = np.zeros(shape, np.float32)
    for x0, y0, x1, y1 in boxes:
        x0, y0, x1, y1 = x0 // SCALE, y0 // SCALE, x1 // SCALE, y1 // SCALE
        dx = (1 if (x0 + x1) / 2 < w / 2 else -1) * (60 if sun_left else 45)   # away from the window's wall
        corners = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], np.float32)
        far = corners + np.array([dx, 0.55 * h], np.float32)
        hull = cv2.convexHull(np.vstack([corners, far]).astype(np.int32))
        shaft = np.zeros(shape, np.uint8)
        cv2.fillConvexPoly(shaft, hull, 1)
        yy, xx = np.mgrid[0:h, 0:w]
        along = np.clip(np.hypot(xx - (x0 + x1) / 2, yy - (y0 + y1) / 2) / (0.75 * h), 0, 1)
        light = np.maximum(light, shaft * (1 - along))
    dither = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w]
    return np.floor(light * 3 + dither * 0.9) / 3


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
    out_mask = outdoors(day, WINDOWS.get(name, []))
    base = move_sun(name, day, time)
    img = base.astype(np.float32)
    room = np.clip(img * np.array(t["room"], np.float32), 0, 255)
    lum = (img.mean(axis=2, keepdims=True) / 255)
    if t["cool"]:                                                       # cooler shadows
        cool = room * np.array((0.86, 0.93, 1.1), np.float32)
        room = room + (cool - room) * (t["cool"] * (1 - lum) ** 2)
    if t.get("haze"):                                                   # morning haze: softer, paler colors
        pale = room.mean(axis=2, keepdims=True) * np.array((1.04, 1.03, 1.06), np.float32) + 20
        room = room + (pale - room) * t["haze"]
    if t["gold"]:                                                       # golden highlights
        room = room + (np.array((255, 232, 190), np.float32) - room) * (t["gold"] * lum ** 3)
    if t["beams"]:
        color, strength = t["beams"]
        shaft = beams(WINDOWS.get(name, []), (h, w), time == "morning")[..., None] * strength
        room = room + (np.array(color, np.float32) - room) * shaft * (0.4 + lum)
    sky = np.array(t["sky"], np.float32)
    outside = img * (1 - t["sky_mix"]) + sky * t["sky_mix"] * (0.55 + 0.9 * lum)
    if t["stars"]:
        rng = np.random.default_rng(len(name))
        stars = (rng.random((h, w)) < 0.012) & out_mask & (img.mean(axis=2) > 120)
        outside[stars] = (255, 246, 210)
    result = np.where(out_mask[..., None], outside, room)
    if name in SUNS:                                                    # the sun or moon itself stays as drawn
        (nx, ny), r = SUNS[name][time], SUNS[name]["radius"]
        yy, xx = np.mgrid[0:h, 0:w]
        disc = (np.hypot(xx - nx, yy - ny) <= r)[..., None]
        result = np.where(disc, img, result)
    if t["lights"] > 0:                                                 # warm lamplight brings the day colors back
        glow = glow_of(lights_of(name), (h, w))[..., None] * t["lights"] * ~out_mask[..., None]
        warm = np.clip(day.astype(np.float32) * np.array((1.12, 1.0, 0.82), np.float32), 0, 255)
        result = result * (1 - glow) + warm * glow
        result = np.where(lamp_mask(name, (h, w))[..., None], day, result)   # the lanterns stay bright
    return palette_of(np.clip(result, 0, 255).astype(np.uint8), COLORS)


def main(names: list[str]) -> None:
    rows = []
    for name in names:
        folder = TRACED / name
        day = np.array(Image.open(folder / f"{name}.png").convert("RGB"))
        versions = {}
        for time in TIMES:
            # the afternoon is the v5 kitchen itself, unless its sun has to move
            img = day if time == "afternoon" and name not in SUNS else hour(name, day, time)
            versions[time] = img
            Image.fromarray(img).save(folder / f"{name}_{time}.png")
            Image.fromarray(img).resize((img.shape[1] * 4, img.shape[0] * 4), Image.NEAREST).save(folder / f"{name}_{time}_x4.png")
        row = np.concatenate([np.pad(np.kron(v, np.ones((2, 2, 1), np.uint8)), ((0, 0), (0, 6), (0, 0)), constant_values=255)
                              for v in versions.values()], axis=1)
        rows.append(np.pad(row, ((0, 6), (0, 0), (0, 0)), constant_values=255))
        print(f"{name}: {', '.join(versions)} written to {folder}")
    Image.fromarray(np.concatenate(rows, axis=0)).save(TRACED / "compare_day_night.png")


if __name__ == "__main__":
    main(sys.argv[1:] or list(WINDOWS))
