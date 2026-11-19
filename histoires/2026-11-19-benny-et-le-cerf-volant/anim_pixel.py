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


# ---------------------------------------------------------------- background (forêt d'automne)
SKY_TOP, SKY_BOT = (125, 190, 250), (255, 228, 175)
LEAF_COLS = [(240, 140, 50), (220, 85, 60), (250, 190, 60), (200, 110, 40)]
GROUND = (165, 160, 70)
KITE_IN_SCENE = True      # anim_vert met False : le cerf-volant est dessiné par-dessus tout l'écran vertical
ANCHORS = {}              # point au-dessus de la tête de chaque personnage (pour les bulles)
KITE = (0, 0, 0, None)    # x, y, angle, point d'attache de la ficelle (ou None)


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


def small_leaf(d, x, y, ang, col, k=1.0):
    leaf(d, (x - 11 * k * math.cos(ang), y - 11 * k * math.sin(ang)), ang, 22 * k, 8 * k, col)


def make_hills():
    img = Image.new("RGBA", (int(W * S), int(H * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = random.Random(7)
    far = [(235, 175, 110), (230, 150, 115), (240, 200, 120), (215, 165, 120)]
    for i, x in enumerate(range(-40, 1340, 92)):
        h = rng.uniform(0, 50)
        d.rectangle([P(x - 7), P(470 - h), P(x + 7), P(600)], fill=(170, 125, 105))
        col = far[i % 4]
        circ(d, x, 450 - h, 52, col)
        circ(d, x - 28, 478 - h, 36, col)
        circ(d, x + 28, 478 - h, 36, col)
    ell(d, 250, 770, 680, 260, (180, 175, 85))
    ell(d, 1100, 790, 640, 280, (170, 165, 78))
    d.rectangle([0, P(600), int(W * S), int(H * S)], fill=GROUND)
    ell(d, 640, 618, 900, 45, GROUND)
    for _ in range(70):
        x, y = rng.uniform(0, 1280), rng.uniform(612, 715)
        small_leaf(d, x, y, rng.uniform(0, 6.3), rng.choice(LEAF_COLS), rng.uniform(0.6, 1.0))
    # grand arbre (tronc, branche, feuillage)
    d.polygon([(P(995), P(618)), (P(1080), P(618)), (P(1062), P(190)), (P(1015), P(190))],
              fill=(130, 85, 55))
    d.line([(P(1022), P(232)), (P(940), P(214)), (P(845), P(222))], fill=(130, 85, 55), width=P(16))
    d.line([(P(1035), P(400)), (P(1035), P(470))], fill=(105, 65, 40), width=P(5))
    ell(d, 1040, 330, 13, 18, (85, 50, 30))
    for cx, cy, r, col in [(1120, 130, 95, (220, 85, 60)), (900, 140, 70, (250, 190, 60)),
                           (980, 70, 95, (240, 140, 50)), (1090, 30, 85, (250, 190, 60)),
                           (1180, 70, 80, (240, 140, 50)), (860, 60, 60, (220, 85, 60)),
                           (1010, 150, 70, (220, 85, 60)), (960, -10, 80, (220, 85, 60))]:
        circ(d, cx, cy, r + 5, lerpc(col, (90, 40, 20), 0.35))
    for cx, cy, r, col in [(1120, 130, 95, (220, 85, 60)), (900, 140, 70, (250, 190, 60)),
                           (980, 70, 95, (240, 140, 50)), (1090, 30, 85, (250, 190, 60)),
                           (1180, 70, 80, (240, 140, 50)), (860, 60, 60, (220, 85, 60)),
                           (1010, 150, 70, (220, 85, 60)), (960, -10, 80, (220, 85, 60))]:
        circ(d, cx, cy, r, col)
        circ(d, cx - r * 0.3, cy - r * 0.3, r * 0.35, lerpc(col, (255, 255, 220), 0.3))
    return img


SKY = make_sky()
HILLS = make_hills()
BASE = SKY.copy()
BASE.paste(HILLS, (0, 0), HILLS)


# ---------------------------------------------------------------- pieces
INK = (50, 35, 35)


def plain_cloud(d, x, y, k):
    for dx, dy, r in [(-40, 5, 28), (0, -12, 36), (40, 5, 28)]:
        circ(d, x + dx * k, y + dy * k, r * k, (255, 250, 245))
    d.rounded_rectangle([P(x - 62 * k), P(y), P(x + 62 * k), P(y + 32 * k)],
                        radius=P(16 * k), fill=(255, 250, 245))


def eyes(d, x, y, sp, r, mood, t, ph=0.0):
    if mood in ("closed", "oops"):
        for sx in (-1, 1):
            d.arc([P(x + sx * sp - 9), P(y - 6), P(x + sx * sp + 9), P(y + 10)], 200, 340, fill=INK, width=P(4))
        return
    blink = ((t + ph) % 3.4) < 0.13
    for sx in (-1, 1):
        ell(d, x + sx * sp, y, r * 0.8, 2 if blink else r, INK)
        if not blink:
            circ(d, x + sx * sp + 2, y - r * 0.4, r * 0.35, (255, 255, 255))


BROWN, BROWN_D, CREAM = (170, 108, 62), (125, 75, 45), (238, 205, 155)


def bear(d, x, fy, t, mood, talk=0.0, arms=(0.0, 0.0), hug=0.0, sq=1.0, sit=0.0):
    """Benny l'ourson. Renvoie le haut de la tête."""
    def Y(v):
        return fy - v * sq
    # pieds (en avant quand il est assis)
    for sx in (-1, 1):
        ell(d, x + sx * (30 + 18 * sit), fy - 10 + 4 * sit, 24 + 4 * sit, 14, BROWN_D)
        if sit > 0.5:
            ell(d, x + sx * (30 + 18 * sit), fy - 12, 12, 8, CREAM)
    # bras derrière le corps quand ils sont levés
    sh = [(x - 50, Y(102)), (x + 50, Y(102))]

    def paw(i):
        sx = -1 if i == 0 else 1
        a = arms[i]
        down = (x + sx * 72, Y(52))
        up = (x + sx * 88, Y(240))
        p = (lerp(down[0], up[0], a), lerp(down[1], up[1], a))
        hg = (x - sx * 18, Y(84))
        return (lerp(p[0], hg[0], hug), lerp(p[1], hg[1], hug))
    paws = [paw(0), paw(1)]
    ell(d, x, Y(68), 64, 64 * sq, BROWN)
    ell(d, x, Y(60), 41, 43 * sq, CREAM)
    for i in (0, 1):
        d.line([(P(sh[i][0]), P(sh[i][1])), (P(paws[i][0]), P(paws[i][1]))], fill=BROWN, width=P(26))
        circ(d, paws[i][0], paws[i][1], 16, BROWN_D)
    # écharpe bleue
    d.rounded_rectangle([P(x - 50), P(Y(128)), P(x + 50), P(Y(108))], radius=P(9), fill=(70, 140, 230))
    d.polygon([(P(x + 22), P(Y(110))), (P(x + 44), P(Y(110))), (P(x + 50 + 6 * math.sin(t * 5)), P(Y(66))),
               (P(x + 30 + 6 * math.sin(t * 5)), P(Y(70)))], fill=(55, 115, 205))
    # tête
    hy = Y(176)
    for sx in (-1, 1):
        circ(d, x + sx * 44, hy - 44, 21, BROWN)
        circ(d, x + sx * 44, hy - 44, 11, (225, 160, 140))
    circ(d, x, hy, 58, BROWN)
    circ(d, x - 41, hy + 16, 9, (240, 140, 130))
    circ(d, x + 41, hy + 16, 9, (240, 140, 130))
    ell(d, x, hy + 20, 28, 21, CREAM)
    ell(d, x, hy + 8, 10, 7, (60, 35, 30))
    eyes(d, x, hy - 10, 22, 8, mood, t)
    if mood == "worried":
        for sx in (-1, 1):
            d.line([P(x + sx * 12), P(hy - 30), P(x + sx * 32), P(hy - 25)], fill=INK, width=P(4))
    my = hy + 28
    if talk > 0.02:
        ell(d, x, my + 2, 9, 2 + 8 * talk, (130, 40, 50))
    elif mood in ("happy", "closed"):
        d.pieslice([P(x - 13), P(my - 6), P(x + 13), P(my + 12)], 0, 180, fill=(130, 40, 50))
    elif mood in ("worried", "oops"):
        ell(d, x, my + 3, 6, 7, (130, 40, 50))
    else:
        d.arc([P(x - 11), P(my - 8), P(x + 11), P(my + 6)], 20, 160, fill=INK, width=P(3))
    return (x, hy - 64), paws


FUR, FUR_D, FUR_C = (215, 118, 55), (170, 85, 38), (252, 228, 185)


def squirrel(d, x, fy, t, mood, talk=0.0, reach=0.0, face=-1):
    """Lila l'écureuil. Renvoie le haut de la tête et la patte levée."""
    wig = 6 * math.sin(t * 3)
    tail = [(x - face * 24, fy - 22, 20), (x - face * 46, fy - 48, 25), (x - face * 56, fy - 85, 28),
            (x - face * (48 + wig * 0.3), fy - 120, 27), (x - face * (26 + wig), fy - 138, 22)]
    for tx, ty, r in tail:
        circ(d, tx, ty, r + 4, FUR_D)
    for tx, ty, r in tail:
        circ(d, tx, ty, r, FUR)
    circ(d, x - face * (30 + wig), fy - 140, 10, FUR_C)
    for sx in (-1, 1):
        ell(d, x + sx * 13, fy - 5, 14, 7, FUR_D)
    ell(d, x, fy - 38, 27, 34, FUR)
    ell(d, x + face * 4, fy - 34, 16, 24, FUR_C)
    # bras (patte de devant), levé si reach
    sh = (x + face * 16, fy - 52)
    pw = (lerp(x + face * 22, x + face * 12, reach), lerp(fy - 34, fy - 160, reach))
    d.line([(P(sh[0]), P(sh[1])), (P(pw[0]), P(pw[1]))], fill=FUR, width=P(10))
    circ(d, pw[0], pw[1], 7, FUR_D)
    hy = fy - 90
    for sx in (-1, 1):
        d.polygon([(P(x + sx * 9), P(hy - 18)), (P(x + sx * 27), P(hy - 14)), (P(x + sx * 21), P(hy - 44))],
                  fill=FUR)
        d.polygon([(P(x + sx * 15), P(hy - 18)), (P(x + sx * 23), P(hy - 17)), (P(x + sx * 20), P(hy - 34))],
                  fill=(240, 160, 150))
    circ(d, x, hy, 28, FUR)
    ell(d, x + face * 5, hy + 12, 17, 12, FUR_C)
    # nœud violet
    bx, by = x - face * 20, hy - 22
    d.polygon([(P(bx), P(by)), (P(bx - 14), P(by - 9)), (P(bx - 14), P(by + 9))], fill=(165, 85, 220))
    d.polygon([(P(bx), P(by)), (P(bx + 14), P(by - 9)), (P(bx + 14), P(by + 9))], fill=(165, 85, 220))
    circ(d, bx, by, 4, (200, 130, 245))
    ex = x + face * 4
    eyes(d, ex, hy - 4, 11, 5, "closed" if mood == "happy" else mood, t, 1.1)
    if mood == "sad":
        for sx in (-1, 1):
            d.line([P(ex + sx * 4), P(hy - 21), P(ex + sx * 16), P(hy - 15)], fill=INK, width=P(3))
        ell(d, ex + 15, hy + 8, 3, 5, (110, 170, 255))
    ell(d, x + face * 6, hy + 5, 4, 3, (200, 90, 100))
    circ(d, x - 18, hy + 8, 4, (250, 140, 140))
    circ(d, x + 18, hy + 8, 4, (250, 140, 140))
    my = hy + 15
    if talk > 0.02:
        ell(d, x + face * 5, my, 5, 1.5 + 5 * talk, (130, 40, 50))
    elif mood == "sad":
        d.arc([P(x + face * 5 - 7), P(my - 1), P(x + face * 5 + 7), P(my + 9)], 200, 340, fill=INK, width=P(3))
    elif mood == "happy":
        d.pieslice([P(x + face * 5 - 8), P(my - 4), P(x + face * 5 + 8), P(my + 8)], 0, 180, fill=(130, 40, 50))
    else:
        d.arc([P(x + face * 5 - 7), P(my - 7), P(x + face * 5 + 7), P(my + 4)], 20, 160, fill=INK, width=P(3))
    return (x, hy - 48), pw


KITE_COLS = [(255, 220, 60), (70, 150, 240), (255, 110, 160), (110, 200, 110)]


def kite(d, x, y, ang, t, ox=0, oy=0, n=6):
    """Cerf-volant en losange (x, y = centre), décalé de (ox, oy) pour l'écran vertical."""
    x, y = x + ox, y + oy
    ca, sa = math.cos(ang), math.sin(ang)

    def R(px, py):
        return (P(x + px * ca - py * sa), P(y + px * sa + py * ca))
    tips = [(0, -46), (32, -10), (0, 46), (-32, -10)]
    for i in range(4):
        d.polygon([R(0, -10), R(*tips[i]), R(*tips[(i + 1) % 4])], fill=KITE_COLS[i])
    d.line([R(0, -46), R(0, 46)], fill=(120, 80, 50), width=P(3))
    d.line([R(-32, -10), R(32, -10)], fill=(120, 80, 50), width=P(3))
    circ(d, x - 6 * sa, y + 6 * ca - 16 * ca, 0, (0, 0, 0))
    # petits yeux souriants
    ex, ey = R(0, 2)
    # queue avec nœuds
    px, py = 0, 46
    for i in range(1, n + 1):
        nx, ny = 10 * math.sin(t * 4 + i * 0.9), 46 + i * 15
        d.line([R(px, py), R(nx, ny)], fill=(90, 70, 60), width=P(3))
        if i % 2 == 0:
            c = KITE_COLS[(i // 2) % 4]
            a, b = R(nx, ny)
            d.polygon([(a, b), (a - P(10), b - P(6)), (a - P(10), b + P(6))], fill=c)
            d.polygon([(a, b), (a + P(10), b - P(6)), (a + P(10), b + P(6))], fill=c)
        px, py = nx, ny


def draw_kite(d, t, ox=0, oy=0):
    x, y, ang, anchor = KITE
    if anchor is not None:
        ax, ay = anchor
        mx, my = (ax + x) / 2 + 30, (ay + y) / 2 + 40
        pts = [bez((ax + ox, ay + oy), (mx + ox, my + oy), (x + ox, y + 46 * 0.3 + oy), i / 16) for i in range(17)]
        d.line([(P(a), P(b)) for a, b in pts], fill=(255, 255, 255), width=P(3))
    kite(d, x, y, ang, t, ox, oy, 6 if anchor is not None else 3)


def wind_lines(d, t, t0, t1, y0, y1, seed=3):
    if not (t0 < t < t1):
        return
    a = min(ease((t - t0) / 0.4), ease((t1 - t) / 0.5))
    for i in range(6):
        r = random.Random(i + seed)
        y = r.uniform(y0, y1)
        x = (r.uniform(0, 1400) + (t - t0) * 900) % 1600 - 200
        L = 120 * a
        pts = [(P(x + k * L / 8), P(y + 8 * math.sin(k * 0.8 + t * 6))) for k in range(9)]
        d.line(pts, fill=(255, 255, 255), width=P(4))


def falling_leaves(d, t, x0, x1, y0, y1, n, seed, speed=60, wind=0.0):
    for i in range(n):
        r = random.Random(seed + i)
        span = y1 - y0
        ph = r.random()
        y = y0 + ((t * speed / span + ph) % 1) * span
        x = r.uniform(x0, x1) + 30 * math.sin(t * 1.5 + i) + wind
        x = x0 + (x - x0) % (x1 - x0)
        small_leaf(d, x, y, t * 2 + i, LEAF_COLS[i % 4], 1.1)


def sun(d, t):
    cx, cy = 130, 115
    for k in range(10):
        a = k * 2 * math.pi / 10 + t * 0.4
        d.line([P(cx + 70 * math.cos(a)), P(cy + 70 * math.sin(a)),
                P(cx + 95 * math.cos(a)), P(cy + 95 * math.sin(a))],
               fill=(255, 190, 70), width=P(8))
    circ(d, cx, cy, 58, (255, 215, 70))
    circ(d, cx, cy, 50, (255, 228, 100))
    circ(d, cx - 17, cy - 8, 5, (90, 60, 40))
    circ(d, cx + 17, cy - 8, 5, (90, 60, 40))
    d.arc([P(cx - 18), P(cy - 2), P(cx + 18), P(cy + 22)], 20, 160,
          fill=(90, 60, 40), width=P(4))
    circ(d, cx - 30, cy + 10, 7, (255, 170, 120))
    circ(d, cx + 30, cy + 10, 7, (255, 170, 120))


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


# ---------------------------------------------------------------- frame
KITE_HOME = (862, 226)


def scene(t, with_sun=True):
    global KITE
    img = BASE.copy()
    d = ImageDraw.Draw(img)
    if with_sun:
        sun(d, t)
        for base, y, k, sp in [(300, 90, 0.9, 10), (700, 160, 0.7, 14)]:
            plain_cloud(d, (base + t * sp) % 1580 - 150, y, k)
    windy = 23.4 < t < 25.8
    falling_leaves(d, t, 420, 1120, -40, 600, 6, 11, 55, (t - 23.6) * 300 if t > 23.6 else 0)

    # ---- Benny
    bx, _ = path(t, [(0, 600, 0), (1.5, 640, 0), (4.4, 640, 0), (6.6, 690, 0), (9.2, 690, 0),
                     (11.2, 850, 0), (25.0, 850, 0), (26.2, 690, 0)])
    fy = 615
    lift = 0.0
    if t < 1.6:
        lift = abs(math.sin(t * 6)) * 14          # accroche : il sautille tout de suite
    if 4.4 < t < 6.6 or 9.2 < t < 11.2 or 25.0 < t < 26.2:
        lift = abs(math.sin(t * 9)) * 12           # il marche en écrasant les feuilles
    sq, sit = 1.0, 0.0
    if 13.8 < t < 14.2:
        sq = 1 - 0.12 * math.sin(math.pi * (t - 13.8) / 0.4)
    if 14.2 <= t < 15.0:
        lift = 34 * math.sin(math.pi * (t - 14.2) / 0.8)
    if 15.0 <= t < 17.6:
        sit = 1.0
        sq = 0.82 + (0.06 * math.sin(math.pi * (t - 15.0) / 0.3) if t < 15.3 else 0)
    if 17.6 <= t < 18.0:
        sit = 1 - (t - 17.6) / 0.4
        sq = lerp(0.82, 1.0, (t - 17.6) / 0.4)
    if t > 26.2:
        lift = abs(math.sin(t * 5)) * 20           # danse de la fin
    if 22.2 <= t < 23.2:
        sq = 0.96
    fy -= lift
    al = ar = 0.0
    hug = 0.0
    if t < 1.7:
        ar = 0.75 + 0.2 * math.sin(t * 12)
    if 1.8 <= t < 3.2:
        hug = math.sin(math.pi * min(1, (t - 1.8) / 1.4)) ** 0.5
    if 4.4 < t < 6.6:
        al = 0.2 + 0.15 * math.sin(t * 9)
        ar = 0.2 - 0.15 * math.sin(t * 9)
    if 10.2 < t < 11.4:
        ar = 0.6
    if 13.6 < t < 15.0:
        al = ar = ease((t - 13.6) / 0.5)
    if 15.0 <= t < 17.6:
        al = ar = 0.35
    if 20.7 < t < 21.6:
        al = 0.5 + 0.1 * math.sin(t * 8)
    if 22.0 < t < 23.3:
        al = ar = 0.62
    if t > 24.2:
        al = ar = 0.85 + 0.12 * math.sin(t * 7)
    bm = "smile"
    if t < 1.8 or 24.0 <= t:
        bm = "happy"
    if 1.8 <= t < 3.2:
        bm = "closed"
    if 7.8 <= t < 10.1:
        bm = "worried"
    if 14.2 <= t < 15.0:
        bm = "happy"
    if 15.0 <= t < 17.6:
        bm = "oops"
    if 22.9 <= t < 24.0:
        bm = "happy"
    if 17.6 <= t < 18.2:
        bx += 6 * math.sin(t * 40)                 # il secoue les feuilles

    # ---- Lila
    lx, ly = 960, 615
    if 21.4 <= t < 22.2:
        u = (t - 21.4) / 0.8
        lx, ly = lerp(960, 852, ease(u)), lerp(615, 398, u) - 110 * math.sin(math.pi * u)
    elif 22.2 <= t < 23.2:
        lx, ly = bx + 2, 398 + (615 - fy) * -1 + (1 - sq) * 176
    elif 23.2 <= t < 23.8:
        u = (t - 23.2) / 0.6
        lx, ly = lerp(852, 950, u), lerp(398, 615, u) - 80 * math.sin(math.pi * u)
    elif t >= 23.8:
        lx, ly = 950, 615
        if t > 26.2:
            ly -= abs(math.sin(t * 5 + 1)) * 16
    if 18.6 < t < 19.4:
        ly -= 22 * math.sin(math.pi * (t - 18.6) / 0.8)   # bonne idée : petit saut
    lm = "sad"
    if 18.6 <= t < 22.9:
        lm = "smile"
    elif t >= 22.9:
        lm = "happy"
    reach = 0.0
    if 22.3 <= t < 22.9:
        reach = ease((t - 22.3) / 0.5)
    elif 22.9 <= t:
        reach = 0.9
    if 7.2 < t < 9.6:
        reach = 0.5 + 0.1 * math.sin(t * 6)          # elle montre son cerf-volant

    # ---- cerf-volant
    lhead, lpaw = None, None
    # dessin
    (bh, paws) = bear(d, bx, fy, t, bm, talking(story.HERO, t), (al, ar), hug, sq, sit)
    (lh, lpaw) = squirrel(d, lx, ly, t, lm, talking(story.FRIEND, t), reach, -1)
    if t < 22.9:
        KITE = (KITE_HOME[0], KITE_HOME[1], -0.25 + 0.05 * math.sin(t * 2.5), None)
    elif t < 23.8:
        KITE = (lpaw[0] + 4, lpaw[1] - 40, -0.1, None)
    else:
        u = ease((t - 23.8) / 2.0)
        tx, ty = 1050 + 20 * math.sin(t * 1.3), -420 + 15 * math.sin(t * 2.1)
        KITE = (lerp(lpaw[0] + 4, tx, u), lerp(lpaw[1] - 40, ty, u), 0.15 * math.sin(t * 2), lpaw)
    if KITE_IN_SCENE:
        draw_kite(d, t)

    # feuilles écrasées sous les pas
    if 4.4 < t < 6.8:
        for i in range(10):
            r = random.Random(i + 70)
            age = ((t - 4.4) * 1.6 + r.random()) % 1
            small_leaf(d, bx + r.uniform(-70, 70) + (age - 0.5) * r.uniform(-60, 60),
                       612 - 70 * math.sin(math.pi * age), t * 5 + i, LEAF_COLS[i % 4])
    # feuilles qui tombent sur Benny après la chute
    if 15.0 <= t < 18.2:
        for i in range(5):
            dx = [-30, 12, 40, -8, 22][i]
            t0 = 15.05 + i * 0.22
            u = clamp01((t - t0) / 0.9)
            if t < t0:
                continue
            tx, ty = bh[0] + dx, bh[1] + 14 + (36 if i == 3 else 0) + (abs(dx) * 0.4)
            if i == 3:
                tx, ty = bh[0] + 12, bh[1] + 70     # une feuille sur son nez
            y = lerp(230, ty, u)
            x = tx + (1 - u) * 25 * math.sin(t * 6 + i)
            if t > 17.6:
                v = (t - 17.6) / 0.6
                x += (dx + 10) * 3 * v
                y -= 90 * math.sin(math.pi * min(1, v))
            small_leaf(d, x, y, 0.4 * i + (1 - u) * t * 3, LEAF_COLS[i % 4], 1.2)
    # « bonne idée » : petites étoiles au-dessus de Lila
    if 18.6 < t < 19.8:
        g = (t - 18.6) / 1.2
        for i in range(5):
            a = -math.pi / 2 + (i - 2) * 0.5
            rr = 30 + 40 * g
            star(d, lh[0] + rr * math.cos(a), lh[1] + 10 + rr * math.sin(a), 11 * math.sin(math.pi * g),
                 t * 3 + i, (255, 230, 70))
    # vent + fête des feuilles
    wind_lines(d, t, 23.6, 25.8, 120, 560)
    if t > 24.2:
        g = t - 24.2
        for i in range(14):
            r = random.Random(i + 300)
            a = i * 2 * math.pi / 14 + g * (0.9 + 0.3 * r.random())
            rr = 60 + min(1, g / 1.5) * r.uniform(90, 200)
            cx, cy = (bx + lx) / 2, 470 - 10 * g
            small_leaf(d, cx + rr * math.cos(a), cy + 0.55 * rr * math.sin(a), g * 4 + i, LEAF_COLS[i % 4], 1.2)
        if g < 3.5:
            for i in range(8):
                a = i * math.pi / 4 + t * 0.8
                rr = 60 + 40 * g
                sz = 12 * math.sin(math.pi * min(1, g / 3.5))
                if sz > 1:
                    star(d, lh[0] + rr * math.cos(a), lh[1] + 30 + rr * math.sin(a), sz, t * 2 + i,
                         (255, 220, 60) if i % 2 else (255, 255, 255))

    ANCHORS["benny"] = (bh[0], min(bh[1], paws[0][1] - 20, paws[1][1] - 20) - 4)
    if 12.8 < t < 15.0:
        ANCHORS["benny"] = (bh[0] - 70, bh[1] + 20)   # bulle à gauche, le cerf-volant reste visible
    ANCHORS["lila"] = (lh[0], lh[1] - 4)
    return img, bx, fy, ANCHORS["lila"]


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
