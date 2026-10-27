"""The no-photo picture as pixel art, recreated from the CC0 photo ("Wooden Spatula", Nordwood Themes, StockSnap).

Every shape is placed at the position measured on the photo (960x640 pixels): a round stoneware pan with two lugs,
a slotted turner with a blue handle underneath, a solid spatula with a yellow handle on top. Flat colours, and every
border drawn once, one pixel wide (on the lower part's side), so outlines never double up.
Run: python -I design/pixel-art/no_photo_outlined.py design/pixel-art/previews
"""
import math
import sys

from PIL import Image, ImageDraw

out = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 64  # 64: shown at 128 px on the card, exactly 2x
X0, Y0, SIDE = 438, 122, 492  # the square of the photo that holds the picture


def P(x, y):
    """A photo pixel to an art pixel."""
    return ((x - X0) * N / SIDE, (y - Y0) * N / SIDE)


INK = (0x2B, 0x1E, 0x1A, 255)
PAN, PAN_D, PAN_L = (0xE2, 0xDD, 0xD0, 255), (0xBF, 0xB6, 0xA4, 255), (0xF0, 0xEC, 0xE3, 255)
WOOD, WOOD_D, WOOD_L = (0xD8, 0xAB, 0x72, 255), (0xB3, 0x82, 0x4C, 255), (0xEC, 0xCB, 0x98, 255)
YEL, BLUE = (0xEC, 0xCE, 0x2E, 255), (0x8C, 0xC4, 0xF2, 255)


def layer():
    return Image.new("RGBA", (N, N), (0, 0, 0, 0))


def bar(d, a, b, w, fill):
    """A straight strip w photo pixels wide from a to b."""
    (x1, y1), (x2, y2) = P(*a), P(*b)
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    w = w * N / SIDE
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    d.polygon([(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)], fill=fill)


def ink(parts):
    """Stack the parts (bottom first) and draw every border once, one pixel wide: around the whole picture just
    outside it, and between two parts on the lower part's side, so two outlines never sit side by side."""
    owner = [[0] * N for _ in range(N)]
    art = layer()
    for k, img in enumerate(parts, 1):
        a = img.load()
        for y in range(N):
            for x in range(N):
                if a[x, y][3]:
                    owner[y][x] = k
        art.alpha_composite(img)
    px = art.load()

    def near(x, y):
        return [owner[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= x + dx < N and 0 <= y + dy < N]
    for y in range(N):
        for x in range(N):
            o = owner[y][x]
            if (o == 0 and any(near(x, y))) or (o and any(n > o for n in near(x, y))):
                px[x, y] = INK
    return art


# The pan: a circle (centre 715,362, radius 202 on the photo), a lug at the top and one at the bottom right
pan = layer()
d = ImageDraw.Draw(pan)
d.ellipse([*P(612, 136), *P(766, 200)], fill=PAN_D)        # top lug
d.ellipse([*P(700, 530), *P(838, 592)], fill=PAN_D)        # bottom-right lug
d.ellipse([*P(513, 160), *P(917, 564)], fill=PAN_D)        # rim
d.ellipse([*P(540, 187), *P(890, 537)], fill=PAN)          # floor
d.arc([*P(552, 199), *P(878, 525)], 200, 300, fill=PAN_L)  # light on the far wall
d.arc([*P(540, 187), *P(890, 537)], 20, 110, fill=PAN_D)   # shade on the near wall

# The slotted turner (underneath): blue handle from the bottom left, wood shaft, head at the top right
blue = layer()
d = ImageDraw.Draw(blue)
bar(d, (501, 575), (625, 480), 36, BLUE)
bar(d, (625, 480), (760, 385), 30, WOOD)
d.polygon([P(732, 356), P(818, 258), P(896, 320), P(812, 412)], fill=WOOD)
for x, y in ((800, 290), (832, 296)):                      # its two slots, along the tool
    d.line([P(x, y), P(x + 22, y + 22)], fill=WOOD_D, width=1)
d.point([P(520, 560)], fill=INK)                           # the hanging hole

# The solid spatula (on top): yellow handle from the top left, wood shaft, paddle at the right
yel = layer()
d = ImageDraw.Draw(yel)
bar(d, (450, 260), (598, 302), 36, YEL)
bar(d, (598, 302), (748, 352), 30, WOOD)
d.polygon([P(742, 340), P(780, 330), P(870, 358), P(886, 366), P(893, 382), P(888, 440), P(878, 452), P(842, 450), P(752, 402)], fill=WOOD)
d.line([P(780, 336), P(886, 372)], fill=WOOD_L)            # light on its top edge
d.point([P(472, 268)], fill=INK)                           # the hanging hole

art = ink([pan, blue, yel])
art.save(f"{out}/no_photo_pixel_outlined{'' if N == 64 else f'_{N}'}.png")

sheet = Image.new("RGBA", (460, 250), (0xE8, 0xD5, 0xB5, 255))
dd = ImageDraw.Draw(sheet)
photo = Image.open(f"{out}/no_photo_photo.png").convert("RGBA").resize((200, 200), Image.LANCZOS)
sheet.alpha_composite(photo, (20, 15))
sheet.alpha_composite(art.resize((192, 192), Image.NEAREST), (244, 19))
dd.text((20, 225), "photo (the concept)", fill=INK)
dd.text((244, 225), "pixel art, 64 px", fill=INK)
sheet.convert("RGB").save(f"{out}/no_photo_pixel_compare.png")
