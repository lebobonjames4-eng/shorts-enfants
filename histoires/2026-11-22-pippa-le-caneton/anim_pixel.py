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




# ---------------------------------------------------------------- décor : jardin sous la pluie
SKY_TOP, SKY_BOT = (120, 138, 170), (175, 192, 212)        # ciel de pluie
SUN_TOP, SUN_BOT = (110, 185, 255), (195, 232, 255)        # ciel bleu de la fin
GROUND = (104, 170, 92)
WATER, WATER_L = (120, 170, 220), (200, 230, 250)
PUDDLE = (600, 652, 122, 22)        # cx, cy, rx, ry
MUSH = (985, 612)                   # pied du champignon
CAP_Y, CAP_RX, CAP_RY = 440, 132, 78
DAISY = (800, 540)                  # cœur de la marguerite de Dot
ANCHORS = {}


def path(t, keys):
    if t <= keys[0][0]:
        return keys[0][1], keys[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(keys, keys[1:]):
        if t0 <= t < t1:
            u = ease((t - t0) / (t1 - t0))
            return lerp(x0, x1, u), lerp(y0, y1, u)
    return keys[-1][1], keys[-1][2]


def sunny(t):
    return ease((t - 23.3) / 0.9)


def make_sky(top, bot):
    img = Image.new("RGB", (int(W * S), int(H * S)))
    d = ImageDraw.Draw(img)
    h = int(H * S)
    for y in range(h):
        u = int(y / h * 7) / 6
        d.line([(0, y), (int(W * S), y)], fill=lerpc(top, bot, u))
    return img


def bush(d, x, y, k, col, col2):
    for dx, dy, r in [(-34, 0, 30), (0, -18, 38), (34, 0, 30)]:
        circ(d, x + dx * k, y + dy * k, r * k, col)
    circ(d, x - 8 * k, y - 28 * k, 14 * k, col2)


def tulip(d, x, y, h, col):
    d.line([P(x), P(y), P(x), P(y - h)], fill=(80, 150, 70), width=P(5))
    leaf(d, (x, y - 4), -math.pi / 2 - 0.5, h * 0.5, 7, (95, 170, 80))
    ell(d, x, y - h, 13, 15, col)
    d.polygon([(P(x - 13), P(y - h - 4)), (P(x - 13), P(y - h - 22)), (P(x - 4), P(y - h - 10)),
               (P(x), P(y - h - 24)), (P(x + 4), P(y - h - 10)), (P(x + 13), P(y - h - 22)),
               (P(x + 13), P(y - h - 4))], fill=col)


def fence(d, y):
    col, col2 = (225, 205, 175), (190, 165, 135)
    d.rectangle([0, P(y - 70), int(W * S), P(y - 62)], fill=col2)
    d.rectangle([0, P(y - 34), int(W * S), P(y - 26)], fill=col2)
    for x in range(10, 1290, 56):
        d.rectangle([P(x), P(y - 92), P(x + 30), P(y)], fill=col)
        d.polygon([(P(x), P(y - 92)), (P(x + 15), P(y - 106)), (P(x + 30), P(y - 92))], fill=col)


def mushroom(d):
    x, y = MUSH
    d.rounded_rectangle([P(x - 36), P(CAP_Y - 10), P(x + 36), P(y + 2)], radius=P(16), fill=(245, 232, 205))
    d.rectangle([P(x + 18), P(CAP_Y + 10), P(x + 30), P(y - 6)], fill=(225, 210, 180))
    # petit visage souriant sur le pied
    for sx in (-1, 1):
        circ(d, x + sx * 13, 540, 4, INK)
    d.arc([P(x - 10), P(546), P(x + 10), P(560)], 20, 160, fill=INK, width=P(3))
    circ(d, x - 24, 556, 5, (255, 170, 170))
    circ(d, x + 24, 556, 5, (255, 170, 170))
    # chapeau
    ell(d, x, CAP_Y + 4, CAP_RX, 18, (130, 80, 170))
    d.pieslice([P(x - CAP_RX), P(CAP_Y - CAP_RY), P(x + CAP_RX), P(CAP_Y + CAP_RY)], 180, 360,
               fill=(175, 110, 215))
    ell(d, x, CAP_Y, CAP_RX, 10, (175, 110, 215))
    for dx, dy, r in [(-70, -26, 16), (-14, -56, 13), (44, -34, 17), (92, -12, 10), (-104, -6, 9)]:
        circ(d, x + dx, CAP_Y + dy, r, (255, 245, 250))


def daisy(d):
    x, y = DAISY
    d.line([P(x), P(612), P(x + 6), P(580), P(x), P(y)], fill=(80, 150, 70), width=P(6))
    leaf(d, (x + 3, 596), -0.4, 40, 10, (95, 170, 80))
    for i in range(10):
        a = i * math.pi / 5
        ell(d, x + math.cos(a) * 26, y + math.sin(a) * 11, 15, 7, (255, 255, 255))
    ell(d, x, y, 18, 8, (255, 205, 60))


def make_hills():
    img = Image.new("RGBA", (int(W * S), int(H * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = random.Random(11)
    ell(d, 200, 630, 620, 220, (130, 185, 120))
    ell(d, 1100, 640, 600, 210, (120, 178, 112))
    fence(d, 604)
    bush(d, 430, 596, 0.75, (90, 160, 88), (125, 195, 110))
    bush(d, 1180, 594, 0.8, (90, 160, 88), (125, 195, 110))
    d.rectangle([0, P(598), int(W * S), int(H * S)], fill=GROUND)
    ell(d, 640, 604, 900, 26, GROUND)
    for x, h, col in [(460, 60, (255, 120, 150)), (488, 48, (255, 190, 70)), (1130, 62, (255, 120, 150)),
                      (1156, 46, (150, 130, 255)), (1100, 52, (255, 190, 70))]:
        tulip(d, x, 618, h, col)
    cx, cy, rx, ry = PUDDLE
    ell(d, cx, cy + 3, rx + 8, ry + 6, (90, 140, 80))
    ell(d, cx, cy, rx, ry, WATER)
    for _ in range(80):
        x, y = rng.uniform(0, 1280), rng.uniform(612, 718)
        if ((x - cx) / (rx + 20)) ** 2 + ((y - cy) / (ry + 16)) ** 2 < 1:
            continue
        d.line([P(x), P(y), P(x + rng.uniform(-4, 4)), P(y - 12)], fill=(78, 145, 72), width=P(3))
    for _ in range(14):
        x, y = rng.uniform(10, 1270), rng.uniform(632, 712)
        if ((x - cx) / (rx + 30)) ** 2 + ((y - cy) / (ry + 22)) ** 2 < 1:
            continue
        col = rng.choice([(255, 255, 255), (255, 200, 90), (255, 160, 200)])
        for a in range(5):
            circ(d, x + 6 * math.cos(a * 1.26), y + 6 * math.sin(a * 1.26), 4, col)
        circ(d, x, y, 3, (255, 210, 80))
    daisy(d)
    mushroom(d)
    return img


HILLS = None


def make_base(top, bot):
    img = make_sky(top, bot)
    img.paste(HILLS, (0, 0), HILLS)
    return img


def make_puddle_mask():
    m = Image.new("L", (int(W * S), int(H * S)), 0)
    cx, cy, rx, ry = PUDDLE
    ImageDraw.Draw(m).ellipse([P(cx - rx), P(cy - ry), P(cx + rx), P(cy + ry)], fill=255)
    return m


INK = (40, 40, 50)
HILLS = make_hills()
BASE_R = make_base(SKY_TOP, SKY_BOT)
BASE_S = make_base(SUN_TOP, SUN_BOT)
PUDDLE_MASK = make_puddle_mask()


def get_base(t):
    s = sunny(t)
    if s <= 0:
        return BASE_R
    if s >= 1:
        return BASE_S
    return Image.blend(BASE_R, BASE_S, s)


def water_cover(img, base, x, y, rx, ry):
    """Remet l'eau de la flaque par-dessus les pattes."""
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse([P(x - rx), P(y - ry), P(x + rx), P(y + ry)], fill=255)
    m = ImageChops.multiply(m, PUDDLE_MASK)
    img.paste(base, (0, 0), m)


def cloud(d, x, y, k, col):
    for dx, dy, r in [(-44, 5, 30), (0, -14, 40), (44, 5, 30)]:
        circ(d, x + dx * k, y + dy * k, r * k, col)
    d.rounded_rectangle([P(x - 68 * k), P(y), P(x + 68 * k), P(y + 32 * k)],
                        radius=P(16 * k), fill=col)


def cloud_col(t):
    return lerpc((205, 212, 228), (252, 253, 255), sunny(t))


def rain(d, t, x0, x1, y0, y1, n, seed, skip=None):
    a = 1 - ease((t - 23.2) / 0.7)
    if a <= 0:
        return
    rng = random.Random(seed)
    for i in range(n):
        if rng.random() > a:
            rng.random(); rng.random(); rng.random()
            continue
        bx = rng.uniform(x0, x1)
        sp = rng.uniform(700, 900)
        ph = rng.uniform(0, 1)
        ln = rng.uniform(16, 26)
        y = y0 + ((t * sp / (y1 - y0) + ph) % 1) * (y1 - y0)
        x = bx - (y - y0) * 0.12
        if skip and skip(x, y):
            continue
        d.line([P(x), P(y), P(x - 3), P(y + ln)], fill=(215, 230, 250), width=P(4))


def under_cap(x, y):
    return abs(x - MUSH[0]) < CAP_RX + 4 and y > CAP_Y - 30 - (CAP_RX - abs(x - MUSH[0])) * 0.4


def puddle_rings(d, t):
    if t > 23.8:
        return
    cx, cy, rx, ry = PUDDLE
    for i in range(5):
        k = (t * 1.3 + i * 0.37) % 1
        j = int(t * 1.3 + i * 0.37)
        rr = random.Random(i * 31 + j)
        x = cx + rr.uniform(-0.65, 0.65) * rx
        y = cy + rr.uniform(-0.4, 0.5) * ry
        ell(d, x, y, 6 + 18 * k, 2 + 5 * k, (185, 215, 245))
        ell(d, x, y, 4 + 18 * k, 1 + 4 * k, WATER)


# ---------------------------------------------------------------- personnages
DUCK, DUCK_D, BEAK = (255, 214, 64), (240, 175, 40), (255, 140, 40)
HAT, HAT_D = (70, 135, 225), (45, 100, 190)


def duck(d, x, fy, t, mood, talk=0.0, sq=1.0, f=1, wings=0.0, flap=0.0, step=0.0):
    """Pippa la petite cane (x, fy = pieds). Renvoie le haut du chapeau."""
    def Y(v):
        return fy - v * sq
    # pattes
    for k in (-1, 1):
        lift = max(0, math.sin(step + (0 if k < 0 else math.pi))) * 8
        ell(d, x + k * 18 + 6 * f, fy - 4 - lift, 15, 6, BEAK)
    # queue
    d.polygon([(P(x - 40 * f), P(Y(44))), (P(x - 66 * f), P(Y(70))), (P(x - 34 * f), P(Y(64)))], fill=DUCK_D)
    # ailes levées (derrière)
    for k in (-1, 1):
        a = wings if k == f else wings * 0.8
        if a > 0.05:
            ang = -math.pi / 2 - k * (1.25 - a * 0.85 + 0.35 * flap * math.sin(t * 30))
            leaf(d, (x + k * 34, Y(44)), ang, 50, 15, DUCK_D)
    ell(d, x, Y(40), 48, 38 * sq, DUCK)
    ell(d, x + 8 * f, Y(30), 30, 20 * sq, (255, 236, 140))
    if wings <= 0.05:
        leaf(d, (x - 16 * f, Y(48)), math.pi / 2 + 0.95 * f if f > 0 else math.pi / 2 - 0.95, 40, 13, DUCK_D)
    # tête
    hx, hy = x + 12 * f, Y(92)
    circ(d, hx, hy, 34, DUCK)
    # bec
    bx = hx + 34 * f
    if talk > 0.02 or mood in ("happy", "oops"):
        o = 4 + 8 * talk if talk > 0.02 else 6
        ell(d, bx, hy + 2 - o * 0.5, 17, 6, BEAK)
        ell(d, bx - 2 * f, hy + 6 + o * 0.5, 14, 5, (230, 110, 30))
        ell(d, bx - 6 * f, hy + 3, 8, o * 0.5, (150, 50, 60))
    else:
        ell(d, bx, hy + 4, 18, 8, BEAK)
        d.line([P(bx - 14 * f), P(hy + 4), P(bx + 12 * f), P(hy + 4)], fill=(220, 110, 30), width=P(2))
    # yeux
    for ex in (hx - 4 * f, hx + 18 * f):
        ey = hy - 6
        if mood in ("happy", "oops"):
            d.arc([P(ex - 7), P(ey - 5), P(ex + 7), P(ey + 7)], 200, 340, fill=INK, width=P(4))
            continue
        if (t % 3.1) < 0.13:
            d.line([P(ex - 7), P(ey), P(ex + 7), P(ey)], fill=INK, width=P(3))
            continue
        circ(d, ex, ey, 7, INK)
        circ(d, ex + 2, ey - 3, 2.5, (255, 255, 255))
        if mood == "worried":
            d.line([P(ex - 8), P(ey - 16), P(ex + 6), P(ey - 12 - (4 if ex > hx else -4) * f)], fill=INK, width=P(3))
    circ(d, hx - 18 * f, hy + 10, 7, (255, 160, 140))
    circ(d, hx + 26 * f, hy + 12, 5, (255, 160, 140))
    # chapeau de pluie
    ell(d, hx - 2 * f, hy - 24, 42, 9, HAT_D)
    d.pieslice([P(hx - 26), P(hy - 58), P(hx + 26), P(hy - 6)], 180, 360, fill=HAT)
    ell(d, hx - 2 * f, hy - 27, 40, 7, HAT)
    circ(d, hx - 8, hy - 44, 4, (150, 195, 255))
    return (hx, hy - 60)


LADY, LADY_D = (232, 58, 58), (190, 35, 40)


def ladybug(d, x, fy, t, mood="smile", talk=0.0, f=1, k=1.0, fly=0.0, wet=False, col=LADY):
    """Dot la coccinelle (x, fy = bas). Renvoie le point au-dessus de la tête."""
    cy = fy - 24 * k
    if fly > 0.05:                                     # petites ailes transparentes
        fl = math.sin(t * 45)
        for sy in (-1, 1):
            a = -math.pi / 2 - f * 0.5 + sy * (0.4 + 0.3 * fl) * fly
            ell(d, x - 4 * f * k + math.cos(a) * 20 * k, cy + math.sin(a) * 22 * k, 13 * k, 9 * k,
                (235, 245, 255))
    # pattes
    for i in (-1, 0, 1):
        d.line([P(x + i * 12 * k), P(cy + 14 * k), P(x + i * 16 * k), P(fy)], fill=INK, width=P(3))
    # carapace (s'ouvre un peu quand elle vole)
    op = 0.55 * fly
    circ(d, x, cy, 26 * k, INK)
    d.pieslice([P(x - 26 * k), P(cy - 26 * k), P(x + 26 * k), P(cy + 26 * k)],
               270 + math.degrees(op), 450 + math.degrees(op) * 0.2, fill=col)
    d.pieslice([P(x - 26 * k), P(cy - 26 * k), P(x + 26 * k), P(cy + 26 * k)],
               90 - math.degrees(op) * 0.2, 270 - math.degrees(op), fill=col)
    d.line([P(x), P(cy - 26 * k), P(x), P(cy + 26 * k)], fill=INK, width=P(2))
    for dx, dy, r in [(-12, -8, 5), (12, -8, 5), (-10, 10, 4.5), (10, 10, 4.5), (0, 18, 3)]:
        if not (fly > 0.05 and dy < 0):
            circ(d, x + dx * k, cy + dy * k, r * k, INK)
    circ(d, x - 8 * k, cy - 16 * k, 4 * k, (255, 170, 170))
    # tête
    hx, hy = x + 22 * f * k, cy - 4 * k
    circ(d, hx, hy, 16 * k, INK)
    for sx in (-1, 1):
        d.line([P(hx + sx * 5 * k), P(hy - 14 * k), P(hx + sx * 12 * k + 4 * f * k), P(hy - 28 * k)],
               fill=INK, width=P(2.5))
        circ(d, hx + sx * 12 * k + 4 * f * k, hy - 28 * k, 3.5 * k, INK)
    for ex in (hx - 3 * k + 2 * f * k, hx + 7 * f * k + 3 * k):
        ex = hx + (ex - hx)
    for ex in (hx - 4 * k, hx + 6 * k):
        ex += 2 * f * k
        ey = hy - 3 * k
        circ(d, ex, ey, 5.5 * k, (255, 255, 255))
        if mood in ("happy", "oops"):
            d.arc([P(ex - 4 * k), P(ey - 3 * k), P(ex + 4 * k), P(ey + 4 * k)], 200, 340, fill=INK, width=P(2))
        else:
            circ(d, ex + f * 1.5 * k, ey + (1.5 if mood == "sad" else 0) * k, 3 * k, INK)
    my = hy + 7 * k
    if talk > 0.02:
        ell(d, hx + 2 * f * k, my, 4 * k, (1.5 + 3 * talk) * k, (255, 120, 140))
    elif mood == "sad":
        d.arc([P(hx - 4 * k), P(my), P(hx + 6 * k), P(my + 6 * k)], 200, 340, fill=(255, 255, 255), width=P(2))
    else:
        d.arc([P(hx - 4 * k), P(my - 5 * k), P(hx + 7 * k), P(my + 3 * k)], 20, 160, fill=(255, 255, 255), width=P(2))
    if wet:
        for i in range(2):
            g = (t * 1.6 + i * 0.5) % 1
            ell(d, x + (-14 + 28 * i) * k, cy + 22 * k + g * 26 * k, 3 * k, 4 * k, (150, 200, 255))
    return (x + 6 * f * k, hy - 34 * k)


def splash(d, x, y, g, n=7, size=1.0):
    if not 0 <= g < 1:
        return
    for i in range(n):
        a = math.pi + (i + 0.5) * math.pi / n
        r = (30 + 70 * g) * size
        px, py = x + math.cos(a) * r, y + math.sin(a) * r * 0.9 + 140 * g * g * size
        circ(d, px, py, 9 * (1 - g) * size + 2, WATER_L)
    ell(d, x, y + 4, (40 + 50 * g) * size, (8 + 8 * g) * size, (215, 235, 252))


def heart(d, hx, hy, r, col=(255, 110, 150)):
    circ(d, hx - r * 0.55, hy, r * 0.62, col)
    circ(d, hx + r * 0.55, hy, r * 0.62, col)
    d.polygon([(P(hx - r * 1.15), P(hy + r * 0.15)), (P(hx + r * 1.15), P(hy + r * 0.15)),
               (P(hx), P(hy + r * 1.3))], fill=col)


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


def hop(t, t0, t1, a, b, h):
    u = clamp01((t - t0) / (t1 - t0))
    return lerp(a[0], b[0], u), lerp(a[1], b[1], u) - h * math.sin(math.pi * u)


def pink_cloud(d, x, y, k):          # gardé pour compatibilité
    cloud(d, x, y, k, (250, 252, 255))


# ---------------------------------------------------------------- frame
PX0 = 600                 # Pippa dans la flaque
PFY = 652                 # pieds dans la flaque
GFY = 612                 # pieds sur l'herbe
PLANT = 700
JUMPS = [(-0.3, 0.4), (0.45, 1.15), (1.2, 1.9), (1.95, 2.65), (3.9, 4.6), (4.8, 5.5),
         (25.2, 25.85), (25.9, 26.55), (26.6, 27.25), (27.3, 27.95), (28.0, 28.65), (28.7, 29.35)]
SPOT_P, SPOT_D = 905, 1052          # sous le champignon
DOT0 = (DAISY[0] - 2, DAISY[1] + 2)


def plant(d, t):
    x, y = PLANT, 614
    d.line([P(x), P(y), P(x - 4), P(y - 40)], fill=(70, 140, 70), width=P(6))
    leaf(d, (x - 2, y - 20), math.pi + 0.6, 70, 22, (70, 160, 85))
    leaf(d, (x - 2, y - 26), -0.5, 64, 20, (80, 170, 90))
    if t < 12.3:                                 # la grande feuille que Pippa va prendre
        leaf(d, (x - 4, y - 36), -math.pi / 2 - 0.15, 110, 30, (90, 185, 95))
        d.line([P(x - 4), P(y - 36), P(x - 20), P(y - 136)], fill=(60, 140, 70), width=P(3))


def cam(t):
    """Centre de la caméra verticale (unités monde) : elle suit l'action."""
    return path(t, [(0, 690, 0), (12.0, 690, 0), (13.0, 740, 0), (17.9, 740, 0), (19.6, 965, 0),
                    (24.3, 965, 0), (25.3, 690, 0)])[0]


def scene(t, with_sun=True):
    base = get_base(t)
    img = base.copy()
    d = ImageDraw.Draw(img)
    s = sunny(t)
    if with_sun and s > 0:
        sun(d, t, 1130, lerp(260, 120, back((t - 23.4) / 0.9)))
    cc = cloud_col(t)
    for bx, y, k, sp in [(180, 150, 1.0, 8), (620, 90, 0.8, 11), (1000, 200, 0.9, 6), (1350, 120, 0.8, 9)]:
        cloud(d, (bx + t * sp) % 1500 - 110, y + 60 - 40 * s, k, cc)

    # ---------------- Pippa
    px, pfy = PX0, PFY
    sq, wings, flap, mood, f, step = 1.0, 0.0, 0.0, "smile", 1, 0.0
    in_puddle = False
    for j0, j1 in JUMPS:
        if j0 <= t < j1:
            u = (t - j0) / (j1 - j0)
            pfy = PFY - 70 * math.sin(math.pi * u)
            wings = 0.8 * math.sin(math.pi * u)
            mood = "happy"
            break
    else:
        if t < 3.9 or 25.2 <= t:
            mood = "happy"
            for j0, j1 in JUMPS:
                if 0 <= t - j1 < 0.12:
                    sq = 0.88
    if t < 9.0 or t >= 25.2:
        in_puddle = True
        if 5.5 <= t < 9.0:
            mood = "smile" if t < 7.7 else "worried"
            if 4.0 < t < 5.6:
                mood = "happy"
    elif t < 10.0:                                  # elle sort de la flaque
        px, pfy = path(t, [(9.0, PX0, PFY), (10.0, 730, GFY)])
        pfy -= abs(math.sin(t * 10)) * 6
        step = t * 10
        in_puddle = t < 9.4
        mood = "worried"
    elif t < 12.0:
        px, pfy = 730, GFY
        mood = "smile"
        if 11.3 < t:
            f = -1                                  # elle regarde la feuille
    elif t < 12.6:
        px, pfy = 730, GFY
        f = -1 if t < 12.35 else 1
        wings = ease((t - 12.0) / 0.3)
        mood = "happy"
    elif t < 13.2:
        px, pfy = path(t, [(12.6, 730, GFY), (13.2, 712, GFY)])
        wings = 1.0
        mood = "happy"
    elif t < 14.9:
        px, pfy, wings = 712, GFY, 1.0
        mood = "happy" if t < 14.3 else "smile"
    elif t < 16.4:
        px, pfy = 712, GFY
        mood = "oops"
        sq = 1 - 0.14 * math.sin(math.pi * clamp01((t - 14.9) / 0.5))
    elif t < 17.4:
        px, pfy = 712 + 4 * math.sin(t * 40) * (17.4 - t), GFY     # elle s'ébroue
        mood = "happy"
        wings = 0.3 + 0.3 * math.sin(t * 30)
    elif t < 18.8:
        px, pfy = 712, GFY
        mood = "smile"
    elif t < 19.9:
        px, pfy = path(t, [(18.8, 712, GFY), (19.9, SPOT_P, GFY)])
        pfy -= abs(math.sin(t * 10)) * 6
        step = t * 10
    elif t < 20.3:
        px, pfy = SPOT_P, GFY
    elif t < 22.4:
        px, pfy = SPOT_P, GFY
        wings, flap, mood = 1.0, 1.0, "happy"
    elif t < 24.4:
        px, pfy = SPOT_P, GFY
        mood = "happy"
        wings = 0.6 if t > 23.6 else 0.0
    elif t < 24.8:
        px, pfy = hop(t, 24.4, 24.8, (SPOT_P, GFY), (760, GFY), 60)
        f, wings, mood = -1, 0.8, "happy"
    elif t < 25.2:
        px, pfy = hop(t, 24.8, 25.2, (760, GFY), (PX0, PFY), 60)
        f, wings, mood = -1, 0.8, "happy"
    if t >= 25.2:
        f = 1 if (t // 0.7) % 2 == 0 else -1

    # ---------------- Dot
    dx, dfy, dmood, df, dfly, dwet = DOT0[0], DOT0[1], "smile", -1, 0.0, False
    if t < 7.2:
        dmood = "smile"
        dwet = True
    elif t < 13.2:
        dmood = "sad"
        dwet = True
        if 8.6 < t < 9.6:                          # elle essaie de voler... non
            dfly = 0.7
            dfy -= 10 * abs(math.sin(t * 12))
        if t > 12.0:
            dmood = "smile"
    elif t < 14.9:
        dmood = "happy"
    elif t < 16.4:
        dmood = "oops"
    elif t < 18.6:
        dmood = "smile" if t < 17.8 else "happy"
        dwet = t < 17.8
        df = -1 if t < 17.9 else 1
    elif t < 20.1:                                 # trois petits bonds jusqu'au champignon
        keys = [(18.6, DOT0[0], DOT0[1]), (19.1, 880, GFY), (19.6, 970, GFY), (20.1, SPOT_D, GFY)]
        for (a0, x0, y0), (a1, x1, y1) in zip(keys, keys[1:]):
            if a0 <= t < a1:
                dx, dfy = hop(t, a0, a1, (x0, y0), (x1, y1), 40)
        df, dmood = 1, "happy"
    elif t < 22.6:
        dx, dfy = SPOT_D, GFY
        df, dmood = -1, "happy"
        dfly = 0.5 if t > 20.5 else 0.0
        dwet = t < 21.6
    elif t < 24.0:                                 # elle s'envole !
        dx, dfy = path(t, [(22.6, SPOT_D, GFY), (23.2, 1135, 520), (24.0, 900, 360)])
        dfy += 6 * math.sin(t * 8)
        df = 1 if t < 23.2 else -1
        dfly, dmood = 1.0, "happy"
    else:                                          # elle tourne autour de Pippa
        a = (t - 24.0) * 1.7
        cx, cy = lerp(900, PX0 + 10, ease((t - 24.0) / 1.6)), 380
        dx, dfy = cx + 115 * math.sin(a), cy + 40 * math.sin(a * 2) * 0.5 + 30 * math.cos(a)
        df = 1 if math.cos(a) > 0 else -1
        dfly, dmood = 1.0, "happy"

    # ---------------- dessin
    plant(d, t)
    puddle_rings(d, t)
    for gx, gy, rx in [(PX0, PFY, 0)]:
        pass
    ptop = duck(d, px, pfy, t, mood, talking("pippa", t), sq, f, wings, flap, step)
    if in_puddle and pfy >= PFY - 6:
        water_cover(img, base, px, pfy - 2, 62, 9)
        d = ImageDraw.Draw(img)
    dtop = ladybug(d, dx, dfy, t, dmood, talking("dot", t), df, 1.0, dfly, dwet)

    # éclaboussures de flaque
    for j0, j1 in JUMPS:
        if j1 <= t < j1 + 0.8 and (j1 < 9 or j1 > 25):
            splash(d, PX0, PFY, (t - j1) / 0.8, 9, 0.9)
    if 24.95 < t < 25.75:
        splash(d, PX0, PFY, (t - 24.95) / 0.8, 9, 0.9)

    # feuille-parapluie
    if 12.0 <= t < 16.5:
        if t < 12.6:
            lx, ly = px + 30 * f, pfy - 140
            ang, L = -math.pi / 2 + (0.0 if t < 12.35 else -0.0), 110
            ang = lerp(-math.pi / 2 - 0.2, -0.12, ease((t - 12.3) / 0.3)) if t > 12.3 else -math.pi / 2 - 0.2
        elif t < 14.3:
            lx, ly, ang, L = px + 34, pfy - 136, -0.12 + 0.03 * math.sin(t * 3), 150
        elif t < 14.9:
            u = ease((t - 14.3) / 0.6)
            lx, ly, ang, L = px + 34, pfy - 136, lerp(-0.12, -1.9, u), 150
        else:
            u = (t - 14.9) / 1.6
            lx, ly = lerp(px + 34, 1250, u), lerp(pfy - 136, 160, u) - 60 * math.sin(math.pi * u)
            ang, L = -1.9 + u * 9, 150
        cx_, cy_ = lx + math.cos(ang) * L * 0.5, ly + math.sin(ang) * L * 0.5
        leaf(d, (lx, ly), ang, L, 38, (90, 185, 95))
        d.line([P(lx), P(ly), P(lx + math.cos(ang) * L * 0.9), P(ly + math.sin(ang) * L * 0.9)],
               fill=(60, 140, 70), width=P(3))
        if 12.6 <= t < 14.3:                       # gouttes qui s'accumulent sur la feuille
            for i in range(4):
                circ(d, lx + 40 + i * 26, ly - 12 - 2 * math.sin(t * 4 + i), 5, (200, 225, 255))
    if 14.3 < t < 15.1:                              # coup de vent
        u = (t - 14.3) / 0.8
        for i in range(3):
            yy = 420 + i * 40
            x0 = lerp(450, 1100, u) - i * 50
            d.arc([P(x0 - 80), P(yy - 12), P(x0 + 80), P(yy + 12)], 200, 340, fill=(240, 248, 255), width=P(4))
    if 14.8 < t < 15.5:                              # toute l'eau tombe sur Pippa
        g = (t - 14.8) / 0.7
        for i in range(9):
            xx = px - 50 + i * 13 + 6 * math.sin(i * 3)
            yy = lerp(400, ptop[1] + 30 + 40 * (i % 3), g) + 10 * (i % 2)
            ell(d, xx, yy, 6, 9, (170, 210, 255))
    if 15.0 < t < 16.4:                              # petites étoiles d'étourdissement
        for i in range(3):
            a = t * 5 + i * 2.09
            star(d, ptop[0] + 44 * math.cos(a), ptop[1] + 8 + 10 * math.sin(a), 8, t * 4, (255, 240, 120))
    # idée de Dot
    if 17.9 < t < 18.9:
        g = (t - 17.9) / 1.0
        for i in range(5):
            a = -math.pi / 2 + (i - 2) * 0.5
            rr = 30 + 36 * g
            star(d, dtop[0] + rr * math.cos(a), dtop[1] + 16 + rr * math.sin(a), 9 * math.sin(math.pi * g),
                 t * 3 + i, (255, 230, 70))
    # Pippa bat des ailes : petits souffles vers Dot, gouttes qui s'envolent
    if 20.4 < t < 22.4:
        for i in range(3):
            g = ((t - 20.4) * 2.5 + i / 3) % 1
            yy = 540 + i * 22
            x0 = lerp(950, 1020, g)
            d.arc([P(x0 - 20), P(yy - 8), P(x0 + 20), P(yy + 8)], 200, 340, fill=(240, 250, 255), width=P(3))
        if t < 21.8:
            for i in range(3):
                g = ((t - 20.4) * 1.8 + i / 3) % 1
                ell(d, SPOT_D + 20 + 60 * g, 570 - 50 * g + 60 * g * g, 3, 4, (150, 200, 255))
    if 22.3 < t < 23.4:                              # elle est sèche !
        for i in range(6):
            a = i * 1.05 + t * 2
            rr = 36 + 20 * (t - 22.3)
            star(d, dx + rr * math.cos(a), dfy - 24 + rr * math.sin(a), 7, t * 4, (255, 245, 150))

    # pluie (pas sous le champignon)
    rain(d, t, 0, 1400, -40, 720, 150, 3, under_cap)

    # fin : les amies coccinelles + cœurs
    if t > 24.0:
        g = ease((t - 24.0) / 1.2)
        ccx, ccy = lerp(1350, 760, g), lerp(180, 330, g)
        for i, col in enumerate([(255, 150, 40), (245, 205, 40), (255, 110, 170), (232, 58, 58)]):
            a = (t - 24.0) * 1.4 + i * math.pi / 2
            fx, fy_ = ccx + 130 * math.cos(a), ccy + 50 * math.sin(a)
            ladybug(d, fx, fy_ + 18, t + i, "happy", 0, 1 if -math.sin(a) > 0 else -1, 0.6, 1.0, False, col)
    if t > 24.6:
        for i in range(5):
            k = ((t - 24.6) * 0.45 + i / 5) % 1
            r = 10 * math.sin(math.pi * k)
            if r > 3:
                heart(d, 470 + i * 70 + 18 * math.sin(t * 2 + i), 560 - k * 260, r)

    ANCHORS["pippa"] = (ptop[0], ptop[1] - 4)
    ANCHORS["dot"] = (dtop[0], dtop[1])
    if 19.9 <= t < 22.6:
        ANCHORS["pippa"] = (ptop[0], CAP_Y - CAP_RY - 6)
        ANCHORS["dot"] = (dtop[0], CAP_Y - CAP_RY - 6)
    return img, px, pfy, ANCHORS["dot"]

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
