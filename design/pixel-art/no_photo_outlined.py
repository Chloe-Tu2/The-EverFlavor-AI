"""The no-photo picture as hand-placed pixel art, traced from the CC0 photo's layout; every part outlined."""
import math
import sys

from PIL import Image, ImageDraw

out = sys.argv[1]
N = 40
def P(x, y):  # photo pixel -> art pixel (crop 430..930 x 120..620)
    return ((x - 430) * N / 500, (y - 120) * N / 500)
INK = (0x2B, 0x1E, 0x1A, 255)
PAN, PAN_D, PAN_L = (0xDC, 0xD6, 0xC8, 255), (0xB4, 0xAB, 0x98, 255), (0xEE, 0xEA, 0xE0, 255)
WOOD, WOOD_D, WOOD_L = (0xD9, 0xA5, 0x62, 255), (0xA8, 0x74, 0x3C, 255), (0xEC, 0xC4, 0x8A, 255)
YEL, BLUE = (0xF2, 0xC6, 0x1F, 255), (0x6C, 0xAA, 0xE6, 255)

def layer():
    return Image.new("RGBA", (N, N), (0, 0, 0, 0))
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
        return [owner[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= x + dx < N and 0 <= y + dy < N]
    for y in range(N):
        for x in range(N):
            o = owner[y][x]
            if (o == 0 and any(near(x, y))) or (o and any(n > o for n in near(x, y))):
                px[x, y] = INK
    return art
def bar(d, a, b, w, fill):
    (x1, y1), (x2, y2) = P(*a), P(*b); dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy); nx, ny = -dy / L * w / 2, dx / L * w / 2
    d.polygon([(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)], fill=fill)

pan = layer(); d = ImageDraw.Draw(pan)
d.ellipse([*P(615, 140), *P(830, 575)], fill=PAN_D)           # lugs (top-left, bottom-right) behind the rim
d.ellipse([*P(530, 155), *P(915, 545)], fill=PAN_D)           # rim
d.ellipse([*P(557, 182), *P(888, 518)], fill=PAN)             # floor
d.arc([*P(575, 185), *P(870, 515)], 200, 290, fill=PAN_L)      # light on the far wall

def tool(handle_from, handle_to, shaft_to, head, color):
    t = layer(); d = ImageDraw.Draw(t)
    bar(d, handle_from, handle_to, 3.2, color)
    bar(d, handle_to, shaft_to, 2.6, WOOD)
    d.polygon([P(*p) for p in head], fill=WOOD)
    return t
blue = tool((505, 580), (625, 485), (760, 390), [(735, 330), (860, 250), (905, 320), (785, 405)], BLUE)
bd = ImageDraw.Draw(blue)
for x, y in ((823, 300), (850, 285)):                            # the turner's two slots, one dark pixel each
    bd.point([P(x, y), P(x + 12, y + 12)], fill=WOOD_D)
yel = tool((452, 262), (600, 300), (760, 360), [(735, 330), (900, 355), (895, 460), (745, 420)], YEL)
yd = ImageDraw.Draw(yel)
yd.line([P(760, 405), P(875, 445)], fill=WOOD_D)                  # shade under the paddle
yd.line([P(760, 340), P(880, 368)], fill=WOOD_L)                  # light on its top edge

art = ink([pan, blue, yel])
art.save(f"{out}/no_photo_pixel_outlined.png")
sheet = Image.new("RGBA", (460, 250), (0xE8, 0xD5, 0xB5, 255)); dd = ImageDraw.Draw(sheet)
photo = Image.open(f"{out}/no_photo_photo.png").convert("RGBA").resize((200, 200), Image.LANCZOS)
sheet.alpha_composite(photo, (20, 15)); sheet.alpha_composite(art.resize((200, 200), Image.NEAREST), (240, 15))
dd.text((20, 225), "photo (in the app now)", fill=INK); dd.text((240, 225), "pixel art, outlined", fill=INK)
sheet.convert("RGB").save(f"{out}/no_photo_pixel_compare.png")
