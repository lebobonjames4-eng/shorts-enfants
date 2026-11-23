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


def star(d, x, y, r, rot, col):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = rot + i * math.pi / 5 - math.pi / 2
        pts.append((P(x + rr * math.cos(a)), P(y + rr * math.sin(a))))
    d.polygon(pts, fill=col)


def path(t, keys):
    if t <= keys[0][0]:
        return keys[0][1], keys[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(keys, keys[1:]):
        if t0 <= t < t1:
            u = ease((t - t0) / (t1 - t0))
            return lerp(x0, x1, u), lerp(y0, y1, u)
    return keys[-1][1], keys[-1][2]


def hop(t, t0, t1, a, b, h):
    u = clamp01((t - t0) / (t1 - t0))
    return lerp(a[0], b[0], u), lerp(a[1], b[1], u) - h * math.sin(math.pi * u)


# ---------------------------------------------------------------- décor : petite planète dans l'espace
INK = (30, 30, 55)
GY = 612                                   # sol
SKY_TOP, SKY_BOT = (22, 18, 64), (118, 78, 168)
GROUND, GROUND_D, GROUND_L = (196, 160, 232), (162, 124, 205), (225, 200, 250)
ANCHORS = {}


def sky_col(y):
    u = int(clamp01(y / GY) * 8) / 8
    return lerpc(SKY_TOP, SKY_BOT, u)


def make_sky():
    img = Image.new("RGB", (int(W * S), int(H * S)))
    d = ImageDraw.Draw(img)
    h = int(H * S)
    for y in range(h):
        d.line([(0, y), (int(W * S), y)], fill=sky_col(y / S))
    return img


STARS = [(random.Random(i).uniform(0, 1280), random.Random(i + 500).uniform(0, 560),
          random.Random(i + 900).uniform(0, 6.28)) for i in range(120)]


def stars(d, t, w, h, seed_list=STARS):
    for x, y, ph in seed_list:
        if x > w or y > h:
            continue
        tw = 0.5 + 0.5 * math.sin(t * 2.2 + ph)
        if tw > 0.8:
            star(d, x, y, 7, 0, (255, 250, 200))
        else:
            circ(d, x, y, 2.5, (230, 225, 255) if tw > 0.3 else (160, 150, 210))


def ringed_planet(d, x, y, r):
    ell(d, x, y, r * 1.8, r * 0.45, (255, 200, 120))           # anneau (arrière)
    circ(d, x, y, r, (255, 140, 170))
    d.chord([P(x - r), P(y - r), P(x + r), P(y + r)], 100, 260, fill=(240, 115, 150))
    ell(d, x + 6, y - r * 0.35, r * 0.7, r * 0.12, (255, 175, 195))
    ell(d, x - 4, y + r * 0.3, r * 0.8, r * 0.1, (230, 105, 145))
    # anneau (devant)
    d.chord([P(x - r * 1.8), P(y - r * 0.45), P(x + r * 1.8), P(y + r * 0.45)], 0, 180, fill=(255, 200, 120))
    d.chord([P(x - r * 1.35), P(y - r * 0.25), P(x + r * 1.35), P(y + r * 0.25)], 0, 180, fill=(255, 140, 170))


def moon(d, x, y, r):
    circ(d, x, y, r, (120, 215, 220))
    circ(d, x - r * 0.3, y - r * 0.2, r * 0.25, (95, 185, 195))
    circ(d, x + r * 0.35, y + r * 0.3, r * 0.18, (95, 185, 195))


def crater(d, x, y, rx):
    ell(d, x, y, rx, rx * 0.32, GROUND_D)
    ell(d, x, y + rx * 0.06, rx * 0.8, rx * 0.22, (178, 140, 220))
    d.arc([P(x - rx), P(y - rx * 0.32), P(x + rx), P(y + rx * 0.32)], 200, 340, fill=GROUND_L, width=P(3))


def crystal(d, x, y, h, col):
    d.polygon([(P(x - 10), P(y)), (P(x - 8), P(y - h * 0.7)), (P(x), P(y - h)), (P(x + 8), P(y - h * 0.7)),
               (P(x + 10), P(y))], fill=col)
    d.line([P(x), P(y - h + 4), P(x), P(y - 2)], fill=(255, 255, 255), width=P(2))


def make_ground():
    img = Image.new("RGBA", (int(W * S), int(H * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ell(d, 260, 640, 520, 110, (150, 115, 195))
    ell(d, 1080, 640, 560, 120, (140, 105, 188))
    d.rectangle([0, P(GY - 4), int(W * S), int(H * S)], fill=GROUND)
    ell(d, 640, GY - 2, 900, 16, GROUND)
    for x, y, rx in [(150, 650, 60), (430, 690, 44), (560, 640, 30), (940, 668, 54), (1180, 640, 36),
                     (760, 700, 34), (300, 625, 22), (1060, 704, 28)]:
        crater(d, x, y, rx)
    for x, h, col in [(420, 40, (120, 230, 255)), (436, 26, (170, 245, 255)), (905, 44, (255, 150, 210)),
                      (922, 28, (255, 190, 230)), (1220, 38, (140, 255, 190)), (90, 34, (255, 230, 120))]:
        crystal(d, x, GY + 8, h, col)
    rng = random.Random(4)
    for _ in range(40):
        x, y = rng.uniform(0, 1280), rng.uniform(GY + 10, 718)
        circ(d, x, y, rng.uniform(2, 4), GROUND_L if rng.random() < 0.5 else GROUND_D)
    return img


SKY = make_sky()
_d = ImageDraw.Draw(SKY)
ringed_planet(_d, 520, 330, 40)
moon(_d, 880, 290, 24)
ringed_planet(_d, 1130, 150, 30)
moon(_d, 200, 170, 18)
GROUND_IMG = make_ground()
BASE = SKY.copy()
BASE.paste(GROUND_IMG, (0, 0), GROUND_IMG)


# ---------------------------------------------------------------- personnages
BODY, BODY_D = (255, 140, 70), (225, 105, 50)
HEAD, HEAD_D = (205, 228, 245), (160, 190, 215)
SCREEN, GLOW = (32, 42, 88), (110, 240, 255)


def robot(d, x, fy, t, mood="smile", talk=0.0, sq=1.0, f=1, arms="down", k=1.0, crank=0.0):
    """Zip le petit robot (x, fy = pieds). Renvoie le point au-dessus de l'antenne."""
    sh = 30 * k * sq
    # jambes-ressorts
    for sx in (-1, 1):
        lx = x + sx * 16 * k
        pts = [(P(lx), P(fy - 6 * k))]
        for i in range(1, 7):
            pts.append((P(lx + (7 * k if i % 2 else -7 * k)), P(fy - 6 * k - sh * i / 6)))
        d.line(pts, fill=(140, 150, 170), width=max(1, P(4 * k)))
        ell(d, lx + 3 * f * k, fy - 4 * k, 15 * k, 6 * k, (90, 100, 130))
    bb = fy - 6 * k - sh
    bt = bb - 52 * k
    sy = (bb + bt) / 2 - 8 * k
    # bras (derrière si "down")
    def arm(sx, hx, hy):
        d.line([P(x + sx * 30 * k), P(sy), P(hx), P(hy)], fill=(140, 150, 170), width=max(1, P(6 * k)))
        circ(d, hx, hy, 8 * k, (90, 100, 130))
    hands = []
    for sx in (-1, 1):
        if arms == "down":
            hands.append((sx, x + sx * 44 * k, sy + 26 * k))
        elif arms == "up":
            hands.append((sx, x + sx * 50 * k, sy - 44 * k + 6 * math.sin(t * 12 + sx) * k))
        elif arms == "push":
            hands.append((sx, x + f * 62 * k, sy + (-6 if sx < 0 else 8) * k))
        elif arms == "crank":
            if sx == f:
                hands.append((sx, x + f * 58 * k + 12 * k * math.cos(crank), sy + 12 * k * math.sin(crank)))
            else:
                hands.append((sx, x + sx * 44 * k, sy + 26 * k))
    # corps
    d.rounded_rectangle([P(x - 32 * k), P(bt), P(x + 32 * k), P(bb)], radius=P(12 * k), fill=BODY)
    d.rectangle([P(x + 18 * k), P(bt + 8 * k), P(x + 26 * k), P(bb - 8 * k)], fill=BODY_D)
    for i, col in enumerate([(255, 80, 90), (255, 220, 80), (110, 220, 255)]):
        circ(d, x - 14 * k + i * 14 * k, bt + 26 * k, 5 * k, col)
    d.rounded_rectangle([P(x - 16 * k), P(bt + 36 * k), P(x + 16 * k), P(bt + 44 * k)], radius=P(3 * k),
                        fill=BODY_D)
    for sx, hx, hy in hands:
        arm(sx, hx, hy)
    # tête
    hb = bt - 4 * k
    ht = hb - 56 * k
    hx, hy = x, (hb + ht) / 2
    # antenne
    ax = x + 3 * k * math.sin(t * 6)
    d.line([P(x), P(ht), P(ax), P(ht - 20 * k)], fill=(140, 150, 170), width=max(1, P(3 * k)))
    circ(d, ax, ht - 22 * k, 7 * k, (255, 80, 110))
    circ(d, ax - 2 * k, ht - 24 * k, 2.5 * k, (255, 200, 210))
    for sx in (-1, 1):
        d.rounded_rectangle([P(x + sx * 40 * k - 6 * k), P(hy - 12 * k), P(x + sx * 40 * k + 6 * k),
                             P(hy + 12 * k)], radius=P(4 * k), fill=(140, 150, 170))
    d.rounded_rectangle([P(x - 38 * k), P(ht), P(x + 38 * k), P(hb)], radius=P(16 * k), fill=HEAD)
    d.rectangle([P(x - 34 * k), P(hb - 8 * k), P(x + 34 * k), P(hb - 4 * k)], fill=HEAD_D)
    d.rounded_rectangle([P(x - 28 * k), P(ht + 8 * k), P(x + 28 * k), P(hb - 12 * k)], radius=P(9 * k),
                        fill=SCREEN)
    # visage sur l'écran
    ex0 = x + 3 * f * k
    ey = ht + 22 * k
    for ex in (ex0 - 11 * k, ex0 + 11 * k):
        if mood == "happy":
            d.arc([P(ex - 6 * k), P(ey - 4 * k), P(ex + 6 * k), P(ey + 6 * k)], 200, 340, fill=GLOW,
                  width=max(1, P(3 * k)))
        elif mood in ("oops", "strain"):
            sgn = 1 if ex < ex0 else -1
            d.line([P(ex - 5 * k), P(ey - 4 * k), P(ex + 5 * k * sgn * 0 + 4 * k), P(ey)], fill=GLOW,
                   width=max(1, P(3 * k)))
            d.line([P(ex - 5 * k), P(ey + 4 * k), P(ex + 4 * k), P(ey)], fill=GLOW, width=max(1, P(3 * k)))
        elif (t % 3.3) < 0.12:
            d.line([P(ex - 6 * k), P(ey), P(ex + 6 * k), P(ey)], fill=GLOW, width=max(1, P(3 * k)))
        else:
            d.rectangle([P(ex - 5 * k), P(ey - 6 * k), P(ex + 5 * k), P(ey + 6 * k)], fill=GLOW)
            d.rectangle([P(ex - 2 * k), P(ey - 5 * k), P(ex + 1 * k), P(ey - 2 * k)], fill=(255, 255, 255))
            if mood == "worried":
                d.line([P(ex - 6 * k), P(ey - 11 * k), P(ex + 6 * k), P(ey - 9 * k + (3 if ex > ex0 else -3) * k)],
                       fill=GLOW, width=max(1, P(2 * k)))
    my = ht + 36 * k
    if talk > 0.02:
        ell(d, ex0, my, 7 * k, (2 + 5 * talk) * k, GLOW)
    elif mood in ("happy", "smile"):
        d.arc([P(ex0 - 8 * k), P(my - 6 * k), P(ex0 + 8 * k), P(my + 4 * k)], 20, 160, fill=GLOW,
              width=max(1, P(3 * k)))
    elif mood == "oops":
        ell(d, ex0, my, 5 * k, 4 * k, GLOW)
    else:
        d.line([P(ex0 - 6 * k), P(my), P(ex0 + 6 * k), P(my)], fill=GLOW, width=max(1, P(3 * k)))
    for sx in (-1, 1):
        d.rectangle([P(ex0 + sx * 20 * k - 3 * k), P(my - 4 * k), P(ex0 + sx * 20 * k + 3 * k), P(my)],
                    fill=(255, 130, 170))
    return (x, ht - 32 * k)


GREEN, GREEN_D, GREEN_L = (125, 215, 110), (90, 175, 85), (185, 240, 165)


def alien(d, x, fy, t, mood="smile", talk=0.0, f=1, k=1.0, arms="down", sq=1.0, tear=False):
    """Blip le petit extraterrestre (x, fy = pieds). Renvoie le point au-dessus des antennes."""
    r = 40 * k
    cy = fy - 6 * k - r * sq
    for sx in (-1, 1):
        ell(d, x + sx * 16 * k + 3 * f * k, fy - 5 * k, 13 * k, 6 * k, GREEN_D)
    # antennes
    for sx in (-1, 1):
        bx = x + sx * 26 * k + 3 * k * math.sin(t * 5 + sx)
        by = cy - r * sq - 22 * k
        d.line([P(x + sx * 12 * k), P(cy - r * sq + 8 * k), P(bx), P(by)], fill=GREEN_D, width=max(1, P(4 * k)))
        circ(d, bx, by, 7 * k, (255, 225, 90))
    # bras
    def nub(hx, hy):
        circ(d, hx, hy, 9 * k, GREEN_D)
    if arms == "up":
        nub(x - 44 * k, cy - 30 * k + 4 * math.sin(t * 12) * k)
        nub(x + 44 * k, cy - 30 * k - 4 * math.sin(t * 12) * k)
    elif arms == "point":
        nub(x - f * 40 * k, cy + 14 * k)
        nub(x + f * 52 * k, cy - 22 * k)
    elif arms == "push":
        nub(x + f * 46 * k, cy - 4 * k)
        nub(x + f * 44 * k, cy + 12 * k)
    else:
        nub(x - 40 * k, cy + 14 * k)
        nub(x + 40 * k, cy + 14 * k)
    ell(d, x, cy, r, r * sq, GREEN)
    ell(d, x + 4 * f * k, cy + 16 * k * sq, 24 * k, 16 * k * sq, GREEN_L)
    for dx, dy in [(-24, -18), (22, -26), (-6, -30)]:
        circ(d, x + dx * k, cy + dy * k * sq, 3.5 * k, GREEN_D)
    # yeux
    for ex in (x - 13 * k + 5 * f * k, x + 13 * k + 5 * f * k):
        ey = cy - 8 * k
        if mood == "happy":
            ell(d, ex, ey, 10 * k, 11 * k, (255, 255, 255))
            d.arc([P(ex - 7 * k), P(ey - 4 * k), P(ex + 7 * k), P(ey + 6 * k)], 200, 340, fill=INK,
                  width=max(1, P(3 * k)))
            continue
        if mood == "oops":
            ell(d, ex, ey, 11 * k, 13 * k, (255, 255, 255))
            circ(d, ex, ey, 4 * k, INK)
            continue
        if (t % 2.9) < 0.12:
            d.line([P(ex - 9 * k), P(ey), P(ex + 9 * k), P(ey)], fill=INK, width=max(1, P(3 * k)))
            continue
        ell(d, ex, ey, 10 * k, 12 * k, (255, 255, 255))
        py = ey + (3 if mood == "sad" else 0) * k
        circ(d, ex + 2 * f * k, py, 6 * k, INK)
        circ(d, ex + 4 * f * k, py - 3 * k, 2 * k, (255, 255, 255))
        if mood == "sad":
            inner = 1 if ex < x + 5 * f * k else -1
            d.line([P(ex - 9 * k), P(ey - 16 * k + inner * 4 * k), P(ex + 9 * k), P(ey - 16 * k - inner * 4 * k)],
                   fill=GREEN_D, width=max(1, P(3 * k)))
    my = cy + 12 * k
    mx = x + 5 * f * k
    if talk > 0.02:
        ell(d, mx, my, 6 * k, (2 + 6 * talk) * k, (150, 50, 80))
    elif mood == "sad":
        d.arc([P(mx - 8 * k), P(my), P(mx + 8 * k), P(my + 8 * k)], 200, 340, fill=INK, width=max(1, P(3 * k)))
    elif mood == "oops":
        ell(d, mx, my + 2 * k, 5 * k, 6 * k, (150, 50, 80))
    else:
        d.arc([P(mx - 9 * k), P(my - 6 * k), P(mx + 9 * k), P(my + 5 * k)], 20, 160, fill=INK,
              width=max(1, P(3 * k)))
    for sx in (-1, 1):
        circ(d, mx + sx * 24 * k, my - 2 * k, 5 * k, (255, 150, 160))
    if tear:
        g = (t * 0.9) % 1
        ell(d, x - 15 * k + 5 * f * k, cy + 6 * k + g * 22 * k, 3.5 * k, 5 * k, (150, 210, 255))
    return (x, cy - r * sq - 34 * k)


# ---------------------------------------------------------------- fusée
RED, RED_D, WHITE = (240, 70, 80), (200, 45, 60), (245, 245, 252)
KEY, KEY_D = (255, 205, 60), (220, 160, 30)
RX = 790                                   # position de la fusée au sol


def rocket_back(d, x, by):
    """Dôme vitré (fond), dessiné avant les passagers."""
    d.pieslice([P(x - 46), P(by - 186), P(x + 46), P(by - 94)], 180, 360, fill=(175, 220, 255))


def rocket(d, x, by, t, lights=0, hatch=0.0, key_ang=0.0, flame=0.0):
    """Fusée (x, by = bas des pieds). by-140 = haut du corps, dôme au-dessus."""
    # flamme
    if flame > 0.02:
        fl = flame * (1 + 0.25 * math.sin(t * 40))
        ell(d, x, by - 10 + 40 * fl, 26 * min(1, flame * 2), 46 * fl, (255, 150, 50))
        ell(d, x, by - 12 + 30 * fl, 16 * min(1, flame * 2), 32 * fl, (255, 230, 110))
    # pieds
    for sx in (-1, 1):
        d.line([P(x + sx * 30), P(by - 26), P(x + sx * 46), P(by - 4)], fill=(150, 150, 175), width=P(6))
        ell(d, x + sx * 48, by - 3, 12, 4, (120, 120, 150))
    # ailerons
    for sx in (-1, 1):
        d.polygon([(P(x + sx * 44), P(by - 92)), (P(x + sx * 74), P(by - 40)), (P(x + sx * 72), P(by - 14)),
                   (P(x + sx * 44), P(by - 34))], fill=RED)
        d.polygon([(P(x + sx * 44), P(by - 60)), (P(x + sx * 72), P(by - 30)), (P(x + sx * 72), P(by - 14)),
                   (P(x + sx * 44), P(by - 34))], fill=RED_D)
    # tuyère
    d.polygon([(P(x - 24), P(by - 30)), (P(x + 24), P(by - 30)), (P(x + 30), P(by - 14)), (P(x - 30), P(by - 14))],
              fill=(150, 150, 175))
    # corps
    d.rounded_rectangle([P(x - 50), P(by - 142), P(x + 50), P(by - 26)], radius=P(22), fill=WHITE)
    d.rectangle([P(x + 30), P(by - 130), P(x + 40), P(by - 38)], fill=(215, 218, 235))
    d.rectangle([P(x - 50), P(by - 112), P(x + 50), P(by - 100)], fill=RED)
    for i in range(3):
        on = lights > i
        lx = x - 24 + 24 * i
        if on:
            circ(d, lx, by - 64, 13, (255, 245, 170))
        circ(d, lx, by - 64, 9, (255, 220, 80) if on else (110, 115, 145))
        circ(d, lx - 3, by - 67, 3, (255, 255, 230) if on else (150, 155, 185))
    # trappe + clé
    hx, hy = x - 50, by - 82
    if hatch <= 0:
        d.rectangle([P(hx + 4), P(hy - 12), P(hx + 20), P(hy + 12)], fill=(215, 218, 235))
        circ(d, hx + 16, hy, 2, (150, 150, 175))
    else:
        d.rectangle([P(hx + 4), P(hy - 12), P(hx + 20), P(hy + 12)], fill=(60, 60, 90))
        w = 16 * (1 - hatch * 0.9)
        d.rectangle([P(hx + 4 - w), P(hy - 13), P(hx + 4), P(hy + 13)], fill=(215, 218, 235))
        s = ease(hatch)
        L = 30 * s
        d.rectangle([P(hx - L), P(hy - 4), P(hx + 8), P(hy + 4)], fill=KEY_D)
        bw = 22 * abs(math.cos(key_ang)) * s + 4
        bx = hx - L - 10
        for sy in (-1, 1):
            ell(d, bx, hy + sy * 13 * s, bw * 0.55, 12 * s, KEY)
            ell(d, bx, hy + sy * 13 * s, bw * 0.25, 5 * s, KEY_D)
        circ(d, bx, hy, 7 * s, KEY)
    # anneau du dôme + reflet
    d.rounded_rectangle([P(x - 54), P(by - 146), P(x + 54), P(by - 134)], radius=P(6), fill=(150, 150, 175))
    d.arc([P(x - 36), P(by - 178), P(x + 36), P(by - 110)], 200, 250, fill=(255, 255, 255), width=P(5))
    circ(d, x, by - 192, 6, RED)


def smoke(d, x, y, g, n=5, col=(235, 230, 245)):
    if not 0 <= g < 1:
        return
    for i in range(n):
        a = math.pi * (i + 0.5) / n
        r = 20 + 70 * g
        circ(d, x - math.cos(a) * r, y - math.sin(a) * r * 0.35, (18 + 10 * g) * (1 - g * 0.6), col)


def firework(d, x, y, g, col):
    if not 0 <= g < 1:
        return
    if g < 0.25:                                    # la fusée qui monte
        u = g / 0.25
        circ(d, x, y + 120 * (1 - u), 4, (255, 240, 200))
        return
    u = (g - 0.25) / 0.75
    r = 20 + 70 * ease(u)
    for i in range(12):
        a = i * math.pi / 6
        px, py = x + math.cos(a) * r, y + math.sin(a) * r + 20 * u * u
        rr = 7 * (1 - u) + 1.5
        circ(d, px, py, rr, col)
        circ(d, x + math.cos(a) * r * 0.6, y + math.sin(a) * r * 0.6 + 14 * u * u, rr * 0.6, (255, 255, 220))


FW_COLS = [(255, 110, 150), (110, 230, 255), (255, 220, 90), (160, 255, 140), (200, 140, 255)]
# (t0, x, y) en unités monde ; ils éclatent dans le ciel visible pendant le vol
FIREWORKS = [(23.3, 560, 150), (23.9, 900, 110), (24.4, 640, 80), (24.9, 860, 200), (25.4, 540, 220),
             (25.9, 760, 70), (26.4, 920, 150), (26.8, 600, 130)]


def heart(d, hx, hy, r, col=(255, 110, 150)):
    circ(d, hx - r * 0.55, hy, r * 0.62, col)
    circ(d, hx + r * 0.55, hy, r * 0.62, col)
    d.polygon([(P(hx - r * 1.15), P(hy + r * 0.15)), (P(hx + r * 1.15), P(hy + r * 0.15)),
               (P(hx), P(hy + r * 1.3))], fill=col)


def sun(d, t, cx=1130, cy=120):          # gardé pour compatibilité (pas de soleil dans l'espace)
    pass


def plain_cloud(d, x, y, k):             # gardé pour compatibilité
    pass


# ---------------------------------------------------------------- frame
ZX0, BX0 = 500, 615                       # Zip et Blip au début
PUSH_X, CRANK_X, LAND_X = 688, 662, 498
BLIP_SIDE = 585


def rocket_pos(t):
    """Bas de la fusée (x, y)."""
    if t < 21.9:
        x, y = RX, GY
        if 8.3 < t < 9.0 or 11.7 < t < 13.9:
            x += 2 * math.sin(t * 45)
        if 13.9 < t < 14.8:
            x += 6 * math.sin(t * 30) * (14.8 - t)
        if 20.2 < t:
            x += 3 * math.sin(t * 50)
        return x, y
    x, y = path(t, [(21.9, RX, GY), (23.5, 720, 330)])
    if t >= 23.5:
        a = (t - 23.5) * 1.1
        x = 720 + 90 * math.sin(a)
        y = 330 + 14 * math.sin(a * 2.3)
    return x, y


def cam(t):
    """Centre x de la caméra verticale : elle suit la fusée quand elle décolle."""
    if t < 22.0:
        return 672
    return lerp(672, 720, ease((t - 22.0) / 1.5))


def cam_y(t):
    """Haut de la fenêtre verticale (unités monde) : la caméra monte avec la fusée."""
    return lerp(240, 60, ease((t - 22.1) / 1.5))


def scene(t, with_sun=True):
    img = BASE.copy()
    d = ImageDraw.Draw(img)
    stars(d, t, 1280, 560)

    # ---------------- Zip
    zx, zfy, zsq, zmood, zf, zarms, zk, crank = ZX0, GY, 1.0, "smile", 1, "down", 1.0, 0.0
    if t < 7.0:                                    # il rebondit sur ses ressorts
        ph = (t + 0.3) % 1.0
        zfy = GY - 80 * math.sin(math.pi * ph)
        zsq = 1.3 if 0.08 < ph < 0.6 else (0.65 if ph < 0.06 or ph > 0.94 else 1.0)
        zmood, zarms = "happy", ("up" if 0.1 < ph < 0.7 else "down")
        zf = 1
    elif t < 9.6:
        zmood = "worried" if t > 7.6 else "smile"
        zsq = 1 - 0.3 * math.sin(math.pi * clamp01((t - 7.0) / 0.15))
    elif t < 10.4:
        zx, zfy = hop(t, 9.6, 10.4, (ZX0, GY), (PUSH_X, GY), 130)
        zsq, zmood = 1.25, "happy"
    elif t < 11.6:
        zx = PUSH_X
        zsq = 1 - 0.3 * math.sin(math.pi * clamp01((t - 10.4) / 0.15))
        zarms = "push" if t > 11.2 else "down"
    elif t < 13.9:                                 # il pousse, pousse...
        zx = PUSH_X + 2 * math.sin(t * 40)
        zarms, zmood = "push", "strain"
    elif t < 14.1:                                 # le ressort se tasse...
        zx, zarms, zmood = PUSH_X, "push", "strain"
        zsq = lerp(1.0, 0.4, (t - 13.9) / 0.2)
    elif t < 15.0:                                 # ...boing ! il est projeté en arrière
        zx, zfy = hop(t, 14.1, 15.0, (PUSH_X, GY), (LAND_X, GY), 170)
        zsq, zarms, zmood = 1.35, "up", "oops"
    elif t < 16.3:
        zx = LAND_X
        zsq = 1 - 0.35 * math.sin(math.pi * clamp01((t - 15.0) / 0.25))
        zmood = "oops"
    elif t < 17.0:
        zx, zmood = LAND_X, "smile"
    elif t < 17.8:
        zx, zfy = hop(t, 17.0, 17.8, (LAND_X, GY), (CRANK_X, GY), 120)
        zsq, zmood = 1.25, "happy"
    elif t < 20.6:                                 # il remonte la clé
        zx = CRANK_X
        zarms, zmood = "crank", "happy"
        crank = (t - 17.9) * 2 * math.pi * 0.9 if t > 17.9 else 0
        if t > 20.2:
            zarms = "up"
    zriding = t >= 20.6
    # ---------------- Blip
    bx, bfy, bmood, bf, barms, btear, bsq = BX0, GY, "sad", -1, "down", True, 1.0
    if t < 7.2:
        bf = -1
        bsq = 1 + 0.03 * math.sin(t * 3)
    elif t < 9.0:
        bf, barms = 1, ("point" if t < 8.6 else "down")
        btear = t < 8.3
    elif t < 9.6:
        bx = lerp(BX0, BLIP_SIDE, ease((t - 9.0) / 0.6))
        bfy = GY - 8 * abs(math.sin(t * 14))
        bf, btear = -1, False
    elif t < 11.6:
        bx, bf, btear = BLIP_SIDE, 1, False
        bmood = "smile" if t > 10.0 else "sad"
    elif t < 14.1:
        bx, bf, btear, bmood, barms = BLIP_SIDE, 1, False, "happy", "up"
    elif t < 16.1:
        bx, bf, btear, bmood = BLIP_SIDE, (1 if t < 14.5 else -1), False, "oops"
    elif t < 17.0:
        bx, bf, btear, bmood, barms = BLIP_SIDE, 1, False, "happy", "point"
    elif t < 17.8:
        bx = lerp(BLIP_SIDE, 582, ease((t - 17.0) / 0.8))
        bfy = GY - 8 * abs(math.sin(t * 14))
        bf, btear, bmood = 1, False, "happy"
    elif t < 20.6:
        bx, bf, btear, bmood, barms = 582, 1, False, "happy", ("push" if t < 20.2 else "up")
    briding = t >= 20.6

    # ---------------- fusée
    rx, rby = rocket_pos(t)
    lights = sum(1 for lt in (18.6, 19.3, 20.0) if t >= lt)
    hatch = ease((t - 14.3) / 0.3) if t > 14.3 else 0.0
    key_ang = crank * 0.5
    flame = 0.0
    if t > 21.2:
        flame = 0.4 + 0.6 * ease((t - 21.6) / 0.6)
    elif 8.3 < t < 9.0:                            # petit pfft raté
        flame = 0.15 * math.sin(math.pi * (t - 8.3) / 0.7)

    # passagers dans le dôme
    rocket_back(d, rx, rby)
    zride = (rx - 20, rby - 110)
    bride = (rx + 22, rby - 140)
    if t >= 20.6:
        u = clamp01((t - 20.6) / 0.6)
        if u < 1:
            zx, zfy = hop(t, 20.6, 21.2, (CRANK_X, GY), zride, 120)
            bx, bfy = hop(t, 20.65, 21.25, (582, GY), bride, 140)
        else:
            zx, zfy = zride
            bx, bfy = bride
        zk = lerp(1.0, 0.55, ease(u))
        zarms, zmood, zsq, zf = "up" if u >= 1 else "down", "happy", 1.0, 1
        bk = lerp(1.0, 0.6, ease(u))
        bmood, bf, barms, btear = "happy", -1, "down", False
        if t > 21.25:
            zfy += 3 * math.sin(t * 9)
            bfy += 3 * math.sin(t * 9 + 1)
        ztop = robot(d, zx, zfy, t, zmood, talking("zip", t), 1.0, zf, "down", zk)
        btop = alien(d, bx, bfy, t, bmood, talking("blip", t), bf, bk, "down")
    rocket(d, rx, rby, t, lights, hatch, key_ang, flame)
    if t >= 20.6:                                  # petites mains qui saluent au-dessus du bord
        if t > 21.3:
            for sx, px_ in ((-1, rx - 20), (1, rx + 22)):
                circ(d, px_ + sx * 34 + 4 * math.sin(t * 10), rby - 150 - 6 * abs(math.sin(t * 8)), 6,
                     (90, 100, 130) if sx < 0 else GREEN_D)
    else:
        btop = alien(d, bx, bfy, t, bmood, talking("blip", t), bf, 1.0, barms, bsq, btear)
        ztop = robot(d, zx, zfy, t, zmood, talking("zip", t), zsq, zf, zarms, 1.0, crank)

    # ---------------- effets
    if 8.3 < t < 9.4:                                # pfft : petite fumée, rien ne se passe
        smoke(d, rx, GY - 6, (t - 8.3) / 1.1, 4, (190, 185, 205))
    if 11.9 < t < 13.9:                              # gouttes d'effort
        for i in range(2):
            g = ((t - 11.9) * 1.5 + i * 0.5) % 1
            ell(d, ztop[0] - 36 - 20 * g, ztop[1] + 50 + 30 * g, 4, 6, (150, 210, 255))
    if 15.0 < t < 16.3:                              # étoiles d'étourdissement
        for i in range(3):
            a = t * 5 + i * 2.09
            star(d, ztop[0] + 44 * math.cos(a), ztop[1] + 24 + 10 * math.sin(a), 9, t * 4, (255, 240, 120))
    if 14.3 < t < 15.0:                              # pop ! la trappe s'ouvre
        g = (t - 14.3) / 0.7
        for i in range(6):
            a = i * 1.05
            star(d, RX - 70 + math.cos(a) * 34 * (0.5 + g), GY - 82 + math.sin(a) * 34 * (0.5 + g),
                 8 * (1 - g) + 2, t, (255, 245, 170))
    if 16.2 < t < 17.4:                              # la clé brille
        g = (t - 16.2) / 1.2
        for i in range(5):
            a = -math.pi / 2 + (i - 2) * 0.6
            star(d, RX - 92 + math.cos(a) * (34 + 20 * g), GY - 82 + math.sin(a) * (34 + 20 * g),
                 9 * math.sin(math.pi * g), t * 3 + i, (255, 235, 90))
    if 18.0 < t < 20.6:                              # cric-crac de la clé
        for i in range(7):
            g = (t - (18.0 + 0.36 * i)) / 0.4
            if 0 <= g < 1:
                d.text((P(RX - 120 - 10 * g), P(GY - 140 - 40 * g)), "click", font=font(22),
                       fill=(255, 240, 150))
    if 21.2 < t < 23.6:                              # fumée du décollage
        for k0 in (21.2, 21.6, 22.0):
            smoke(d, RX, GY - 4, (t - k0) / 1.6, 6)
    if t > 23.0:                                     # feu d'artifice
        for i, (f0, fx, fy) in enumerate(FIREWORKS):
            for rep in (0, 2.6):
                firework(d, fx, fy, (t - f0 - rep) / 1.3, FW_COLS[i % len(FW_COLS)])
    if t > 24.4:                                     # cœurs autour de la fusée
        for i in range(4):
            g = ((t - 24.4) * 0.5 + i / 4) % 1
            r = 16 * math.sin(math.pi * g)
            if r > 5:
                heart(d, rx - 90 + i * 60 + 10 * math.sin(t * 2 + i), rby - 200 - g * 120, r)

    if t >= 20.6:
        ztop = (rx - 20, rby - 215) if t > 21.2 else ztop
        btop = (rx + 22, rby - 215) if t > 21.2 else btop
    ANCHORS["zip"] = (ztop[0], ztop[1])
    ANCHORS["blip"] = (btop[0], btop[1])
    return img, zx, zfy, ANCHORS["blip"]


# ---------------------------------------------------------------- textes (version 16:9)
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
                        fill=(110, 70, 170))
    d.rounded_rectangle([P(x0), P(y0), P(x0 + bw), P(y0 + 72)], radius=P(36),
                        fill=(255, 255, 255))
    d.text((P(640), P(y0 + 36)), text, font=f, fill=(90, 60, 140), anchor="mm")


def bubble(d, text, ax, ay, side, u):
    f = font(26)
    w = f.getlength(text) / S + 36
    off = (1 - u) * 18
    y0, y1 = ay - 72 + off, ay - 16 + off
    x0 = ax + 18 if side == "right" else ax - 18 - w
    x0 = min(max(x0, 10), W - 10 - w)
    ol = (90, 60, 140)
    tail = [(P(ax), P(ay + off * 0.3)), (P(x0 + (22 if side == "right" else w - 52)), P(y1 - 4)),
            (P(x0 + (52 if side == "right" else w - 22)), P(y1 - 4))]
    d.rounded_rectangle([P(x0 - 3), P(y0 - 3), P(x0 + w + 3), P(y1 + 3)], radius=P(28), fill=ol)
    d.polygon([(a, b + P(3)) for a, b in tail], fill=ol)
    d.rounded_rectangle([P(x0), P(y0), P(x0 + w), P(y1)], radius=P(26), fill=(255, 255, 255))
    d.polygon(tail, fill=(255, 255, 255))
    d.text((P(x0 + w / 2), P((y0 + y1) / 2)), text, font=f, fill=ol, anchor="mm")


TITLE_COLS = [(255, 90, 120), (255, 150, 40), (240, 190, 20), (70, 200, 90),
              (60, 170, 250), (190, 120, 255)]


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
            bubble(d, text, ax + (40 if side == "right" else -40), max(ay + 30, 90), side, u)

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
