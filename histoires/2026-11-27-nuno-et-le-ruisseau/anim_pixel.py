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


# ---------------------------------------------------------------- monde : prairie de montagne au printemps
SX0, SX1 = 462, 572                        # le ruisseau (bords en haut de la bande d'herbe)
LOGB = (446, GY - 4)                       # pied du vieux tronc (pivot quand il tombe)
LOGL = 178                                 # longueur du tronc
BALLX = 660                                # le ballon de Lulu, de l'autre côté
G1, G2, G3 = (110, 190, 80), (125, 205, 90), (150, 220, 110)
WATER, WATERD, WATERL = (90, 175, 235), (70, 150, 215), (170, 220, 250)


def cam(t):
    """Centre x de la caméra verticale : elle suit l'action."""
    return path(t, [(0, 470), (21.0, 470), (23.0, 515)])


def pine(d, x, y, h, col=(55, 130, 85)):
    d.rectangle([P(x - 6), P(y - 14), P(x + 6), P(y)], fill=(120, 85, 55))
    for k in range(3):
        w = (0.55 - k * 0.12) * h
        y0 = y - 10 - k * h * 0.27
        d.polygon([(P(x - w / 2), P(y0)), (P(x + w / 2), P(y0)), (P(x), P(y0 - h * 0.45))],
                  fill=lerpc(col, (90, 170, 110), k * 0.25))


def flower(d, x, y, r, col):
    for k in range(5):
        a = k * 2 * math.pi / 5
        circ(d, x + r * math.cos(a), y + r * math.sin(a), r * 0.75, col)
    circ(d, x, y, r * 0.6, (255, 215, 60))


def make_back():
    img = Image.new("RGB", (int(W * S), int(H * S)))
    d = ImageDraw.Draw(img)
    top, bot = (110, 185, 245), (215, 238, 252)
    h = int(600 * S)
    for y in range(h):
        u = int(y / h * 7) / 6
        d.line([(0, y), (int(W * S), y)], fill=lerpc(top, bot, u))
    # montagnes violettes avec neige
    for row, (col, base) in enumerate([((160, 150, 210), 560), ((185, 175, 225), 575)]):
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
    # collines vertes au loin
    for cx, cy, rx, ry, c in [(150, 610, 330, 80, (150, 205, 115)), (640, 615, 360, 70, (140, 200, 105)),
                              (1120, 610, 330, 85, (150, 205, 115))]:
        ell(d, cx, cy, rx, ry, c)
    for x, hh in [(60, 120), (140, 150), (215, 110), (790, 130), (860, 160), (1180, 140), (1250, 115)]:
        pine(d, x, 600, hh)
    # bande d'herbe
    d.rectangle([0, P(590), int(W * S), int(H * S)], fill=G1)
    for i in range(4):
        d.rectangle([0, P(612 + i * 26), int(W * S), int(H * S)], fill=lerpc(G2, G3, i / 3))
    rng = random.Random(7)
    for _ in range(90):
        x, y = rng.uniform(0, 1280), rng.uniform(600, 718)
        if SX0 - 40 < x < SX1 + 40:
            continue
        d.line([P(x), P(y), P(x - 3), P(y - 9)], fill=(90, 165, 70), width=P(3))
        d.line([P(x), P(y), P(x + 4), P(y - 8)], fill=(90, 165, 70), width=P(3))
    cols = [(255, 255, 255), (255, 150, 190), (190, 140, 240), (255, 220, 70), (120, 180, 255)]
    for i in range(34):
        x, y = rng.uniform(0, 1280), rng.uniform(675, 715)
        if SX0 - 30 < x < SX1 + 30 or 250 < x < 440 and y < 700:
            continue
        flower(d, x, y, rng.uniform(5, 8), cols[i % 5])
    # le ruisseau
    d.polygon([(P(SX0 - 6), P(590)), (P(SX1 + 6), P(590)), (P(SX1 + 22), P(720)), (P(SX0 - 22), P(720))],
              fill=(95, 150, 70))
    d.polygon([(P(SX0), P(590)), (P(SX1), P(590)), (P(SX1 + 14), P(720)), (P(SX0 - 14), P(720))], fill=WATER)
    d.polygon([(P(SX0 + 30), P(590)), (P(SX1 - 30), P(590)), (P(SX1 - 24), P(720)), (P(SX0 + 24), P(720))],
              fill=WATERD)
    for x, y, r in [(SX0 - 10, 640, 10), (SX1 + 12, 660, 12), (SX0 - 18, 700, 13), (SX1 + 20, 705, 11),
                    (SX0 - 2, 605, 7), (SX1 + 4, 615, 8)]:
        circ(d, x, y, r, (150, 150, 160))
        circ(d, x - r * 0.3, y - r * 0.3, r * 0.45, (190, 190, 200))
    return img


BACK = make_back()


def stream_anim(d, t):
    for i in range(10):
        y = 592 + ((i * 29 + t * 45) % 126)
        f = (y - 590) / 130
        x0 = lerp(SX0, SX0 - 14, f) + 18 + (i * 37) % 60
        d.line([P(x0), P(y), P(x0 + 16), P(y)], fill=WATERL, width=P(3))


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


def old_log(d, th):
    bx, by = LOGB
    dx, dy = math.sin(th), -math.cos(th)
    tx, ty = bx + LOGL * dx, by + LOGL * dy
    d.line([P(bx), P(by), P(tx), P(ty)], fill=(145, 98, 58), width=P(30))
    nx, ny = -dy, dx
    for o in (-7, 6):
        d.line([P(bx + nx * o + dx * 14), P(by + ny * o + dy * 14), P(tx + nx * o - dx * 20), P(ty + ny * o - dy * 20)],
               fill=(115, 75, 45), width=P(3))
    circ(d, tx, ty, 15, (225, 190, 140))
    circ(d, tx, ty, 9, (195, 150, 100))
    circ(d, tx, ty, 3, (160, 115, 75))
    # petite branche avec une feuille
    mx, my = bx + dx * LOGL * 0.6, by + dy * LOGL * 0.6
    ex, ey = mx + nx * 26 + dx * 14, my + ny * 26 + dy * 14
    d.line([P(mx), P(my), P(ex), P(ey)], fill=(145, 98, 58), width=P(6))
    ell(d, ex, ey, 9, 6, (110, 190, 80))


def seeds(d, t, t0, n=24, seed=3):
    """Graines de pissenlit et pétales qui volent."""
    cols = [(255, 255, 255), (255, 180, 210), (200, 160, 245), (255, 230, 120)]
    for i in range(n):
        r = random.Random(i * 7 + seed)
        ts = t0 + r.uniform(0, 4.0)
        if t < ts:
            continue
        a = t - ts
        x = r.uniform(250, 760) + 30 * math.sin(a * 2 + i) + a * 12
        y = 700 - a * r.uniform(70, 110)
        if y < 260:
            continue
        c = cols[i % 4]
        if i % 2:
            d.line([P(x), P(y), P(x), P(y + 10)], fill=(220, 220, 220), width=P(2))
            for k in range(6):
                aa = k * math.pi / 3
                d.line([P(x), P(y), P(x + 7 * math.cos(aa)), P(y + 7 * math.sin(aa))], fill=c, width=P(2))
        else:
            ell(d, x, y, 6, 4, c)


# ---------------------------------------------------------------- frame
def scene(t, with_sun=True):
    img = BACK.copy()
    d = ImageDraw.Draw(img)
    if with_sun:
        sun(d, t)
    for base, y, k, sp in [(300, 150, 0.8, 10), (900, 210, 0.7, 14)]:
        plain_cloud(d, (base + t * sp) % 1580 - 150, y, k)
    stream_anim(d, t)

    # ---------------- le vieux tronc
    if t < 16.3:
        th = 0.0
    elif t < 18.4:
        g = (t - 16.3) / 0.7
        th = 0.07 * max(0.0, math.sin(math.pi * (g % 1))) * (1 + int(g) * 0.4)
    elif t < 19.0:
        g = (t - 18.4) / 0.6
        th = 0.1 + (math.pi / 2 - 0.1) * g * g
    else:
        th = math.pi / 2 - 0.06 * max(0.0, math.sin(math.pi * clamp01((t - 19.0) / 0.3)))
    old_log(d, th)

    # ---------------- le ballon (avant que Lulu le prenne)
    if t < 23.3:
        ball(d, BALLX, GY - 25 - 4 * abs(math.sin(t * 2)), 0.3)

    # ---------------- Nuno
    nx = 415.0
    gy, mood, lean, wet, run = GY, "smile", 0.0, 0.0, 0.0
    if t < 3.4:
        gy -= bounce(t, 6, 24)
        mood = "happy"
    elif t < 6.6:
        gy -= bounce(t, 4.5, 46) if 3.8 < t < 6.2 else 0
        mood = "happy"
    elif 7.4 <= t < 10.6:
        mood = "sad"
    if 11.2 <= t < 11.6:
        gy += 8
        mood = "strain"
    elif 11.6 <= t < 12.3:
        g = (t - 11.6) / 0.7
        nx = lerp(415, 517, g)
        gy = GY - 130 * math.sin(math.pi * g) + 36 * g * g
        mood = "happy"
        run = t
    elif 12.3 <= t < 13.6:
        nx, gy = 517, GY + 36
        mood = "oops" if t < 13.0 else "smile"
        wet = 1.0
    elif 13.6 <= t < 14.3:
        g = (t - 13.6) / 0.7
        nx = lerp(517, 415, g)
        gy = lerp(GY + 36, GY, g) - 80 * math.sin(math.pi * g)
        mood = "smile"
        wet = 1.0
    elif 14.3 <= t < 15.2:
        mood = "closed"
        nx += 7 * math.sin(t * 45)
        wet = 1 - clamp01((t - 14.3) / 0.9)
    elif 16.3 <= t < 18.4:
        mood = "strain"
        g = (t - 16.3) / 0.7
        lean = 6 * max(0.0, math.sin(math.pi * (g % 1)))
        nx += lean
    elif 18.4 <= t < 19.0:
        mood = "oops"
    elif t >= 19.0:
        mood = "happy"
        if t < 20.4 or t > 23.6:
            gy -= bounce(t, 6.5, 16)
    ntop = goat(d, nx, gy, t, mood, talking("nuno", t), lean, wet, run)
    if 12.3 <= t < 13.9:                                       # l'eau du ruisseau par-dessus
        d.polygon([(P(455), P(GY - 12)), (P(579), P(GY - 12)), (P(588), P(722)), (P(446), P(722))], fill=WATER)
        ell(d, 517, GY - 12, 70, 9, WATERL)
        if t < 13.0:
            g = (t - 12.3) / 0.7
            for i in range(9):
                a = math.pi + i * math.pi / 8
                circ(d, 517 + (40 + 90 * g) * math.cos(a), GY - 20 + (40 + 120 * g) * math.sin(a) + 160 * g * g,
                     9 * (1 - g) + 2, WATERL if i % 2 else WATER)
        if 12.5 < t < 13.4:                                    # petit jet d'eau rigolo
            for k in range(5):
                u = ((t - 12.5) * 2 + k * 0.2) % 1
                circ(d, ntop[0] + 30 * u * (1 if k % 2 else -1), ntop[1] + 60 - 70 * math.sin(math.pi * u),
                     5, WATERL)
    if 14.3 < t < 15.2:                                        # il s'ébroue
        g = ((t - 14.3) * 2) % 1
        for i in range(10):
            a = i * math.pi / 5 + 0.2
            circ(d, nx + (60 + 70 * g) * math.cos(a), GY - 110 + (50 + 60 * g) * math.sin(a), 6 * (1 - g) + 2,
                 (110, 190, 255))

    # ---------------- Lulu
    lx = path(t, [(0, 296), (21.0, 296), (23.2, 610)])
    walking = 21.0 < t < 23.2
    on_log = clamp01((lx - 425) / 25) * clamp01((630 - lx) / 25) * 22 if walking else 0
    lmood, tears, llift, llean = "sad", False, 0.0, 0.0
    if t < 6.2 or 7.6 <= t < 11.2:
        tears = True
    if 6.2 <= t < 7.6:
        lmood = "smile"
    if 11.2 <= t < 12.3:
        lmood = "smile"
    elif 12.3 <= t < 14.4:
        lmood = "oops"
    elif 14.4 <= t < 16.3:
        lmood = "smile"
    elif 16.3 <= t < 18.4:
        lmood = "strain"
        g = (t - 16.3) / 0.7
        lx += 6 * max(0.0, math.sin(math.pi * (g % 1)))
        llean = 4
    elif 18.4 <= t < 19.0:
        lmood = "oops"
    elif t >= 19.0:
        lmood = "happy"
        if t < 20.4 or t > 23.3:
            llift = bounce(t + 0.3, 6.5, 12)
    if t < 3.4:
        lx += 2 * math.sin(t * 30) if 1.6 < t < 3.0 else 0
    ltop = lamb(d, lx, GY - on_log - (bounce(t, 9, 5) if walking else 0), t, lmood, talking("lulu", t), tears,
                llift, t if walking else 0, llean)

    # ---------------- le ballon qui vole entre Lulu et Nuno
    if t >= 23.3:
        pl = (ltop[0], ltop[1] - 10)
        pn = (ntop[0], ntop[1] - 14)
        if t < 23.7:
            g = (t - 23.3) / 0.4
            bx, by2 = lerp(BALLX, pl[0], g), lerp(GY - 25, pl[1], g) - 40 * math.sin(math.pi * g)
        else:
            n = int((t - 23.7) / 0.9)
            g = ((t - 23.7) % 0.9) / 0.9
            a, b = (pl, pn) if n % 2 == 0 else (pn, pl)
            bx, by2 = lerp(a[0], b[0], g), lerp(a[1], b[1], g) - 55 * math.sin(math.pi * g)
        ball(d, bx, by2, t * 5)

    # ---------------- Flutter le papillon
    if t >= 14.5:
        perch = (LOGB[0], LOGB[1] - LOGL - 30)
        sp = 14
        if t < 15.6:
            g = ease((t - 14.5) / 1.1)
            fx, fy = lerp(760, perch[0], g), lerp(330, perch[1], g) + 30 * math.sin(g * 6)
        elif t < 16.3:
            fx, fy = perch
            sp = 4
        elif t < 21.0:
            g = ease((t - 16.3) / 0.6)
            hx, hy = (520 + 30 * math.sin(t * 1.5), 420 + 14 * math.sin(t * 3))
            fx, fy = lerp(perch[0], hx, g), lerp(perch[1], hy, g)
        else:
            fx, fy = 470 + 70 * math.sin(t * 1.2), 400 + 18 * math.sin(t * 2.6)
        ftop = butterfly(d, fx, fy, t, 1.3, (255, 140, 40), (255, 210, 70), True, talking("flutter", t), sp)
        ANCHORS["flutter"] = ftop

    # ---------------- effets
    if 15.0 < t < 16.2:                                        # l'idée du papillon
        splash_stars(d, LOGB[0], LOGB[1] - LOGL, (t - 15.0) / 1.2, 6, 26)
    if 19.0 < t < 20.5:                                        # le pont est prêt !
        splash_stars(d, 530, GY - 40, (t - 19.0) / 1.5, 10, 60)
    if t > 19.2:
        seeds(d, t, 19.2, 14, 3)
    if t > 23.4:
        seeds(d, t, 23.4, 26, 11)
    if t > 24.0:                                               # les amis papillons arrivent
        cols = [((120, 170, 255), (190, 220, 255)), ((255, 120, 180), (255, 190, 220)),
                ((170, 120, 240), (220, 190, 255)), ((110, 210, 140), (190, 240, 200)),
                ((255, 230, 90), (255, 245, 170))]
        for i, (c1, c2) in enumerate(cols):
            g = ease((t - 24.0 - i * 0.25) / 1.2)
            if g <= 0:
                continue
            sx, sy = [(250, 280), (790, 300), (250, 520), (790, 470), (520, 250)][i]
            hx = 320 + i * 90 + 30 * math.sin(t * 1.7 + i)
            hy = 330 + (i % 2) * 70 + 20 * math.sin(t * 2.3 + i * 2)
            butterfly(d, lerp(sx, hx, g), lerp(sy, hy, g), t + i * 0.3, 0.7, c1, c2)

    ANCHORS["nuno"] = ntop
    ANCHORS["lulu"] = ltop
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
    x0 = ax + 18 if side == "right" else ax - 18 - w
    ol = (90, 60, 140)
    tail = [(P(ax), P(ay + off * 0.3)), (P(x0 + (22 if side == "right" else w - 52)), P(y1 - 4)),
            (P(x0 + (52 if side == "right" else w - 22)), P(y1 - 4))]
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
            y = lerp(-140, 115, u) + out + 6 * math.sin(t * 3 + i * 0.6)
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
