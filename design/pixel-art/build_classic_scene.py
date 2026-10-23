"""The Classic kitchen in four hours, as one interactive scene (assets/scene_classic_hours.json), like the v5 kitchens:
the Morning and Night kitchens of make_pixel_art.py become its morning and night, Classic its afternoon, and the
evening is the afternoon in warm, low sunset light (the room a little darker and orange, as in day_night.py).
The four pictures share every piece and place, so the pieces move and answer taps the same at every hour.

    python design/pixel-art/build_classic_scene.py
"""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
HOURS = {"morning": "morning", "afternoon": "classic", "night": "night"}     # hour -> make_pixel_art.py kitchen
EVENING = np.array((0.94, 0.80, 0.68), np.float32)                         # the sunset's tint on the room


def kind_of(name: str) -> str:
    """What a piece does when tapped (the Classic kitchen's own pieces)."""
    if name.startswith("curtain"):
        return "curtain"
    if name.startswith("pan") or name == "lamp":
        return "swing"
    return {"lid": "hop", "pot": "steam"}.get(name, "shake")


def evening(uri: str) -> str:
    """A picture (data URI) in the evening's light: tinted warm and a little darker, transparency kept."""
    img = np.array(Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1]))).convert("RGBA")).astype(np.float32)
    img[..., :3] = np.clip(img[..., :3] * EVENING, 0, 255)
    buf = io.BytesIO()
    Image.fromarray(img.astype(np.uint8), "RGBA").save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def main() -> None:
    scenes = {hour: json.loads((ASSETS / f"scene_{name}.json").read_text(encoding="utf-8")) for hour, name in HOURS.items()}
    base = scenes["afternoon"]
    order = list(base["pieces"])
    pieces = {k: {"x": p["x"], "y": p["y"], "w": p["w"], "h": p["h"], "kind": kind_of(k)} for k, p in base["pieces"].items()}

    def hour_of(scene: dict, tint=None) -> dict:
        tint = tint or (lambda uri: uri)
        return {"on": False, "backdrop": tint(scene["backdrop"]), "glows": {},
                "pieces": {k: {"png": tint(scene["pieces"][k]["png"]), "lit": {}} for k in order}}

    hours = {"morning": hour_of(scenes["morning"]), "afternoon": hour_of(base),
             "evening": hour_of(base, evening), "night": hour_of(scenes["night"])}
    data = {"size": base["size"], "order": order, "pieces": pieces, "lights": [], "hours": hours}
    (ASSETS / "scene_classic_hours.json").write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    Image.open(ASSETS / "kitchen_classic.png").save(ASSETS / "kitchen_classic_hours.png")   # the still picture
    print(f"scene_classic_hours.json: {(ASSETS / 'scene_classic_hours.json').stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
