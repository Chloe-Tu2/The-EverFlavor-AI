"""The v5 kitchens as interactive scenes for the app: assets/scene_v5_<name>.json and assets/kitchen_v5_<name>.png.

For every hour (morning, afternoon, evening, night) a scene holds the kitchen with its lights off and, for each light
(lantern, lamp, candle), the pixels it changes when switched on: on the room behind and on each piece, so a light
stays right on a piece that moves. app/kitchen_scene.html draws the hour of the visitor's clock and makes the key
pieces answer a tap:

  - light   lanterns, lamps, candles: switch on and off (off by day, on in the evening and at night)
  - plant   plants, vines, flowers: shake and drop a few of their own leaves or petals
  - tree    trees seen through a window: sway and drop leaves or blossom petals inside the window
  - wobble  stools and chairs: rock a little
  - steam   woks, steamers, cooking pots: hop and give off steam
  - swing   hanging pans: swing

Pieces are tapped by their own pixels, not their boxes, so a piece in front of another only takes the taps on itself.

    python design/pixel-art/build_scenes.py [names]
"""
from __future__ import annotations

import base64
import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import day_night as dn  # the hours of the v5 kitchens

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
MIN_TREE = 40                     # a tree seen through a window: at least this many foliage pixels

# What a piece does, by the words in its name (first match wins); pieces with none of them stay still
KINDS = [
    ("light", ("lantern", "lamp", "candle")),
    ("steam", ("wok", "steamer", "red_pot", "steel_pot", "copper_pots", "pots_mid", "tea_set")),
    ("swing", ("pan_",)),
    ("wobble", ("stool", "chair")),
    ("plant", ("plant", "palm", "vine", "herb", "bamboo", "sunflower", "cactus", "flower", "bowl_greens",
               "basket_greens", "garlic_vine")),
]


def kind_of(key: str) -> str | None:
    return next((kind for kind, words in KINDS if any(w in key for w in words)), None)


def uri(rgba: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA" if rgba.shape[2] == 4 else "RGB").save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def leaves_of(rgb: np.ndarray, mask: np.ndarray) -> list[str]:
    """The colors a plant drops: its three most common leaf or petal colors (green or pink), as hex."""
    px = rgb[mask].astype(int)
    if not len(px):
        return []
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    leafy = ((g > r + 8) & (g > b + 8)) | ((r > g + 30) & (b > g + 10))      # green leaves or pink petals
    colors, counts = np.unique(px[leafy], axis=0, return_counts=True)
    return ["#{:02x}{:02x}{:02x}".format(*c) for c in colors[np.argsort(-counts)][:3]]


def trees_of(name: str, day: np.ndarray) -> dict[str, dict]:
    """Trees seen through the windows: connected patches of foliage (green or blossom pink) in the outdoors."""
    out = dn.outdoors(day, dn.WINDOWS.get(name, []))
    rgb = day.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    foliage = out & (((g > r + 6) & (g > b + 6)) | ((r > g + 25) & (b > g + 5)))
    foliage = cv2.morphologyEx(foliage.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0
    count, labels, stats, _ = cv2.connectedComponentsWithStats(foliage.astype(np.uint8), 8)
    trees = {}
    for i in range(1, count):
        x, y, w, h, area = stats[i]
        if area >= MIN_TREE:
            trees[f"tree_{len(trees) + 1}"] = {"x": int(x), "y": int(y), "mask": labels[y:y + h, x:x + w] == i,
                                               "window": window_of(name, x + w / 2, y + h / 2)}
    return trees


def window_of(name: str, x: float, y: float) -> list[int]:
    """The window box (on the pixel grid) a point is in: falling leaves stay inside it."""
    for x0, y0, x1, y1 in dn.WINDOWS.get(name, []):
        if x0 / dn.SCALE <= x <= x1 / dn.SCALE and y0 / dn.SCALE <= y <= y1 / dn.SCALE:
            return [x0 // dn.SCALE, y0 // dn.SCALE, x1 // dn.SCALE, y1 // dn.SCALE]
    return [0, 0, 0, 0]


def owner_of(lights: dict[str, tuple[float, float, float]], shape: tuple[int, int]) -> tuple[list[str], np.ndarray]:
    """For each pixel, the light it belongs to: the nearest one, measured in each light's reach."""
    names = list(lights)
    if not names:
        return names, np.zeros(shape, int)
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    reach = np.stack([np.hypot(xx - x, yy - y) / r for x, y, r in lights.values()])
    return names, reach.argmin(axis=0)


def crop_rgba(img: np.ndarray, mask: np.ndarray, x: int, y: int) -> np.ndarray:
    h, w = mask.shape
    return np.dstack([img[y:y + h, x:x + w], mask.astype(np.uint8) * 255])


def build(name: str) -> dict:
    folder = dn.TRACED / name
    day = np.array(Image.open(folder / f"{name}.png").convert("RGB"))
    off = dn.lamps_off(name)
    scene = json.loads((folder / "scene.json").read_text(encoding="utf-8"))["pieces"]
    h, w = day.shape[:2]
    shapes = {key: (p["x"], p["y"], np.array(Image.open(folder / "sprites" / f"{key}.png").convert("RGBA"))[..., 3] > 0)
              for key, p in scene.items()}
    trees = trees_of(name, day)
    lights = dn.lights_of(name)
    names, owner = owner_of(lights, (h, w))

    pieces: dict[str, dict] = {}
    for key, (x, y, mask) in shapes.items():
        pieces[key] = {"x": x, "y": y, "w": int(mask.shape[1]), "h": int(mask.shape[0]), "kind": kind_of(key)}
        if pieces[key]["kind"] == "plant":
            pieces[key]["leaves"] = leaves_of(day[y:y + mask.shape[0], x:x + mask.shape[1]], mask)
    for key, t in trees.items():
        mask = t["mask"]
        pieces[key] = {"x": t["x"], "y": t["y"], "w": int(mask.shape[1]), "h": int(mask.shape[0]), "kind": "tree",
                       "window": t["window"],
                       "leaves": leaves_of(day[t["y"]:t["y"] + mask.shape[0], t["x"]:t["x"] + mask.shape[1]], mask)}
        shapes[key] = (t["x"], t["y"], mask)
    order = list(trees) + list(scene)            # trees are behind everything in the room

    hours = {}
    for time in dn.TIMES:
        lit, dark = dn.hour_pair(name, day, off, time)
        changed = (lit != dark).any(axis=2)
        hour: dict = {"on": dn.TIMES[time]["lights"] > 0, "backdrop": uri(dark), "pieces": {}, "glows": {}}
        for i, light in enumerate(names):          # what each light changes on the room
            m = changed & (owner == i)
            if m.any():
                ys, xs = np.nonzero(m)
                x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
                hour["glows"][light] = {"x": int(x0), "y": int(y0),
                                        "png": uri(crop_rgba(lit, m[y0:y1, x0:x1], int(x0), int(y0)))}
        for key in order:                          # each piece, lights off, and what each light changes on it
            x, y, mask = shapes[key]
            sub = {"png": uri(crop_rgba(dark, mask, x, y)), "lit": {}}
            part_changed = changed[y:y + mask.shape[0], x:x + mask.shape[1]] & mask
            part_owner = owner[y:y + mask.shape[0], x:x + mask.shape[1]]
            for i, light in enumerate(names):
                m = part_changed & (part_owner == i)
                if m.any():
                    sub["lit"][light] = uri(crop_rgba(lit, m, x, y))
            hour["pieces"][key] = sub
        hours[time] = hour
        if time == "afternoon":
            Image.fromarray(dark).save(ASSETS / f"kitchen_v5_{name}.png")   # the still picture under the scene
    return {"size": [w, h], "order": order, "pieces": pieces, "lights": names, "hours": hours}


def main(names: list[str]) -> None:
    for name in names:
        data = build(name)
        path = ASSETS / f"scene_v5_{name}.json"
        path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        kinds = {}
        for p in data["pieces"].values():
            if p["kind"]:
                kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
        print(f"{name}: {path.stat().st_size // 1024} KB, {kinds}")


if __name__ == "__main__":
    main(sys.argv[1:] or list(dn.WINDOWS))
