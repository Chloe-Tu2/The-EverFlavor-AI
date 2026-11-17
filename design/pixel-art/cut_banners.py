"""The team's banners, cut one by one from their sheet.

    python design/pixel-art/cut_banners.py <Banner_Designs.png> design/pixel-art/originals/banners
        cuts the sheet into its four banners, each trimmed to its own edges (no resampling)
The app shows pixel-art versions of them, made by pixel_banners.py ("Meet the Waiter" from edit_waiter_banner.py's
version, with its text fitted to Walter).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ORIGINALS = HERE / "originals" / "banners"
ROWS = {"whats_cooking": (0, 280), "meet_the_waiter": (293, 521), "new_chefs": (533, 772), "app_update": (784, 1014)}


def cut(sheet_path: Path, out: Path) -> None:
    sheet = Image.open(sheet_path).convert("RGB")
    out.mkdir(parents=True, exist_ok=True)
    for name, (top, bottom) in ROWS.items():
        band = sheet.crop((0, top, sheet.width, bottom))
        a = np.asarray(band).astype(int)
        dark = (a.min(axis=2) < 235)
        cols = np.where(dark.mean(axis=0) > 0.05)[0]
        lines = np.where(dark.mean(axis=1) > 0.05)[0]
        box = (int(cols[0]), int(lines[0]), int(cols[-1]) + 1, int(lines[-1]) + 1)
        piece = band.crop(box)
        piece.save(out / f"banner_{name}.png", optimize=True)
        print(name, "rows", top + box[1], top + box[3], "cols", box[0], box[2], "size", piece.size)


if __name__ == "__main__":
    cut(Path(sys.argv[1]), Path(sys.argv[2]))
