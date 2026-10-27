"""The no-photo picture as true pixel art, from Gemini concept art (design/pixel-art/previews/skillet_concept_gemini.jpg,
made by med27-coder): crop to the skillet, one colour per cell (the cell's most common colour, so edges stay sharp),
a shared palette of K flat colours, white made transparent.
Run: python -I design/pixel-art/skillet_from_concept.py <out folder> <size> [<colours>]
"""
import sys
from collections import Counter

import numpy as np
from PIL import Image

out, N = sys.argv[1], int(sys.argv[2])
K = int(sys.argv[3]) if len(sys.argv) > 3 else 32
src = Image.open("design/pixel-art/previews/skillet_concept_gemini.jpg").convert("RGB")
a = np.asarray(src)
ys, xs = np.nonzero(a.min(axis=2) < 225)                     # everything that is not the white background
x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
side = max(x1 - x0, y1 - y0) + 8
cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
box = (cx - side // 2, cy - side // 2, cx - side // 2 + side, cy - side // 2 + side)
crop = Image.new("RGB", (side, side), "white")                  # white beyond the concept's edges, never black
crop.paste(src.crop((max(box[0], 0), max(box[1], 0), min(box[2], src.width), min(box[3], src.height))),
           (max(-box[0], 0), max(-box[1], 0)))
c = np.asarray(crop)
body = c[c.min(axis=2) < 225]                                   # the palette comes from the skillet alone, so the
sample = Image.fromarray(body.reshape(1, -1, 3))                # white background cannot crowd out yellow and blue
palimg = sample.quantize(colors=K - 1, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
hsv = np.asarray(Image.fromarray(body.reshape(1, -1, 3)).convert("HSV"))[0] / 255
pinned = []                                                     # small areas a palette would merge: pin their colour
for lo, hi, smin in ((0.52, 0.66, 0.30), (0.12, 0.19, 0.60)):  # the blue handle, the yellow handle
    m = (hsv[:, 0] > lo) & (hsv[:, 0] < hi) & (hsv[:, 1] > smin) & (hsv[:, 2] > 0.5)
    pinned += np.median(body[m], axis=0).astype(int).tolist() if m.any() else []
flat = palimg.getpalette()[:3 * (K - 1)] + pinned + [255, 255, 255]
palimg.putpalette(flat + [0] * (768 - len(flat)))
pal = crop.quantize(palette=palimg, dither=Image.Dither.NONE)
p = np.asarray(pal)
cell = side / N
art = Image.new("RGBA", (N, N))
colors = pal.getpalette()
for y in range(N):
    for x in range(N):
        blk = p[int(y * cell + cell * 0.2):int((y + 1) * cell - cell * 0.2) + 1,
                int(x * cell + cell * 0.2):int((x + 1) * cell - cell * 0.2) + 1]
        i = Counter(blk.ravel().tolist()).most_common(1)[0][0]
        r, g, b = colors[3 * i:3 * i + 3]
        art.putpixel((x, y), (0, 0, 0, 0) if min(r, g, b) >= 225 else (r, g, b, 255))
art.save(f"{out}/skillet_pixel_{N}.png")
print(N, "px,", len({c for c in art.get_flattened_data() if c[3]}), "colours")
