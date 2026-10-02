"""A bowl of ramen, seen from above, drawn with code (ANSI block art).

Every "pixel" is built from shapes (circles, ellipses, curves and lines),
then shown in one of two ways:

    python docs/art/ramen.py          # print it in color in a terminal or notebook
    python docs/art/ramen.py --svg    # also save docs/art/ramen.svg for the README

In a terminal, each character cell shows two pixels stacked on top of each
other: the upper half block "▀" in the top pixel's color, on a background
in the bottom pixel's color. Works in Colab, VS Code and Antigravity, and
uses only the Python standard library.
"""
import math
import os
import random
import sys
from pathlib import Path

SIZE = 88                      # the picture is SIZE x SIZE pixels
SCALE = 72                     # the bowl scene fills SCALE x SCALE in the middle
MARGIN = (SIZE - SCALE) / 2    # room around it for the aroma lines
TITLE = "EverFlavor AI"
SUBTITLE = "authentic recipes · calories · restrictions · stores"

# Colors as (red, green, blue)
TABLE = (226, 224, 220)
GOLD_DARK = (168, 116, 18)      # shaded edge
GOLD = (236, 184, 38)           # main gold
GOLD_SHINE = (255, 238, 150)    # highlight where light catches it
SPARKLE = (255, 252, 230)
TABLE_DARK = (214, 211, 206)
RIM = (66, 52, 40)
RIM_LIGHT = (104, 84, 64)
BROTH = (196, 140, 66)
NOODLE = (242, 220, 160)
NOODLE_DARK = (214, 182, 112)
EGG_WHITE = (251, 247, 238)
YOLK = (247, 166, 35)
YOLK_CENTER = (255, 196, 60)
SESAME = (30, 28, 26)
NORI = (31, 40, 36)
NORI_LIGHT = (52, 66, 58)
ONION = (118, 196, 84)
ONION_LIGHT = (214, 240, 186)
BAMBOO = (243, 231, 184)
BAMBOO_EDGE = (196, 170, 96)
PORK = (196, 146, 124)
PORK_EDGE = (140, 92, 72)
PORK_FAT = (236, 210, 196)
SPINACH = (47, 107, 42)
SPINACH_LIGHT = (70, 140, 58)
SPINACH_DARK = (31, 76, 30)
SPROUT = (246, 238, 214)
SPROUT_HEAD = (245, 215, 110)
WOOD = (214, 160, 70)
WOOD_LIGHT = (240, 196, 106)
TITLE_COLOR = (247, 166, 35)
SUBTITLE_COLOR = (150, 150, 160)

rng = random.Random(7)         # fixed seed: the same picture every run
pixels = [[TABLE] * SIZE for _ in range(SIZE)]


# ------------------------------------------------------------- drawing helpers
def at(fx, fy):
    """Turn fractions of the scene (0 to 1) into pixel coordinates."""
    return MARGIN + fx * SCALE, MARGIN + fy * SCALE


def paint(x, y, color):
    if 0 <= x < SIZE and 0 <= y < SIZE:
        pixels[y][x] = color


def fill_ellipse(cx, cy, rx, ry, color, angle=0.0, inside=None):
    """Fill an ellipse (centre and radii in fractions), optionally rotated and clipped."""
    cx, cy = at(cx, cy)
    rx, ry = rx * SCALE, ry * SCALE
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    for y in range(SIZE):
        for x in range(SIZE):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = (dx * cos_a + dy * sin_a) / rx
            v = (-dx * sin_a + dy * cos_a) / ry
            if u * u + v * v <= 1 and (inside is None or inside(x, y)):
                pixels[y][x] = color(x, y) if callable(color) else color


def draw_line(x0, y0, x1, y1, width, color, inside=None):
    """Draw a thick line between two points given in fractions."""
    x0, y0 = at(x0, y0)
    x1, y1 = at(x1, y1)
    length2 = (x1 - x0) ** 2 + (y1 - y0) ** 2 or 1
    for y in range(SIZE):
        for x in range(SIZE):
            px, py = x + 0.5, y + 0.5
            t = max(0, min(1, ((px - x0) * (x1 - x0) + (py - y0) * (y1 - y0)) / length2))
            dist = math.hypot(px - (x0 + t * (x1 - x0)), py - (y0 + t * (y1 - y0)))
            if dist <= width / 2 and (inside is None or inside(x, y)):
                pixels[y][x] = color(t) if callable(color) else color


def draw_curve(points, width, color, inside=None):
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        draw_line(ax, ay, bx, by, width, color, inside)


# ------------------------------------------------------------------- the scene
BOWL_X, BOWL_Y, BOWL_R, INNER_R = 0.50, 0.50, 0.45, 0.405


def in_bowl(x, y):
    """True for pixels inside the bowl's rim."""
    cx, cy = at(BOWL_X, BOWL_Y)
    return math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= INNER_R * SCALE


def stone(x, y):
    return TABLE_DARK if rng.random() < 0.12 else TABLE


# Table, with a little texture
fill_ellipse(0.5, 0.5, 2, 2, stone)

# Aroma: shiny gold wisps curling around the bowl. Each wisp has a dark
# edge, a bright body, and a pale highlight along its middle stretch.
WISPS = [(200, 0.53), (265, 0.555), (330, 0.53), (20, 0.555), (85, 0.53), (135, 0.555)]
for start, radius in WISPS:
    points = []
    for step in range(16):
        angle = math.radians(start + step * 2.6)
        r = radius + 0.018 * math.sin(step / 15 * 2 * math.pi)   # one gentle wave
        points.append((BOWL_X + r * math.cos(angle), BOWL_Y + r * math.sin(angle)))
    draw_curve(points, 2.6, GOLD_DARK)
    draw_curve(points, 1.8, GOLD)
    draw_curve(points[4:12], 0.8, GOLD_SHINE)
    # a small curl at the end of each wisp
    end_x, end_y = points[-1]
    fill_ellipse(end_x, end_y, 0.014, 0.014, GOLD_DARK)
    fill_ellipse(end_x, end_y, 0.010, 0.010, GOLD)
    fill_ellipse(end_x, end_y, 0.004, 0.004, GOLD_SHINE)


def sparkle(fx, fy, big=False):
    """A small four-pointed twinkle."""
    x, y = (int(v) for v in at(fx, fy))
    arm = 2 if big else 1
    for d in range(1, arm + 1):
        for dx, dy in [(d, 0), (-d, 0), (0, d), (0, -d)]:
            paint(x + dx, y + dy, GOLD_SHINE if d == arm else GOLD)
    paint(x, y, SPARKLE)


# Twinkles just outside some of the wisps
for start, radius in WISPS:
    angle = math.radians(start + 22)
    sparkle(BOWL_X + (radius + 0.06) * math.cos(angle),
            BOWL_Y + (radius + 0.06) * math.sin(angle), big=start % 130 == 70)

# Bowl rim (lighter on the inner edge), then the broth
fill_ellipse(BOWL_X, BOWL_Y, BOWL_R, BOWL_R, RIM)
fill_ellipse(BOWL_X, BOWL_Y, INNER_R + 0.02, INNER_R + 0.02, RIM_LIGHT)
fill_ellipse(BOWL_X, BOWL_Y, INNER_R, INNER_R, BROTH)

# Noodles: many wavy strands across the bowl
for _ in range(85):
    sx, sy = rng.uniform(0.12, 0.88), rng.uniform(0.12, 0.88)
    heading, curl = rng.uniform(0, 2 * math.pi), rng.uniform(-0.5, 0.5)
    points = []
    for step in range(14):
        points.append((sx, sy))
        heading += curl + 0.6 * math.sin(step * 1.3)
        sx += 0.025 * math.cos(heading)
        sy += 0.025 * math.sin(heading)
    draw_curve(points, 2.0, NOODLE_DARK, in_bowl)
    draw_curve(points, 1.2, NOODLE, in_bowl)

# Bean sprouts (lower left)
for _ in range(14):
    x0, y0 = rng.uniform(0.16, 0.36), rng.uniform(0.52, 0.80)
    angle = rng.uniform(-0.9, 0.9) - math.pi / 2
    x1, y1 = x0 + 0.09 * math.cos(angle), y0 + 0.09 * math.sin(angle)
    draw_line(x0, y0, x1, y1, 1.0, SPROUT, in_bowl)
    fill_ellipse(x1, y1, 0.012, 0.012, SPROUT_HEAD, inside=in_bowl)

# Spinach (lower middle): a leafy patch
for _ in range(26):
    lx, ly = rng.gauss(0.47, 0.06), rng.gauss(0.66, 0.06)
    shade = rng.choice([SPINACH, SPINACH, SPINACH_LIGHT, SPINACH_DARK])
    fill_ellipse(lx, ly, 0.045, 0.028, shade, angle=rng.uniform(0, math.pi), inside=in_bowl)

# Chashu pork slices (lower right): edge, meat, a line of fat
for px, py in [(0.69, 0.76), (0.77, 0.66)]:
    fill_ellipse(px, py, 0.105, 0.085, PORK_EDGE, angle=0.5, inside=in_bowl)
    fill_ellipse(px, py, 0.09, 0.07, PORK, angle=0.5, inside=in_bowl)
    draw_line(px - 0.06, py - 0.01, px + 0.05, py + 0.04, 0.8, PORK_FAT, in_bowl)

# Bamboo shoots (right): pale wedges
for i in range(3):
    bx, by = 0.79 - 0.02 * i, 0.46 + 0.06 * i
    fill_ellipse(bx, by, 0.11, 0.040, BAMBOO_EDGE, angle=-0.35, inside=in_bowl)
    fill_ellipse(bx, by, 0.10, 0.028, BAMBOO, angle=-0.35, inside=in_bowl)

# Nori (top right): a dark sheet with a slightly rough texture
fill_ellipse(0.71, 0.25, 0.16, 0.10, lambda x, y: NORI_LIGHT if rng.random() < 0.18 else NORI,
             angle=0.45, inside=in_bowl)

# Two soft-boiled egg halves with sesame seeds
for ex, ey, tilt in [(0.29, 0.38, -0.25), (0.50, 0.36, 0.15)]:
    fill_ellipse(ex, ey, 0.095, 0.125, EGG_WHITE, angle=tilt)
    fill_ellipse(ex, ey + 0.01, 0.065, 0.08, YOLK, angle=tilt)
    fill_ellipse(ex, ey + 0.01, 0.035, 0.045, YOLK_CENTER, angle=tilt)
    for _ in range(9):
        sx, sy = at(ex + rng.uniform(-0.06, 0.06), ey + rng.uniform(-0.08, 0.08))
        paint(int(sx), int(sy), SESAME)

# Green onion rings (middle right)
for _ in range(12):
    ox, oy = rng.gauss(0.66, 0.035), rng.gauss(0.39, 0.04)
    fill_ellipse(ox, oy, 0.022, 0.022, ONION, inside=in_bowl)
    fill_ellipse(ox, oy, 0.010, 0.010, ONION_LIGHT, inside=in_bowl)

# Chopsticks, lifting noodles from the lower left
for (x0, y0), (x1, y1) in [((-0.04, 1.08), (0.30, 0.58)), ((0.05, 1.10), (0.35, 0.62))]:
    draw_line(x0, y0, x1, y1, 2.4, WOOD)
    draw_line(x0, y0, x1, y1, 0.8, WOOD_LIGHT)

# Loose green onion (top right) and sesame seeds (bottom) on the table
for _ in range(7):
    ox, oy = rng.uniform(0.80, 0.97), rng.uniform(0.02, 0.18)
    fill_ellipse(ox, oy, 0.017, 0.017, ONION)
    lx, ly = at(ox, oy)
    paint(int(lx), int(ly), ONION_LIGHT)
for _ in range(16):
    sx, sy = at(rng.uniform(0.25, 0.65), rng.uniform(0.96, 1.04))
    x, y = int(sx), int(sy)
    if not in_bowl(x, y):
        paint(x, y, SESAME)


# ------------------------------------------------------------------ output
def print_ansi():
    """Print with 24-bit colors: one character cell = two stacked pixels."""
    if os.name == "nt":
        os.system("")   # switches on ANSI colors in the Windows console
    try:
        sys.stdout.reconfigure(encoding="utf-8")   # older Windows consoles cannot print "▀" otherwise
    except (AttributeError, ValueError):
        pass   # notebooks already use UTF-8
    reset = "\033[0m"
    for y in range(0, SIZE, 2):
        row = []
        for x in range(SIZE):
            top, bottom = pixels[y][x], pixels[y + 1][x]
            row.append("\033[38;2;{};{};{}m".format(*top)
                       + "\033[48;2;{};{};{}m▀".format(*bottom))
        print("".join(row) + reset)
    print()
    print("\033[1;38;2;{};{};{}m".format(*TITLE_COLOR) + TITLE.center(SIZE) + reset)
    print("\033[38;2;{};{};{}m".format(*SUBTITLE_COLOR) + SUBTITLE.center(SIZE) + reset)


def save_svg(path, cell=7):
    """Save the picture as an SVG in a terminal-style window, for the README."""
    pad, bar = 24, 34
    art = SIZE * cell
    width, height = art + 2 * pad, art + 2 * pad + bar + 70

    def rgb(c):
        return "#{:02x}{:02x}{:02x}".format(*c)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="A bowl of ramen drawn with code: {TITLE}">',
        f'<rect width="{width}" height="{height}" rx="12" fill="#1e1e2e"/>',
        f'<path d="M0 12 a12 12 0 0 1 12 -12 h{width - 24} a12 12 0 0 1 12 12 v{bar - 12} h-{width} z" fill="#2a2a3c"/>',
    ]
    for i, dot in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        parts.append(f'<circle cx="{20 + i * 20}" cy="{bar / 2}" r="6" fill="{dot}"/>')
    parts.append(f'<text x="{width / 2}" y="{bar / 2 + 5}" text-anchor="middle" fill="#8a8aa0" '
                 f'font-family="Consolas, Menlo, monospace" font-size="13">python ramen.py</text>')

    # One rectangle per run of same-colored pixels in a row keeps the file small
    top = bar + pad
    parts.append('<g shape-rendering="crispEdges">')
    for y in range(SIZE):
        x = 0
        while x < SIZE:
            run = 1
            while x + run < SIZE and pixels[y][x + run] == pixels[y][x]:
                run += 1
            parts.append(f'<rect x="{pad + x * cell}" y="{top + y * cell}" width="{run * cell}" '
                         f'height="{cell}" fill="{rgb(pixels[y][x])}"/>')
            x += run
    parts.append("</g>")

    text_y = top + art + 36
    parts.append(f'<text x="{width / 2}" y="{text_y}" text-anchor="middle" fill="{rgb(TITLE_COLOR)}" '
                 f'font-family="Consolas, Menlo, monospace" font-size="24" font-weight="bold">{TITLE}</text>')
    parts.append(f'<text x="{width / 2}" y="{text_y + 24}" text-anchor="middle" fill="{rgb(SUBTITLE_COLOR)}" '
                 f'font-family="Consolas, Menlo, monospace" font-size="13">{SUBTITLE}</text>')
    parts.append("</svg>")
    Path(path).write_text("\n".join(parts), encoding="utf-8")
    print(f"\nSaved {path}")


if __name__ == "__main__":
    print_ansi()
    if "--svg" in sys.argv:
        save_svg(Path(__file__).with_name("ramen.svg"))
