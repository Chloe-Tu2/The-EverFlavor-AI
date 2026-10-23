"""The "cooking in progress" loading animation: an egg frying in a pan over a fire, four frames of 40 x 32 pixels side
by side in assets/loading_eggs.png (the app plays them in a loop while it works).

    python design/pixel-art/make_loading.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
W, H, FRAMES = 40, 32, 4
OUTLINE, PAN, PAN_LIGHT, HANDLE = (40, 30, 34), (70, 70, 80), (110, 112, 124), (120, 72, 40)
WHITE_RAW, WHITE, WHITE_EDGE = (236, 232, 214), (255, 253, 244), (226, 196, 150)
YOLK, YOLK_LIGHT = (246, 168, 28), (255, 214, 92)
FIRE = [(186, 40, 30), (240, 104, 32), (255, 196, 64)]          # outer to inner
STEAM = (255, 255, 255, 170)


def frame(k: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # the fire under the pan: three flames whose heights change frame to frame
    heights = [(5, 7, 6), (7, 5, 7), (6, 8, 5), (8, 6, 6)][k]
    for x, hgt in zip((12, 19, 26), heights, strict=True):
        for i, color in enumerate(FIRE):
            top = H - 1 - hgt + i * 2
            d.polygon([(x - 3 + i, H - 1), (x + 3 - i, H - 1), (x, top)], fill=color)
    # the pan: a dark oval with a lighter rim, and its handle to the right
    d.rectangle((31, 17, 39, 19), fill=HANDLE, outline=OUTLINE)
    d.ellipse((3, 12, 33, 24), fill=PAN, outline=OUTLINE)
    d.arc((4, 12, 32, 23), 200, 340, fill=PAN_LIGHT)
    # the egg: the white sets (from glassy to white, browning at the edge), the yolk sits in the middle
    white = [WHITE_RAW, WHITE_RAW, WHITE, WHITE][k]
    d.ellipse((10, 14, 26, 21), fill=white, outline=WHITE_EDGE if k >= 2 else white)
    d.ellipse((16, 15, 21, 19), fill=YOLK)
    d.point((17, 16), fill=YOLK_LIGHT)
    # sizzle and steam: little bubbles at the edge, a puff rising a bit higher each frame
    for x, y in [(11, 17), (25, 18), (13, 20), (24, 15)][: k + 1]:
        d.point((x, y), fill=WHITE_EDGE)
    for i in range(2):
        y = 10 - k * 2 - i * 4
        if y >= 0:
            d.point((14 + i * 7 + (k + i) % 2, y), fill=STEAM)
            d.point((14 + i * 7 + (k + i) % 2, y + 1), fill=STEAM)
    return img


def main() -> None:
    sheet = Image.new("RGBA", (W * FRAMES, H), (0, 0, 0, 0))
    for k in range(FRAMES):
        sheet.paste(frame(k), (k * W, 0))
    sheet.save(HERE / "assets" / "loading_eggs.png")
    sheet.resize((W * FRAMES * 6, H * 6), Image.NEAREST).save(HERE / "previews" / "loading_eggs_x6.png")


if __name__ == "__main__":
    main()
