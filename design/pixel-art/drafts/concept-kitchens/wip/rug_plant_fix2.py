from pathlib import Path

p = Path("design/pixel-art/concept_kitchens.py")
s = p.read_text(encoding="utf-8")
start = s.index("def rug(a: Art, top: tuple[int, int], bottom: tuple[int, int]")
end = s.index("def vine(a: Art, x: int, y: int, length: int")
new = '''def rug(a: Art, top: tuple[int, int], bottom: tuple[int, int], y0: int, y1: int, base: str, border: str, motif: str,
        fringe: bool = False, accent: str | None = None) -> None:
    """A floor rug in perspective (narrower at the back). Every pixel is worked out from where it sits inside the rug
    (u across, v down, both 0 to 1), so the pattern always stays on the rug and scales with it: a double border with a
    running pattern, a field of small repeating diamonds, a nested medallion, and a diamond on each side."""
    accent = accent or border
    def edge(y: int) -> tuple[int, int]:
        t = (y - y0) / max(1, y1 - y0 - 1)
        return round(top[0] + (bottom[0] - top[0]) * t), round(top[1] + (bottom[1] - top[1]) * t)
    height = y1 - y0
    for y in range(y0, y1):
        lx, rx = edge(y)
        width = rx - lx
        v = (y - y0) / max(1, height - 1)
        for x in range(lx, rx):
            u = (x - lx) / max(1, width - 1)
            pu, pv = (x - lx), (y - y0)                                # rug-local pixels, for repeating patterns
            in_u, in_v = min(pu, width - 1 - pu), min(pv, height - 1 - pv)   # distance to the rug's edges
            ring = min(in_u, in_v * 1.4)
            if ring < 2:
                col = border
            elif ring < 4:
                col = motif if (pu + pv) % 4 < 2 else accent            # the running pattern in the border
            elif ring < 5:
                col = border
            else:
                col = base
                if (pu % 8 + pv % 6 * 1.3) < 2.5 or (abs(pu % 8 - 4) + abs(pv % 6 - 3) * 1.3) < 1.6:
                    col = tone(base, 0.82)                             # a field of small diamonds
                du, dv = abs(u - 0.5) / 0.18, abs(v - 0.5) / 0.38
                d = du + dv
                if d < 1:                                              # the medallion: nested diamonds
                    col = motif if d > 0.8 else accent if d > 0.62 else base if d > 0.42 else motif if d > 0.24 else border
                for side in (0.2, 0.8):
                    ds = abs(u - side) / 0.07 + abs(v - 0.5) / 0.3
                    if ds < 1:
                        col = accent if ds < 0.5 else motif
            a.put(x, y, col)
    if fringe:
        for y in (y0 - 1, y1):
            lx, rx = edge(min(max(y, y0), y1 - 1))
            for x in range(lx, rx, 2):
                a.put(x, y, "#F1E6CF")


def leaves(a: Art, cx: int, cy: int, w: int, h: int, greens: tuple[str, ...] = ("#3F7A2E", "#5E9B3A", "#7DB84A"),
           count: int = 40, leaf: tuple[int, int] = (7, 4)) -> None:
    """Foliage. A wide, low area (trees seen through a window, a hedge) becomes rounded, shaded clumps; anything else
    becomes a potted plant: a fan of long arching leaves from the stem, each widest a third of the way out, with a
    vein, lighter on the upper side and drooping at the sides, as in the concept art."""
    if w > 2.2 * h:                                                   # canopy: rounded clumps, back row first
        for row in range(3):
            for k in range(max(2, w // 8)):
                bw = a.rand.randint(8, 14)
                bx = cx - w // 2 + a.rand.randrange(max(1, w - bw))
                by = cy - h // 2 + row * h // 3
                a.ellipse(bx, by, bw, max(6, h // 2), greens[min(len(greens) - 1, row)], "sphere", 0.55)
        return
    stem = (cx, cy + h * 0.45)
    reach = max(w, h) * 0.6
    n = max(5, min(16, count // 3))
    for k in range(n):
        side = -1 if k % 2 else 1
        spread = (k // 2) / max(1, n // 2)                          # 0 = upright, 1 = out to the side
        ang = math.radians(90 + side * (10 + 75 * spread) + a.rand.uniform(-8, 8))
        length = reach * a.rand.uniform(0.75, 1.05) * (1.0 - 0.15 * spread)
        width = max(2.5, leaf[1] * 0.9 + reach * 0.09)
        droop = 0.25 + 0.6 * spread
        pts_l, pts_r, spine = [], [], []
        for j in range(9):
            t = j / 8
            x = stem[0] + math.cos(ang) * length * t
            y = stem[1] - math.sin(ang) * length * t + droop * length * t * t   # the leaf arches over
            spine.append((x, y))
        for j, (x, y) in enumerate(spine):
            t = j / 8
            half = width * (t / 0.35 if t < 0.35 else (1 - t) / 0.65) / 2
            if j < 8:
                nx, ny = spine[j + 1][0] - x, spine[j + 1][1] - y
            else:
                nx, ny = x - spine[j - 1][0], y - spine[j - 1][1]
            norm = math.hypot(nx, ny) or 1
            px, py = -ny / norm, nx / norm
            pts_l.append((x + px * half, y + py * half))
            pts_r.append((x - px * half, y - py * half))
        outline = pts_l + list(reversed(pts_r))
        shade = greens[-1] if spread < 0.34 else greens[1] if spread < 0.7 else greens[0]
        a.shape(lambda d, outline=outline: d.polygon(outline, fill=255), shade, "plain", 0.55)
        a.shape(lambda d, pts_l=pts_l: d.line(pts_l[1:-1], fill=255), tone(shade, 1.18), "plain", 0)   # lit edge
        a.line([(round(x), round(y)) for x, y in spine[1:-1]], tone(shade, 0.75))                        # the vein


'''
s = s[:start] + new + s[end:]
# A second colour in the rugs that have one in the originals
s = s.replace('''    rug(a, (198, 350), (192, 356), 202, 227, "#C8392A", "#8E2414", "#3FA34D", fringe=True)''',
              '''    rug(a, (198, 350), (192, 356), 202, 227, "#C8392A", "#8E2414", "#F2C14E", fringe=True, accent="#2F6DB5")''')
s = s.replace('''    rug(a, (112, 350), (107, 355), 201, 231, "#C8392A", "#2F4F8C", "#F2C14E", fringe=True)''',
              '''    rug(a, (112, 350), (107, 355), 201, 231, "#C8392A", "#2F4F8C", "#F2C14E", fringe=True, accent="#2F6DB5")''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
