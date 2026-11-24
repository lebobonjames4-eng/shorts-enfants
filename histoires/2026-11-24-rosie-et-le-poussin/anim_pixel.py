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


def cam(t):
    """Centre x de la caméra verticale : elle suit l'action."""
    return path(t, [(0, 380), (11.2, 380), (12.4, 560), (16.0, 560), (17.2, 790), (20.8, 790),
                    (21.8, 830)])


def star(d, x, y, r, rot, col):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = rot + i * math.pi / 5 - math.pi / 2
        pts.append((P(x + rr * math.cos(a)), P(y + rr * math.sin(a))))
    d.polygon(pts, fill=col)


def heart(d, hx, hy, r, col=(255, 110, 150)):
    circ(d, hx - r * 0.5, hy, r * 0.6, col)
    circ(d, hx + r * 0.5, hy, r * 0.6, col)
    d.polygon([(P(hx - r * 1.05), P(hy + r * 0.2)), (P(hx + r * 1.05), P(hy + r * 0.2)),
               (P(hx), P(hy + r * 1.3))], fill=col)


def note_sym(d, x, y, col):
    """Petite note de musique."""
    ell(d, x, y, 9, 7, col)
    d.line([P(x + 7), P(y), P(x + 7), P(y - 30)], fill=col, width=P(4))
    d.line([P(x + 7), P(y - 30), P(x + 20), P(y - 22)], fill=col, width=P(4))


# ---------------------------------------------------------------- background
def make_sky():
    img = Image.new("RGB", (int(W * S), int(H * S)))
    d = ImageDraw.Draw(img)
    top, bot = (120, 190, 255), (210, 238, 255)
    h = int(H * S)
    for y in range(h):
        u = int(y / h * 7) / 6
        d.line([(0, y), (int(W * S), y)], fill=lerpc(top, bot, u))
    return img


def sunflower(d, x, y, h):
    d.line([P(x), P(y), P(x), P(y - h)], fill=(70, 150, 60), width=P(7))
    ell(d, x + 12, y - h * 0.45, 16, 7, (80, 165, 70))
    ell(d, x - 12, y - h * 0.3, 16, 7, (80, 165, 70))
    for i in range(10):
        a = i * math.pi / 5
        circ(d, x + 20 * math.cos(a), y - h + 20 * math.sin(a), 11, (255, 205, 40))
    circ(d, x, y - h, 14, (140, 85, 40))


def tree(d, x, y):
    d.rectangle([P(x - 14), P(y - 120), P(x + 14), P(y)], fill=(140, 95, 60))
    for dx, dy, r in [(-45, -150, 55), (40, -160, 58), (0, -205, 62), (0, -140, 60)]:
        circ(d, x + dx, y + dy, r, (75, 165, 80))
    for dx, dy in [(-40, -150), (30, -190), (45, -140), (-10, -210), (10, -120)]:
        circ(d, x + dx, y + dy, 9, (235, 60, 60))


def haybale(d, x, y):
    d.rounded_rectangle([P(x - 60), P(y - 70), P(x + 60), P(y)], radius=P(14), fill=(235, 195, 90))
    for k in range(-40, 50, 20):
        d.line([P(x + k), P(y - 64), P(x + k), P(y - 6)], fill=(210, 165, 60), width=P(3))
    d.line([P(x - 60), P(y - 35), P(x + 60), P(y - 35)], fill=(190, 120, 70), width=P(4))


def barn(d, door_open):
    x0, x1, yt, peak = 860, 1120, 430, 330
    cx = (x0 + x1) / 2
    d.polygon([(P(x0 - 20), P(yt + 6)), (P(cx), P(peak)), (P(x1 + 20), P(yt + 6))], fill=(120, 70, 60))
    d.polygon([(P(x0), P(yt + 6)), (P(cx), P(peak + 18)), (P(x1), P(yt + 6))], fill=(215, 60, 55))
    d.rectangle([P(x0), P(yt), P(x1), P(GY)], fill=(215, 60, 55))
    for k in range(int(x0) + 20, int(x1), 26):
        d.line([P(k), P(yt + 4), P(k), P(GY)], fill=(195, 50, 48), width=P(2))
    circ(d, cx, peak + 70, 22, (255, 250, 240))
    circ(d, cx, peak + 70, 16, (90, 50, 40))
    dx0, dx1, dy0 = cx - 62, cx + 62, 520
    d.rectangle([P(dx0 - 6), P(dy0 - 6), P(dx1 + 6), P(GY)], fill=(255, 250, 240))
    if door_open:
        d.rectangle([P(dx0), P(dy0), P(dx1), P(GY)], fill=(70, 40, 35))
        for sx in (-1, 1):                              # battants ouverts sur les côtés
            xa = cx + sx * 66
            d.rectangle([P(min(xa, xa + sx * 30)), P(dy0), P(max(xa, xa + sx * 30)), P(GY)],
                        fill=(230, 80, 70))
    else:
        d.rectangle([P(dx0), P(dy0), P(dx1), P(GY)], fill=(230, 80, 70))
        for a, b in [((dx0, dy0), (cx, GY)), ((cx, dy0), (dx0, GY)), ((cx, dy0), (dx1, GY)),
                     ((dx1, dy0), (cx, GY))]:
            d.line([P(a[0]), P(a[1]), P(b[0]), P(b[1])], fill=(255, 250, 240), width=P(5))
        d.line([P(cx), P(dy0), P(cx), P(GY)], fill=(255, 250, 240), width=P(5))
    return cx


def make_back():
    img = make_sky()
    d = ImageDraw.Draw(img)
    ell(d, 200, 640, 520, 170, (150, 210, 110))
    ell(d, 800, 650, 600, 160, (135, 200, 100))
    ell(d, 1250, 640, 380, 170, (150, 210, 110))
    d.rectangle([0, P(590), int(W * S), int(H * S)], fill=(120, 195, 90))
    tree(d, 70, 600)
    for i, x in enumerate(range(150, 270, 30)):
        sunflower(d, x, 610, 120 + 18 * (i % 2))
    haybale(d, 520, 610)
    d.rectangle([0, P(GY - 14), int(W * S), int(H * S)], fill=(105, 185, 80))
    ell(d, 500, 692, 700, 22, (215, 180, 120))              # chemin de terre
    rng = random.Random(4)
    for _ in range(45):
        x, y = rng.uniform(10, 1270), rng.uniform(640, 715)
        if 660 < y < 712 and abs(x - 500) < 560:
            continue
        c = rng.choice([(255, 255, 255), (255, 230, 90), (255, 160, 190)])
        for k in range(5):
            a = k * 2 * math.pi / 5
            circ(d, x + 4 * math.cos(a), y + 4 * math.sin(a), 3.5, c)
        circ(d, x, y, 2.5, (255, 200, 50))
    return img


BACK = make_back()


def fence(d):
    col, sh = (255, 250, 240), (205, 190, 175)
    for yy in (572, 610):
        d.rectangle([P(520), P(yy), P(845), P(yy + 12)], fill=col)
        d.rectangle([P(520), P(yy + 10), P(845), P(yy + 14)], fill=sh)
    for x in range(525, 850, 46):
        d.rectangle([P(x - 8), P(552), P(x + 8), P(GY - 4)], fill=col)
        d.polygon([(P(x - 8), P(552)), (P(x), P(542)), (P(x + 8), P(552))], fill=col)
        d.rectangle([P(x + 4), P(556), P(x + 8), P(GY - 4)], fill=sh)


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
INK = (60, 40, 50)


def eyes(d, x, y, sp, r, mood, t, seed=0):
    blink = ((t + seed) % 3.4) < 0.12
    for sx in (-1, 1):
        ex = x + sx * sp
        if mood in ("closed", "happy") or blink:
            d.arc([P(ex - r), P(y - r * 0.8), P(ex + r), P(y + r)], 200, 340, fill=INK, width=P(4))
        elif mood == "sad":
            ell(d, ex, y + 2, r * 0.8, r * 0.9, INK)
            circ(d, ex + 2, y - 2, r * 0.3, (255, 255, 255))
            d.line([P(ex - sx * r * 1.1), P(y - r * 1.6), P(ex + sx * r * 0.9), P(y - r * 2.2)],
                   fill=INK, width=P(3))
        else:
            ell(d, ex, y, r * 0.8, r, INK)
            circ(d, ex + 2, y - 3, r * 0.32, (255, 255, 255))


def pig(d, x, gy, t, mood="smile", talk=0.0, sq=1.0, step=0.0):
    """Rosie la petite cochonne (vue de face). Renvoie le point au-dessus de sa tête."""
    pink, dark, light = (255, 165, 190), (230, 125, 155), (255, 200, 215)
    for i, lx in enumerate((-38, -14, 14, 38)):               # pattes
        lift = 8 * max(0, math.sin(step + i * math.pi)) if step else 0
        d.rounded_rectangle([P(x + lx - 10), P(gy - 30 - lift), P(x + lx + 10), P(gy - lift)],
                            radius=P(5), fill=dark)
        d.rectangle([P(x + lx - 10), P(gy - 8 - lift), P(x + lx + 10), P(gy - lift)], fill=(170, 90, 110))
    by = gy - 58 * sq
    ell(d, x, by, 66, 44 * sq, pink)                          # corps
    ell(d, x, by + 12 * sq, 42, 24 * sq, light)
    d.arc([P(x + 56), P(by - 30), P(x + 82), P(by - 4)], 180, 90, fill=dark, width=P(4))  # queue
    hy = gy - 122 * sq
    for sx in (-1, 1):                                        # oreilles
        d.polygon([(P(x + sx * 18), P(hy - 34)), (P(x + sx * 46), P(hy - 62)), (P(x + sx * 44), P(hy - 18))],
                  fill=dark)
    circ(d, x, hy, 48, pink)                                  # tête
    for k in range(5):                                        # petite fleur sur l'oreille
        a = k * 2 * math.pi / 5
        circ(d, x + 40 + 8 * math.cos(a), hy - 46 + 8 * math.sin(a), 6, (255, 240, 120))
    circ(d, x + 40, hy - 46, 5, (255, 150, 60))
    circ(d, x - 32, hy + 14, 9, (255, 130, 160))
    circ(d, x + 32, hy + 14, 9, (255, 130, 160))
    eyes(d, x, hy - 12, 20, 8, mood, t)
    ell(d, x, hy + 12, 20, 14, dark)                          # groin
    ell(d, x - 7, hy + 12, 3.5, 5, (150, 70, 95))
    ell(d, x + 7, hy + 12, 3.5, 5, (150, 70, 95))
    my = hy + 34
    if talk > 0.02:
        ell(d, x, my, 10, 3 + 9 * talk, (140, 50, 70))
    elif mood == "sing":
        ell(d, x, my, 8, 8, (140, 50, 70))
    elif mood in ("happy", "sing2"):
        d.pieslice([P(x - 14), P(my - 8), P(x + 14), P(my + 12)], 0, 180, fill=(140, 50, 70))
    elif mood == "oops":
        ell(d, x, my + 2, 9, 4, (140, 50, 70))
    else:
        d.arc([P(x - 12), P(my - 8), P(x + 12), P(my + 6)], 20, 160, fill=INK, width=P(3))
    return x, hy - 66


def chick(d, x, gy, t, mood="smile", talk=0.0, k=1.0, hop=0.0, flap=0.0, seed=0):
    """Pip le poussin (et ses frères et sœurs, plus petits)."""
    y = gy - hop
    yel, dk = (255, 220, 70), (240, 185, 40)
    for sx in (-1, 1):                                        # pattes
        fx = x + sx * 12 * k
        d.line([P(fx), P(y - 12 * k), P(fx), P(y)], fill=(240, 140, 40), width=P(4 * k))
        d.line([P(fx - 8 * k), P(y), P(fx + 8 * k), P(y)], fill=(240, 140, 40), width=P(4 * k))
    cy = y - 44 * k
    for sx in (-1, 1):                                        # ailes
        a = flap * math.sin(t * 22 + seed)
        ell(d, x + sx * (36 + 4 * a) * k, cy + (6 - 8 * a) * k, 13 * k, 20 * k, dk)
    circ(d, x, cy, 38 * k, yel)
    for i, (dx, dy) in enumerate([(-6, -42), (0, -48), (7, -42)]):   # houppette
        ell(d, x + dx * k, cy + dy * k, 4 * k, 9 * k, dk)
    eyes(d, x, cy - 8 * k, 14 * k, 7 * k, mood, t, seed)
    by = cy + 6 * k
    if talk > 0.02:
        d.polygon([(P(x - 9 * k), P(by)), (P(x + 9 * k), P(by)), (P(x), P(by - 7 * k))], fill=(245, 130, 30))
        d.polygon([(P(x - 8 * k), P(by + 2)), (P(x + 8 * k), P(by + 2)), (P(x), P(by + (6 + 9 * talk) * k))],
                  fill=(245, 130, 30))
    else:
        d.polygon([(P(x - 9 * k), P(by - 2 * k)), (P(x + 9 * k), P(by - 2 * k)), (P(x), P(by + 10 * k))],
                  fill=(245, 130, 30))
    circ(d, x - 24 * k, cy + 6 * k, 6 * k, (255, 160, 140))
    circ(d, x + 24 * k, cy + 6 * k, 6 * k, (255, 160, 140))
    if mood == "sad":                                         # petite larme
        ty = cy + 4 * k + (t * 30 % 22) * k
        ell(d, x + 20 * k, ty, 3.5 * k, 5 * k, (110, 170, 255))
    return x, cy - 52 * k


def hen(d, x, gy, t, mood="smile", talk=0.0, flap=0.0, hop=0.0):
    """Maman Poule."""
    y = gy - hop
    wh, sh = (255, 252, 245), (225, 220, 210)
    for sx in (-1, 1):
        fx = x + sx * 18
        d.line([P(fx), P(y - 22), P(fx), P(y)], fill=(240, 140, 40), width=P(5))
        d.line([P(fx - 12), P(y), P(fx + 12), P(y)], fill=(240, 140, 40), width=P(5))
    by = y - 62
    for dx, dy, r in ((44, -30, 20), (58, -18, 18), (60, -40, 15)):   # queue derrière
        circ(d, x + dx, by + dy, r, sh)
    ell(d, x, by, 56, 46, wh)
    for sx in (-1, 1):
        a = flap * math.sin(t * 16)
        ell(d, x + sx * (52 + 6 * a), by + 2 - 10 * a, 16, 28, sh)
    hy = by - 58
    circ(d, x, hy, 32, wh)
    for dx, dy, r in [(-12, -30, 9), (0, -36, 11), (12, -30, 9)]:  # crête
        circ(d, x + dx, hy + dy, r, (235, 60, 60))
    eyes(d, x, hy - 6, 12, 6, mood, t, 1.7)
    if talk > 0.02:
        d.polygon([(P(x - 9), P(hy + 6)), (P(x + 9), P(hy + 6)), (P(x), P(hy - 2))], fill=(245, 150, 30))
        d.polygon([(P(x - 8), P(hy + 8)), (P(x + 8), P(hy + 8)), (P(x), P(hy + 14 + 9 * talk))],
                  fill=(245, 150, 30))
    else:
        d.polygon([(P(x - 10), P(hy + 4)), (P(x + 10), P(hy + 4)), (P(x), P(hy + 18))], fill=(245, 150, 30))
    ell(d, x, hy + 24, 6, 9, (235, 60, 60))                   # barbillon
    circ(d, x - 22, hy + 8, 6, (255, 170, 160))
    circ(d, x + 22, hy + 8, 6, (255, 170, 160))
    return x, hy - 50


def cow(d, x, cy, t, talk=0.0):
    """Tête de vache qui dépasse de la clôture."""
    wh, blk = (255, 255, 255), (50, 45, 50)
    for sx in (-1, 1):
        d.polygon([(P(x + sx * 20), P(cy - 34)), (P(x + sx * 34), P(cy - 62)), (P(x + sx * 38), P(cy - 30))],
                  fill=(240, 225, 180))
        ell(d, x + sx * 58, cy - 14, 22, 10, wh)
        ell(d, x + sx * 58, cy - 14, 14, 6, (255, 180, 190))
    ell(d, x, cy, 46, 48, wh)
    ell(d, x - 22, cy - 26, 16, 12, blk)
    ell(d, x + 28, cy - 4, 10, 14, blk)
    eyes(d, x, cy - 10, 18, 7, "smile", t, 0.9)
    ell(d, x, cy + 30, 36, 22, (255, 180, 195))
    ell(d, x - 12, cy + 26, 4, 6, (190, 100, 120))
    ell(d, x + 12, cy + 26, 4, 6, (190, 100, 120))
    if talk > 0.02:
        ell(d, x, cy + 42, 10, 2 + 6 * talk, (150, 60, 80))
    return x, cy - 66


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
    for base, y, k, sp in [(300, 300, 0.8, 10), (900, 270, 0.7, 14), (1400, 330, 0.6, 8)]:
        plain_cloud(d, (base + t * sp) % 1580 - 150, y, k)
    barn(d, t >= 18.6)

    # vache : sort de derrière la clôture, dit « Moo? », puis redescend
    cu = min(back((t - 14.0) / 0.45), ease((16.4 - t) / 0.5))
    ANCHORS.pop("cow", None)
    if cu > 0.01:
        cx_, cy_ = 720, lerp(640, 512, cu)
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ctop = cow(ImageDraw.Draw(layer), cx_, cy_ + 3 * math.sin(t * 5), t, talking("cow", t))
        mask = layer.split()[3]
        ImageDraw.Draw(mask).rectangle([0, P(GY - 14), img.width, img.height], fill=0)
        img.paste(layer, (0, 0), mask)
        d = ImageDraw.Draw(img)
        ANCHORS["cow"] = (cx_, ctop[1])
    fence(d)

    # ---- Rosie
    rx = path(t, [(0, 290), (11.3, 290), (12.5, 470), (16.2, 470), (17.4, 680)])
    walking = 11.3 < t < 12.5 or 16.2 < t < 17.4
    rmood, sq, hop = "smile", 1.0, 0.0
    if t < 3.2:
        rmood, hop = "sing", bounce(t, 5.5, 16)
        rx += 10 * math.sin(t * 3)
    elif 4.8 < t < 11.3:
        rmood = "sad" if 9.6 < t < 11.3 else "smile"
    elif 12.6 < t < 14.2:
        rmood, sq = "sing", 1.0 + 0.06 * math.sin(t * 10)        # elle crie très fort
    elif 14.2 <= t < 16.2:
        rmood = "oops"
        if t < 14.6:
            hop = 30 * math.sin(math.pi * (t - 14.2) / 0.4)      # sursaut
    elif 17.4 <= t < 20.6:
        rmood, hop = "sing", bounce(t, 6, 12)
    elif t >= 20.6:
        rmood, hop = "happy", bounce(t, 6.5, 18) if 21.6 < t < 26.5 else 0
    if walking:
        hop = bounce(t, 9, 8)
    rtop = pig(d, rx, GY - hop, t, rmood, talking("rosie", t), sq, t * 12 if walking else 0)

    # ---- Pip
    px = path(t, [(0, 450), (11.5, 450), (12.7, 570), (16.4, 570), (17.6, 760), (19.7, 760),
                  (20.4, 790)])
    pmood, phop, flap = "sad", 0.0, 0.0
    if 12.5 < t < 18.0:
        pmood = "smile"
    if 17.6 <= t < 19.7:
        pmood, phop, flap = "closed", bounce(t, 7, 10), 1.0
    if t >= 19.7:
        pmood, flap = "happy", 1.0 if t < 21 else 0.0
        phop = bounce(t, 7, 14) if 21.6 < t < 26.5 else 0
    if 11.5 < t < 12.7 or 16.4 < t < 17.6:
        phop = bounce(t, 10, 8)
    if t < 3.0:
        phop = 0
    ptop = chick(d, px, GY - 2 - phop, t, pmood, talking("pip", t), 1.0, 0, flap)

    # ---- notes de musique quand Rosie chante
    for t0, t1 in [(0, 3.2), (12.6, 14.2), (17.4, 20.6)]:
        if t0 <= t < t1:
            for i in range(4):
                g = ((t - t0) * 0.8 + i * 0.25) % 1
                note_sym(d, rx + 50 + 50 * g + 10 * math.sin(g * 9 + i), rtop[1] + 20 - 120 * g,
                         [(150, 90, 220), (240, 90, 140), (60, 140, 230), (60, 170, 90)][i])

    # ---- Maman Poule et les petits
    if t >= 18.8:
        hx = path(t, [(18.8, 990), (20.2, 860)])
        hhop = bounce(t, 9, 10) if t < 20.2 else (bounce(t, 6, 12) if 21.6 < t < 26.5 else 0)
        htop = hen(d, hx, GY - hhop, t, "happy" if t > 20.2 else "smile", talking("mama", t),
                   1.0 if 19.6 < t < 21.0 else 0.0)
        ANCHORS["mama"] = (hx, htop[1])
    if t >= 21.6:
        for i, (bx0, bx1) in enumerate([(990, 935), (990, 975), (990, 1015)]):
            tt = t - 21.6 - i * 0.35
            if tt < 0:
                continue
            bx = lerp(bx0, bx1, ease(tt / 0.8))
            chick(d, bx, GY - 2 - bounce(t + i, 7, 12), t, "happy", 0, 0.5, 0, 1.0, seed=i * 1.3)
    if 20.2 < t < 26.5:                                       # cœurs
        for i in range(5):
            g = ((t - 20.2) * 0.5 + i * 0.2) % 1
            heart(d, 825 + 40 * math.sin(i * 2.1 + g * 5), 520 - 180 * g, 9 + 4 * math.sin(math.pi * g),
                  [(255, 110, 150), (255, 150, 190), (240, 80, 120)][i % 3])
    if 20.0 < t < 21.6:
        splash_stars(d, 830, 560, (t - 20.0) / 1.6)
    if 23.8 < t < 25.6:
        splash_stars(d, rx, rtop[1] + 40, (t - 23.8) / 1.8, 10, 60, (255, 160, 200))

    ANCHORS["rosie"] = (rx, rtop[1])
    ANCHORS["pip"] = (px, ptop[1])
    return img, rx, GY, ANCHORS["pip"]


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
