import math, random, sys
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
import speech
import story
from speech import talking, SPANS

W, H, S, FPS = 1280, 720, 0.25, 30
SCENE_S, TEXT_S = 0.25, 0.5
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


@lru_cache(None)
def _font(px):
    return ImageFont.truetype(FONT, max(6, px))


def font(sz):
    return _font(int(sz * S))


def P(v):
    return int(round(v * S))


def clamp01(x):
    return max(0.0, min(1.0, x))


def ease(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def back(x):
    x = clamp01(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, u):
    return a + (b - a) * u


def lerpc(c1, c2, u):
    return tuple(int(lerp(a, b, u)) for a, b in zip(c1, c2))


def circ(d, x, y, r, fill):
    d.ellipse([P(x - r), P(y - r), P(x + r), P(y + r)], fill=fill)


def ell(d, x, y, rx, ry, fill):
    d.ellipse([P(x - rx), P(y - ry), P(x + rx), P(y + ry)], fill=fill)


# ---------------------------------------------------------------- helpers
ANCHORS = {}
GY = 650                                   # sol : les pieds des personnages



def path(t, keys):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= t < t1:
            return lerp(a, b, ease((t - t0) / (t1 - t0)))
    return keys[-1][1]


# ---------------------------------------------------------------- background
def star(d, x, y, r, rot, col):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = rot + i * math.pi / 5 - math.pi / 2
        pts.append((P(x + rr * math.cos(a)), P(y + rr * math.sin(a))))
    d.polygon(pts, fill=col)


def plain_cloud(d, x, y, k):
    for dx, dy, r in [(-40, 5, 28), (0, -12, 36), (40, 5, 28)]:
        circ(d, x + dx * k, y + dy * k, r * k, (250, 252, 255))
    d.rounded_rectangle([P(x - 62 * k), P(y), P(x + 62 * k), P(y + 32 * k)],
                        radius=P(16 * k), fill=(250, 252, 255))


def sun(d, t):
    cx, cy = 130, 115
    for k in range(10):
        a = k * 2 * math.pi / 10 + t * 0.4
        d.line([P(cx + 70 * math.cos(a)), P(cy + 70 * math.sin(a)),
                P(cx + 95 * math.cos(a)), P(cy + 95 * math.sin(a))],
               fill=(255, 205, 60), width=P(8))
    circ(d, cx, cy, 58, (255, 215, 70))
    circ(d, cx, cy, 50, (255, 228, 100))
    circ(d, cx - 17, cy - 8, 5, (90, 60, 40))
    circ(d, cx + 17, cy - 8, 5, (90, 60, 40))
    d.arc([P(cx - 18), P(cy - 2), P(cx + 18), P(cy + 22)], 20, 160,
          fill=(90, 60, 40), width=P(4))
    circ(d, cx - 30, cy + 10, 7, (255, 170, 120))
    circ(d, cx + 30, cy + 10, 7, (255, 170, 120))


# ---------------------------------------------------------------- characters
INK = (50, 35, 35)


def eyes(d, x, y, sp, r, mood, t, seed=0):
    blink = ((t + seed) % 3.4) < 0.12
    for sx in (-1, 1):
        ex = x + sx * sp
        if mood in ("closed", "happy", "strain") or blink:
            if mood == "strain":
                d.line([P(ex - r), P(y - r * 0.5 * sx), P(ex + r), P(y + r * 0.5 * sx)], fill=INK, width=P(4))
            else:
                d.arc([P(ex - r), P(y - r * 0.8), P(ex + r), P(y + r)], 200, 340, fill=INK, width=P(4))
        elif mood == "dizzy":
            d.line([P(ex - r), P(y - r), P(ex + r), P(y + r)], fill=INK, width=P(4))
            d.line([P(ex - r), P(y + r), P(ex + r), P(y - r)], fill=INK, width=P(4))
        elif mood == "sad":
            ell(d, ex, y + 2, r * 0.8, r * 0.9, INK)
            circ(d, ex + 2, y - 2, r * 0.3, (255, 255, 255))
            d.line([P(ex - sx * r * 1.1), P(y - r * 2.2), P(ex + sx * r * 0.9), P(y - r * 1.6)],
                   fill=INK, width=P(3))
        else:
            ell(d, ex, y, r * 0.8, r, INK)
            circ(d, ex + 2, y - 3, r * 0.32, (255, 255, 255))


def mouth(d, x, my, mood, talk, w=12):
    if talk > 0.02:
        ell(d, x, my, w * 0.85, 3 + 9 * talk, (140, 50, 60))
    elif mood in ("happy", "closed"):
        d.pieslice([P(x - w * 1.2), P(my - 8), P(x + w * 1.2), P(my + 12)], 0, 180, fill=(140, 50, 60))
    elif mood in ("oops", "dizzy"):
        ell(d, x, my + 2, w * 0.6, 6, (140, 50, 60))
    elif mood == "sad":
        d.arc([P(x - w), P(my), P(x + w), P(my + 14)], 200, 340, fill=INK, width=P(4))
    elif mood == "strain":
        d.line([P(x - w), P(my + 2), P(x + w), P(my + 2)], fill=INK, width=P(4))
    else:
        d.arc([P(x - w), P(my - 8), P(x + w), P(my + 6)], 20, 160, fill=INK, width=P(4))


def splash_stars(d, cx, cy, g, n=8, rr0=50, col2=(255, 220, 60)):
    for i in range(n):
        a = i * 2 * math.pi / n + g * 2
        rr = rr0 + 60 * g
        sz = 12 * math.sin(math.pi * min(1, g))
        if sz > 1:
            star(d, cx + rr * math.cos(a), cy + rr * math.sin(a), sz, g * 4 + i,
                 col2 if i % 2 else (255, 255, 255))


def bounce(t, f=6.0, h=14):
    return abs(math.sin(t * f)) * h



# ---------------------------------------------------------------- personnages
GW, GWD, GBR = (252, 250, 244), (218, 212, 202), (195, 135, 85)
HORN = (205, 185, 150)


def goat(d, x, gy, t, mood="smile", talk=0.0, lean=0.0, wet=0.0, run=0.0):
    """Nuno la petite chèvre (de face). Renvoie le haut de la tête."""
    by = gy - 64
    for lx, k in ((-38, 1), (38, 1), (-15, 0), (15, 0)):
        ph = math.sin(run * 14 + lx) * 6 if run else 0
        top_y = by + 10 - 6 * k
        d.rectangle([P(x + lx - 8), P(top_y), P(x + lx + 8), P(gy - 10 - ph)], fill=GWD if k else GW)
        d.rectangle([P(x + lx - 9), P(gy - 13 - ph), P(x + lx + 9), P(gy - ph)], fill=(110, 80, 70))
    ell(d, x, by, 56, 46, GWD)
    ell(d, x, by - 3, 52, 42, GW)
    ell(d, x + 24, by - 10, 18, 14, GBR)
    ell(d, x - 30, by + 14, 10, 8, GBR)
    hx, hy = x + lean, by - 94
    # collier et clochette
    d.arc([P(hx - 30), P(by - 66), P(hx + 30), P(by - 26)], 30, 150, fill=(70, 140, 230), width=P(7))
    circ(d, hx, by - 26, 10, (255, 205, 50))
    circ(d, hx, by - 22, 3, (150, 110, 30))
    # cornes
    for sx in (-1, 1):
        for k in range(7):
            u = k / 6
            circ(d, hx + sx * (16 + 10 * u + 8 * u * u), hy - 34 - 26 * u + 6 * u * u, 8 - 3 * u, HORN)
    # oreilles
    for sx in (-1, 1):
        ell(d, hx + sx * 50, hy - 4 + (6 if mood == "sad" else 0), 22, 10, GWD)
        ell(d, hx + sx * 50, hy - 3 + (6 if mood == "sad" else 0), 14, 5, (255, 190, 190))
    circ(d, hx, hy, 44, GWD)
    circ(d, hx, hy - 2, 41, GW)
    ell(d, hx + 6, hy - 34, 18, 9, GBR)                     # mèche brune
    # barbichette
    d.polygon([(P(hx - 9), P(hy + 36)), (P(hx + 9), P(hy + 36)), (P(hx + 2), P(hy + 62))], fill=GWD)
    ell(d, hx, hy + 18, 23, 16, (255, 218, 208))
    circ(d, hx - 7, hy + 12, 3, (150, 90, 90))
    circ(d, hx + 7, hy + 12, 3, (150, 90, 90))
    mouth(d, hx, hy + 24, mood, talk, 9)
    eyes(d, hx, hy - 10, 18, 9, mood, t)
    circ(d, hx - 31, hy + 10, 7, (255, 170, 185))
    circ(d, hx + 31, hy + 10, 7, (255, 170, 185))
    if wet > 0.02:
        for i in range(6):
            u = (t * 1.8 + i * 0.37) % 1
            dx = [-50, -20, 10, 40, -36, 28][i]
            circ(d, x + dx, by - 20 + 70 * u, 5 * wet, (110, 190, 255))
        for sx in (-1, 1):
            circ(d, hx + sx * 22, hy - 44 + 4 * math.sin(t * 6), 4 * wet, (110, 190, 255))
    return hx, hy - 72


LW, LWD, LF, LD = (252, 252, 255), (222, 222, 236), (250, 228, 212), (95, 85, 100)


def lamb(d, x, gy, t, mood="smile", talk=0.0, tears=False, lift=0.0, walk=0.0, lean=0.0):
    """Lulu le petit agneau, tourné vers la droite. Renvoie le haut de la tête."""
    for i, lx in enumerate((-36, -14, 16, 36)):
        sw = math.sin(walk * 13 + i * 1.7) * 7 if walk else 0
        d.line([P(x + lx), P(gy - 55 - lift), P(x + lx + sw), P(gy - 6)], fill=LD, width=P(9))
        ell(d, x + lx + sw, gy - 5, 7, 5, (60, 50, 60))
    cy = gy - 80 - lift
    ell(d, x, cy + 6, 58, 38, LWD)
    for k in range(10):
        a = k * 2 * math.pi / 10
        circ(d, x + 46 * math.cos(a), cy + 28 * math.sin(a), 22, LWD)
    for k in range(10):
        a = k * 2 * math.pi / 10
        circ(d, x + 44 * math.cos(a), cy - 3 + 26 * math.sin(a), 20, LW)
    ell(d, x, cy - 2, 46, 28, LW)
    circ(d, x - 54, cy - 8, 12, LW)                          # petite queue
    hx, hy = x + 50 + lean, cy - 44
    droop = 8 if mood == "sad" else 0
    ell(d, hx - 30, hy - 2 + droop, 20, 9, LD)
    ell(d, hx + 30, hy - 2 + droop, 20, 9, LD)
    ell(d, hx - 30, hy - 1 + droop, 12, 4, (255, 180, 190))
    ell(d, hx + 30, hy - 1 + droop, 12, 4, (255, 180, 190))
    ell(d, hx, hy + 4, 27, 31, (225, 200, 185))
    ell(d, hx, hy + 3, 25, 29, LF)
    for dx, dy in [(-16, -26), (0, -32), (16, -26), (-8, -20), (8, -20)]:
        circ(d, hx + dx, hy + dy, 12, LW)
    # petite fleur violette dans la laine
    fx, fy = hx + 14, hy - 38
    for k in range(5):
        a = k * 2 * math.pi / 5
        circ(d, fx + 6 * math.cos(a), fy + 6 * math.sin(a), 5, (175, 110, 230))
    circ(d, fx, fy, 4, (255, 220, 70))
    eyes(d, hx, hy - 2, 11, 7, mood, t, 1.3)
    ell(d, hx, hy + 14, 5, 3, (200, 120, 130))
    mouth(d, hx, hy + 20, mood, talk, 7)
    circ(d, hx - 18, hy + 10, 5, (255, 165, 185))
    circ(d, hx + 18, hy + 10, 5, (255, 165, 185))
    if tears:
        for s in (-1, 1):
            u = (t * 1.6 + (0.5 if s > 0 else 0)) % 1
            circ(d, hx + s * 13, hy + 2 + 34 * u, 5, (110, 190, 255))
    return hx, hy - 46


def butterfly(d, x, y, t, k=1.0, col=(255, 150, 50), col2=(255, 215, 80), face=False, talk=0.0, sp=14):
    w = 0.25 + 0.75 * abs(math.cos(t * sp))
    for s in (-1, 1):
        ell(d, x + s * 19 * w * k, y - 9 * k, 19 * w * k + 2, 16 * k, col)
        ell(d, x + s * 13 * w * k, y + 10 * k, 12 * w * k + 2, 11 * k, col2)
        circ(d, x + s * 21 * w * k, y - 11 * k, 5 * k * w + 1, (255, 255, 255))
    ell(d, x, y + 2 * k, 5 * k, 17 * k, (80, 55, 70))
    circ(d, x, y - 18 * k, 8 * k, (80, 55, 70))
    for s in (-1, 1):
        d.line([P(x + s * 3 * k), P(y - 24 * k), P(x + s * 12 * k), P(y - 38 * k)], fill=(80, 55, 70),
               width=max(1, P(3 * k)))
        circ(d, x + s * 12 * k, y - 38 * k, 3 * k, (80, 55, 70))
    if face:
        circ(d, x - 3 * k, y - 19 * k, 2 * k, (255, 255, 255))
        circ(d, x + 3 * k, y - 19 * k, 2 * k, (255, 255, 255))
        if talk > 0.05:
            circ(d, x, y - 13 * k, 2 * k, (255, 150, 160))
    return x, y - 44 * k


def ball(d, x, y, rot=0.0):
    circ(d, x, y, 25, (200, 45, 55))
    circ(d, x, y, 23, (240, 70, 70))
    nx, ny = math.cos(rot), math.sin(rot)
    d.line([P(x - 23 * nx), P(y - 23 * ny), P(x + 23 * nx), P(y + 23 * ny)], fill=(255, 215, 60), width=P(9))
    circ(d, x - 8, y - 9, 6, (255, 170, 170))



# ---------------------------------------------------------------- monde : le verger de Sunny Meadow en automne (après-midi venteux)
G1, G2, G3 = (150, 175, 75), (165, 188, 85), (185, 200, 100)
TRUNKX = 1030                              # le grand pommier
APPLE = (780, 212)                         # la grosse pomme rouge, tout en haut
PILE = (780, 642)                          # le tas de feuilles sous la pomme
LEAFC = [(235, 120, 40), (250, 175, 50), (210, 75, 45), (240, 200, 70), (190, 110, 50)]


def pine(d, x, y, h, col=(55, 120, 85)):
    d.rectangle([P(x - 6), P(y - 14), P(x + 6), P(y)], fill=(120, 85, 55))
    for k in range(3):
        w = (0.55 - k * 0.12) * h
        y0 = y - 10 - k * h * 0.27
        d.polygon([(P(x - w / 2), P(y0)), (P(x + w / 2), P(y0)), (P(x), P(y0 - h * 0.45))],
                  fill=lerpc(col, (90, 160, 110), k * 0.25))


def round_tree(d, x, y, h, col):
    d.rectangle([P(x - 6), P(y - h * 0.45), P(x + 6), P(y)], fill=(120, 85, 55))
    circ(d, x, y - h * 0.65, h * 0.33, lerpc(col, (0, 0, 0), 0.15))
    circ(d, x - h * 0.08, y - h * 0.7, h * 0.27, col)


def make_back():
    img = Image.new("RGB", (int(W * S), int(H * S)))
    d = ImageDraw.Draw(img)
    top, bot = (120, 180, 240), (255, 222, 175)            # ciel d'après-midi d'automne
    h = int(600 * S)
    for y in range(h):
        u = int(y / h * 7) / 6
        d.line([(0, y), (int(W * S), y)], fill=lerpc(top, bot, u))
    # montagnes violettes avec neige
    for row, (col, base) in enumerate([((160, 145, 200), 560), ((190, 165, 205), 575)]):
        peaks = [(80, 300), (390, 275), (720, 310), (1010, 265), (1260, 320)] if row == 0 else \
                [(230, 390), (560, 380), (870, 395), (1150, 385)]
        for px, py in peaks:
            wv = (base - py) * 1.25
            d.polygon([(P(px - wv), P(base)), (P(px + wv), P(base)), (P(px), P(py))], fill=col)
            k = 0.28
            d.polygon([(P(px - wv * k), P(py + (base - py) * k)), (P(px + wv * k), P(py + (base - py) * k)),
                       (P(px), P(py))], fill=(250, 250, 255))
            for j in range(-2, 3):
                circ(d, px + j * wv * k * 0.4, py + (base - py) * k, wv * k * 0.22, (250, 250, 255))
    # collines d'automne
    for cx, cy, rx, ry, c in [(170, 600, 330, 95, (205, 165, 80)), (640, 615, 360, 70, (185, 160, 75)),
                              (1120, 610, 330, 85, (200, 150, 70))]:
        ell(d, cx, cy, rx, ry, c)
    for x, hh in [(420, 120), (490, 150), (560, 110), (1190, 140), (1255, 115)]:
        pine(d, x, 600, hh)
    for x, hh, c in [(330, 120, (235, 130, 45)), (640, 110, (225, 90, 50)), (720, 130, (245, 180, 60)),
                     (860, 120, (230, 120, 45))]:
        round_tree(d, x, 600, hh, c)
    # bande d'herbe
    d.rectangle([0, P(590), int(W * S), int(H * S)], fill=G1)
    for i in range(4):
        d.rectangle([0, P(612 + i * 26), int(W * S), int(H * S)], fill=lerpc(G2, G3, i / 3))
    rng = random.Random(5)
    for _ in range(80):
        x, y = rng.uniform(0, 1280), rng.uniform(600, 718)
        d.line([P(x), P(y), P(x - 3), P(y - 9)], fill=(120, 150, 60), width=P(3))
        d.line([P(x), P(y), P(x + 4), P(y - 8)], fill=(120, 150, 60), width=P(3))
    for i in range(60):                                      # feuilles tombées dans l'herbe
        x, y = rng.uniform(0, 1280), rng.uniform(605, 716)
        ell(d, x, y, 7, 4, LEAFC[i % 5])
    for i, x in enumerate([60, 470, 1150, 1240]):            # petites citrouilles
        y = 690 if i % 2 else 670
        for dx in (-9, 0, 9):
            ell(d, x + dx, y, 12, 14, (240, 140, 40) if dx else (250, 160, 55))
        d.rectangle([P(x - 2), P(y - 20), P(x + 2), P(y - 12)], fill=(90, 130, 60))
    return img


BACK = make_back()


def windmill(d, t):
    """Le moulin à vent sur la colline (nouveau lieu de Sunny Meadow)."""
    x, y = 95, 525
    d.polygon([(P(x - 28), P(y + 60)), (P(x + 28), P(y + 60)), (P(x + 16), P(y - 40)), (P(x - 16), P(y - 40))],
              fill=(245, 235, 215))
    d.polygon([(P(x - 24), P(y - 38)), (P(x + 24), P(y - 38)), (P(x), P(y - 70))], fill=(200, 80, 70))
    d.rectangle([P(x - 8), P(y + 34), P(x + 8), P(y + 60)], fill=(150, 100, 70))
    a0 = t * 1.6
    for k in range(4):
        a = a0 + k * math.pi / 2
        ex, ey = x + 70 * math.cos(a), y - 40 + 70 * math.sin(a)
        d.line([P(x), P(y - 40), P(ex), P(ey)], fill=(130, 95, 70), width=P(5))
        px, py = -math.sin(a), math.cos(a)
        mx, my = x + 40 * math.cos(a), y - 40 + 40 * math.sin(a)
        d.polygon([(P(mx), P(my)), (P(ex), P(ey)), (P(ex + px * 16), P(ey + py * 16)),
                   (P(mx + px * 12), P(my + py * 12))], fill=(255, 250, 240))
    circ(d, x, y - 40, 6, (110, 80, 60))


def apple_draw(d, x, y, k=1.0, rot=0.0):
    circ(d, x - 9 * k, y, 19 * k, (205, 40, 50))
    circ(d, x + 9 * k, y, 19 * k, (205, 40, 50))
    circ(d, x - 8 * k, y - 2 * k, 16 * k, (235, 60, 60))
    circ(d, x + 8 * k, y - 2 * k, 16 * k, (235, 60, 60))
    circ(d, x - 10 * k, y - 9 * k, 5 * k, (255, 170, 170))
    sx, sy = x + 16 * k * math.sin(rot), y - 16 * k * math.cos(rot)
    tx, ty = x + 28 * k * math.sin(rot), y - 28 * k * math.cos(rot)
    d.line([P(sx), P(sy), P(tx), P(ty)], fill=(110, 75, 45), width=max(1, P(5 * k)))
    ell(d, tx + 9 * k, ty + 2 * k, 9 * k, 5 * k, (90, 170, 70))


def slice_draw(d, x, y, k=1.0):
    """Une tranche de pomme."""
    d.pieslice([P(x - 18 * k), P(y - 18 * k), P(x + 18 * k), P(y + 18 * k)], 180, 360, fill=(220, 50, 55))
    d.pieslice([P(x - 15 * k), P(y - 15 * k), P(x + 15 * k), P(y + 15 * k)], 180, 360, fill=(255, 245, 205))
    circ(d, x - 4 * k, y - 6 * k, 2 * k, (110, 70, 40))
    circ(d, x + 4 * k, y - 6 * k, 2 * k, (110, 70, 40))


def tree_back(d, t, sway):
    """Branches et feuillage du grand pommier (derrière tout le monde)."""
    s = sway
    d.line([P(TRUNKX), P(360), P(APPLE[0] + 10 + s), P(APPLE[1] - 40)], fill=(130, 85, 50), width=P(16))
    d.line([P(TRUNKX), P(330), P(1180 + s), P(170)], fill=(130, 85, 50), width=P(16))
    for cx, cy, r in [(1000, 120, 110), (880, 160, 90), (1130, 150, 100), (820, 200, 70), (960, 230, 100),
                      (1100, 250, 90), (1200, 230, 70)]:
        circ(d, cx + s * (1 - cy / 400), cy + 6, r, (175, 120, 40))
    for cx, cy, r in [(1000, 112, 104), (880, 152, 84), (1130, 142, 94), (820, 192, 64), (960, 222, 94),
                      (1100, 242, 84), (1200, 222, 64)]:
        circ(d, cx + s * (1 - cy / 400), cy, r, (215, 150, 45))
    rng = random.Random(3)
    for i in range(26):                                      # petites taches de feuilles colorées
        x, y = rng.uniform(800, 1220), rng.uniform(70, 300)
        ell(d, x + s * (1 - y / 400), y, 9, 6, LEAFC[i % 5])
    for x, y in [(900, 240), (1060, 170), (1160, 280), (980, 290)]:   # petites pommes au loin (déjà hautes)
        circ(d, x + s * (1 - y / 400), y, 9, (210, 50, 50))


def trunk(d):
    d.polygon([(P(TRUNKX - 30), P(GY + 2)), (P(TRUNKX + 30), P(GY + 2)), (P(TRUNKX + 20), P(330)),
               (P(TRUNKX - 20), P(330))], fill=(140, 92, 55))
    for o in (-10, 8):
        d.line([P(TRUNKX + o), P(GY - 10), P(TRUNKX + o * 0.7), P(360)], fill=(110, 72, 42), width=P(3))
    ell(d, TRUNKX, GY - 160, 9, 12, (95, 62, 38))


def pile(d, front=False):
    x, y = PILE
    if not front:
        ell(d, x, y, 112, 46, (200, 110, 40))
    rng = random.Random(9 if front else 4)
    for i in range(46 if not front else 30):
        a = rng.uniform(math.pi * 0.05, math.pi * 0.95)
        r = rng.uniform(0.2, 1.0)
        lx = x + 104 * r * math.cos(a)
        ly = y - 42 * r * math.sin(a) + (22 if front else 0)
        ell(d, lx, ly, 10, 6, LEAFC[i % 5])


def falling_leaves(d, t, n=16, wind=1.0):
    for i in range(n):
        r = random.Random(i * 13 + 1)
        per = r.uniform(7, 11)
        u = ((t + r.uniform(0, per)) % per) / per
        x = (r.uniform(-200, 1280) + u * 600 * wind + 30 * math.sin(t * 2 + i)) % 1480 - 100
        y = 60 + u * 600
        w = 8 * abs(math.cos(t * 3 + i))
        ell(d, x, y, w + 2, 5, LEAFC[i % 5])


def gust(d, t, t0, t1):
    """Lignes de vent qui traversent l'écran."""
    if not (t0 <= t <= t1):
        return
    g = (t - t0) / (t1 - t0)
    for i in range(5):
        x = -300 + g * 1900 - i * 120
        y = 200 + i * 70 + 10 * math.sin(t * 5 + i)
        d.arc([P(x), P(y - 20), P(x + 160), P(y + 20)], 200, 340, fill=(255, 255, 255), width=P(5))


def leaf_burst(d, cx, cy, g, n=16, seed=1):
    for i in range(n):
        r = random.Random(i + seed * 100)
        a = r.uniform(math.pi * 1.05, math.pi * 1.95)
        sp = r.uniform(150, 320)
        x = cx + sp * g * math.cos(a)
        y = cy + sp * g * math.sin(a) + 260 * g * g
        ell(d, x, y, 9, 6, LEAFC[i % 5])


def confetti_leaves(d, t, t0, n=40):
    for i in range(n):
        r = random.Random(i * 31 + 7)
        ts = t0 + r.uniform(0, 3)
        if t < ts:
            continue
        a = t - ts
        ang = r.uniform(0, 2 * math.pi) + a * 0.9
        rad = 120 + r.uniform(0, 380) + 20 * math.sin(a * 2 + i)
        x = 640 + rad * math.cos(ang) * 1.3
        y = 380 + rad * 0.55 * math.sin(ang) - 40
        ell(d, x, y, 8 * abs(math.cos(a * 4 + i)) + 2, 6, LEAFC[i % 5] if i % 6 else (255, 120, 170))


# ---------------------------------------------------------------- l'invité : Pom le petit hérisson
SP1, SP2 = (135, 90, 60), (105, 68, 45)


def hedgehog(d, x, gy, t, mood="smile", talk=0.0, curl=0.0, apple=False, hop=0.0, k=1.45):
    """Pom le petit hérisson (de face), une petite feuille verte piquée sur le dos. Renvoie le haut de la tête."""
    gy = gy - hop

    def X(v):
        return x + v * k

    def Y(v):
        return gy + v * k

    if curl > 0.5:                                           # roulé en boule
        cx, cy = x, Y(-40)
        for j in range(16):
            a = j * 2 * math.pi / 16 + curl * 6
            d.polygon([(P(cx + 34 * k * math.cos(a - 0.25)), P(cy + 34 * k * math.sin(a - 0.25))),
                       (P(cx + 50 * k * math.cos(a)), P(cy + 50 * k * math.sin(a))),
                       (P(cx + 34 * k * math.cos(a + 0.25)), P(cy + 34 * k * math.sin(a + 0.25)))], fill=SP2)
        circ(d, cx, cy, 38 * k, SP1)
        circ(d, cx + 10 * k * math.cos(curl * 6), cy + 10 * k * math.sin(curl * 6), 8 * k, (245, 222, 190))
        return x, Y(-90)
    by = -42
    for j in range(13):                                      # piquants
        a = math.pi + j * math.pi / 12
        d.polygon([(P(X(44 * math.cos(a - 0.2))), P(Y(by + 38 * math.sin(a - 0.2)))),
                   (P(X(66 * math.cos(a))), P(Y(by + 56 * math.sin(a) - 4))),
                   (P(X(44 * math.cos(a + 0.2))), P(Y(by + 38 * math.sin(a + 0.2))))], fill=SP2)
    ell(d, x, Y(by), 52 * k, 42 * k, SP1)
    for j in range(7):
        a = math.pi * 1.15 + j * math.pi * 0.7 / 6
        d.line([P(X(30 * math.cos(a))), P(Y(by + 24 * math.sin(a))), P(X(46 * math.cos(a))),
                P(Y(by + 36 * math.sin(a)))], fill=SP2, width=P(4))
    # petite feuille verte sur le dos
    ell(d, X(30), Y(by - 44), 12 * k, 6 * k, (100, 175, 70))
    d.line([P(X(20)), P(Y(by - 44)), P(X(40)), P(Y(by - 44))], fill=(70, 130, 50), width=P(2))
    for sx in (-1, 1):                                       # pieds
        ell(d, X(sx * 20), Y(-5), 13 * k, 7 * k, (90, 60, 50))
    ell(d, x, Y(by + 12), 34 * k, 30 * k, (240, 215, 180))  # visage + ventre
    for sx in (-1, 1):
        circ(d, X(sx * 28), Y(by - 22), 9 * k, SP1)          # oreilles
        circ(d, X(sx * 28), Y(by - 22), 5 * k, (240, 170, 160))
    hy = Y(by)
    eyes(d, x, hy - 2 * k, 12 * k, 6 * k, mood, t, 0.7)
    circ(d, x, hy + 10 * k, 6 * k, (60, 40, 40))             # petit nez
    circ(d, x - 2 * k, hy + 8 * k, 2 * k, (200, 200, 200))
    mouth(d, x, hy + 20 * k, mood, talk, 6 * k)
    circ(d, X(-22), hy + 10 * k, 5 * k, (255, 160, 170))
    circ(d, X(22), hy + 10 * k, 5 * k, (255, 160, 170))
    for sx in (-1, 1):                                       # petites mains
        circ(d, X(sx * 36), Y(by + 22), 7 * k, (215, 180, 150))
    if apple:
        apple_draw(d, X(-4), Y(by - 52), 1.0, 0.2)
    return x, Y(by - (95 if apple else 62))


def leaf_hat(d, x, y, rot=0.0):
    """Une feuille d'automne posée sur la tête de Nuno."""
    ell(d, x, y, 22, 10, (235, 130, 40))
    d.line([P(x - 20), P(y), P(x + 20), P(y)], fill=(170, 80, 30), width=P(3))
    ell(d, x + 14, y - 8, 14, 7, (250, 190, 60))

# ---------------------------------------------------------------- frame
NX0, LX0, PX0 = 560, 250, 930              # places de départ de Nuno, Lulu et Pom
LEGS0, LEG = 2.6, 1.0                      # passes de ballon au début


def seg(t, a, b):
    return a <= t < b


def nuno_state(t):
    nx, gy, mood, lean, run = NX0, GY, "smile", 0.0, 0.0
    if t < 15.6:
        mood = "happy"
        k = (t - LEGS0) / LEG
        for c in range(1, 14, 2):                          # il renvoie le ballon de la tête
            if abs(k - c) < 0.25:
                gy -= 26 * math.cos((k - c) / 0.25 * math.pi / 2)
    elif t < 19.4:
        mood = "smile"
        if t > 16.4:
            lean = 20 * math.sin((t - 16.4) * 3.2)
    elif t < 20.2:
        mood = "closed"
        nx += 6 * math.sin(t * 45)
    elif t < 27.3:
        mood = "happy"
    elif t < 31.0:
        mood = "oops"
    elif t < 39.6:
        mood = "smile"
    elif t < 46.8:
        mood = "sad"
    elif t < 49.0:
        mood = "happy"
        gy -= bounce(t, 7, 12)
    elif t < 50.6:                                         # il prend de l'élan
        g = (t - 49.0) / 1.6
        nx, mood, run = lerp(NX0, 440, ease(g)), "happy", t
    elif t < 51.4:
        nx, mood, gy = 440, "strain", GY + 6
    elif t < 53.4:
        g = (t - 51.4) / 2.0
        nx, mood, run = lerp(440, 670, g), "happy", t
    elif t < 54.3:                                         # boing boing ! trop court
        g = (t - 53.4) / 0.9
        nx = lerp(670, 780, g)
        gy = GY - 150 * math.sin(math.pi * g) + 70 * g * g
        mood, run = "happy", t
    elif t < 57.0:                                         # dans le tas de feuilles
        nx, gy = 780, GY + 70
        mood = "oops" if t < 55.6 else "dizzy" if t < 56.3 else "happy"
    elif t < 57.8:
        g = (t - 57.0) / 0.8
        nx = lerp(780, 670, g)
        gy = lerp(GY + 70, GY, g) - 90 * math.sin(math.pi * g)
        mood = "happy"
    elif t < 60.6:
        g = (t - 57.8) / 2.8
        nx, mood, run = lerp(670, NX0, ease(g)), "happy", t
    elif t < 63.2:
        mood = "happy"
    elif t < 64.0:
        mood = "closed"
        nx += 6 * math.sin(t * 45)
    elif t < 74.4:
        mood = "smile"
    elif t < 80.0:
        mood = "oops"
    elif t < 88.8:
        mood = "smile"
    elif t < 89.6:
        mood, gy = "oops", GY + 6
    elif t < 95.0:
        mood = "happy"
    elif t < 100.8:
        mood = "sad"
    elif t < 104.2:
        mood = "happy"
    elif t < 108.2:
        g = (t - 104.2) / 4.0
        nx, mood, run = lerp(NX0, 590, ease(g)), "smile", t
    elif t < 115.0:
        nx, mood = 590, "smile"
    elif t < 115.5:
        nx, mood, gy = 590, "strain", GY + 8
    elif t < 116.3:                                        # le grand saut : il renvoie le ballon !
        g = (t - 115.5) / 0.8
        nx, gy, mood = 590, GY - 140 * math.sin(math.pi * g), "happy"
    elif t < 117.0:
        nx, mood = 590, "oops"
    elif t < 125.0:
        nx, mood = 590, "happy"
        gy -= bounce(t, 6.5, 16)
    elif t < 127.0:
        g = (t - 125.0) / 2.0
        nx, mood, run = lerp(590, 575, ease(g)), "smile", t
    elif t < 138.6:
        nx, mood = 575, "happy" if t > 129 else "smile"
    else:
        nx, mood = 575, "happy"
        gy -= bounce(t, 6, 20)
        lean = 16 * math.sin(t * 4)
    return nx, gy, mood, lean, run


def lulu_state(t):
    lx, gy, mood, lift, walk, tears = LX0, GY, "smile", 0.0, 0.0, False
    if t < 15.6:
        mood = "happy"
        k = (t - LEGS0) / LEG
        for c in range(0, 14, 2):                          # elle renvoie le ballon
            if abs(k - c) < 0.25 and c > 0:
                lift = 20 * math.cos((k - c) / 0.25 * math.pi / 2)
    elif t < 20.2:
        mood = "happy"
    elif t < 27.3:
        mood = "smile"
    elif t < 31.0:
        mood = "oops"
    elif t < 39.6:
        mood = "smile"
    elif t < 46.8:
        mood = "sad"
    elif t < 54.3:
        mood = "smile"
    elif t < 57.0:
        mood = "oops"
    elif t < 64.0:
        mood = "happy"
    elif t < 74.4:
        mood = "smile"
    elif t < 80.0:
        mood = "oops"
    elif t < 84.4:
        mood = "happy"
    elif t < 87.4:
        mood = "strain" if t > 86.4 else "smile"
    elif t < 88.8:
        mood = "smile"
    elif t < 89.8:
        mood = "oops"
    elif t < 95.0:
        mood = "happy"
    elif t < 100.8:
        mood = "sad"
    elif t < 104.2:
        mood = "happy"
        lift = bounce(t, 7, 10) if t < 102.4 else 0
    elif t < 108.2:
        g = (t - 104.2) / 4.0
        lx, walk = lerp(LX0, 340, ease(g)), t
    elif t < 115.2:
        lx = 340
        mood = "strain" if t > 114.4 else "smile"
    elif t < 117.0:
        lx, mood = 340, "oops"
    elif t < 138.6:
        lx, mood = 340, "happy"
        if t < 125:
            lift = bounce(t + 0.3, 6.5, 12)
    else:
        lx, mood = 340, "happy"
        lift = bounce(t + 0.2, 6, 16)
    return lx, gy, mood, lift, walk, tears


def pom_state(t):
    """x, mood, curl, apple, hop, visible, behind_trunk"""
    if t < 28.0:
        return None
    px, mood, curl, apple, hop = PX0, "smile", 0.0, False, 0.0
    behind = False
    if t < 32.4:
        px = lerp(1190, 1120, ease((t - 28.0) / 1.0))
        mood, behind = "sad", True
    elif t < 35.6:
        px, mood = lerp(1120, PX0, ease((t - 32.4) / 3.2)), "sad"
        hop = bounce(t, 9, 5)
    elif t < 39.4:
        mood = "smile" if t > 36.6 else "sad"
    elif t < 47.0:
        mood = "sad"
    elif t < 54.3:
        mood = "smile"
    elif t < 57.0:
        mood = "oops"
    elif t < 64.0:
        mood = "happy"
    elif t < 74.4:
        mood = "smile"
    elif t < 80.0:
        mood = "oops"
    elif t < 95.0:
        mood = "smile"
    elif t < 100.8:
        mood = "sad"
    elif t < 104.2:
        mood = "smile"
    elif t < 108.2:
        px, mood = lerp(PX0, 780, ease((t - 104.2) / 4.0)), "smile"
        hop = bounce(t, 9, 5)
    elif t < 117.0:
        px, mood = 780, "smile" if t < 116.3 else "oops"
    elif t < 125.2:
        px, mood, apple = 780, "happy", True
        hop = bounce(t, 6, 14) if t > 117.8 else 0
    elif t < 138.6:
        px, mood = 780, "happy"
    elif t < 142.6:                                        # il roule en boule de joie
        g = (t - 138.6) / 4.0
        px = 780 + 90 * math.sin(math.pi * g)
        curl, mood = 1 + g * 4, "happy"
        hop = abs(math.sin(g * math.pi * 3)) * 30
    else:
        px, mood = 780, "happy"
        hop = bounce(t, 6, 18)
    return px, mood, curl, apple, hop, behind


def flutter_pos(t, ltop):
    """Position de Flutter (ou None), vitesse des ailes, dizzy."""
    hover = (430 + 40 * math.sin(t * 1.2), 350 + 15 * math.sin(t * 2.6))
    sp, dizzy = 14, False
    if t < 19.6:
        return None, sp, dizzy
    if t < 22.0:
        g = ease((t - 19.6) / 2.4)
        p = (lerp(1330, 600, g), lerp(300, 330, g) + 30 * math.sin(g * 7))
    elif t < 23.6:                                         # le vent la fait tourner
        g = (t - 22.0) / 1.6
        a = g * 2 * math.pi
        p = (600 - 60 * g + 55 * math.sin(a), 280 + 55 * math.cos(a))
    elif t < 25.0:
        g = ease((t - 23.6) / 1.4)
        p = (lerp(540, hover[0], g), lerp(335, hover[1], g))
    elif t < 64.6:
        p = hover
    elif t < 67.8:
        g = ease((t - 64.6) / 3.2)
        p = (lerp(hover[0], 738, g), lerp(hover[1], 214, g) - 40 * math.sin(math.pi * g))
    elif t < 74.4:                                         # elle pousse la pomme
        p = (738 + 3 * math.sin(t * 20), 214)
        sp = 22
    elif t < 78.6:                                         # emportée par le vent
        g = (t - 74.4) / 4.2
        a = g * 4 * math.pi
        bx, by = lerp(738, 330, ease(g)), lerp(214, 400, ease(g))
        p = (bx + 50 * math.sin(a), by - 50 * math.cos(a) + 50)
    elif t < 80.4:
        g = ease((t - 78.6) / 1.8)
        tx, ty = ltop[0] + 14, ltop[1] - 6
        p = (lerp(330, tx, g), lerp(450, ty, g))
    elif t < 84.4:                                         # posée sur la tête de Lulu
        p = (ltop[0] + 14, ltop[1] - 6)
        sp, dizzy = 4, t < 83.0
    elif t < 86.0:
        g = ease((t - 84.4) / 1.6)
        p = (lerp(ltop[0] + 14, hover[0], g), lerp(ltop[1] - 6, hover[1], g))
    elif t < 104.2:
        p = hover
    elif t < 107.0:
        g = ease((t - 104.2) / 2.8)
        p = (lerp(hover[0], 680, g), lerp(hover[1], 130, g))
    elif t < 116.4:
        p = (680 + 10 * math.sin(t * 2), 130 + 8 * math.sin(t * 3))
    elif t < 118.4:
        g = ease((t - 116.4) / 2.0)
        p = (lerp(680, 480, g), lerp(130, 330, g))
    elif t < 138.6:
        p = (480 + 30 * math.sin(t * 1.3), 330 + 12 * math.sin(t * 2.6))
    else:                                                  # danse en huit
        a = (t - 138.6) * 1.6
        p = (640 + 220 * math.sin(a), 300 + 50 * math.sin(2 * a))
    return p, sp, dizzy


def arc(a, b, g, hgt):
    return lerp(a[0], b[0], g), lerp(a[1], b[1], g) - hgt * math.sin(math.pi * g)


def ball_pos(t, ntop, ltop, lx):
    """Position du ballon rouge de Lulu."""
    nhead = (ntop[0], ntop[1] - 14)
    lhead = (ltop[0], ltop[1] - 12)
    feet = (lx + 110, GY - 25)
    if t < LEGS0:
        return lhead[0], lhead[1], 0
    if t < 15.6:
        k = int((t - LEGS0) / LEG)
        g = ((t - LEGS0) % LEG) / LEG
        a, b = (lhead, nhead) if k % 2 == 0 else (nhead, lhead)
        x, y = arc(a, b, g, 120)
        return x, y, t * 5
    if t < 19.4:
        return nhead[0], nhead[1], 0
    if t < 20.2:
        g = (t - 19.4) / 0.8
        x, y = arc(nhead, (NX0 - 90, GY - 25), g, 60)
        return x, y, t * 6
    if t < 21.4:
        g = ease((t - 20.2) / 1.2)
        x = lerp(NX0 - 90, LX0 + 110, g)
        return x, GY - 25 - 18 * abs(math.sin(g * 6)) * (1 - g), -x / 25
    if t < 84.4:
        return feet[0], feet[1], -feet[0] / 25
    if t < 85.2:
        g = ease((t - 84.4) / 0.8)
        return lerp(feet[0], lhead[0], g), lerp(feet[1], lhead[1], g), 0
    if t < 87.4:
        return lhead[0], lhead[1], 0
    if t < 88.0:                                           # vers la pomme : toc !
        x, y = arc(lhead, (735, 238), (t - 87.4) / 0.6, 90)
        return x, y, t * 6
    if t < 88.8:                                           # ... et retombe sur la tête de Nuno
        x, y = arc((735, 238), nhead, (t - 88.0) / 0.8, 40)
        return x, y, t * 6
    if t < 89.8:
        x, y = arc(nhead, (470, GY - 25), (t - 88.8) / 1.0, 80)
        return x, y, t * 6
    if t < 97.0:
        return 470, GY - 25, -470 / 25
    if t < 99.5:
        g = ease((t - 97.0) / 2.5)
        x = lerp(470, LX0 + 110, g)
        return x, GY - 25, -x / 25
    if t < 112.6:
        return feet[0], feet[1], -feet[0] / 25
    if t < 113.4:
        g = ease((t - 112.6) / 0.8)
        return lerp(feet[0], lhead[0], g), lerp(feet[1], lhead[1], g), 0
    if t < 115.2:
        return lhead[0], lhead[1], 0
    if t < 115.9:
        x, y = arc(lhead, (590, 266), (t - 115.2) / 0.7, 70)
        return x, y, t * 6
    if t < 116.3:
        x, y = arc((590, 266), (752, 222), (t - 115.9) / 0.4, 40)
        return x, y, t * 6
    if t < 117.5:
        x, y = arc((752, 222), (1150, GY - 25), (t - 116.3) / 1.2, 90)
        return x, y, t * 6
    return 1150, GY - 25, 0


def scene(t, with_sun=True):
    img = BACK.copy()
    d = ImageDraw.Draw(img)
    if with_sun:
        sun(d, t)
    gusty = 1.0 + (1.5 if 74.4 < t < 77 or 138.6 < t < 141 else 0)
    for base, y, k, sp in [(300, 150, 0.8, 18), (900, 220, 0.7, 24)]:
        plain_cloud(d, (base + t * sp) % 1580 - 150, y, k)
    windmill(d, t * gusty)
    sway = 5 * math.sin(t * 1.3) + (14 * math.sin((t - 74.4) * 6) if 74.4 < t < 76.4 else 0)
    tree_back(d, t, sway)

    # ---------------- la grosse pomme
    if t < 116.3:
        r = 0.06 * math.sin(t * 1.5)
        if 67.8 < t < 74.4:
            r = 0.13 * math.sin(t * 14)
        elif 88.0 <= t < 90.0:
            r = 0.45 * math.sin((t - 88.0) * 16) * (1 - (t - 88.0) / 2.0)
        pvx, pvy = APPLE[0] + sway * 0.5, APPLE[1] - 30
        apple_draw(d, pvx + 30 * math.sin(r), pvy + 30 * math.cos(r), 1.0, -r)
    elif t < 117.0:
        g = (t - 116.3) / 0.7
        apple_draw(d, lerp(APPLE[0], 776, g), lerp(APPLE[1], GY - 136, g * g), 1.0, g * 6)

    pile(d)

    # ---------------- Pom (derrière le tronc au début)
    ps = pom_state(t)
    ptop = None
    if ps and ps[5]:
        ptop = hedgehog(d, ps[0], GY, t, ps[1], talking("pom", t), ps[2], ps[3], ps[4])
    trunk(d)
    if ps and not ps[5]:
        ptop = hedgehog(d, ps[0], GY, t, ps[1], talking("pom", t), ps[2], ps[3], ps[4])
        if 125.2 <= t < 129.0:                              # il soulève la pomme
            u = ease((t - 125.2) / 0.8)
            apple_draw(d, ps[0], lerp(GY - 136, GY - 190, u) + 5 * math.sin(t * 4), 1.0 + 0.2 * u, 0.0)
    if ps and 28.0 < t < 31.4:                              # snif snif
        for k in range(2):
            u = ((t - 28.0) * 0.8 + k * 0.5) % 1
            circ(d, ps[0] + (k * 2 - 1) * 20, GY - 66 + 40 * u, 5, (110, 190, 255))   # petites larmes

    # ---------------- Nuno
    nx, gy, nmood, nlean, nrun = nuno_state(t)
    ntop = goat(d, nx, gy, t, nmood, talking("nuno", t), nlean, 0.0, nrun)
    if 54.3 <= t < 57.0:                                   # les feuilles par-dessus Nuno
        pile(d, front=True)
    if 54.3 <= t < 55.8:
        leaf_burst(d, PILE[0], PILE[1] - 30, (t - 54.3) / 1.5, 22, 1)
    if 54.5 <= t < 63.2:
        leaf_hat(d, ntop[0] + 4, ntop[1] + 30, 0)
    elif 63.2 <= t < 64.6:
        g = (t - 63.2) / 1.4
        leaf_hat(d, ntop[0] + 4 + 140 * g, ntop[1] + 30 - 80 * math.sin(math.pi * g) + 200 * g * g, g * 4)

    # ---------------- Lulu
    lx, lgy, lmood, llift, lwalk, ltears = lulu_state(t)
    ltop = lamb(d, lx, lgy - (bounce(t, 9, 5) if lwalk else 0), t, lmood, talking("lulu", t), ltears, llift,
                lwalk, 0.0)

    # ---------------- le ballon rouge
    bx, by, brot = ball_pos(t, ntop, ltop, lx)
    ball(d, bx, by, brot)

    # ---------------- Flutter
    fp, fsp, fdizzy = flutter_pos(t, ltop)
    ftop = None
    if fp:
        ftop = butterfly(d, fp[0], fp[1], t, 1.3, (255, 140, 40), (255, 210, 70), True, talking("flutter", t), fsp)
        if fdizzy:
            for k in range(3):
                a = t * 5 + k * 2.1
                star(d, fp[0] + 34 * math.cos(a), fp[1] - 60 + 10 * math.sin(a), 8, a, (255, 220, 60))

    # ---------------- tranches de pomme partagées
    if 129.0 <= t < 138.4:
        targets = [(ps[0] + 52, GY - 80), (nx + 40, gy - 130), (ltop[0] + 36, ltop[1] + 64)]
        if fp:
            targets.append((fp[0] + 32, fp[1] + 6))
        g = ease((t - 129.0) / 1.0)
        kk = 1.0 if t < 136.0 else max(0.0, 1 - (t - 136.0) / 2.4)
        for i, (tx, ty) in enumerate(targets):
            sx, sy = ps[0] + (i - 1.5) * 20, GY - 190
            if kk > 0.05:
                slice_draw(d, lerp(sx, tx, g), lerp(sy, ty, g) - 50 * math.sin(math.pi * g), 0.9 * kk)

    # ---------------- effets
    falling_leaves(d, t, 14 if gusty < 2 else 26, gusty)
    gust(d, t, 74.4, 76.6)
    gust(d, t, 138.6, 140.8)
    if 100.8 < t < 102.4:                                  # l'idée de Lulu
        splash_stars(d, ltop[0], ltop[1] - 20, (t - 100.8) / 1.6, 8, 30)
    if 117.0 < t < 118.6:
        splash_stars(d, ps[0], GY - 120, (t - 117.0) / 1.6, 10, 50)
    if 129.0 < t < 130.4:
        splash_stars(d, ps[0], GY - 190, (t - 129.0) / 1.4, 8, 30)
    if t > 138.6:
        confetti_leaves(d, t, 138.6)

    ANCHORS["nuno"] = ntop
    ANCHORS["lulu"] = ltop
    if ptop:
        ANCHORS["pom"] = ptop
    if ftop:
        ANCHORS["flutter"] = ftop
    elif "flutter" in ANCHORS:
        del ANCHORS["flutter"]
    return img, nx, GY, ltop



def caption(d, text, t0, t1, t):
    if not (t0 <= t <= t1):
        return
    u = min(ease((t - t0) / 0.4), ease((t1 - t) / 0.3))
    off = (1 - u) * 130
    sz = 40
    while font(sz).getlength(text) / S > 1020:
        sz -= 1
    f = font(sz)
    tw = f.getlength(text) / S
    bw = tw + 70
    x0, y0 = 640 - bw / 2, 628 + off
    d.rounded_rectangle([P(x0 + 4), P(y0 + 6), P(x0 + bw + 4), P(y0 + 78)], radius=P(36),
                        fill=(40, 120, 175))
    d.rounded_rectangle([P(x0), P(y0), P(x0 + bw), P(y0 + 72)], radius=P(36),
                        fill=(255, 255, 255))
    d.text((P(640), P(y0 + 36)), text, font=f, fill=(90, 60, 140), anchor="mm")


def bubble(d, text, ax, ay, side, u):
    f = font(26)
    w = f.getlength(text) / S + 36
    off = (1 - u) * 18
    y0, y1 = ay - 72 + off, ay - 16 + off
    if side == "up":                                    # bulle centrée au-dessus de la tête
        y0, y1 = y0 - 22, y1 - 22
        x0 = min(max(ax - w / 2, 12), 1268 - w)
        tx = min(max(ax, x0 + 30), x0 + w - 30)
        tail = [(P(ax), P(ay + off * 0.3)), (P(tx - 15), P(y1 - 4)), (P(tx + 15), P(y1 - 4))]
    else:
        x0 = ax + 18 if side == "right" else ax - 18 - w
        x0 = min(max(x0, 12), 1268 - w)
        tail = [(P(ax), P(ay + off * 0.3)), (P(x0 + (22 if side == "right" else w - 52)), P(y1 - 4)),
                (P(x0 + (52 if side == "right" else w - 22)), P(y1 - 4))]
    ol = (90, 60, 140)
    d.rounded_rectangle([P(x0 - 3), P(y0 - 3), P(x0 + w + 3), P(y1 + 3)], radius=P(28), fill=ol)
    d.polygon([(a, b + P(3)) for a, b in tail], fill=ol)
    d.rounded_rectangle([P(x0), P(y0), P(x0 + w), P(y1)], radius=P(26), fill=(255, 255, 255))
    d.polygon(tail, fill=(255, 255, 255))
    d.text((P(x0 + w / 2), P((y0 + y1) / 2)), text, font=f, fill=ol, anchor="mm")


TITLE_COLS = [(255, 90, 120), (255, 150, 40), (240, 190, 20), (70, 180, 90),
              (60, 140, 250), (160, 100, 230)]


def title(d, t):
    if t > story.TITLE_OUT + 0.7:
        return
    series = getattr(story, "SERIES", "")
    if series:                                              # nom de la série, au-dessus du titre de l'épisode
        u = back((t + 0.1) / 0.4)
        out = ease((t - story.TITLE_OUT) / 0.6) * -320
        d.text((P(640), P(lerp(-60, 38, u) + out)), series, font=font(38), fill=(255, 255, 255), anchor="mm",
               stroke_width=P(6), stroke_fill=(90, 60, 140))
    text = story.TITLE
    f = font(72)
    total = f.getlength(text) / S
    x = 640 - total / 2
    out = ease((t - story.TITLE_OUT) / 0.6) * -320
    ci = 0
    for i, ch in enumerate(text):
        wch = f.getlength(ch) / S
        u = back((t + 0.2 - i * 0.03) / 0.4)
        if ch != " " and u > 0:
            y = lerp(-140, 145 if getattr(story, "SERIES", "") else 115, u) + out + 6 * math.sin(t * 3 + i * 0.6)
            d.text((P(x), P(y)), ch, font=f, fill=TITLE_COLS[ci % 6], anchor="ls",
                   stroke_width=P(7), stroke_fill=(255, 255, 255))
        if ch != " ":
            ci += 1
        x += wch


def fin(d, t):
    if t < story.DURATION - 2.7:
        return
    u = back((t - story.DURATION + 2.7) / 0.7)
    sz = max(8, 95 * u)
    d.text((P(640), P(120 + 5 * math.sin(t * 4))), "The End!", font=font(sz),
           fill=(255, 100, 150), anchor="mm", stroke_width=P(8 * u), stroke_fill=(255, 255, 255))



def frame(t):
    global S
    img, x, y, head = scene(t)
    img = img.resize((int(W * TEXT_S), int(H * TEXT_S)), Image.NEAREST)
    S = TEXT_S
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    for who, t0, t1, text, side in SPANS:
        if t0 - 0.1 <= t <= t1 + 0.9 and who in ANCHORS:
            u = min(back((t - t0 + 0.1) / 0.3), ease((t1 + 0.9 - t) / 0.2))
            ax, ay = ANCHORS[who]
            bubble(d, text, ax, ay + 20, side, u)
    title(d, t)
    for text, c0, c1 in story.CAPTIONS:
        caption(d, text, c0, c1, t)
    fin(d, t)
    S = SCENE_S
    return img.resize((W, H), Image.NEAREST)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        for tt in sys.argv[2:]:
            frame(float(tt)).save(f"still_{tt}.png")
    else:
        f0, f1 = int(sys.argv[2]), int(sys.argv[3])
        out = sys.stdout.buffer
        for n in range(f0, f1):
            out.write(frame(n / FPS).tobytes())
