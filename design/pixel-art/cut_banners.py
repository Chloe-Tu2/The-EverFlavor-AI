"""Cut the team's banner sheet into its four banners, each trimmed to its own edges (no resampling)."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sheet = Image.open(sys.argv[1]).convert("RGB")
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
rows = {"whats_cooking": (0, 280), "meet_the_waiter": (293, 521), "new_chefs": (533, 772), "app_update": (784, 1014)}
for name, (top, bottom) in rows.items():
    band = sheet.crop((0, top, sheet.width, bottom))
    a = np.asarray(band).astype(int)
    dark = (a.min(axis=2) < 235)
    cols = np.where(dark.mean(axis=0) > 0.05)[0]
    lines = np.where(dark.mean(axis=1) > 0.05)[0]
    box = (int(cols[0]), int(lines[0]), int(cols[-1]) + 1, int(lines[-1]) + 1)
    cut = band.crop(box)
    cut.save(out / f"banner_{name}.png", optimize=True)
    print(name, "rows", top + box[1], top + box[3], "cols", box[0], box[2], "size", cut.size)
