import math, random, sys
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageChops
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


def bez(p0, c, p1, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0],
            (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1])


def leaf(d, p, ang, L, w, col):
    pts_a, pts_b = [], []
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx
    for i in range(13):
        u = i / 12
        hw = w * math.sin(math.pi * u)
        x, y = p[0] + dx * u * L, p[1] + dy * u * L
        pts_a.append((P(x + nx * hw), P(y + ny * hw)))
        pts_b.append((P(x - nx * hw), P(y - ny * hw)))
    d.polygon(pts_a + pts_b[::-1], fill=col)


def star(d, x, y, r, rot, col):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = rot + i * math.pi / 5 - math.pi / 2
        pts.append((P(x + rr * math.cos(a)), P(y + rr * math.sin(a))))
    d.polygon(pts, fill=col)




# ---------------------------------------------------------------- décor : mare au soleil couchant
SKY_TOP, SKY_BOT = (255, 160, 150), (255, 222, 160)
GROUND = (112, 178, 82)
WATER, WATER_L, WATER_D = (72, 178, 200), (140, 220, 230), (52, 140, 175)
POND = (740, 650, 228, 60)          # cx, cy, rx, ry
ANCHORS = {}


def path(t, keys):
    if t <= keys[0][0]:
        return keys[0][1], keys[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(keys, keys[1:]):
        if t0 <= t < t1:
            u = ease((t - t0) / (t1 - t0))
            return lerp(x0, x1, u), lerp(y0, y1, u)
    return keys[-1][1], keys[-1][2]


def make_sky():
    img = Image.new("RGB", (int(W * S), int(H * S)))
    d = ImageDraw.Draw(img)
    h = int(H * S)
    for y in range(h):
        u = int(y / h * 7) / 6
        d.line([(0, y), (int(W * S), y)], fill=lerpc(SKY_TOP, SKY_BOT, u))
    return img


def bush(d, x, y, k, col, col2):
    for dx, dy, r in [(-34, 0, 30), (0, -18, 38), (34, 0, 30)]:
        circ(d, x + dx * k, y + dy * k, r * k, col)
    circ(d, x - 8 * k, y - 28 * k, 14 * k, col2)


def tree(d, x, y, k):
    d.rectangle([P(x - 10 * k), P(y - 90 * k), P(x + 10 * k), P(y)], fill=(140, 90, 60))
    for dx, dy, r in [(-38, -110, 44), (36, -112, 46), (0, -150, 52)]:
        circ(d, x + dx * k, y + dy * k, r * k, (88, 160, 84))
    circ(d, x - 14 * k, y - 165 * k, 18 * k, (130, 200, 100))
    for dx, dy in [(-30, -120), (22, -140), (40, -100)]:
        circ(d, x + dx * k, y + dy * k, 7 * k, (255, 120, 120))     # petites pommes


def cattail(d, x, y, h, lean):
    d.line([P(x), P(y), P(x + lean), P(y - h)], fill=(80, 140, 70), width=P(5))
    ell(d, x + lean * 0.85, y - h * 0.82, 8, 22, (150, 95, 60))
    leaf(d, (x, y), -math.pi / 2 - 0.35, h * 0.6, 7, (95, 165, 80))
    leaf(d, (x, y), -math.pi / 2 + 0.4, h * 0.5, 7, (95, 165, 80))


def make_hills():
    img = Image.new("RGBA", (int(W * S), int(H * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = random.Random(7)
    ell(d, 250, 640, 640, 230, (150, 200, 120))
    ell(d, 1060, 650, 600, 220, (140, 195, 115))
    tree(d, 300, 585, 1.0)
    tree(d, 1180, 590, 0.85)
    bush(d, 470, 590, 0.8, (95, 168, 88), (130, 200, 110))
    bush(d, 900, 588, 0.7, (95, 168, 88), (130, 200, 110))
    d.rectangle([0, P(598), int(W * S), int(H * S)], fill=GROUND)
    ell(d, 640, 604, 900, 30, GROUND)
    cx, cy, rx, ry = POND
    ell(d, cx, cy + 4, rx + 12, ry + 10, (150, 125, 90))       # berge
    ell(d, cx, cy, rx, ry, WATER)
    for _ in range(14):                                          # reflets
        x = rng.uniform(cx - rx * 0.7, cx + rx * 0.7)
        y = rng.uniform(cy - ry * 0.6, cy + ry * 0.7)
        w = rng.uniform(14, 34)
        d.line([P(x - w), P(y), P(x + w), P(y)], fill=WATER_L, width=P(3))
    # herbe et fleurs
    for _ in range(70):
        x, y = rng.uniform(0, 1280), rng.uniform(612, 718)
        if ((x - cx) / (rx + 20)) ** 2 + ((y - cy) / (ry + 16)) ** 2 < 1:
            continue
        d.line([P(x), P(y), P(x + rng.uniform(-4, 4)), P(y - 12)], fill=(80, 150, 70), width=P(3))
    for _ in range(16):
        x, y = rng.uniform(10, 1270), rng.uniform(625, 712)
        if ((x - cx) / (rx + 30)) ** 2 + ((y - cy) / (ry + 22)) ** 2 < 1:
            continue
        col = rng.choice([(255, 255, 255), (255, 200, 90), (190, 160, 255)])
        for a in range(5):
            circ(d, x + 6 * math.cos(a * 1.26), y + 6 * math.sin(a * 1.26), 4, col)
        circ(d, x, y, 3, (255, 210, 80))
    for x, h, lean in [(515, 120, -8), (532, 95, 4), (958, 135, 6), (975, 105, 12)]:
        cattail(d, x, 615, h, lean)
    return img


def make_base():
    img = make_sky()
    d = ImageDraw.Draw(img)
    for x, y, k in [(180, 150, 0.9), (620, 90, 0.7), (1000, 190, 0.8)]:
        pink_cloud(d, x, y, k)
    hills = make_hills()
    img.paste(hills, (0, 0), hills)
    return img


def pink_cloud(d, x, y, k):
    for dx, dy, r in [(-40, 5, 28), (0, -12, 36), (40, 5, 28)]:
        circ(d, x + dx * k, y + dy * k, r * k, (255, 236, 236))
    d.rounded_rectangle([P(x - 62 * k), P(y), P(x + 62 * k), P(y + 30 * k)],
                        radius=P(15 * k), fill=(255, 236, 236))


def make_pond_mask():
    m = Image.new("L", (int(W * S), int(H * S)), 0)
    cx, cy, rx, ry = POND
    ImageDraw.Draw(m).ellipse([P(cx - rx), P(cy - ry), P(cx + rx), P(cy + ry)], fill=255)
    return m


BASE = make_base()
POND_MASK = make_pond_mask()


def water_cover(img, x, y, rx, ry):
    """Remet l'eau de la mare par-dessus (personnage dans l'eau)."""
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse([P(x - rx), P(y - ry), P(x + rx), P(y + ry)], fill=255)
    m = ImageChops.multiply(m, POND_MASK)
    img.paste(BASE, (0, 0), m)


# ---------------------------------------------------------------- personnages
INK = (40, 40, 50)
FROG, FROG_D, BELLY = (118, 205, 78), (70, 150, 60), (235, 245, 160)


def frog(d, x, fy, t, mood, talk=0.0, sq=1.0, look=(0, 0), legs=0.0, arms=0.0):
    """Momo la petite grenouille (x, fy = pieds). Renvoie le haut de la tête."""
    def Y(v):
        return fy - v * sq
    # pattes arrière
    for sx in (-1, 1):
        if legs > 0.05:
            a = math.pi / 2 - sx * (0.9 - 0.5 * legs)
            L = 34 + 22 * legs
            leaf(d, (x + sx * 34, Y(22)), a, L, 13, FROG_D)
            ell(d, x + sx * 34 + math.cos(a) * L, Y(22) + math.sin(a) * L, 14, 6, FROG_D)
        else:
            ell(d, x + sx * 46, Y(20), 26, 18, FROG_D)
            ell(d, x + sx * 64, fy - 4, 20, 7, FROG_D)
    ell(d, x, Y(46), 60, 46 * sq, FROG)
    ell(d, x, Y(34), 40, 28 * sq, BELLY)
    # bras
    for i, sx in enumerate((-1, 1)):
        a = arms if i == 1 else arms * 0.7
        if a > 0.05:
            leaf(d, (x + sx * 44, Y(42)), -math.pi / 2 - sx * (1.2 - a * 0.9), 52, 10, FROG_D)
        else:
            ell(d, x + sx * 30, fy - 8, 14, 8, FROG_D)
    # yeux sur le dessus
    for sx in (-1, 1):
        circ(d, x + sx * 30, Y(90), 24, FROG)
    for sx in (-1, 1):
        ex, ey = x + sx * 30, Y(92)
        if mood in ("happy", "oops"):
            d.arc([P(ex - 12), P(ey - 8), P(ex + 12), P(ey + 10)], 200, 340, fill=INK, width=P(5))
            if mood == "oops":
                d.line([P(ex - 10), P(ey + 8), P(ex + 10), P(ey + 8)], fill=INK, width=P(3))
            continue
        blink = (t % 3.3) < 0.13
        if blink:
            d.line([P(ex - 13), P(ey), P(ex + 13), P(ey)], fill=INK, width=P(4))
            continue
        circ(d, ex, ey, 17, (255, 255, 255))
        circ(d, ex + look[0] * 6, ey + look[1] * 6, 9, INK)
        circ(d, ex + look[0] * 6 + 3, ey + look[1] * 6 - 4, 3.5, (255, 255, 255))
        if mood == "worried":
            d.line([P(x + sx * 14), P(Y(118)), P(x + sx * 40), P(Y(112))], fill=INK, width=P(4))
    circ(d, x - 44, Y(58), 9, (255, 150, 150))
    circ(d, x + 44, Y(58), 9, (255, 150, 150))
    my = Y(60)
    if talk > 0.02:
        ell(d, x, my + 4, 18, 3 + 10 * talk, (150, 50, 60))
        ell(d, x, my + 6 + 6 * talk, 9, 3 * talk + 1, (255, 130, 140))
    elif mood == "worried":
        d.arc([P(x - 14), P(my + 2), P(x + 14), P(my + 14)], 200, 340, fill=INK, width=P(4))
    elif mood in ("happy", "oops"):
        d.pieslice([P(x - 22), P(my - 6), P(x + 22), P(my + 16)], 0, 180, fill=(150, 50, 60))
    else:
        d.arc([P(x - 26), P(my - 14), P(x + 26), P(my + 8)], 25, 155, fill=INK, width=P(4))
    return (x, Y(116))


SHELL, SHELL_D, SNAIL = (245, 125, 175), (205, 80, 140), (255, 215, 140)


def snail(d, x, fy, t, mood, talk=0.0, face=1, sq=1.0):
    """Shelly le petit escargot (x, fy = bas du pied). Renvoie le point au-dessus des yeux."""
    f = face
    ell(d, x + 4 * f, fy - 10, 52, 12, SNAIL)
    ell(d, x + 38 * f, fy - 30 * sq, 18, 24 * sq, SNAIL)
    droop = 14 if mood == "sad" else 0
    tips = []
    for k in (-1, 1):
        bx, by = x + (36 + k * 6) * f, fy - 50 * sq
        tx, ty = x + (36 + k * 16 + droop * 0.8) * f, fy - 84 * sq + droop
        d.line([P(bx), P(by), P(tx), P(ty)], fill=SNAIL, width=P(5))
        tips.append((tx, ty))
    # coquille
    sx, sy = x - 10 * f, fy - 44 * sq
    circ(d, sx, sy, 36, SHELL_D)
    circ(d, sx, sy, 32, SHELL)
    for r, a0 in [(22, 0), (13, 90), (6, 180)]:
        d.arc([P(sx - r), P(sy - r), P(sx + r), P(sy + r)], a0, a0 + 270, fill=SHELL_D, width=P(4))
    circ(d, sx - 14, sy - 16, 5, (255, 200, 225))
    # yeux au bout des antennes
    for tx, ty in tips:
        circ(d, tx, ty, 9, SNAIL)
        if mood in ("happy", "oops"):
            d.arc([P(tx - 6), P(ty - 4), P(tx + 6), P(ty + 6)], 200, 340, fill=INK, width=P(3))
        else:
            blink = ((t + 1.3) % 3.0) < 0.13
            if blink:
                d.line([P(tx - 6), P(ty), P(tx + 6), P(ty)], fill=INK, width=P(3))
            else:
                circ(d, tx + 2 * f, ty, 5, INK)
                circ(d, tx + 3 * f, ty - 2, 1.8, (255, 255, 255))
    hx, hy = x + 42 * f, fy - 26 * sq
    circ(d, hx + 6 * f, hy - 2, 4, (255, 150, 140))
    if mood == "sad":
        ell(d, hx + 12 * f, hy - 10, 2.5, 4, (110, 170, 255))
    if talk > 0.02:
        ell(d, hx - 2 * f, hy + 6, 4, 1.5 + 4 * talk, (150, 50, 60))
    elif mood == "sad":
        d.arc([P(hx - 8), P(hy + 4), P(hx + 4), P(hy + 12)], 200, 340, fill=INK, width=P(3))
    elif mood in ("happy", "oops"):
        d.pieslice([P(hx - 8), P(hy), P(hx + 6), P(hy + 10)], 0, 180, fill=(150, 50, 60))
    else:
        d.arc([P(hx - 8), P(hy - 4), P(hx + 6), P(hy + 8)], 20, 160, fill=INK, width=P(3))
    return (x + 30 * f, min(tips[0][1], tips[1][1]) - 14)


def dragonfly(d, x, y, t, face=1):
    fl = math.sin(t * 40)
    for k, (dx, ln) in enumerate([(-4, 36), (6, 30)]):
        for sy in (-1, 1):
            a = sy * (0.5 + 0.35 * fl) - math.pi / 2
            ell(d, x + dx * face + math.cos(a) * ln * 0.5, y + math.sin(a) * ln * 0.5 * 0.6 - 4,
                ln * 0.5, 7, (225, 245, 255))
    for i in range(5):
        circ(d, x - (12 + i * 8) * face, y + i * 1, 5 - i * 0.4, (70, 120, 230))
    circ(d, x, y, 8, (80, 140, 240))
    circ(d, x + 7 * face, y - 2, 6, (60, 200, 170))
    circ(d, x + 9 * face, y - 4, 2, INK)


def lily(d, x, y, rx, ry, col=(80, 170, 80)):
    ell(d, x, y + 3, rx, ry, (50, 125, 70))
    d.pieslice([P(x - rx), P(y - ry), P(x + rx), P(y + ry)], 290, 250 + 360, fill=col)
    ell(d, x - rx * 0.3, y - ry * 0.3, rx * 0.3, ry * 0.3, (120, 200, 105))


def lotus(d, x, y, g):
    if g <= 0:
        return
    for a in (-0.9, -0.45, 0, 0.45, 0.9):
        leaf(d, (x, y), -math.pi / 2 + a, 30 * g, 9 * g, (255, 160, 200))
    circ(d, x, y - 6 * g, 5 * g, (255, 230, 100))


def big_flower(d, t, x=1035, y=612):
    d.line([P(x), P(y), P(x - 6), P(y - 120), P(x), P(y - 230)], fill=(70, 150, 70), width=P(8))
    leaf(d, (x - 3, y - 70), -0.5, 70, 18, (95, 175, 80))
    leaf(d, (x - 3, y - 110), math.pi + 0.5, 60, 16, (95, 175, 80))
    cx, cy = x, y - 240
    g = back((t - 24.0) / 0.6) if t >= 24.0 else 0.0
    if g <= 0:                                       # bouton fermé
        sway = 3 * math.sin(t * 2)
        d.polygon([(P(cx - 22 + sway), P(cy + 18)), (P(cx + 22 + sway), P(cy + 18)), (P(cx + sway), P(cy - 40))],
                  fill=(255, 120, 170))
        ell(d, cx + sway, cy + 12, 22, 16, (255, 120, 170))
        leaf(d, (cx, cy + 26), -math.pi / 2 - 0.5, 30, 8, (95, 175, 80))
        leaf(d, (cx, cy + 26), -math.pi / 2 + 0.5, 30, 8, (95, 175, 80))
        return
    rot = (t - 24) * 0.4
    for i in range(8):
        a = rot + i * math.pi / 4
        col = (255, 120, 170) if i % 2 else (255, 170, 205)
        ell(d, cx + math.cos(a) * 44 * g, cy + math.sin(a) * 44 * g, 28 * g, 28 * g, col)
    circ(d, cx, cy, 32 * g, (255, 215, 70))
    for sx in (-1, 1):
        d.arc([P(cx + sx * 10 - 6), P(cy - 10), P(cx + sx * 10 + 6), P(cy + 2)], 200, 340, fill=INK, width=P(3))
    d.pieslice([P(cx - 10), P(cy + 2), P(cx + 10), P(cy + 16)], 0, 180, fill=(150, 50, 60))
    for i in range(6):
        k = (t - 24.0) * 1.2 + i / 6
        a = i * 1.05 + t
        rr = 72 + 14 * math.sin(t * 2 + i)
        star(d, cx + rr * math.cos(a), cy + rr * math.sin(a), 6 + 4 * math.sin(t * 6 + i), t * 3,
             (255, 250, 170))


def sun(d, t, cx=1130, cy=120):
    for i in range(10):
        a = t * 0.5 + i * math.pi / 5
        d.line([P(cx + 70 * math.cos(a)), P(cy + 70 * math.sin(a)),
                P(cx + 92 * math.cos(a)), P(cy + 92 * math.sin(a))], fill=(255, 200, 90), width=P(8))
    circ(d, cx, cy, 58, (255, 190, 70))
    circ(d, cx, cy, 50, (255, 215, 90))
    for sx in (-1, 1):
        d.arc([P(cx + sx * 18 - 8), P(cy - 12), P(cx + sx * 18 + 8), P(cy + 2)], 200, 340, fill=(150, 90, 50),
              width=P(4))
    d.arc([P(cx - 15), P(cy), P(cx + 15), P(cy + 22)], 20, 160, fill=(150, 90, 50), width=P(4))
    circ(d, cx - 32, cy + 12, 7, (255, 150, 120))
    circ(d, cx + 32, cy + 12, 7, (255, 150, 120))


def splash(d, x, y, g, n=7, size=1.0):
    if not 0 <= g < 1:
        return
    for i in range(n):
        a = math.pi + (i + 0.5) * math.pi / n
        r = (30 + 70 * g) * size
        px, py = x + math.cos(a) * r, y + math.sin(a) * r * 0.9 + 140 * g * g * size
        circ(d, px, py, 9 * (1 - g) * size + 2, WATER_L)
    ell(d, x, y + 4, (40 + 50 * g) * size, (8 + 8 * g) * size, (180, 235, 240))


def ripple(d, x, y, t):
    k = (t * 1.5) % 1
    ell(d, x, y, 60 + 30 * k, 10 + 5 * k, (150, 225, 235))
    ell(d, x, y, 56 + 30 * k, 8 + 5 * k, WATER)


def hop(t, t0, t1, a, b, h):
    u = clamp01((t - t0) / (t1 - t0))
    return lerp(a[0], b[0], u), lerp(a[1], b[1], u) - h * math.sin(math.pi * u)


# ---------------------------------------------------------------- frame
P1 = (740, 634)          # nénuphar de Momo
SH0 = (450, 612)         # Shelly au départ
BANK = (550, 612)        # Momo sur la berge
SWIM = 670               # pieds de Momo quand il nage
B0, B1 = 668, 905        # le bateau-feuille avance de B0 à B1
BY = 664
SH_END = (965, 612)


def scene(t, with_sun=True):
    img = BASE.copy()
    d = ImageDraw.Draw(img)
    if with_sun:
        sun(d, t)

    # ---------------- Momo
    mx, mfy = P1
    sq, legs, arms, mood, look = 1.0, 0.0, 0.0, "smile", (0, 0)
    in_water = False
    if t < 3.3:                                   # accroche : il saute tout de suite
        u = (t * 1.25) % 1
        mfy = P1[1] - 60 * math.sin(math.pi * u)
        legs = math.sin(math.pi * u) ** 0.5
        arms = 0.9 * math.sin(math.pi * u)
        mood = "happy"
        if u < 0.08 or u > 0.92:
            sq = 0.88
    elif t < 9.0:
        mood = "smile"
        if 3.5 < t < 6.6:
            look = (0.6, -1)
            if 4.2 < t < 5.6:
                arms = 0.6 + 0.3 * math.sin(t * 10)
        elif t >= 6.6:
            look = (-1, 0)
            mood = "worried" if t > 7.6 else "smile"
    elif t < 9.6:
        mx, mfy = hop(t, 9.0, 9.6, P1, (B0, BY - 4), 70)
        legs, look = math.sin(math.pi * (t - 9.0) / 0.6), (-1, 0)
    elif t < 10.2:
        mx, mfy = hop(t, 9.6, 10.2, (B0, BY - 4), BANK, 70)
        legs, look = math.sin(math.pi * (t - 9.6) / 0.6), (-1, 0)
    elif t < 14.0:
        mx, mfy = BANK
        look = (-1, -0.2)
        if 10.4 < t < 11.6:
            arms = 0.8
        if 12.6 < t < 13.4:
            look = (0, -1)
        if 13.3 < t < 14.0:
            sq = 1 - 0.13 * ease((t - 13.3) / 0.4)
            look = (1, 0)
    elif t < 14.9:
        mx, mfy = hop(t, 14.0, 14.9, BANK, P1, 170)
        legs, arms = math.sin(math.pi * (t - 14.0) / 0.9), 0.9
        mood = "happy"
    elif t < 15.4:
        u = ease((t - 14.9) / 0.5)
        mx, mfy = P1[0], lerp(P1[1], SWIM, u)
        mood, in_water = "oops", True
        sq = 1 - 0.1 * math.sin(math.pi * u)
    elif t < 16.6:
        mx, mfy = P1[0] + 3 * math.sin(t * 12), SWIM + 3 * math.sin(t * 4)
        mood, in_water = ("oops" if t < 16.2 else "smile"), True
    elif t < 17.7:
        mx, mfy = path(t, [(16.6, P1[0], SWIM), (17.7, 590, SWIM)])
        mfy += 3 * math.sin(t * 9)
        in_water, look = True, (-1, 0)
    elif t < 18.1:
        mx, mfy = hop(t, 17.7, 18.1, (590, SWIM), BANK, 50)
        legs = math.sin(math.pi * (t - 17.7) / 0.4)
    elif t < 19.4:
        mx, mfy = BANK
        look = (-1, 0) if t < 19.0 else (1, 0.3)
    elif t < 20.2:
        mx, mfy = hop(t, 19.4, 20.2, BANK, (B0 - 88, SWIM), 60)
        legs = math.sin(math.pi * (t - 19.4) / 0.8)
        in_water = t > 19.95
    elif t < 23.3:
        bx, _ = path(t, [(20.3, B0, 0), (23.2, B1, 0)])
        mx, mfy = bx - 88, SWIM + 3 * math.sin(t * 10)
        in_water, look, mood = True, (1, 0), ("happy" if t > 20.9 else "smile")
    elif t < 23.9:
        mx, mfy = hop(t, 23.3, 23.9, (B1 - 88, SWIM), P1, 90)
        legs = math.sin(math.pi * (t - 23.3) / 0.6)
        in_water = t < 23.4
        look = (1, -0.5)
    else:                                         # danse de la fin sur son nénuphar
        u = (t * 1.6) % 1
        mx, mfy = P1[0], P1[1] - 34 * math.sin(math.pi * u)
        legs = math.sin(math.pi * u) * 0.8
        arms = 0.7 + 0.3 * math.sin(t * 8)
        mood = "happy"
        if 24.0 < t < 25.6:
            mood, look = "smile", (1, -1)

    # ---------------- bateau-feuille
    bx, _ = path(t, [(20.3, B0, 0), (23.2, B1, 0)])
    if 9.25 < t < 9.75:                              # Momo rebondit dessus
        by = BY + 6 * math.sin(math.pi * (t - 9.25) / 0.5)
    else:
        by = BY + 2 * math.sin(t * 2.5)

    # ---------------- Shelly
    sx, sfy, smood, sface, ssq = SH0[0], SH0[1], "smile", 1, 1.0
    head_y = mfy - 108 * sq
    if t < 7.2:
        smood = "smile" if t > 1.0 else "happy"
    elif t < 10.5:
        smood = "sad"
    elif t < 12.6:
        smood = "happy" if t < 12.0 else "smile"
    elif t < 13.1:
        sx, sfy = hop(t, 12.6, 13.1, SH0, (BANK[0], BANK[1] - 108), 90)
        smood = "happy"
    elif t < 18.0:
        sx, sfy = mx - 4, head_y + 2
        smood = "oops" if 14.9 < t < 16.4 else "happy"
    elif t < 18.4:
        sx, sfy = hop(t, 18.0, 18.4, (BANK[0], BANK[1] - 106), (SH0[0] + 10, SH0[1]), 50)
    elif t < 19.4:
        sx, sfy = SH0[0] + 10, SH0[1]
        smood = "happy"
        if 18.5 < t < 19.1:
            sfy -= 24 * math.sin(math.pi * (t - 18.5) / 0.6)
    elif t < 20.2:
        sx, sfy = hop(t, 19.4, 20.2, (SH0[0] + 10, SH0[1]), (B0 + 6, BY - 4), 90)
        smood = "happy"
    elif t < 23.2:
        sx, sfy = bx + 6, by - 4
        smood = "happy" if (t % 1.4) < 0.7 else "smile"
    elif t < 23.7:
        sx, sfy = hop(t, 23.2, 23.7, (B1 + 6, BY - 4), SH_END, 70)
        smood = "happy"
    else:
        sx, sfy = SH_END
        smood = "happy" if t > 24.2 else "smile"
        if t > 26.0:
            sfy -= abs(math.sin(t * 4)) * 12

    # ---------------- dessin (arrière vers avant)
    big_flower(d, t)
    for x, y, rx, ry, k in [(860, 616, 36, 9, 0), (880, 684, 42, 11, 1), (640, 696, 38, 10, 2)]:
        lily(d, x, y, rx, ry)
        lotus(d, x + 6, y - 4, back((t - 24.4 - k * 0.25) / 0.4) if t > 24.4 else 0)
    # nénuphar de Momo (il coule quand Momo atterrit avec Shelly)
    if not (14.9 <= t < 16.8):
        lily(d, P1[0], P1[1] + 2, 50, 12)
        if t > 25.2:
            lotus(d, P1[0] - 46, P1[1] - 2, back((t - 25.2) / 0.4))
    elif t < 15.2:
        lily(d, P1[0], P1[1] + 2 + 60 * (t - 14.9), 50, 12)

    shelly_on_frog = 13.1 <= t < 18.0
    if in_water and shelly_on_frog:
        pass
    if not shelly_on_frog and not (20.2 <= t < 23.2) and not (19.4 <= t < 20.2):
        sh_top = snail(d, sx, sfy, t, smood, talking("shelly", t), sface, ssq)
    mtop = frog(d, mx, mfy, t, mood, talking("momo", t), sq, look, legs, arms)
    if in_water:
        water_cover(img, mx, mfy - 6, 92, 30)
        d = ImageDraw.Draw(img)
        ripple(d, mx, mfy - 4, t)
    if shelly_on_frog:
        sh_top = snail(d, sx, sfy, t, smood, talking("shelly", t), sface, ssq)
    # bateau-feuille (devant Momo qui pousse)
    lily(d, bx, by, 74, 17, (95, 185, 85))
    if 19.4 <= t < 23.2:
        sh_top = snail(d, sx, sfy, t, smood, talking("shelly", t), sface, ssq)

    # éclaboussures
    splash(d, P1[0], P1[1] + 4, (t - 14.9) / 0.8, 9, 1.1)
    if 20.3 < t < 23.2:                                # Momo bat des pattes
        for k in range(3):
            g = ((t - 20.3) * 2.2 + k / 3) % 1
            splash(d, mx - 60 - 30 * g, SWIM - 8, g, 3, 0.45)
    if 19.95 < t < 20.6:
        splash(d, B0 - 88, SWIM - 6, (t - 19.95) / 0.65, 5, 0.6)
    if 23.3 < t < 23.9:
        splash(d, B1 - 88, SWIM - 6, (t - 23.3) / 0.6, 5, 0.6)

    # étoiles d'étourdissement / idée
    if 15.2 <= t < 16.6:
        for i in range(3):
            a = t * 5 + i * 2.09
            star(d, sh_top[0] - 30 + 60 * math.cos(a), sh_top[1] + 16 + 14 * math.sin(a), 8, t * 4,
                 (255, 240, 120))
    if 18.5 < t < 19.6:
        g = (t - 18.5) / 1.1
        for i in range(5):
            a = -math.pi / 2 + (i - 2) * 0.5
            rr = 40 + 40 * g
            star(d, sh_top[0] + rr * math.cos(a), sh_top[1] + 10 + rr * math.sin(a), 10 * math.sin(math.pi * g),
                 t * 3 + i, (255, 230, 70))
    # cœurs de la fin
    if t > 24.3:
        for i in range(5):
            k = ((t - 24.3) * 0.45 + i / 5) % 1
            hx = 820 + i * 60 + 18 * math.sin(t * 2 + i)
            hy = 560 - k * 260
            r = 9 * math.sin(math.pi * k)
            circ(d, hx - r * 0.55, hy, r * 0.62, (255, 110, 150))
            circ(d, hx + r * 0.55, hy, r * 0.62, (255, 110, 150))
            d.polygon([(P(hx - r * 1.15), P(hy + r * 0.15)), (P(hx + r * 1.15), P(hy + r * 0.15)),
                       (P(hx), P(hy + r * 1.3))], fill=(255, 110, 150))

    # libellule
    if t < 3.4:
        dx, dy, df = 1000 + 10 * math.sin(t * 3), 470 + 8 * math.sin(t * 5), -1
    elif t < 6.6:
        u = (t - 3.4) / 3.2
        dx = lerp(1000, 980, u) - 260 * math.sin(math.pi * u)
        dy = 470 - 100 * math.sin(math.pi * u) + 12 * math.sin(t * 6)
        df = -1 if u < 0.5 else 1
    elif t < 24.0:
        dx, dy, df = 980 + 6 * math.sin(t * 2), 470 + 6 * math.sin(t * 3), -1
    else:
        a = (t - 24.0) * 2.4
        dx, dy = 1030 + 72 * math.cos(a), 372 + 95 * math.sin(a)
        df = -1 if math.sin(a) > 0 else 1
    dragonfly(d, dx, dy, t, df)

    ANCHORS["momo"] = (mtop[0], mtop[1] - 8 - (legs * 6))
    if shelly_on_frog:
        ANCHORS["momo"] = (mtop[0], sh_top[1] - 6)
    ANCHORS["shelly"] = (sh_top[0], sh_top[1])
    return img, mx, mfy, ANCHORS["shelly"]


def plain_cloud(d, x, y, k):
    for dx, dy, r in [(-40, 5, 28), (0, -12, 36), (40, 5, 28)]:
        circ(d, x + dx * k, y + dy * k, r * k, (250, 252, 255))
    d.rounded_rectangle([P(x - 62 * k), P(y), P(x + 62 * k), P(y + 32 * k)],
                        radius=P(16 * k), fill=(250, 252, 255))



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
        if t0 - 0.1 <= t <= t1 + 0.9:
            u = min(back((t - t0 + 0.1) / 0.3), ease((t1 + 0.9 - t) / 0.2))
            ax, ay = ANCHORS[who]
            bubble(d, text, ax + (40 if side == "right" else -40), ay + 30, side, u)

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
