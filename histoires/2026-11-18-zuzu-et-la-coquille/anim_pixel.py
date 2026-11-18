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


# ---------------------------------------------------------------- background (sous la mer)
WATER_TOP, WATER_BOT = (70, 178, 228), (28, 104, 172)
SAND, SAND_D = (240, 214, 150), (222, 190, 125)


def make_sky():
    img = Image.new("RGB", (int(W * S), int(H * S)))
    d = ImageDraw.Draw(img)
    h = int(H * S)
    for y in range(h):
        u = int(y / h * 7) / 6
        d.line([(0, y), (int(W * S), y)], fill=lerpc(WATER_TOP, WATER_BOT, u))
    # rayons de lumière
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for x0 in (300, 560, 820, 1060):
        od.polygon([(P(x0), 0), (P(x0 + 70), 0), (P(x0 - 90), P(640)), (P(x0 - 200), P(640))],
                   fill=(255, 255, 255, 28))
    img.paste(ov, (0, 0), ov)
    return img


def coral(d, x, y, col, k=1.0):
    for ang, L in [(-1.9, 90), (-1.45, 120), (-1.0, 85), (-1.25, 60)]:
        x1, y1 = x + L * k * math.cos(ang), y + L * k * math.sin(ang)
        d.line([P(x), P(y), P(x1), P(y1)], fill=col, width=P(18 * k))
        circ(d, x1, y1, 11 * k, col)


def make_hills():
    img = Image.new("RGBA", (int(W * S), int(H * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    coral(d, 1085, 615, (255, 120, 150), 1.0)
    coral(d, 335, 620, (255, 160, 80), 0.9)
    ell(d, 250, 790, 650, 210, SAND_D)
    ell(d, 1100, 800, 620, 220, SAND_D)
    d.rectangle([0, P(612), int(W * S), int(H * S)], fill=SAND)
    ell(d, 640, 618, 900, 22, SAND)
    rng = random.Random(4)
    for _ in range(26):
        x, y = rng.uniform(20, 1260), rng.uniform(640, 712)
        circ(d, x, y, rng.uniform(4, 7), rng.choice([(205, 175, 120), (250, 235, 190), (230, 160, 150)]))
    return img


SKY = make_sky()
HILLS = make_hills()
BASE = SKY.copy()
BASE.paste(HILLS, (0, 0), HILLS)


# ---------------------------------------------------------------- pieces
def seaweed(d, x, y, t, h=170, col=(70, 170, 100), ph=0.0):
    pts = []
    for i in range(13):
        u = i / 12
        pts.append((P(x + 18 * u * math.sin(t * 1.6 + ph + u * 3)), P(y - h * u)))
    d.line(pts, fill=col, width=P(16), joint="curve")
    for i in (4, 8):
        px, py = pts[i]
        circ(d, px / S + (12 if i == 4 else -12), py / S, 9, col)


def bubble_dot(d, x, y, r, col=(225, 245, 255)):
    d.ellipse([P(x - r), P(y - r), P(x + r), P(y + r)], outline=col, width=max(1, P(3)))
    circ(d, x - r * 0.35, y - r * 0.35, max(1.5, r * 0.25), (255, 255, 255))


PARTY = [(255, 120, 150), (255, 190, 90), (255, 235, 110), (140, 225, 130), (130, 190, 255), (200, 150, 245)]


def bubbles(d, t, x0, x1, ytop, ybot, n, seed, party=0.0, t0=0.0):
    for i in range(n):
        r = random.Random(seed + i)
        bx = r.uniform(x0, x1)
        sp = r.uniform(50, 90) * (1 + 1.4 * party)
        start = r.uniform(0, 20)
        y = ybot - ((t - t0 + start) * sp) % (ybot - ytop + 60)
        rad = r.uniform(5, 11) * (1 + 0.8 * party)
        col = PARTY[i % 6] if party > 0 else (225, 245, 255)
        bubble_dot(d, bx + 8 * math.sin(t * 2 + i), y, rad, col)


def zuzu(d, cx, cy, t, mood, k=1.0, talk=0.0, puff=0.0, face=1):
    """Zuzu, petit poisson-globe orange."""
    R = 52 * k * (1 + 0.32 * puff)
    body, belly, edge = (255, 175, 60), (255, 225, 140), (215, 120, 40)
    # queue
    tw = 10 * math.sin(t * 9)
    tx = cx - face * (R + 6)
    d.polygon([(P(tx + face * 12), P(cy)), (P(tx - face * 38), P(cy - 30 + tw)),
               (P(tx - face * 38), P(cy + 30 + tw))], fill=edge)
    # piquants quand il gonfle
    if puff > 0.08:
        for i in range(14):
            a = i * 2 * math.pi / 14
            L = R + 16 * puff
            d.polygon([(P(cx + (R - 4) * math.cos(a - 0.12)), P(cy + (R - 4) * math.sin(a - 0.12))),
                       (P(cx + (R - 4) * math.cos(a + 0.12)), P(cy + (R - 4) * math.sin(a + 0.12))),
                       (P(cx + L * math.cos(a)), P(cy + L * math.sin(a)))], fill=edge)
    circ(d, cx, cy, R + 5, edge)
    circ(d, cx, cy, R, body)
    ell(d, cx + face * 6, cy + R * 0.45, R * 0.7, R * 0.4, belly)
    # taches
    for dx, dy in [(-0.45, -0.45), (-0.1, -0.7), (-0.6, 0.0)]:
        circ(d, cx + face * dx * R, cy + dy * R, 5, edge)
    # nageoire
    fl = 8 * math.sin(t * 7)
    ell(d, cx - face * 6, cy + 10, 14, 9 + fl * 0.4, edge)
    # dessus : petite nageoire
    d.polygon([(P(cx - 14), P(cy - R + 4)), (P(cx + 10), P(cy - R + 4)), (P(cx - 6), P(cy - R - 18))], fill=edge)
    ink = (60, 40, 70)
    ex, ey = cx + face * R * 0.38, cy - R * 0.18
    for sx in (-1, 1):
        exx = ex + sx * 16
        if mood == "closed":
            d.arc([P(exx - 9), P(ey - 4), P(exx + 9), P(ey + 10)], 200, 340, fill=ink, width=P(4))
            continue
        blink = (t % 3.1) < 0.13
        circ(d, exx, ey, 12, (255, 255, 255))
        if blink:
            d.line([P(exx - 9), P(ey), P(exx + 9), P(ey)], fill=ink, width=P(4))
        else:
            circ(d, exx + face * 3, ey + 1, 7, ink)
            circ(d, exx + face * 5, ey - 2, 2.5, (255, 255, 255))
        if mood == "worried":
            d.line([P(exx - 10), P(ey - 16 - sx * 3), P(exx + 10), P(ey - 16 + sx * 3)], fill=ink, width=P(3))
    circ(d, ex - 30 * face, ey + 22, 8, (255, 140, 140))
    circ(d, ex + 32 * face, ey + 22, 6, (255, 140, 140))
    mx, my = cx + face * R * 0.42, cy + R * 0.3
    if talk > 0.02:
        ell(d, mx, my, 8, 3 + 9 * talk, (130, 40, 60))
    elif mood == "worried":
        ell(d, mx, my, 6, 7, (130, 40, 60))
    elif mood == "happy":
        d.pieslice([P(mx - 13), P(my - 8), P(mx + 13), P(my + 14)], 0, 180, fill=(130, 40, 60))
    else:
        d.arc([P(mx - 11), P(my - 8), P(mx + 11), P(my + 8)], 20, 160, fill=ink, width=P(4))


def shell(d, x, y, r, col, rot=0.0):
    """Coquillage en spirale (vu de côté), pointe vers le haut-droite."""
    dark = lerpc(col, (90, 50, 80), 0.35)
    light = lerpc(col, (255, 255, 255), 0.45)
    tip_a = -0.9 + rot
    d.polygon([(P(x + r * 0.55 * math.cos(tip_a - 1.0)), P(y + r * 0.55 * math.sin(tip_a - 1.0))),
               (P(x + r * 0.55 * math.cos(tip_a + 1.0)), P(y + r * 0.55 * math.sin(tip_a + 1.0))),
               (P(x + r * 1.45 * math.cos(tip_a)), P(y + r * 1.45 * math.sin(tip_a)))], fill=dark)
    circ(d, x, y, r + 3, dark)
    circ(d, x, y, r, col)
    for i, f in enumerate((0.72, 0.46, 0.24)):
        circ(d, x + r * (1 - f) * 0.25 * math.cos(tip_a), y + r * (1 - f) * 0.25 * math.sin(tip_a),
             r * f, light if i % 2 == 0 else col)
    d.arc([P(x - r * 0.8), P(y - r * 0.8), P(x + r * 0.8), P(y + r * 0.8)], 100, 300, fill=dark, width=P(4))


def crab(d, cx, cy, t, mood, talk=0.0, walk=0.0):
    """Pipa, petite bernard-l'hermite rouge corail. Renvoie le point au-dessus de sa tête."""
    body, dark = (245, 105, 95), (200, 70, 70)
    # pattes
    for sx in (-1, 1):
        for j in range(3):
            lx = cx + sx * (18 + j * 14)
            kick = 6 * math.sin(walk * 12 + j * 2 + sx) if walk else 0
            d.line([P(lx), P(cy + 14), P(lx + sx * 22), P(cy + 24 + kick * 0.3), P(lx + sx * 26 + kick), P(cy + 40)],
                   fill=dark, width=P(7), joint="curve")
    # pinces
    lift = 10 * math.sin(t * 6) if mood == "happy" else 0
    for sx in (-1, 1):
        px, py = cx + sx * 62, cy - 14 - (lift if sx > 0 else -lift) * 0.5 - (8 if mood == "happy" else 0)
        d.line([P(cx + sx * 36), P(cy + 2), P(px), P(py + 10)], fill=dark, width=P(9))
        circ(d, px, py, 16, body)
        d.polygon([(P(px), P(py - 4)), (P(px + sx * 20), P(py - 14)), (P(px + sx * 18), P(py + 2))], fill=SAND_D)
    ell(d, cx, cy, 48, 30, dark)
    ell(d, cx, cy - 2, 45, 27, body)
    # yeux sur tiges
    ink = (60, 30, 50)
    for sx in (-1, 1):
        sxp = cx + sx * 16
        top = cy - 52 + (4 if mood == "sad" else 0)
        d.line([P(sxp), P(cy - 20), P(sxp + sx * 3), P(top)], fill=dark, width=P(6))
        circ(d, sxp + sx * 3, top, 12, (255, 255, 255))
        blink = ((t + 1.3) % 3.7) < 0.13
        if blink or mood == "closed":
            d.line([P(sxp + sx * 3 - 8), P(top), P(sxp + sx * 3 + 8), P(top)], fill=ink, width=P(4))
        else:
            circ(d, sxp + sx * 3, top + 2, 6.5, ink)
            circ(d, sxp + sx * 3 + 2, top - 1, 2.2, (255, 255, 255))
        if mood == "sad":
            d.line([P(sxp + sx * 3 - 9 * sx), P(top - 16), P(sxp + sx * 3 + 9 * sx), P(top - 11)], fill=ink, width=P(3))
    circ(d, cx - 28, cy + 2, 6, (255, 160, 170))
    circ(d, cx + 28, cy + 2, 6, (255, 160, 170))
    if talk > 0.02:
        ell(d, cx, cy + 6, 8, 2 + 8 * talk, (120, 30, 50))
    elif mood == "sad":
        d.arc([P(cx - 11), P(cy + 4), P(cx + 11), P(cy + 18)], 200, 340, fill=ink, width=P(3))
        ell(d, cx + 22, cy - 10, 3.5, 5, (120, 190, 255))
    elif mood == "happy":
        d.pieslice([P(cx - 12), P(cy - 4), P(cx + 12), P(cy + 16)], 0, 180, fill=(120, 30, 50))
    elif mood == "oops":
        circ(d, cx, cy + 8, 6, (120, 30, 50))
    else:
        d.arc([P(cx - 10), P(cy - 4), P(cx + 10), P(cy + 10)], 20, 160, fill=ink, width=P(3))
    return (cx, cy - 72)


def starfish(d, x, y, t, talk=0.0, excited=0.0):
    col, dark = (190, 130, 240), (140, 90, 200)
    rot = 0.12 * math.sin(t * 2) + excited * 0.25 * math.sin(t * 10)
    for rr, c in ((44, dark), (39, col)):
        pts = []
        for i in range(10):
            r = rr if i % 2 == 0 else rr * 0.5
            a = rot + i * math.pi / 5 - math.pi / 2
            pts.append((P(x + r * math.cos(a)), P(y + r * math.sin(a))))
        d.polygon(pts, fill=c)
    for i in range(5):
        a = rot + i * 2 * math.pi / 5 - math.pi / 2
        circ(d, x + 26 * math.cos(a), y + 26 * math.sin(a), 3, (235, 200, 255))
    ink = (60, 30, 70)
    circ(d, x - 8, y - 4, 4, ink)
    circ(d, x + 8, y - 4, 4, ink)
    if talk > 0.02:
        ell(d, x, y + 8, 5, 2 + 5 * talk, (120, 30, 60))
    else:
        d.arc([P(x - 8), P(y + 1), P(x + 8), P(y + 12)], 20, 160, fill=ink, width=P(3))
    return (x, y - 40)


def star(d, x, y, r, rot, col):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = rot + i * math.pi / 5 - math.pi / 2
        pts.append((P(x + rr * math.cos(a)), P(y + rr * math.sin(a))))
    d.polygon(pts, fill=col)


def path(t, keys):
    """keys = [(t, x, y), ...] -> position interpolée (ease) entre les clés."""
    if t <= keys[0][0]:
        return keys[0][1], keys[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(keys, keys[1:]):
        if t <= t1:
            u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1
            return lerp(x0, x1, u), lerp(y0, y1, u)
    return keys[-1][1], keys[-1][2]


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
STAR_HEAD = (450, 550)


def scene(t, with_sun=True):
    global STAR_HEAD
    img = BASE.copy()
    d = ImageDraw.Draw(img)
    for sx, h, ph, col in [(430, 150, 0.0, (60, 160, 95)), (720, 120, 1.7, (80, 180, 110)),
                           (1010, 175, 3.1, (60, 160, 95))]:
        seaweed(d, sx, 616, t, h, col, ph)
    bubbles(d, t, 380, 1140, 20, 600, 7, 11)

    # ---- Zuzu
    zx, zy = path(t, [(0, 560, 320), (1.5, 610, 300), (4.6, 610, 300), (6.8, 640, 400), (12.8, 640, 400),
                      (13.8, 1030, 525), (14.9, 930, 470), (15.3, 930, 470), (16.0, 680, 400),
                      (20.5, 680, 400), (21.5, 555, 545), (23.5, 735, 545), (24.8, 560, 360)])
    zy += 9 * math.sin(2 * math.pi * 0.6 * t)
    if t > 24.8:
        zy -= abs(math.sin(t * 4)) * 18
    face = -1 if (15.2 < t < 16.0 or 20.5 < t < 21.5 or 23.5 < t < 24.8) else 1
    puff = 0.0
    if 1.8 < t < 3.2:
        puff = math.sin(math.pi * (t - 1.8) / 1.4)
    if 25.9 < t < 27.0:
        puff = math.sin(math.pi * (t - 25.9) / 1.1)
    zm = "smile"
    if 1.8 < t < 3.2 or t >= 24.3:
        zm = "happy"
    elif 8.5 <= t < 10.2 or 15.6 <= t < 18.0:
        zm = "worried"
    elif 21.5 <= t < 23.5:
        zm = "closed"
    zk = 1.0 + (0.04 * math.sin(t * 14) if 21.5 < t < 23.5 else 0)

    # ---- Pipa (crabe)
    cx, cy = path(t, [(0, 900, 585), (23.5, 900, 585), (24.3, 800, 585)])
    walk = 1.0 if 23.5 < t < 24.3 else 0.0
    if 15.6 < t < 16.2:
        cy -= 30 * math.sin(math.pi * (t - 15.6) / 0.6)
    if t > 24.3:
        cy -= abs(math.sin((t - 24.3) * 3.5)) * 22
    cm = "sad"
    if 15.6 <= t < 17.6:
        cm = "oops"
    elif 19.0 <= t < 24.3:
        cm = "smile"
    elif t >= 24.3:
        cm = "happy"

    # ---- petite coquille
    if t < 13.8:
        ss = (1030, 600)
    elif t < 15.0:
        ss = (zx, zy + 62)
    elif t < 15.6:
        u = ease((t - 15.0) / 0.4)
        ss = (lerp(930, cx + 26, u), lerp(zy + 62, cy - 26, u))
    elif t < 16.4:
        u = (t - 15.6) / 0.8
        ss = (lerp(cx + 26, 1065, u), lerp(cy - 26, 600, u) - 110 * math.sin(math.pi * u))
    else:
        ss = (1065, 600)
    small_rot = (t - 15.6) * 9 if 15.6 < t < 16.4 else 0

    # ---- grande coquille
    if t < 21.5:
        bs = (620, 612)
    elif t < 23.5:
        u = ease((t - 21.5) / 2.0)
        bs = (lerp(620, 800, u), lerp(612, 580, u))
    elif t < 24.3:
        u = ease((t - 23.5) / 0.8)
        bs = (lerp(800, cx + 24, u), lerp(580, cy - 34, u))
    else:
        bs = (cx + 24, cy - 34)

    # dessin : coquilles derrière les personnages
    shell(d, bs[0], bs[1], 48, (255, 165, 205))
    if t < 21.5:
        ell(d, 620, 650, 80, 30, SAND)
    if not (13.8 <= t < 15.0):
        shell(d, ss[0], ss[1], 15, (245, 225, 180), small_rot)
    sh = starfish(d, 450, 598 - (abs(math.sin(t * 6)) * 22 if (18.8 < t < 21.0 or t > 24.3) else 0), t,
                  talking("star", t), 1.0 if (18.8 < t < 21.0 or t > 24.3) else 0.0)
    STAR_HEAD = sh
    head = crab(d, cx, cy, t, cm, talking(story.FRIEND, t), walk * t)
    if 13.8 <= t < 15.0:
        shell(d, ss[0], ss[1], 15, (245, 225, 180))
    zuzu(d, zx, zy, t, zm, zk, talking(story.HERO, t), puff, face)

    # fête des bulles + étoiles
    if t > 24.3:
        p = ease((t - 24.3) / 1.0)
        bubbles(d, t, 400, 1120, 20, 640, int(16 * p), 300, party=1.0, t0=24.3)
        g = (t - 24.3) / 4.0
        if g < 1:
            for i in range(8):
                a = i * math.pi / 4 + t * 0.8
                rr = 70 + 60 * g
                sz = 13 * math.sin(math.pi * min(1, g * 1.2)) * (0.8 + 0.3 * math.sin(t * 8 + i))
                if sz > 1:
                    star(d, cx + rr * math.cos(a), cy - 20 + rr * math.sin(a), sz, t * 2 + i,
                         (255, 220, 60) if i % 2 else (255, 255, 255))
    if 21.5 < t < 23.5:   # petits nuages de sable pendant la poussée
        for i in range(5):
            r = random.Random(i + 40)
            age = (t * 1.5 + r.random()) % 1
            circ(d, bs[0] - 40 - age * 60 + r.uniform(-10, 10), 612 - age * 30, 10 * (1 - age) + 2, SAND_D)

    return img, zx, zy, head


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
            if who == story.HERO:
                ax, ay = (x + 112, y - 5) if side == "right" else (x - 112, y - 5)
            else:
                ax, ay = head[0] + 45, head[1] - 35
            bubble(d, text, ax, ay, side, u)

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
