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


# ---------------------------------------------------------------- background (prairie la nuit)
SKY_TOP, SKY_BOT = (28, 32, 92), (92, 78, 150)
GROUND = (52, 112, 88)
STAR_IN_SCENE = True      # anim_vert met False : Twinkle et le ciel magique sont dessinés par-dessus tout l'écran
ANCHORS = {}              # point au-dessus de la tête de chaque personnage (pour les bulles)
TW = (0, 0, "sad", 0.0, 0.0)  # Twinkle : x, y, humeur, bouche, rotation


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


def mushroom(d, x, y, k, cap):
    d.rectangle([P(x - 7 * k), P(y - 26 * k), P(x + 7 * k), P(y)], fill=(235, 225, 200))
    d.pieslice([P(x - 26 * k), P(y - 48 * k), P(x + 26 * k), P(y - 8 * k)], 180, 360, fill=cap)
    for dx in (-12, 2, 13):
        circ(d, x + dx * k, y - 36 * k + abs(dx) * 0.4 * k, 3.5 * k, (255, 250, 220))


def make_hills():
    img = Image.new("RGBA", (int(W * S), int(H * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = random.Random(5)
    ell(d, 200, 640, 620, 260, (48, 72, 120))
    ell(d, 1050, 650, 600, 250, (42, 66, 112))
    ell(d, 300, 760, 700, 250, (44, 95, 85))
    ell(d, 1150, 780, 640, 270, (40, 88, 80))
    d.rectangle([0, P(600), int(W * S), int(H * S)], fill=GROUND)
    ell(d, 640, 618, 900, 45, GROUND)
    # sapins sombres au loin
    for x, h in [(80, 150), (150, 110), (1140, 170), (1215, 120), (1060, 100)]:
        for k in range(3):
            w = 50 - k * 12
            d.polygon([(P(x - w), P(560 - k * h * 0.28)), (P(x + w), P(560 - k * h * 0.28)),
                       (P(x), P(560 - h * 0.45 - k * h * 0.28))], fill=(30, 62, 70))
    # herbe et petites fleurs
    for _ in range(60):
        x, y = rng.uniform(0, 1280), rng.uniform(615, 715)
        d.line([P(x), P(y), P(x + rng.uniform(-4, 4)), P(y - 12)], fill=(75, 145, 105), width=P(3))
    for _ in range(14):
        x, y = rng.uniform(20, 1260), rng.uniform(630, 705)
        col = rng.choice([(255, 170, 200), (180, 200, 255), (255, 240, 150)])
        for a in range(5):
            circ(d, x + 6 * math.cos(a * 1.26), y + 6 * math.sin(a * 1.26), 4, col)
        circ(d, x, y, 3, (255, 220, 90))
    mushroom(d, 1075, 628, 1.2, (215, 80, 120))
    mushroom(d, 1110, 640, 0.8, (120, 110, 230))
    mushroom(d, 330, 636, 1.0, (120, 110, 230))
    return img


def make_base():
    img = make_sky()
    d = ImageDraw.Draw(img)
    rng = random.Random(21)
    for _ in range(70):
        x, y = rng.uniform(0, 1280), rng.uniform(0, 470)
        circ(d, x, y, rng.choice([2, 2, 3, 4]), (255, 250, 210))
    hills = make_hills()
    img.paste(hills, (0, 0), hills)
    return img


BASE = make_base()


# ---------------------------------------------------------------- pieces
INK = (40, 30, 50)


def eyes(d, x, y, sp, r, mood, t, ph=0.0):
    if mood in ("closed", "oops", "happy"):
        for sx in (-1, 1):
            d.arc([P(x + sx * sp - 8), P(y - 5), P(x + sx * sp + 8), P(y + 9)], 200, 340, fill=INK, width=P(4))
        return
    blink = ((t + ph) % 3.1) < 0.13
    for sx in (-1, 1):
        ell(d, x + sx * sp, y, r * 0.8, 2 if blink else r, INK)
        if not blink:
            circ(d, x + sx * sp + 2, y - r * 0.4, r * 0.35, (255, 255, 255))


OWL, OWL_D, OWL_C, BEAK = (200, 135, 80), (150, 95, 55), (250, 225, 180), (255, 165, 40)


def owl(d, x, fy, t, mood, talk=0.0, wings=(0.0, 0.0), sq=1.0, look=(0, 0), flap=0.0):
    """Ollie la petite chouette. Renvoie le haut de la tête et le bout des ailes."""
    def Y(v):
        return fy - v * sq
    for sx in (-1, 1):
        for k in (-1, 0, 1):
            ell(d, x + sx * 24 + k * 8, fy - 6, 6, 9, BEAK)
    # ailes (derrière / sur le côté du corps)
    tips = []
    for i, sx in enumerate((-1, 1)):
        a = wings[i] + flap * math.sin(t * 30)
        down = math.pi / 2 - sx * 0.35
        up = -math.pi / 2 - sx * 0.75
        ang = lerp(down, up, clamp01(a))
        sh = (x + sx * 52, Y(104))
        leaf(d, sh, ang, 82, 25, OWL_D)
        tips.append((sh[0] + 82 * math.cos(ang), sh[1] + 82 * math.sin(ang)))
    ell(d, x, Y(70), 62, 70 * sq, OWL)
    ell(d, x, Y(58), 40, 46 * sq, OWL_C)
    for row in range(3):
        for k in range(-1 + (row % 2), 2):
            cx, cy = x + k * 18 - (9 if row % 2 else 0) + (18 if row % 2 else 0) * 0.5, Y(84 - row * 18)
            d.arc([P(cx - 7), P(cy - 6), P(cx + 7), P(cy + 6)], 20, 160, fill=(215, 175, 125), width=P(3))
    # tête
    hy = Y(160)
    for sx in (-1, 1):
        d.polygon([(P(x + sx * 22), P(hy - 44)), (P(x + sx * 58), P(hy - 36)), (P(x + sx * 52), P(hy - 82))],
                  fill=OWL_D)
    circ(d, x, hy, 60, OWL)
    for sx in (-1, 1):
        circ(d, x + sx * 24, hy - 4, 27, OWL_C)
    if mood in ("closed", "oops", "happy"):
        for sx in (-1, 1):
            d.arc([P(x + sx * 24 - 12), P(hy - 12), P(x + sx * 24 + 12), P(hy + 6)], 200, 340, fill=INK, width=P(5))
    else:
        blink = (t % 3.4) < 0.13
        for sx in (-1, 1):
            ex = x + sx * 24
            if blink:
                d.line([P(ex - 14), P(hy - 4), P(ex + 14), P(hy - 4)], fill=INK, width=P(4))
                continue
            circ(d, ex, hy - 4, 18, (255, 255, 255))
            circ(d, ex + look[0] * 6, hy - 4 + look[1] * 6, 10, INK)
            circ(d, ex + look[0] * 6 + 3, hy - 8 + look[1] * 6, 4, (255, 255, 255))
        if mood == "worried":
            for sx in (-1, 1):
                d.line([P(x + sx * 10), P(hy - 30), P(x + sx * 36), P(hy - 24)], fill=INK, width=P(4))
    circ(d, x - 44, hy + 22, 9, (245, 140, 130))
    circ(d, x + 44, hy + 22, 9, (245, 140, 130))
    # bec
    op = 10 * talk if talk > 0.02 else (5 if mood in ("happy", "oops") else 0)
    d.polygon([(P(x - 10), P(hy + 10)), (P(x + 10), P(hy + 10)), (P(x), P(hy + 22))], fill=BEAK)
    if op > 0:
        d.polygon([(P(x - 8), P(hy + 14 + op)), (P(x + 8), P(hy + 14 + op)), (P(x), P(hy + 24 + op))],
                  fill=(225, 130, 30))
        d.polygon([(P(x - 6), P(hy + 18)), (P(x + 6), P(hy + 18)), (P(x), P(hy + 14 + op))], fill=(130, 40, 50))
    return (x, hy - 84), tips


STAR_Y, STAR_D = (255, 222, 70), (235, 160, 40)


def twinkle(d, x, y, t, mood, talk=0.0, rot=0.0, r=40):
    """Twinkle la petite étoile (x, y = centre)."""
    # petites étincelles autour
    for i in range(4):
        a = t * 1.5 + i * math.pi / 2
        rr = r + 22 + 5 * math.sin(t * 4 + i)
        sx, sy = x + rr * math.cos(a), y + rr * math.sin(a)
        k = 6 + 3 * math.sin(t * 6 + i)
        d.line([P(sx - k), P(sy), P(sx + k), P(sy)], fill=(255, 245, 190), width=P(3))
        d.line([P(sx), P(sy - k), P(sx), P(sy + k)], fill=(255, 245, 190), width=P(3))
    star(d, x, y, r + 7, rot, STAR_D)
    star(d, x, y, r, rot, STAR_Y)
    star(d, x - 5, y - 6, r * 0.45, rot, (255, 245, 170))
    # nœud rose
    bx, by = x + 4, y - r * 0.55
    d.polygon([(P(bx), P(by)), (P(bx - 12), P(by - 8)), (P(bx - 12), P(by + 8))], fill=(255, 120, 170))
    d.polygon([(P(bx), P(by)), (P(bx + 12), P(by - 8)), (P(bx + 12), P(by + 8))], fill=(255, 120, 170))
    circ(d, bx, by, 4, (255, 170, 205))
    eyes(d, x, y + 2, 10, 5, mood if mood != "smile" else "open", t, 0.7)
    if mood == "sad":
        for sx in (-1, 1):
            d.line([P(x + sx * 4), P(y - 13), P(x + sx * 15), P(y - 8)], fill=INK, width=P(3))
        ell(d, x + 15, y + 13, 3, 5, (110, 170, 255))
    circ(d, x - 18, y + 11, 4, (255, 150, 140))
    circ(d, x + 18, y + 11, 4, (255, 150, 140))
    my = y + 15
    if talk > 0.02:
        ell(d, x, my, 5, 1.5 + 5 * talk, (130, 40, 50))
    elif mood == "sad":
        d.arc([P(x - 7), P(my - 1), P(x + 7), P(my + 9)], 200, 340, fill=INK, width=P(3))
    elif mood == "happy":
        d.pieslice([P(x - 8), P(my - 4), P(x + 8), P(my + 8)], 0, 180, fill=(130, 40, 50))
    else:
        d.arc([P(x - 7), P(my - 7), P(x + 7), P(my + 4)], 20, 160, fill=INK, width=P(3))


def draw_twinkle(d, t, ox=0, oy=0):
    x, y, mood, talk, rot = TW
    if 4.6 < t < 6.3:                         # traînée de l'étoile filante
        for i in range(1, 7):
            u = clamp01((t - 4.6) / 1.7)
            px, py = x - 50 * i * 0.6, y - 120 * i * 0.6
            circ(d, px + ox, py + oy, 16 - 2 * i, lerpc((255, 240, 160), (120, 110, 200), i / 7))
    if 22.4 < t < 24.4:                       # traînée de l'envol
        for i in range(1, 7):
            px, py = x - 22 * i, y + 70 * i
            circ(d, px + ox, py + oy, 16 - 2 * i, lerpc((255, 240, 160), (120, 110, 200), i / 7))
    twinkle(d, x + ox, y + oy, t, mood, talk, rot)


HEART_C = (760, -310)


def draw_sky_fx(d, t, ox=0, oy=0):
    """Surprise de la fin : un cœur d'étoiles et des étoiles filantes."""
    if t < 24.4:
        return
    n = 16
    for i in range(n):
        t0 = 24.4 + i * 0.12
        if t < t0:
            continue
        s = i / n * 2 * math.pi
        hx = 16 * math.sin(s) ** 3
        hy = -(13 * math.cos(s) - 5 * math.cos(2 * s) - 2 * math.cos(3 * s) - math.cos(4 * s))
        g = back((t - t0) / 0.4)
        x, y = HEART_C[0] + hx * 8.5 + ox, HEART_C[1] + hy * 8.5 - 10 + oy
        col = [(255, 230, 90), (255, 150, 190), (160, 220, 255)][i % 3]
        star(d, x, y, (11 + 2 * math.sin(t * 5 + i)) * g, t * 1.5 + i, col)
    for k in range(3):
        t0 = 25.0 + k * 1.3
        u = (t - t0) / 0.9
        if 0 < u < 1:
            sx, sy = 980 - k * 160 - u * 520, -520 + k * 40 + u * 200
            for i in range(8):
                circ(d, sx + i * 20 + ox, sy - i * 7.7 + oy, max(1, 7 - i * 0.8),
                     lerpc((255, 255, 230), (130, 120, 220), i / 8))
            star(d, sx + ox, sy + oy, 12, t * 6, (255, 255, 230))


def fireflies(d, t, n=9, seed=40, y0=420, y1=600):
    for i in range(n):
        r = random.Random(seed + i)
        x = r.uniform(380, 1160) + 40 * math.sin(t * 0.7 + i * 2)
        y = r.uniform(y0, y1) + 18 * math.sin(t * 1.1 + i)
        b = 0.5 + 0.5 * math.sin(t * 3 + i * 1.7)
        if b > 0.2:
            circ(d, x, y, 7 * b, lerpc((90, 110, 120), (200, 255, 120), b))
            circ(d, x, y, 3, (255, 255, 200))


def moon(d, t, cx=1120, cy=110):
    circ(d, cx, cy, 70, (70, 70, 140))
    circ(d, cx, cy, 58, (255, 245, 200))
    circ(d, cx + 20, cy - 25, 10, (240, 228, 180))
    circ(d, cx - 28, cy + 22, 7, (240, 228, 180))
    for sx in (-1, 1):
        d.arc([P(cx + sx * 18 - 8), P(cy - 10), P(cx + sx * 18 + 8), P(cy + 4)], 200, 340, fill=(110, 90, 80),
              width=P(4))
    d.arc([P(cx - 14), P(cy + 2), P(cx + 14), P(cy + 22)], 20, 160, fill=(110, 90, 80), width=P(4))
    circ(d, cx - 32, cy + 14, 7, (255, 190, 170))
    circ(d, cx + 32, cy + 14, 7, (255, 190, 170))


sun = moon


# ---------------------------------------------------------------- balançoire
PIV = (570, 556)
HALF = 132


def seesaw_ends(th):
    c, s = math.cos(th), math.sin(th)
    return (PIV[0] - HALF * c, PIV[1] + HALF * s), (PIV[0] + HALF * c, PIV[1] - HALF * s)


def seesaw(d, th):
    d.polygon([(P(PIV[0] - 40), P(612)), (P(PIV[0] + 40), P(612)), (P(PIV[0]), P(PIV[1] + 4))],
              fill=(150, 95, 60))
    d.polygon([(P(PIV[0] - 26), P(606)), (P(PIV[0] + 26), P(606)), (P(PIV[0]), P(PIV[1] + 18))],
              fill=(180, 120, 75))
    c, s = math.cos(th), math.sin(th)
    nx, ny = -s, -c        # normale vers le haut
    pts = []
    for (ex, ey) in seesaw_ends(th):
        pts.append((ex, ey))
    (lx, ly), (rx, ry) = pts
    k = 9
    poly = [(lx + nx * k, ly + ny * k), (rx + nx * k, ry + ny * k), (rx - nx * k, ry - ny * k),
            (lx - nx * k, ly - ny * k)]
    d.polygon([(P(a), P(b)) for a, b in poly], fill=(225, 160, 85))
    d.line([(P(lx + nx * 3), P(ly + ny * 3)), (P(rx + nx * 3), P(ry + ny * 3))], fill=(245, 195, 120),
           width=P(4))
    circ(d, PIV[0], PIV[1], 8, (150, 95, 60))
    for (ex, ey), col in zip(pts, [(255, 120, 170), (110, 180, 255)]):
        circ(d, ex, ey, 11, col)


# ---------------------------------------------------------------- frame
TW_REST = (1040, 577)


def scene(t, with_sun=True):
    global TW
    img = BASE.copy()
    d = ImageDraw.Draw(img)
    if with_sun:
        moon(d, t)
    fireflies(d, t)

    # ---- balançoire
    th = 0.3
    if 22.2 <= t < 22.45:
        th = lerp(0.3, -0.3, ease((t - 22.2) / 0.25))
    elif 22.45 <= t < 23.5:
        th = -0.3
    elif 23.5 <= t < 24.2:
        th = lerp(-0.3, 0.3, ease((t - 23.5) / 0.7))
    (lex, ley), (rex, rey) = seesaw_ends(th)
    seesaw(d, th)

    # ---- Ollie
    ox, _ = path(t, [(0, 730, 0), (9.2, 730, 0), (11.0, 905, 0), (19.4, 905, 0), (20.8, 702, 0),
                     (23.4, 702, 0), (24.0, 800, 0)])
    fy = 615
    lift = 0.0
    sq = 1.0
    flap = 0.0
    if t < 1.7:
        lift = abs(math.sin(t * 6)) * 16          # accroche : il sautille tout de suite
    if 9.2 < t < 11.0 or 19.4 < t < 20.8:
        lift = abs(math.sin(t * 9)) * 12
    if 21.0 < t < 21.4:
        sq = 1 - 0.12 * math.sin(math.pi * (t - 21.0) / 0.4)
    if 21.4 <= t < 22.2:                          # il s'envole en battant des ailes...
        u = (t - 21.4) / 0.8
        fy = lerp(615, rey - 6, u) - 120 * math.sin(math.pi * u)
        flap = 0.35
    elif 22.2 <= t < 23.4:                        # ...et atterrit BOING sur la balançoire
        fy = rey - 6
        if t < 22.6:
            sq = 1 - 0.14 * math.sin(math.pi * (t - 22.2) / 0.4)
    elif 23.4 <= t < 24.0:
        u = (t - 23.4) / 0.6
        fy = lerp(rey - 6, 615, u) - 60 * math.sin(math.pi * u)
    elif t >= 24.0:
        fy = 615 - abs(math.sin(t * 5)) * 20      # danse de la fin
    if 15.0 <= t < 15.3:
        sq = 1 - 0.15 * math.sin(math.pi * (t - 15.0) / 0.3)
    fy -= lift
    wl = wr = 0.0
    if t < 1.8:
        wr = 0.75 + 0.25 * math.sin(t * 12)
    if 1.8 <= t < 3.3:
        wl = wr = 0.3 + 0.15 * math.sin(t * 6)
    if 4.6 < t < 6.0:
        wr = 0.65
    if 10.2 < t < 11.4:
        wl = 0.6
    if 12.8 < t < 14.1:
        wl = wr = ease((t - 12.8) / 0.4) * 0.95
    if 14.1 <= t < 14.5:
        wl = wr = 0.95 - 0.3 * ease((t - 14.1) / 0.4)
    if 15.0 <= t < 17.6:
        wl = 0.2 + 0.1 * math.sin(t * 7)
        wr = 0.2 - 0.1 * math.sin(t * 7)
    if 20.3 < t < 21.0:
        wl = 0.55
    if 21.4 <= t < 22.2:
        wl = wr = 0.6
    if t > 22.6:
        wl = wr = 0.85 + 0.12 * math.sin(t * 7)
    om = "smile"
    if t < 1.8 or t >= 22.6:
        om = "happy"
    if 1.8 <= t < 3.3:
        om = "closed"
    if 7.8 <= t < 10.1:
        om = "worried"
    if 15.0 <= t < 17.6:
        om = "oops"
    look = (0, 0)
    if 4.4 < t < 6.4:
        u = clamp01((t - 4.6) / 1.7)
        look = (lerp(-0.3, 0.9, u), lerp(-1, 0.3, u))
    elif 6.4 <= t < 11.0 or 17.6 < t < 19.4:
        look = (0.9, 0.2)
    elif 13.9 < t < 15.0:
        look = (0, -1)
    elif 19.4 <= t < 22.2:
        look = (-0.9, 0)
    elif 22.4 < t < 24.6:
        look = (0, -1)
    if 15.0 <= t < 17.6:
        ox += 4 * math.sin(t * 25) if t < 15.6 else 0

    # ---- Twinkle
    oh, tips = owl(ImageDraw.Draw(Image.new("RGB", (2, 2))), ox, fy, t, om, 0, (wl, wr), sq, look, flap)
    tm, rot = "sad", 0.0
    head_top = (ox, fy - 220 * sq)
    if t < 4.6:
        tx, ty = 600, -900                         # encore dans le ciel, hors de l'écran
    elif t < 6.3:
        u = (t - 4.6) / 1.7
        tx, ty = lerp(700, TW_REST[0], u), lerp(-560, TW_REST[1], u * u)
        rot = t * 8
        tm = "oops"
    elif t < 6.9:
        u = (t - 6.3) / 0.6
        tx, ty = TW_REST[0] + 20 * u, TW_REST[1] - 50 * math.sin(math.pi * u)
        tx = TW_REST[0]
        tm = "oops"
    elif t < 12.9:
        tx, ty = TW_REST[0], TW_REST[1] + 3 * math.sin(t * 2)
        tm = "sad" if t < 10.2 else "smile"
    elif t < 14.1:
        u = ease((t - 12.9) / 0.5)
        hold = (ox, fy - 262)
        tx, ty = lerp(TW_REST[0], hold[0], u), lerp(TW_REST[1], hold[1], u) - 30 * math.sin(math.pi * u)
        tm = "smile"
    elif t < 15.0:
        u = (t - 14.1) / 0.9
        top = (ox, 150)
        start = (ox, 365)
        tx = ox
        ty = lerp(start[1], head_top[1] - 30, u) - 4 * 230 * u * (1 - u) * 1.0
        rot = (t - 14.1) * 6
        tm = "happy" if u < 0.5 else "oops"
    elif t < 17.6:
        tx, ty = head_top[0] + 3 * math.sin(t * 4), head_top[1] - 28
        rot = 0.15 * math.sin(t * 3)
        tm = "oops" if t < 16.2 else "smile"
    elif t < 18.3:
        u = (t - 17.6) / 0.7
        tx, ty = lerp(ox, TW_REST[0], u), lerp(head_top[1] - 28, TW_REST[1], u) - 80 * math.sin(math.pi * u)
        tm = "smile"
    elif t < 19.6:
        tx, ty = TW_REST
        if 18.6 < t < 19.4:
            ty -= 22 * math.sin(math.pi * (t - 18.6) / 0.8)   # bonne idée : petit saut
        tm = "happy"
    elif t < 21.0:
        u = ease((t - 19.6) / 1.4)
        tx = lerp(TW_REST[0], lex + 6, u)
        ty = lerp(TW_REST[1], ley - 50, u) - 260 * math.sin(math.pi * u)
        rot = u * 2 * math.pi * 0.4 * 5
        tm = "happy"
    elif t < 22.45:
        tx, ty = lex + 6, ley - 50
        tm = "smile" if t < 22.2 else "oops"
    elif t < 24.2:
        u = (t - 22.45) / 1.75
        e = 1 - (1 - u) ** 2
        tx = lerp(lex + 6, HEART_C[0], e)
        ty = lerp(ley - 50, HEART_C[1], e)
        rot = e * 4 * math.pi
        tm = "happy"
    else:
        g = t - 24.2
        tx = HEART_C[0] + 8 * math.sin(t * 1.5)
        ty = HEART_C[1] - min(g, 5) * 14 + 8 * math.sin(t * 2.2)
        rot = 0.12 * math.sin(t * 2)
        tm = "happy"
    ttalk = talking(story.FRIEND, t)
    TW = (tx, ty, tm, ttalk, rot)

    # dessin
    (oh, tips) = owl(d, ox, fy, t, om, talking(story.HERO, t), (wl, wr), sq, look, flap)
    if STAR_IN_SCENE:
        draw_twinkle(d, t)
        draw_sky_fx(d, t)

    # étoiles qui tournent autour de la tête d'Ollie (étourdi)
    if 15.0 <= t < 17.4:
        for i in range(3):
            a = t * 5 + i * 2.09
            star(d, oh[0] + 70 * math.cos(a), oh[1] + 70 + 18 * math.sin(a), 9, t * 4, (255, 240, 120))
    # « bonne idée » : petites étoiles au-dessus de Twinkle
    if 18.6 < t < 19.8:
        g = (t - 18.6) / 1.2
        for i in range(5):
            a = -math.pi / 2 + (i - 2) * 0.5
            rr = 50 + 40 * g
            star(d, tx + rr * math.cos(a), ty - 10 + rr * math.sin(a), 11 * math.sin(math.pi * g),
                 t * 3 + i, (255, 230, 70))
    # petit nuage de poussière à l'atterrissage
    for t0, px in ((6.3, TW_REST[0]), (22.2, rex)):
        if t0 <= t < t0 + 0.6:
            g = (t - t0) / 0.6
            for sx in (-1, 1):
                circ(d, px + sx * (30 + 60 * g), (612 if t0 < 10 else rey) - 10 * g, 14 * (1 - g),
                     (200, 200, 230))

    ANCHORS["ollie"] = (oh[0], min(oh[1], tips[0][1] - 20, tips[1][1] - 20) - 4)
    if 15.0 <= t < 17.6:
        ANCHORS["ollie"] = (oh[0], ty - 50)
    if 12.9 <= t < 14.2:
        ANCHORS["ollie"] = (oh[0], ty - 50)
    ANCHORS["twinkle"] = (tx, ty - 54)
    return img, ox, fy, ANCHORS["twinkle"]


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
