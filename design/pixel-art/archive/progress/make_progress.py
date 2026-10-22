"""Progress sheets: each kitchen from the team's concept through every version we tried, side by side and labelled.

    python design/pixel-art/archive/progress/make_progress.py   ->   design/pixel-art/archive/progress/<kitchen>.png
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROGRESS = Path(__file__).resolve().parent
ARCHIVE = PROGRESS.parent
ART = ARCHIVE.parent
H = 300                                                   # every panel is scaled to this height
STEPS = [                                                 # (label, file pattern with {k} for the kitchen)
    ("Concept (team's art)", ART / "references/concepts/{k}.jpg"),
    ("v1  code-drawn, 18 Oct", ARCHIVE / "v1_2026-10-18_code-drawn/kitchen_{k}_x4.png"),
    ("v2  in the app now (0.5.1), 18 Oct", ART / "previews/kitchen_{k}_x4.png"),
    ("v3  concept sheet in code, 19 Oct", ARCHIVE / "v3_2026-10-19_concept-sheet-recreation/{k}_x4.png"),
    ("v4  full kitchen in code, 21-22 Oct", ARCHIVE / "v4_2026-10-21_full-kitchens-in-code/{k}_x4.png"),
    ("v5  traced per object, 22 Oct (current)", ART / "drafts/traced-kitchens/{k}/{k}_x4.png"),
]
KITCHENS = ["chinese", "mediterranean", "mexican", "middle_eastern"]


def font(size: int) -> ImageFont.ImageFont:
    for name in ("arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def sheet(kitchen: str) -> Image.Image:
    panels = []
    for label, pattern in STEPS:
        path = Path(str(pattern).format(k=kitchen))
        if path.exists():
            im = Image.open(path).convert("RGB")
            im = im.resize((round(im.width * H / im.height), H), Image.NEAREST if "_x4" in path.name else Image.LANCZOS)
            panels.append((label, im))
    pad, cap, top, cols = 10, 34, 44, 3                   # a grid of three columns, read left to right, top to bottom
    cell = max(im.width for _, im in panels)
    rows = -(-len(panels) // cols)
    out = Image.new("RGB", (cols * (cell + pad) + pad, top + rows * (H + cap + pad)), "#1E1A17")
    draw = ImageDraw.Draw(out)
    draw.text((pad, 10), kitchen.replace("_", " ").title() + " kitchen: from the concept to the current version",
              fill="#F5E6C8", font=font(24))
    for n, (label, im) in enumerate(panels):
        x, y = pad + (n % cols) * (cell + pad), top + (n // cols) * (H + cap + pad)
        out.paste(im, (x + (cell - im.width) // 2, y))
        draw.text((x, y + H + 6), label, fill="#F2C14E" if "current" in label or "Concept" in label else "#E8DCC8",
                  font=font(18))
    return out


if __name__ == "__main__":
    sheets = [sheet(k) for k in KITCHENS]
    for k, s in zip(KITCHENS, sheets):
        s.save(PROGRESS / f"{k}.png")
    print("saved", ", ".join(f"{k}.png" for k in KITCHENS), "to", PROGRESS)
