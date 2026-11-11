"""The team's banners: cut from their sheet, and the copies the app shows in What's new.

    python design/pixel-art/cut_banners.py <Banner_Designs.png> design/pixel-art/originals/banners
        cuts the sheet into its four banners, each trimmed to its own edges (no resampling)
    python design/pixel-art/cut_banners.py --app
        writes the app's copies (assets/banner_<name>.png, 760 px wide); "Meet the Waiter" comes from
        edit_waiter_banner.py's version, with its text fitted to Walter
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ORIGINALS = HERE / "originals" / "banners"
ROWS = {"whats_cooking": (0, 280), "meet_the_waiter": (293, 521), "new_chefs": (533, 772), "app_update": (784, 1014)}
IN_APP = {"app_update": "banner_app_update.png", "meet_the_waiter": "banner_meet_the_waiter_walter.png",
          "new_chefs": "banner_new_chefs.png"}
APP_WIDTH = 760    # twice the What's new panel's width, sharp on high-density screens


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


def app_copies() -> None:
    for name, source in IN_APP.items():
        banner = Image.open(ORIGINALS / source).convert("RGB")
        small = banner.resize((APP_WIDTH, round(banner.height * APP_WIDTH / banner.width)), Image.Resampling.LANCZOS)
        small.save(HERE / "assets" / f"banner_{name}.png", optimize=True)
        print(name, small.size)


if __name__ == "__main__":
    if sys.argv[1:] == ["--app"]:
        app_copies()
    else:
        cut(Path(sys.argv[1]), Path(sys.argv[2]))
