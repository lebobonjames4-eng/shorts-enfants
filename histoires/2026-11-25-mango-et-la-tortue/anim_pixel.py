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
TX = 520                                   # Tiki, la tortue (centre)


def path(t, keys):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= t < t1:
            return lerp(a, b, ease((t - t0) / (t1 - t0)))
    return keys[-1][1]


def cam(t):
    """Centre x de la caméra verticale : elle suit l'action."""
    return path(t, [(0, 460), (14.4, 460), (15.4, 515)])


def star(d, x, y, r, rot, col):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = rot + i * math.pi / 5 - math.pi / 2
        pts.append((P(x + rr * math.cos(a)), P(y + rr * math.sin(a))))
    d.polygon(pts, fill=col)


def hibiscus(d, x, y, r, col, rot=0.0):
    for k in range(5):
        a = rot + k * 2 * math.pi / 5
        circ(d, x + r * 0.75 * math.cos(a), y + r * 0.75 * math.sin(a), r * 0.62, col)
    circ(d, x, y, r * 0.35, (255, 225, 90))


def butterfly(d, x, y, t, col):
    f = abs(math.sin(t * 14))
    for sx in (-1, 1):
        d.polygon([(P(x), P(y)), (P(x + sx * 26 * f), P(y - 22)), (P(x + sx * 22 * f), P(y + 4))], fill=col)
        d.polygon([(P(x), P(y)), (P(x + sx * 16 * f), P(y + 18)), (P(x + sx * 6), P(y + 6))], fill=col)
    d.line([P(x), P(y - 10), P(x), P(y + 12)], fill=(70, 50, 60), width=P(4))


# ---------------------------------------------------------------- background
def make_back():
    img = Image.new("RGB", (int(W * S), int(H * S)))
    d = ImageDraw.Draw(img)
    top, bot = (120, 205, 235), (220, 245, 215)
    h = int(H * S)
    for y in range(h):
        u = int(y / h * 7) / 6
        d.line([(0, y), (int(W * S), y)], fill=lerpc(top, bot, u))
    rng = random.Random(7)
    # jungle lointaine
    for i in range(16):
        x = i * 90 + rng.uniform(-20, 20)
        ell(d, x, 520 + rng.uniform(-30, 20), 95, 110, (95, 170, 120))
    for i in range(14):
        x = i * 100 + 40 + rng.uniform(-20, 20)
        ell(d, x, 575 + rng.uniform(-15, 15), 80, 70, (70, 150, 95))
    # palmiers
    for px, ph in [(130, 330), (790, 300), (1150, 340)]:
        for k in range(14):
            u = k / 13
            circ(d, px + 30 * math.sin(u * 2.2), 600 - u * ph, 15, (150, 105, 65) if k % 2 else (130, 90, 55))
        cx, cy = px + 30 * math.sin(2.2), 600 - ph
        for a in [-2.8, -2.2, -1.5, -0.9, -0.3]:
            pts = []
            for j in range(10):
                v = j / 9
                pts.append((cx + math.cos(a) * 130 * v, cy + math.sin(a) * 130 * v + 70 * v * v))
            for j, (xx, yy) in enumerate(pts):
                circ(d, xx, yy, 22 * (1 - 0.6 * j / 9), (60, 160, 80))
        for dx in (-12, 12):
            circ(d, cx + dx, cy + 12, 11, (120, 80, 45))
    # sol : herbe + clairière de sable
    d.rectangle([0, P(600), int(W * S), int(H * S)], fill=(110, 190, 80))
    ell(d, 640, 600, 700, 28, (110, 190, 80))
    ell(d, 540, 668, 420, 52, (235, 210, 150))
    ell(d, 540, 668, 380, 40, (242, 222, 168))
    for _ in range(45):
        x, y = rng.uniform(10, 1270), rng.uniform(600, 715)
        if ((x - 540) / 430) ** 2 + ((y - 668) / 60) ** 2 < 1:
            continue
        for dx in (-6, 0, 6):
            d.line([P(x), P(y), P(x + dx), P(y - 16)], fill=(80, 160, 70), width=P(4))
    for x, y, c in [(150, 640, (240, 70, 90)), (240, 700, (255, 130, 170)), (860, 630, (255, 150, 60)),
                    (980, 700, (240, 70, 90)), (1040, 640, (255, 130, 170)), (60, 690, (255, 150, 60)),
                    (780, 712, (240, 70, 90))]:
        hibiscus(d, x, y, 16, c)
    # buissons de grandes feuilles
    for bx, by in [(180, 610), (880, 615), (1200, 605)]:
        for a in [-2.6, -2.0, -1.4, -0.9, -0.4]:
            leaf_shape(d, bx, by, a, 95, 26, (70, 165, 75))
    return img


def leaf_shape(d, x, y, ang, L, w, col):
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx
    a, b = [], []
    for i in range(11):
        u = i / 10
        hw = w * math.sin(math.pi * u)
        px, py = x + dx * u * L, y + dy * u * L
        a.append((P(px + nx * hw), P(py + ny * hw)))
        b.append((P(px - nx * hw), P(py - ny * hw)))
    d.polygon(a + b[::-1], fill=col)


BACK = make_back()


def vines(d, t):
    for vx, vl, ph in [(250, 420, 0.0), (430, 330, 1.3), (700, 400, 2.1), (980, 360, 0.7)]:
        sw = 6 * math.sin(t * 1.3 + ph)
        prev = None
        for k in range(16):
            u = k / 15
            x = vx + sw * u * u + 8 * math.sin(u * 6 + ph)
            y = 230 + u * (vl - 230) if vl > 230 else 230
            y = u * vl
            if prev:
                d.line([P(prev[0]), P(prev[1]), P(x), P(y)], fill=(70, 140, 60), width=P(7))
            if k % 3 == 2:
                leaf_shape(d, x, y, 0.4 if k % 2 else math.pi - 0.4, 34, 11, (90, 175, 80))
            prev = (x, y)


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
            d.line([P(ex - sx * r * 1.1), P(y - r * 1.6), P(ex + sx * r * 0.9), P(y - r * 2.2)],
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


def banana(d, x, y, ang, bite=0.0):
    """Banane tenue en (x, y), pointe dans la direction ang."""
    n = int(8 * (1 - bite)) + 2
    for k in range(n):
        u = k / 9
        a = ang + 0.9 * (u - 0.5)
        px, py = x + math.cos(ang) * 60 * u, y + math.sin(ang) * 60 * u - 14 * math.sin(math.pi * u)
        circ(d, px, py, 10 * (0.6 + 0.4 * math.sin(math.pi * min(1, u + 0.15))), (255, 215, 60))
    circ(d, x - math.cos(ang) * 6, y - math.sin(ang) * 6, 5, (120, 90, 40))


def monkey(d, x, gy, t, mood="smile", talk=0.0, sit=0.0, lh=None, rh=None, ban=None):
    """Mango le petit singe (vue de face). lh/rh = position des mains (monde). Renvoie le haut de la tête."""
    br, dk, fc = (160, 100, 55), (120, 72, 38), (245, 210, 160)
    drop = 38 * sit
    # queue en spirale (derrière)
    prev = None
    for k in range(18):
        u = k / 17
        if u < 0.6:
            px, py = x + 40 + 80 * u, gy - 60 - 20 * u - 120 * u * u + drop
        else:
            a = (u - 0.6) / 0.4 * 5.0
            cx, cy = x + 88, gy - 115 + drop
            rr = 26 * (1 - (u - 0.6) / 0.4 * 0.6)
            px, py = cx + rr * math.cos(-0.3 - a), cy + rr * math.sin(-0.3 - a)
        px += 4 * math.sin(t * 3)
        if prev:
            d.line([P(prev[0]), P(prev[1]), P(px), P(py)], fill=dk, width=P(11))
        prev = (px, py)
    if sit < 0.5:
        for sx in (-1, 1):
            d.rounded_rectangle([P(x + sx * 22 - 12), P(gy - 48), P(x + sx * 22 + 12), P(gy - 4)],
                                radius=P(6), fill=br)
            ell(d, x + sx * 28, gy - 6, 18, 9, fc)
    else:
        for sx in (-1, 1):
            ell(d, x + sx * 34, gy - 14, 26, 14, br)
            ell(d, x + sx * 56, gy - 14, 13, 11, fc)
    by = gy - 78 + drop
    ell(d, x, by, 46, 48, br)
    ell(d, x, by + 6, 30, 34, fc)
    hy = gy - 162 + drop
    sh = by - 26
    hands = {-1: lh or (x - 56, by + 26), 1: rh or (x + 56, by + 26)}
    for sx in (-1, 1):
        hx, hy2 = hands[sx]
        d.line([P(x + sx * 36), P(sh), P(hx), P(hy2)], fill=br, width=P(16))
        circ(d, hx, hy2, 11, fc)
    for sx in (-1, 1):
        circ(d, x + sx * 52, hy, 21, br)
        circ(d, x + sx * 52, hy, 12, (240, 170, 150))
    circ(d, x, hy, 50, br)
    for k in (-1, 0, 1):
        d.polygon([(P(x + k * 14 - 9), P(hy - 44)), (P(x + k * 14 + 9), P(hy - 44)),
                   (P(x + k * 18), P(hy - 64))], fill=br)
    circ(d, x - 18, hy - 8, 22, fc)
    circ(d, x + 18, hy - 8, 22, fc)
    ell(d, x, hy + 20, 36, 24, fc)
    circ(d, x - 34, hy + 14, 7, (250, 150, 140))
    circ(d, x + 34, hy + 14, 7, (250, 150, 140))
    eyes(d, x, hy - 8, 18, 9, mood, t)
    circ(d, x - 6, hy + 10, 3, dk)
    circ(d, x + 6, hy + 10, 3, dk)
    mouth(d, x, hy + 26, mood, talk, 13)
    if ban is not None:
        hx, hy2 = hands[1]
        banana(d, hx, hy2, ban[0], ban[1])
        circ(d, hx, hy2, 11, fc)
    return x, hy - 64


TG, TGD, TY = (90, 185, 90), (60, 145, 70), (250, 225, 130)
SKIN = (150, 210, 110)


def _turtle_upside(d, ox, oy, t, mood, talk, wig):
    """Tortue sur le dos (origine = centre de la carapace)."""
    # pattes qui gigotent en l'air
    for i, lx in enumerate((-56, -22, 22, 56)):
        a = 0.35 * math.sin(t * 9 * wig + i * 1.7) * wig + (0.25 if lx > 0 else -0.25)
        ex, ey = ox + lx + 30 * math.sin(a), oy - 8 - 34 * math.cos(a)
        d.line([P(ox + lx), P(oy - 4), P(ex), P(ey)], fill=SKIN, width=P(16))
        circ(d, ex, ey, 10, SKIN)
    # queue
    d.polygon([(P(ox - 78), P(oy - 6)), (P(ox - 98), P(oy - 16)), (P(ox - 80), P(oy + 6))], fill=SKIN)
    # carapace (dôme vers le bas)
    d.pieslice([P(ox - 84), P(oy - 58), P(ox + 84), P(oy + 58)], 0, 180, fill=TGD)
    d.pieslice([P(ox - 76), P(oy - 50), P(ox + 76), P(oy + 50)], 0, 180, fill=TG)
    for px, py in [(-40, 18), (0, 30), (40, 18), (-20, 6), (20, 6)]:
        ell(d, ox + px, oy + py, 14, 10, TGD)
    # ventre (plastron) en haut
    d.rounded_rectangle([P(ox - 84), P(oy - 12), P(ox + 84), P(oy + 6)], radius=P(8), fill=TY)
    for px in (-40, 0, 40):
        d.line([P(ox + px), P(oy - 10), P(ox + px), P(oy + 4)], fill=(220, 190, 100), width=P(3))
    # cou + tête à droite, visage à l'endroit
    hx, hy = ox + 108, oy - 22
    d.line([P(ox + 70), P(oy - 2), P(hx - 8), P(hy + 6)], fill=SKIN, width=P(22))
    circ(d, hx, hy, 28, SKIN)
    eyes(d, hx + 2, hy - 6, 11, 7, mood, t, 1.1)
    mouth(d, hx + 2, hy + 12, mood, talk, 9)
    circ(d, hx - 18, hy + 8, 5, (250, 160, 150))
    circ(d, hx + 22, hy + 8, 5, (250, 160, 150))


def _turtle_up(d, ox, oy, t, mood, talk, step):
    """Tortue debout (origine = bord de la carapace), tête à gauche."""
    for i, lx in enumerate((-50, -18, 18, 50)):
        lift = 6 * max(0, math.sin(step + i * math.pi)) if step else 0
        d.rounded_rectangle([P(ox + lx - 12), P(oy - 2 - lift), P(ox + lx + 12), P(oy + 28 - lift)],
                            radius=P(6), fill=SKIN)
    d.polygon([(P(ox + 78), P(oy - 6)), (P(ox + 98), P(oy + 6)), (P(ox + 80), P(oy + 8))], fill=SKIN)
    hx, hy = ox - 106, oy - 26
    d.line([P(ox - 70), P(oy - 4), P(hx + 8), P(hy + 6)], fill=SKIN, width=P(22))
    d.pieslice([P(ox - 84), P(oy - 70), P(ox + 84), P(oy + 70)], 180, 360, fill=TGD)
    d.pieslice([P(ox - 76), P(oy - 62), P(ox + 76), P(oy + 62)], 180, 360, fill=TG)
    for px, py in [(-40, -22), (0, -40), (40, -22), (-18, -10), (20, -10)]:
        ell(d, ox + px, oy + py, 15, 11, TGD)
    d.rounded_rectangle([P(ox - 88), P(oy - 8), P(ox + 88), P(oy + 8)], radius=P(8), fill=TY)
    circ(d, hx, hy, 28, SKIN)
    eyes(d, hx - 2, hy - 6, 11, 7, mood, t, 1.1)
    mouth(d, hx - 2, hy + 12, mood, talk, 9)
    circ(d, hx - 22, hy + 8, 5, (250, 160, 150))
    circ(d, hx + 18, hy + 8, 5, (250, 160, 150))


def turtle(img, t, wx, wy, angle, pivot, upright, mood, talk, wig=1.0, step=0.0):
    """Dessine Tiki dans un calque (pour pouvoir le faire tourner). (wx, wy) = origine monde."""
    L = 440
    layer = Image.new("RGBA", (P(L), P(L)), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    o = L / 2
    if upright:
        _turtle_up(ld, o, o, t, mood, talk, step)
    else:
        _turtle_upside(ld, o, o, t, mood, talk, wig)
    if abs(angle) > 0.5:
        layer = layer.rotate(angle, resample=Image.NEAREST, center=(P(o + pivot[0]), P(o + pivot[1])))
    img.paste(layer, (P(wx - o), P(wy - o)), layer)


def parrot(d, x, y, t, flap=0.0, talk=0.0, mood="smile", wing_out=0.0):
    """Kiwi le perroquet, de profil, tourné vers la gauche. (x, y) = centre du corps."""
    red, blue, yel = (235, 65, 70), (60, 120, 235), (255, 205, 50)
    for k, (dx, col) in enumerate([(4, blue), (16, yel), (26, blue)]):
        d.polygon([(P(x + dx - 6), P(y + 18)), (P(x + dx + 8), P(y + 16)), (P(x + dx + 16), P(y + 70)),
                   (P(x + dx + 4), P(y + 72))], fill=col)
    ell(d, x, y, 24, 32, red)
    ell(d, x - 6, y + 8, 14, 20, (250, 110, 100))
    for sx in (-8, 8):
        d.line([P(x + sx), P(y + 28), P(x + sx), P(y + 42)], fill=(90, 80, 80), width=P(4))
        d.line([P(x + sx - 6), P(y + 44), P(x + sx + 6), P(y + 44)], fill=(90, 80, 80), width=P(4))
    hx, hy = x - 6, y - 36
    circ(d, hx, hy, 22, red)
    circ(d, hx - 6, hy - 3, 10, (255, 255, 255))
    if mood == "happy":
        d.arc([P(hx - 12), P(hy - 9), P(hx - 1), P(hy + 3)], 200, 340, fill=INK, width=P(3))
    else:
        circ(d, hx - 8, hy - 3, 4.5, INK)
    op = 6 * talk
    d.polygon([(P(hx - 18), P(hy - 6)), (P(hx - 38), P(hy + 2)), (P(hx - 26), P(hy + 14 - op * 0.3)),
               (P(hx - 16), P(hy + 6 - op))], fill=(255, 225, 120))
    d.polygon([(P(hx - 18), P(hy + 8 + op * 0.3)), (P(hx - 28), P(hy + 16 + op)), (P(hx - 14), P(hy + 14 + op))],
              fill=(220, 180, 90))
    # aile
    a = -0.5 + flap * 1.6 * math.sin(t * 22) - wing_out * 1.3
    ax, ay = x + 6, y - 10
    pts = [(ax, ay)]
    for j in range(7):
        u = j / 6
        r = 48 * math.sin(math.pi * (0.15 + 0.7 * u)) + 4
        aa = a - 0.6 + 1.2 * u + math.pi / 2
        pts.append((ax + r * math.cos(aa) * (-1), ay + r * math.sin(aa)))
    d.polygon([(P(px), P(py)) for px, py in pts], fill=blue)
    tip = pts[3]
    circ(d, (ax + tip[0]) / 2, (ay + tip[1]) / 2, 8, yel)
    return hx, hy - 30


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
    for base, y, k, sp in [(300, 130, 0.8, 10), (900, 170, 0.7, 14)]:
        plain_cloud(d, (base + t * sp) % 1580 - 150, y, k)
    vines(d, t)
    for i, (bx, by, c) in enumerate([(300, 420, (255, 150, 60)), (720, 380, (170, 110, 240))]):
        butterfly(d, bx + 60 * math.sin(t * 0.7 + i * 2), by + 25 * math.sin(t * 1.3 + i), t + i,
                  c)

    # ---------------- Tiki
    tmood, ttalk = "sad", talking("tiki", t)
    if 6.0 < t < 10.2:
        tmood = "smile" if t < 8.0 else "sad"
    if 11.4 < t < 12.3:
        tmood = "smile"
    if 12.3 <= t < 14.6:
        tmood = "dizzy"
    if 14.6 <= t < 18.6:
        tmood = "smile"
    if 18.6 <= t:
        tmood = "happy"
    wig = 1.0 if t < 16.0 else 0.4
    if t < 12.3 or 13.6 <= t < 16.3:
        hop = 0.0
        if 13.4 <= t < 13.6:
            hop = 0
        turtle(img, t, TX, GY - 52, 0, (0, 52), False, tmood, ttalk, wig)
        thead = (TX + 110, GY - 150)
    elif t < 13.6:                                             # premier essai : Tiki tourne comme une toupie !
        g = (t - 12.3) / 1.3
        ang = -720 * ease(g)
        hop = 40 * math.sin(math.pi * g)
        turtle(img, t, TX, GY - 52 - hop, ang, (0, 0), False, "dizzy", ttalk, 1.5)
        thead = (TX + 110, GY - 150)
    elif t < 18.8:                                             # on balance : un, deux, trois !
        g = t - 16.3
        amp = 4 + 14 * clamp01(g / 2.4)
        ang = amp * math.sin(2 * math.pi * g / 0.8) * (1 if g < 2.4 else 0)
        if g >= 2.4:
            ang = 0
        turtle(img, t, TX, GY - 52, ang, (0, 52), False, tmood, ttalk, 0.6)
        thead = (TX + 110, GY - 150)
    elif t < 19.4:                                             # hop ! il se retourne
        g = (t - 18.8) / 0.6
        ang = 180 * ease(g)
        hop = 110 * math.sin(math.pi * g)
        if ang < 90:
            turtle(img, t, TX, GY - 52 - hop, ang, (0, 0), False, "happy", 0)
        else:
            turtle(img, t, TX, GY - 52 - hop, ang - 180, (0, 0), True, "happy", 0)
        thead = (TX, GY - 190)
    else:
        th = bounce(t, 6.5, 14) if 21.4 < t < 25.4 else 0
        turtle(img, t, TX, GY - 32 - th, 0, (0, 0), True, tmood, ttalk, step=t * 10 if th else 0)
        thead = (TX - 106, GY - 100 - th)
    d = ImageDraw.Draw(img)

    # ---------------- Mango
    mx = path(t, [(0, 300), (5.7, 300), (6.7, 360), (11.0, 360), (11.4, 398), (12.3, 410), (12.7, 340),
                  (14.9, 340), (15.6, 395), (18.8, 395), (19.5, 330)])
    walking = 5.7 < t < 6.7 or 11.0 < t < 11.4 or 14.9 < t < 15.6
    mmood, sit, hop, lh, rh, ban = "smile", 0.0, 0.0, None, None, None
    bx, by = mx, GY - 78
    eat = 0.0
    if t < 3.4:                                                # il mange sa banane en sautillant
        hop = bounce(t, 5.0, 16)
        eat = 0.5 + 0.5 * math.sin(t * 8)
        mmood = "happy"
    by -= hop
    rh_def = (mx + 58, by + 10)
    ban = (-1.2, 0.0)
    if t < 3.4:
        rh = (mx + 62, by - 40 - 26 * eat)
        lh = (mx - 58, by - 30 - 20 * eat)
        ban = (-1.75, 0.0)
    elif t < 5.7:
        rh = (mx + 56, by + 4)
        mmood = "smile"
    if 7.4 < t < 11.0:
        mmood = "sad"
    if 11.0 <= t < 12.3:                                       # il pousse fort
        mmood = "strain"
        lh, rh = (mx + 50, by - 6), (mx + 58, by + 14)
        ban = None
    elif 12.3 <= t < 14.9:                                     # boum ! sur les fesses, la tête qui tourne
        sit = ease((t - 12.3) / 0.3)
        mmood = "dizzy" if t < 14.0 else "oops"
        if t > 12.7:
            mmood = "dizzy" if t < 14.0 else "smile"
        lh, rh = (mx - 66, GY - 60), (mx + 66, GY - 60)
        ban = None
        if t < 12.4:
            mmood = "oops"
    elif 15.6 <= t < 16.3:
        mmood = "smile"
        ban = None
    elif 16.3 <= t < 18.8:                                     # un, deux, trois : on balance la carapace
        g = t - 16.3
        push = max(0, math.sin(2 * math.pi * g / 0.8))
        mmood = "strain" if push > 0.3 else "smile"
        lh, rh = (mx + 46 + 8 * push, by - 10), (mx + 54 + 8 * push, by + 10)
        ban = None
    elif 18.8 <= t < 19.4:
        mmood = "happy"
        ban = None
    elif t >= 19.4:
        mmood = "happy"
        hop = bounce(t, 6.5, 22) if 19.4 < t < 20.2 or 21.4 < t < 25.4 else 0
        by = GY - 78 - hop
        lh, rh = (mx - 62, by - 70), (mx + 62, by - 70)        # bras en l'air
        ban = None
        if t >= 25.3:                                          # il partage sa banane
            u = ease((t - 25.3) / 0.6)
            lh = (mx - 56, by + 10)
            rh = (lerp(mx + 56, mx + 78, u), lerp(by + 10, by - 2, u))
            ban = (-0.15, 0.0 if t < 27.0 else 0.45)
            mmood = "happy" if not talking("mango", t) else "smile"
        elif 21.4 < t < 25.4:
            sw = math.sin(t * 6.5)
            lh, rh = (mx - 62, by - 60 - 20 * sw), (mx + 62, by - 60 + 20 * sw)
    if walking:
        hop = bounce(t, 9, 8)
        by = GY - 78 - hop
    mtop = monkey(d, mx, GY - hop, t, mmood, talking("mango", t), sit, lh, rh, ban)
    if 12.6 < t < 14.6:                                        # étoiles qui tournent
        for i in range(4):
            a = t * 5 + i * math.pi / 2
            star(d, mx + 60 * math.cos(a), mtop[1] + 50 + 16 * math.sin(a), 11, t * 3,
                 (255, 220, 60))
        for i in range(3):
            a = -t * 6 + i * 2.1
            star(d, TX + 70 * math.cos(a), GY - 150 + 14 * math.sin(a), 9, t * 3, (255, 255, 255))

    # ---------------- Kiwi le perroquet
    ktop = None
    if t >= 14.4:
        kx = path(t, [(14.4, 820), (15.8, 690)])
        ky = path(t, [(14.4, 380), (15.8, GY - 50)]) - 30 * math.sin(math.pi * clamp01((t - 14.4) / 1.4))
        flap = 1.0 if t < 15.8 else 0.0
        kmood, wout = "smile", 0.0
        if 16.3 <= t < 18.8:
            g = t - 16.3
            push = max(0, -math.sin(2 * math.pi * g / 0.8))
            kx -= 10 * push
            wout = push
        if t >= 18.8:
            kmood = "happy"
            ky -= bounce(t, 7, 16) if 19.0 < t < 25.4 else 0
            flap = 1.0 if 19.0 < t < 20.4 or 21.4 < t < 25.4 else 0.0
        ktop = parrot(d, kx, ky, t, flap, talking("kiwi", t), kmood, wout)
        ANCHORS["kiwi"] = (kx - 6, ktop[1])

    # ---------------- effets
    if 15.0 < t < 16.4:                                        # Kiwi a une idée
        splash_stars(d, 690, GY - 150, (t - 15.0) / 1.4, 6, 30)
    if 18.9 < t < 20.4:
        splash_stars(d, TX, GY - 120, (t - 18.9) / 1.5, 10, 70)
    if t > 20.8:                                               # pluie de fleurs de la jungle
        cols = [(240, 70, 90), (255, 130, 170), (255, 150, 60), (255, 255, 255)]
        for i in range(26):
            r = random.Random(i * 3 + 1)
            t0 = 20.8 + r.uniform(0, 4.5)
            if t < t0:
                continue
            fx = r.uniform(250, 760) + 20 * math.sin((t - t0) * 2 + i)
            fy = 250 + (t - t0) * r.uniform(70, 110)
            if fy < GY + 20:
                hibiscus(d, fx, fy, 13, cols[i % 4], (t - t0) * 2)
    if 22.0 < t < 25.0:
        splash_stars(d, 500, 380, (t - 22.0) / 3.0, 10, 80, (255, 160, 200))

    ANCHORS["mango"] = (mx, mtop[1])
    ANCHORS["tiki"] = thead
    return img, mx, GY, thead


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
                        fill=(60, 130, 70))
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
