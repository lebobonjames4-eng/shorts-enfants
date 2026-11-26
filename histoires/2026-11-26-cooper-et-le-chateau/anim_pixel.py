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



CX = 462                                   # le château de sable (centre)
PX = 612                                   # Pebble, le bébé phoque
SAND, SANDD, SANDL = (240, 205, 140), (210, 170, 105), (250, 225, 170)


def cam(t):
    """Centre x de la caméra verticale : elle suit l'action."""
    return path(t, [(0, 470), (19.4, 470), (20.2, 462)])


# ---------------------------------------------------------------- background
def star(d, x, y, r, rot, col):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = rot + i * math.pi / 5 - math.pi / 2
        pts.append((P(x + rr * math.cos(a)), P(y + rr * math.sin(a))))
    d.polygon(pts, fill=col)


def shell(d, x, y, r, col):
    d.pieslice([P(x - r), P(y - r), P(x + r), P(y + r)], 180, 360, fill=col)
    for k in range(-2, 3):
        d.line([P(x), P(y), P(x + k * r * 0.4), P(y - r * 0.85)], fill=lerpc(col, (120, 80, 80), 0.35),
               width=P(2))


def starfish(d, x, y, r, rot, col):
    star(d, x, y, r, rot, col)
    circ(d, x, y, r * 0.25, lerpc(col, (255, 255, 255), 0.3))


def make_back():
    img = Image.new("RGB", (int(W * S), int(H * S)))
    d = ImageDraw.Draw(img)
    top, bot = (95, 185, 245), (190, 232, 252)
    h = int(470 * S)
    for y in range(h):
        u = int(y / h * 7) / 6
        d.line([(0, y), (int(W * S), y)], fill=lerpc(top, bot, u))
    # mer
    sea = [(50, 150, 205), (60, 165, 210), (70, 180, 215), (85, 195, 215), (100, 205, 212)]
    for i, c in enumerate(sea):
        d.rectangle([0, P(470 + i * 21), int(W * S), P(470 + (i + 1) * 21 + 1)], fill=c)
    # petite île au loin, avec un palmier
    ell(d, 640, 474, 110, 18, (230, 205, 140))
    ell(d, 640, 470, 80, 14, (120, 185, 95))
    for k in range(8):
        u = k / 7
        circ(d, 640 + 14 * math.sin(u * 2), 465 - u * 70, 5, (140, 100, 60))
    tx, ty = 640 + 14 * math.sin(2), 395
    for a in [-2.8, -2.0, -1.1, -0.3]:
        for j in range(7):
            v = j / 6
            circ(d, tx + math.cos(a) * 42 * v, ty + math.sin(a) * 42 * v + 20 * v * v, 8 * (1 - 0.5 * v),
                 (70, 160, 90))
    # phare (16:9)
    ell(d, 1110, 478, 90, 20, (130, 120, 115))
    for k in range(6):
        y0 = 470 - (k + 1) * 32
        wv = 26 - k * 2
        d.rectangle([P(1110 - wv), P(y0), P(1110 + wv), P(y0 + 32)],
                    fill=(235, 70, 70) if k % 2 == 0 else (250, 250, 250))
    d.rectangle([P(1092), P(256), P(1128), P(278)], fill=(255, 230, 120))
    d.polygon([(P(1084), P(258)), (P(1136), P(258)), (P(1110), P(226))], fill=(200, 60, 60))
    # sable
    d.rectangle([0, P(578), int(W * S), int(H * S)], fill=SAND)
    for i in range(4):
        d.rectangle([0, P(640 + i * 22), int(W * S), int(H * S)], fill=lerpc(SAND, SANDL, (i + 1) / 5))
    rng = random.Random(11)
    for _ in range(140):
        x, y = rng.uniform(0, 1280), rng.uniform(590, 718)
        circ(d, x, y, 3, SANDD)
    for x, y, r, c in [(250, 705, 14, (255, 170, 190)), (690, 700, 12, (255, 240, 225)),
                       (880, 660, 15, (255, 190, 150)), (60, 650, 13, (255, 170, 190)),
                       (1200, 700, 14, (255, 240, 225))]:
        shell(d, x, y, r, c)
    starfish(d, 300, 690, 20, 0.3, (255, 140, 70))
    starfish(d, 1010, 700, 22, 0.8, (250, 110, 150))
    # parasol rayé (16:9)
    d.line([P(80), P(700), P(96), P(480)], fill=(150, 110, 70), width=P(8))
    for k in range(6):
        a0, a1 = 180 + k * 30, 180 + (k + 1) * 30
        d.pieslice([P(-34), P(430), P(226), P(560)], a0, a1, fill=(255, 90, 110) if k % 2 else (255, 250, 240))
    return img


BACK = make_back()


def sailboat(d, x, y):
    d.polygon([(P(x - 30), P(y)), (P(x + 30), P(y)), (P(x + 20), P(y + 12)), (P(x - 20), P(y + 12))],
              fill=(200, 80, 60))
    d.line([P(x), P(y), P(x), P(y - 50)], fill=(120, 90, 60), width=P(3))
    d.polygon([(P(x + 2), P(y - 50)), (P(x + 2), P(y - 4)), (P(x + 30), P(y - 4))], fill=(255, 255, 255))
    d.polygon([(P(x - 2), P(y - 40)), (P(x - 2), P(y - 4)), (P(x - 22), P(y - 4))], fill=(255, 220, 90))


def waves(d, t):
    """Bord de l'eau qui va et vient doucement."""
    edge = 586 + 8 * math.sin(t * 1.4)
    d.rectangle([0, P(578), int(W * S), P(edge + 6)], fill=(205, 175, 120))
    d.rectangle([0, P(570), int(W * S), P(edge)], fill=(115, 210, 215))
    for i in range(0, 1300, 40):
        circ(d, i + 10 * math.sin(t * 2 + i), edge, 13, (250, 252, 255))
    for i in range(0, 1300, 70):
        y = 500 + (i * 37) % 60
        x = (i + t * 12) % 1300
        d.line([P(x - 12), P(y), P(x + 12), P(y)], fill=(160, 220, 240), width=P(3))


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


CR, CRD, CRL = (240, 85, 60), (195, 55, 45), (255, 150, 115)


def claw(d, x, y, ang, pinch):
    """Pince de crabe ouverte vers ang (radians)."""
    circ(d, x, y, 24, CR)
    op = 0.25 + 0.35 * pinch
    a0, a1 = math.degrees(ang - op), math.degrees(ang + op)
    d.pieslice([P(x - 26), P(y - 26), P(x + 26), P(y + 26)], a0, a1, fill=CRD)
    circ(d, x - 7 * math.cos(ang), y - 7 * math.sin(ang), 7, CRL)


def crab(d, x, gy, t, mood="smile", talk=0.0, lc=None, rc=None, pinch=0.0, sand=0.0, walk=0.0):
    """Cooper le petit crabe (vue de face). lc/rc = position des pinces (monde). Renvoie le haut."""
    by = gy - 62
    # pattes
    for sx in (-1, 1):
        for k in range(3):
            ph = math.sin(walk * 12 + k * 2.1 + (0 if sx > 0 else 1.5)) * 6 * (1 if walk else 0)
            bx, byy = x + sx * (42 + k * 12), by + 10
            kx, ky = x + sx * (78 + k * 9), by - 6 - ph
            fx, fy = x + sx * (88 + k * 6), gy - 2 - max(0, ph)
            d.line([P(bx), P(byy), P(kx), P(ky)], fill=CRD, width=P(10))
            d.line([P(kx), P(ky), P(fx), P(fy)], fill=CRD, width=P(10))
    # bras + pinces
    cl = {-1: lc or (x - 96, by - 52), 1: rc or (x + 96, by - 52)}
    for sx in (-1, 1):
        cx, cy = cl[sx]
        d.line([P(x + sx * 56), P(by - 12), P(cx), P(cy)], fill=CR, width=P(13))
    # corps
    ell(d, x, by, 74, 48, CRD)
    ell(d, x, by - 3, 70, 44, CR)
    ell(d, x - 18, by - 22, 22, 10, CRL)
    for sx in (-1, 1):
        cx, cy = cl[sx]
        ang = math.atan2(cy - (by - 12), cx - (x + sx * 56))
        claw(d, cx, cy, ang, pinch)
    circ(d, x - 42, by + 6, 8, (255, 160, 160))
    circ(d, x + 42, by + 6, 8, (255, 160, 160))
    mouth(d, x, by + 8, mood, talk, 14)
    # tas de sable sur la tête
    if sand > 0.02:
        ell(d, x, by - 40, 66 * sand, 34 * sand, SANDD)
        ell(d, x, by - 42, 62 * sand, 30 * sand, SAND)
        for dx, dy in [(-30, -10), (12, -26), (34, -6), (-6, -30)]:
            circ(d, x + dx * sand, by - 40 + dy * sand, 12 * sand, SANDL)
    # yeux sur tiges
    ey = by - 82
    for sx in (-1, 1):
        d.line([P(x + sx * 18), P(by - 36), P(x + sx * 24), P(ey)], fill=CR, width=P(9))
        circ(d, x + sx * 24, ey, 18, CRD)
        circ(d, x + sx * 24, ey, 15, (255, 255, 255))
    eyes(d, x, ey, 24, 8, mood, t)
    return x, ey - 22


SG, SGD, SGL = (150, 170, 198), (115, 135, 168), (222, 230, 242)


def seal(d, x, gy, t, mood="smile", talk=0.0, tip=None, lift=0.0, tears=False):
    """Pebble le bébé phoque, couché, tourné vers la gauche. tip = bout de la nageoire avant. Renvoie le haut."""
    wag = 0.25 * math.sin(t * 4)
    tx, ty = x + 56, gy - 12
    for sgn in (-1, 1):
        a = sgn * 0.5 + wag
        d.polygon([(P(tx), P(ty)), (P(tx + 34 * math.cos(a)), P(ty + 22 * math.sin(a) - 8)),
                   (P(tx + 26 * math.cos(a) + 6), P(ty + 22 * math.sin(a) + 8))], fill=SGD)
    ell(d, x, gy - 62, 68, 62, SGD)
    ell(d, x, gy - 64, 64, 58, SG)
    ell(d, x - 14, gy - 52, 40, 44, SGL)
    for k in range(4):
        circ(d, x + 34 + (k % 2) * 12, gy - 100 + k * 18, 4, SGD)
    hx, hy = x - 16, gy - 152 - lift
    circ(d, hx, hy, 54, SGD)
    circ(d, hx, hy, 51, SG)
    # nœud rose
    bx, by = hx + 26, hy - 44
    d.polygon([(P(bx), P(by)), (P(bx - 26), P(by - 16)), (P(bx - 24), P(by + 14))], fill=(255, 105, 160))
    d.polygon([(P(bx), P(by)), (P(bx + 26), P(by - 16)), (P(bx + 24), P(by + 14))], fill=(255, 105, 160))
    circ(d, bx, by, 8, (255, 160, 200))
    # museau
    ell(d, hx - 14, hy + 20, 30, 20, SGL)
    for s in (-1, 1):
        for k in (-1, 1):
            d.line([P(hx - 14 + s * 20), P(hy + 22 + k * 4), P(hx - 14 + s * 46), P(hy + 18 + k * 10)],
                   fill=(110, 110, 130), width=P(2))
    ell(d, hx - 14, hy + 9, 9, 6, INK)
    mouth(d, hx - 14, hy + 30, mood, talk, 9)
    eyes(d, hx - 12, hy - 14, 21, 11, mood, t, 0.7)
    circ(d, hx - 46, hy + 10, 7, (255, 165, 185))
    circ(d, hx + 22, hy + 10, 7, (255, 165, 185))
    if tears:
        for s in (-1, 1):
            u = (t * 1.6 + (0.5 if s > 0 else 0)) % 1
            ex = hx - 12 + s * 26
            circ(d, ex + s * 6, hy - 2 + 40 * u, 6, (110, 190, 255))
    # nageoire avant
    sx0, sy0 = x - 40, gy - 84
    tx2, ty2 = tip or (x - 72, gy - 22)
    d.line([P(sx0), P(sy0), P(tx2), P(ty2)], fill=SGD, width=P(28))
    ell(d, tx2, ty2, 20, 13, SGD)
    d.line([P(sx0), P(sy0), P(tx2), P(ty2)], fill=SG, width=P(22))
    return hx, hy - 58


def gull(d, x, y, t, flap=0.0, talk=0.0, mood="smile", stand=True):
    """Gus la mouette, de profil, tournée vers la gauche. (x, y) = centre du corps. Renvoie le haut de la tête."""
    wh, gr, grd = (252, 252, 255), (175, 185, 200), (120, 130, 150)
    if stand:
        for sx in (-6, 8):
            d.line([P(x + sx), P(y + 16), P(x + sx), P(y + 32)], fill=(255, 150, 60), width=P(4))
            d.polygon([(P(x + sx - 9), P(y + 34)), (P(x + sx + 5), P(y + 30)), (P(x + sx + 5), P(y + 35))],
                      fill=(255, 150, 60))
    d.polygon([(P(x + 22), P(y - 6)), (P(x + 50), P(y - 2)), (P(x + 24), P(y + 12))], fill=grd)
    ell(d, x, y, 32, 22, wh)
    hx, hy = x - 24, y - 22
    circ(d, hx, hy, 19, wh)
    if mood == "happy":
        d.arc([P(hx - 12), P(hy - 9), P(hx - 1), P(hy + 3)], 200, 340, fill=INK, width=P(3))
    else:
        circ(d, hx - 7, hy - 4, 4.5, INK)
    op = 7 * talk
    d.polygon([(P(hx - 14), P(hy - 2)), (P(hx - 44), P(hy + 2 - op * 0.3)), (P(hx - 14), P(hy + 6))],
              fill=(255, 205, 60))
    d.polygon([(P(hx - 14), P(hy + 6)), (P(hx - 38), P(hy + 6 + op)), (P(hx - 14), P(hy + 11))],
              fill=(240, 175, 50))
    circ(d, hx - 32, hy + 5, 3, (240, 80, 60))
    if flap:
        a = math.sin(t * 20) * flap
        tipy = y - 12 - 46 * a
        d.polygon([(P(x - 10), P(y - 6)), (P(x + 18), P(y - 6)), (P(x + 34), P(tipy)), (P(x + 4), P(tipy + 6))],
                  fill=gr)
        d.polygon([(P(x + 34), P(tipy)), (P(x + 46), P(tipy - 4 * a)), (P(x + 24), P(tipy + 4))], fill=INK)
    else:
        ell(d, x + 8, y - 2, 24, 13, gr)
        d.polygon([(P(x + 24), P(y - 6)), (P(x + 44), P(y + 2)), (P(x + 26), P(y + 6))], fill=INK)
    return hx, hy - 24


def bucket(d, x, yc, g=0.0, fill=0.0):
    """Seau rouge centré en (x, yc). g = retournement (0 droit, 1 à l'envers)."""
    c = math.cos(math.pi * g)
    rim, base = yc - 32 * c, yc + 32 * c
    d.polygon([(P(x - 36), P(rim)), (P(x + 36), P(rim)), (P(x + 26), P(base)), (P(x - 26), P(base))],
              fill=(230, 60, 85))
    d.line([P(x - 34), P(rim + 9 * c), P(x + 34), P(rim + 9 * c)], fill=(255, 210, 70), width=P(5))
    if c > 0.3:
        ell(d, x, rim, 36, 8 * c, (150, 30, 50) if fill < 0.2 else SAND)
        if fill > 0.2:
            for dx in (-18, 0, 16):
                circ(d, x + dx, rim - 6 * fill, 10 * fill, SANDL)
        d.arc([P(x - 34), P(rim - 30 * c), P(x + 34), P(rim + 20 * c)], 190, 350, fill=(255, 210, 70),
              width=P(4))


def tower(d, cx, base_y, wb, wt, h, u, flag=0.0, t=0.0):
    """Tour de château de sable qui pousse depuis le sol (u = 0..1)."""
    if u <= 0.02:
        return
    hh = h * u
    top = base_y - hh
    d.polygon([(P(cx - wb / 2), P(base_y)), (P(cx + wb / 2), P(base_y)), (P(cx + wt / 2), P(top)),
               (P(cx - wt / 2), P(top))], fill=SAND)
    d.polygon([(P(cx + wb / 2 - 10), P(base_y)), (P(cx + wb / 2), P(base_y)), (P(cx + wt / 2), P(top)),
               (P(cx + wt / 2 - 8), P(top))], fill=SANDD)
    n = 3
    cw = wt / (2 * n - 1)
    for k in range(n):
        x0 = cx - wt / 2 + k * 2 * cw
        d.rectangle([P(x0), P(top - 12 * u), P(x0 + cw), P(top + 1)], fill=SAND)
    if hh > 50:
        wy = top + hh * 0.35
        d.pieslice([P(cx - 9), P(wy - 10), P(cx + 9), P(wy + 8)], 180, 360, fill=(140, 100, 70))
        d.rectangle([P(cx - 9), P(wy - 1), P(cx + 9), P(wy + 12)], fill=(140, 100, 70))
    if flag > 0.02:
        fy, fx = top - 12, cx - 18
        d.line([P(fx), P(fy), P(fx), P(fy - 58 * flag)], fill=(120, 90, 60), width=P(4))
        wv = 6 * math.sin(t * 8)
        d.polygon([(P(fx - 2), P(fy - 58 * flag)), (P(fx - 2 - 40 * flag), P(fy - 48 * flag + wv)),
                   (P(fx - 2), P(fy - 36 * flag))], fill=(255, 90, 150))


def castle(d, t, ub, um, ul, ur, flag):
    gy = GY - 4
    if ub > 0.02:
        hb = 70 * ub
        d.rectangle([P(CX - 82), P(gy - hb), P(CX + 82), P(gy)], fill=SAND)
        d.rectangle([P(CX + 70), P(gy - hb), P(CX + 82), P(gy)], fill=SANDD)
        for k in range(7):
            x0 = CX - 82 + k * 25
            d.rectangle([P(x0), P(gy - hb - 10 * ub), P(x0 + 14), P(gy - hb + 1)], fill=SAND)
        for dx, c in [(-50, (255, 170, 190)), (0, (255, 240, 225)), (50, (255, 190, 150))]:
            if ub > 0.6:
                shell(d, CX + dx, gy - 18, 10, c)
    tower(d, CX - 66, gy - 40, 52, 42, 130, ul)
    tower(d, CX + 66, gy - 40, 52, 42, 130, ur)
    tower(d, CX, gy - 50, 86, 64, 170, um, flag, t)


def mound(d):
    ell(d, CX, GY - 10, 78, 24, SANDD)
    ell(d, CX, GY - 12, 74, 20, SAND)
    ell(d, CX + 22, GY - 30, 26, 24, SAND)
    ell(d, CX - 30, GY - 22, 18, 14, SANDL)
    d.polygon([(P(CX - 2), P(GY - 26)), (P(CX + 42), P(GY - 26)), (P(CX + 36), P(GY - 92)),
               (P(CX + 22), P(GY - 80)), (P(CX + 8), P(GY - 98))], fill=SAND)
    d.polygon([(P(CX + 34), P(GY - 26)), (P(CX + 42), P(GY - 26)), (P(CX + 36), P(GY - 92))], fill=SANDD)
    for dx, dy in [(-50, -20), (58, -12), (-14, -34)]:
        circ(d, CX + dx, GY + dy, 10, SANDL)
    shell(d, CX - 40, GY - 6, 9, (255, 170, 190))


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


# ---------------------------------------------------------------- frame
def scene(t, with_sun=True):
    img = BACK.copy()
    d = ImageDraw.Draw(img)
    if with_sun:
        sun(d, t)
    for base, y, k, sp in [(300, 130, 0.8, 10), (900, 190, 0.7, 14)]:
        plain_cloud(d, (base + t * sp) % 1580 - 150, y, k)
    sailboat(d, 300 + t * 9, 468)
    waves(d, t)

    # ---------------- château de sable
    if t < 19.3:
        mound(d)
    if 11.0 <= t < 12.5:                                       # la tour de Cooper qui pousse... et tombe
        g = clamp01((t - 11.0) / 1.2)
        n = 1 + int(5 * g)
        fall = clamp01((t - 12.2) / 0.3)
        for k in range(n):
            wob = (k * k) * 1.6 * math.sin(t * 9) * g
            bxx, byy = 440 + wob, GY - 26 - k * 30
            tx, ty = 350 + (k - 2) * 12, GY - 140 - k * 4
            circ(d, lerp(bxx, tx, ease(fall)), lerp(byy, ty, ease(fall)), 22 - k, SAND if k % 2 else SANDL)
    if t >= 19.3:
        ub = back((t - 19.3) / 0.4)
        um = back((t - 19.3) / 0.4)
        ul = back((t - 19.6) / 0.4)
        ur = back((t - 19.9) / 0.4)
        flag = back((t - 24.3) / 0.5)
        castle(d, t, ub, um, ul, ur, flag)
    if 15.8 <= t < 19.3:                                       # le seau
        fillv = clamp01((t - 16.3) / 2.4)
        if t < 16.1:
            g = (t - 15.8) / 0.3
            yc = lerp(GY - 165, GY - 34, g * g)
            bucket(d, CX, yc, 0, 0)
        elif t < 18.8:
            hop = 12 * max(0, math.sin(math.pi * (t - 16.1) / 0.25)) if t < 16.35 else 0
            bucket(d, CX, GY - 34 - hop, 0, fillv)
        else:
            g = clamp01((t - 18.8) / 0.5)
            bucket(d, CX, GY - 34 - 90 * math.sin(math.pi * g), g, 1.0)

    # ---------------- Pebble
    pmood, tears = "sad", False
    ptalk = talking("pebble", t)
    if t < 6.0 or 8.0 <= t < 11.2:
        tears = True
    if 6.0 <= t < 8.0:
        pmood = "smile"
    if 11.2 <= t < 12.3:
        pmood = "smile"
    elif 12.3 <= t < 14.6:
        pmood = "oops"
    elif 14.6 <= t < 16.3:
        pmood = "smile"
    elif t >= 16.3:
        pmood = "happy"
    if ptalk > 0.02 and pmood == "sad":
        tears = True
    tip, lift = None, 0.0
    if 16.3 <= t < 18.8:                                       # tap, tap : elle tasse le sable
        g = t - 16.3
        tp = max(0, math.sin(2 * math.pi * g / 0.8 + math.pi))
        tip = (CX + 24, GY - 72 - 26 * tp)
    elif t >= 19.3:
        lift = bounce(t, 6.5, 14) if (19.3 < t < 20.4 or 21.2 < t < 25.4 or t > 25.6) else 0
        if 21.2 < t < 25.4 or t > 25.6:
            tip = (PX - 78, GY - 90 - 26 * math.sin(t * 13))
    ptop = seal(d, PX, GY, t, pmood, ptalk, tip, lift, tears)

    # ---------------- Cooper
    mx = path(t, [(0, 340), (5.6, 340), (6.6, 350), (19.4, 350), (20.2, 316)])
    walking = 5.6 < t < 6.6 or 19.4 < t < 20.2
    mmood, lc, rc, pinch, sand, hop = "smile", None, None, 0.0, 0.0, 0.0
    by = GY - 62
    dance = t < 3.4 or 21.2 < t < 25.4 or t > 25.6
    if dance:
        mx += 14 * math.sin(t * 5)
        hop = bounce(t, 5, 10)
        sw = math.sin(t * 10)
        lc, rc = (mx - 72, by - 100 - 18 * sw), (mx + 72, by - 100 + 18 * sw)
        pinch = abs(math.sin(t * 12))
        mmood = "happy"
    elif t < 5.6:
        mmood = "smile"
    if 7.2 < t < 11.0:
        mmood = "sad"
    if 11.0 <= t < 12.3:                                       # il empile le sable, vite vite
        mmood = "happy"
        lc = (mx + 60, by - 20 + 16 * math.sin(t * 14))
        rc = (mx + 78, by - 50 - 16 * math.sin(t * 14))
        pinch = abs(math.sin(t * 14))
    elif 12.3 <= t < 14.9:                                     # boum ! du sable sur la tête
        sand = clamp01((t - 12.4) / 0.2)
        if t > 14.5:
            sand = 1 - clamp01((t - 14.5) / 0.4)
            mx += 6 * math.sin(t * 40)
        mmood = "oops" if t < 12.9 else ("dizzy" if t < 14.0 else "smile")
        lc, rc = (mx - 96, by - 22), (mx + 96, by - 22)
    elif 16.3 <= t < 18.8:                                     # pelle, pelle : il remplit le seau
        g = (t - 16.3) % 0.8 / 0.8
        up = math.sin(math.pi * g)
        rc = (lerp(mx + 74, CX - 32, ease(g)), GY - 24 - 70 * up)
        lc = (mx + 50, GY - 20 - 30 * up)
        pinch = 0.2 if g < 0.5 else 1.0
        mmood = "happy"
    elif 18.8 <= t < 19.4:
        mmood = "oops"
        lc, rc = (mx - 80, by - 110), (mx + 80, by - 110)
    elif t >= 19.4 and not dance:
        mmood = "happy"
        lc, rc = (mx - 86, by - 110), (mx + 86, by - 110)
    if walking:
        hop = bounce(t, 9, 6)
    mtop = crab(d, mx, GY - hop, t, mmood, talking("cooper", t),
                (lc[0], lc[1] - hop) if lc else None, (rc[0], rc[1] - hop) if rc else None,
                pinch, sand, t if walking or dance else 0)
    if 16.3 <= t < 18.8:                                       # le sable vole dans le seau
        g = (t - 16.3) % 0.8 / 0.8
        if 0.3 < g < 0.9:
            u = (g - 0.3) / 0.6
            for k in range(3):
                circ(d, lerp(mx + 80, CX - 4 + k * 8, u), GY - 70 - 60 * math.sin(math.pi * u) + k * 6 - 40 * u,
                     8 - k, SAND)
    if 12.9 < t < 14.4:                                        # étoiles qui tournent
        for i in range(4):
            a = t * 5 + i * math.pi / 2
            star(d, mx + 60 * math.cos(a), mtop[1] + 4 + 14 * math.sin(a), 10, t * 3, (255, 220, 60))
    if 14.5 < t < 15.2:                                        # il secoue le sable
        g = (t - 14.5) / 0.7
        for i in range(8):
            a = i * math.pi / 4 + 0.3
            circ(d, mx + (50 + 70 * g) * math.cos(a), GY - 120 + (50 + 70 * g) * math.sin(a) * 0.6 + 60 * g * g,
                 6 * (1 - g) + 2, SAND)

    # ---------------- Gus la mouette
    if t >= 14.2:
        perch = (ptop[0] + 6, ptop[1] + 6 - 32)               # sur la tête de Pebble
        top_r = (CX + 20, GY - 4 - 50 - 170 - 12 - 32)         # en haut de la grande tour
        flap, stand, gmood = 1.0, False, "smile"
        if t < 15.8:
            g = (t - 14.2) / 1.6
            gx, gy2 = lerp(780, CX + 20, ease(g)), lerp(300, GY - 205, ease(g)) - 40 * math.sin(math.pi * g)
        elif t < 16.5:
            g = ease((t - 15.8) / 0.7)
            gx, gy2 = lerp(CX + 20, perch[0], g), lerp(GY - 205, perch[1], g) - 30 * math.sin(math.pi * g)
        elif t < 23.4:
            gx, gy2 = perch
            flap, stand = 0.0, True
            if 19.3 < t < 20.4:
                gmood = "happy"
                gy2 -= bounce(t, 7, 10)
        elif t < 24.3:
            g = ease((t - 23.4) / 0.9)
            gx, gy2 = lerp(perch[0], top_r[0], g), lerp(perch[1], top_r[1], g) - 50 * math.sin(math.pi * g)
        else:
            gx, gy2 = top_r
            flap, stand, gmood = 0.0, True, "happy"
            if t > 25.6:
                gy2 -= bounce(t, 7, 10)
                flap = 0.6
        if t < 16.5 and t < 15.8:                               # il porte le seau
            bucket(d, gx + 6, gy2 + 50, 0, 0)
        if 23.4 <= t < 24.3:                                    # il porte le drapeau
            d.line([P(gx - 40), P(gy2 - 30), P(gx - 40), P(gy2 + 20)], fill=(120, 90, 60), width=P(4))
            d.polygon([(P(gx - 38), P(gy2 - 30)), (P(gx - 2), P(gy2 - 20)), (P(gx - 38), P(gy2 - 10))],
                      fill=(255, 90, 150))
        gtop = gull(d, gx, gy2, t, flap, talking("gus", t), gmood, stand)
        ANCHORS["gus"] = (gtop[0], gtop[1])

    # ---------------- effets
    if 15.0 < t < 16.4:                                        # Gus a une idée
        splash_stars(d, CX, GY - 120, (t - 15.0) / 1.4, 6, 30)
    if 19.3 < t < 20.8:
        splash_stars(d, CX, GY - 110, (t - 19.3) / 1.5, 10, 70)
    if 24.3 < t < 25.8:
        splash_stars(d, CX, GY - 230, (t - 24.3) / 1.5, 8, 30, (255, 140, 200))
    if t > 21.0:                                               # confettis et bulles de savon
        cols = [(255, 90, 150), (255, 210, 60), (80, 200, 230), (255, 255, 255), (150, 230, 120)]
        for i in range(30):
            r = random.Random(i * 5 + 2)
            t0 = 21.0 + r.uniform(0, 5.5)
            if t < t0:
                continue
            fx = r.uniform(240, 700) + 18 * math.sin((t - t0) * 3 + i)
            fy = 250 + (t - t0) * r.uniform(80, 120)
            if fy < GY + 30:
                if i % 3 == 0:
                    starfish(d, fx, fy, 11, (t - t0) * 2, cols[i % 5])
                else:
                    d.rectangle([P(fx - 6), P(fy - 4), P(fx + 6), P(fy + 4)], fill=cols[i % 5])

    ANCHORS["cooper"] = (mx, mtop[1])
    ANCHORS["pebble"] = ptop
    return img, mx, GY, ptop


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
