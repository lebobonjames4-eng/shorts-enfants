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


# ---------------------------------------------------------------- background
SKY_TOP, SKY_BOT = (50, 60, 135), (175, 145, 215)


def make_sky():
    img = Image.new("RGB", (int(W * S), int(H * S)))
    d = ImageDraw.Draw(img)
    h = int(H * S)
    for y in range(h):
        u = int(y / h * 7) / 6
        d.line([(0, y), (int(W * S), y)], fill=lerpc(SKY_TOP, SKY_BOT, u))
    return img


def pine(d, x, y, k):
    d.rectangle([P(x - 6 * k), P(y - 10 * k), P(x + 6 * k), P(y + 8 * k)], fill=(110, 80, 70))
    for i, (w, h) in enumerate([(48, 40), (38, 36), (26, 32)]):
        by = y - 8 * k - i * 26 * k
        d.polygon([(P(x - w * k), P(by)), (P(x + w * k), P(by)), (P(x), P(by - h * k))],
                  fill=(45, 120, 105))
        d.polygon([(P(x - w * 0.45 * k), P(by - h * 0.55 * k)), (P(x + w * 0.45 * k), P(by - h * 0.55 * k)),
                   (P(x), P(by - h * k))], fill=(240, 246, 255))


def make_hills():
    img = Image.new("RGBA", (int(W * S), int(H * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ell(d, 250, 760, 650, 300, (205, 218, 245))
    ell(d, 1100, 780, 620, 310, (190, 205, 240))
    for x, y, k in [(130, 520, 0.9), (450, 500, 0.8), (520, 520, 0.6), (1060, 515, 0.85),
                    (1150, 530, 0.65), (1230, 510, 0.8)]:
        pine(d, x, y, k)
    d.rectangle([0, P(600), int(W * S), int(H * S)], fill=(232, 240, 255))
    ell(d, 640, 640, 900, 70, (232, 240, 255))
    rng = random.Random(3)
    for _ in range(45):
        x, y = rng.uniform(20, 1260), rng.uniform(600, 715)
        circ(d, x, y, 3, (255, 255, 255) if rng.random() < 0.6 else (170, 200, 255))
    return img


SKY = make_sky()
HILLS = make_hills()
STARS = [(random.Random(i).uniform(0, 1280), random.Random(i + 99).uniform(10, 300)) for i in range(40)]


# ---------------------------------------------------------------- pieces
def stars(d, t, pts, dy=0):
    for i, (x, y) in enumerate(pts):
        tw = 0.5 + 0.5 * math.sin(t * 2.5 + i * 1.7)
        if tw > 0.25:
            circ(d, x, y + dy, 2 + 2 * tw, (255, 250, 210))


def moon(d, t, cx=600, cy=120):
    circ(d, cx, cy, 62, (255, 245, 200))
    circ(d, cx, cy, 55, (255, 238, 170))
    circ(d, cx + 22, cy - 22, 10, (240, 222, 150))
    circ(d, cx - 25, cy + 25, 7, (240, 222, 150))
    ink = (110, 90, 60)
    for sx in (-1, 1):
        d.arc([P(cx + sx * 17 - 9), P(cy - 10), P(cx + sx * 17 + 9), P(cy + 4)], 200, 340, fill=ink, width=P(4))
    d.arc([P(cx - 12), P(cy + 4), P(cx + 12), P(cy + 22)], 20, 160, fill=ink, width=P(4))
    circ(d, cx - 30, cy + 10, 7, (255, 190, 150))
    circ(d, cx + 30, cy + 10, 7, (255, 190, 150))


def snow(d, t, n=60, top=-20, h=760, seed=0):
    for i in range(n):
        r = random.Random(i + seed)
        x0, y0, sp = r.uniform(0, 1280), r.uniform(0, h), r.uniform(25, 50)
        y = (y0 + t * sp) % h + top
        x = x0 + 18 * math.sin(t * 0.9 + i)
        circ(d, x, y, r.choice((2.5, 3.5, 4.5)), (255, 255, 255))


AURORA = [(90, 240, 170), (80, 210, 240), (200, 130, 255)]


def aurora(img, t, p, dy=0):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for k, col in enumerate(AURORA):
        for xi in range(0, 1300, 12):
            yb = 120 + k * 55 + 35 * math.sin(xi * 0.007 + t * 0.9 + k * 1.3) + dy
            hh = 70 + 30 * math.sin(xi * 0.013 - t * 1.2 + k)
            a = int(110 * p * (0.6 + 0.4 * math.sin(xi * 0.02 + t * 2 + k)))
            d.rectangle([P(xi), P(yb), P(xi + 12), P(yb + hh)], fill=col + (max(0, a),))
    img.paste(ov, (0, 0), ov)


def rpoly(cx, cy, rx, ry, ang, n=20):
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((P(cx + x * ca - y * sa), P(cy + x * sa + y * ca)))
    return pts


def rot(cx, cy, x, y, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    return (P(cx + x * ca - y * sa), P(cy + x * sa + y * ca))


def fish(d, x, y, ang):
    d.polygon([rot(x, y, -26, 0, ang), rot(x, y, -46, -16, ang), rot(x, y, -46, 16, ang)],
              fill=(90, 150, 230))
    d.polygon(rpoly(x, y, 30, 15, ang), fill=(120, 185, 245))
    d.polygon(rpoly(x + 4 * math.cos(ang), y + 4 * math.sin(ang), 18, 6, ang, 12), fill=(185, 220, 255))
    ex, ey = rot(x, y, 16, -4, ang)
    d.ellipse([ex - P(4), ey - P(4), ex + P(4), ey + P(4)], fill=(40, 40, 70))


def carrot(d, x, y, ang):
    """(x, y) = base of the carrot; it points along ang."""
    for da in (-0.5, 0, 0.5):
        tip = rot(x, y, -22, 14 * math.sin(da) * 1.4, ang + da)
        d.line([rot(x, y, 0, 0, ang), tip], fill=(80, 170, 80), width=P(6))
    d.polygon([rot(x, y, 0, -9, ang), rot(x, y, 0, 9, ang), rot(x, y, 46, 0, ang)], fill=(255, 140, 40))
    d.line([rot(x, y, 14, -4, ang), rot(x, y, 20, -2, ang)], fill=(220, 100, 30), width=P(3))
    d.line([rot(x, y, 26, 3, ang), rot(x, y, 32, 1, ang)], fill=(220, 100, 30), width=P(3))


def bird(d, x, y, t, flying=True):
    flap = math.sin(t * 22) if flying else 0.2
    circ(d, x, y, 19, (90, 60, 50))
    circ(d, x, y, 16, (255, 205, 70))
    circ(d, x + 4, y + 6, 9, (255, 235, 160))
    ell(d, x - 6, y - 4 - 12 * flap, 13, 7, (240, 160, 50))
    d.polygon([(P(x + 14), P(y - 4)), (P(x + 27), P(y)), (P(x + 14), P(y + 4))], fill=(255, 130, 40))
    circ(d, x + 7, y - 6, 3, (40, 40, 70))
    d.polygon([(P(x - 15), P(y)), (P(x - 28), P(y - 8)), (P(x - 26), P(y + 6))], fill=(240, 160, 50))


def penguin(d, cx, cy, t, mood, talk=0.0, flap=0.0):
    navy, edge = (45, 60, 110), (25, 30, 60)
    orange = (255, 160, 50)
    for sx in (-1, 1):
        ell(d, cx + sx * 24, cy + 82, 22, 10, orange)
    fy = cy + 12 - 30 * flap
    for sx in (-1, 1):
        d.polygon(rpoly(cx + sx * 58, fy, 15, 40, sx * (0.35 + 0.9 * flap)), fill=edge)
        d.polygon(rpoly(cx + sx * 58, fy, 11, 36, sx * (0.35 + 0.9 * flap)), fill=navy)
    ell(d, cx, cy, 63, 90, edge)
    ell(d, cx, cy, 58, 85, navy)
    ell(d, cx, cy + 22, 41, 60, (250, 250, 255))
    ell(d, cx, cy - 36, 40, 28, (250, 250, 255))
    # scarf
    d.rounded_rectangle([P(cx - 52), P(cy - 10), P(cx + 52), P(cy + 6)], radius=P(7), fill=(60, 200, 185))
    d.rectangle([P(cx + 18), P(cy), P(cx + 36), P(cy + 38)], fill=(60, 200, 185))
    for yy in (cy + 12, cy + 26):
        d.rectangle([P(cx + 18), P(yy), P(cx + 36), P(yy + 5)], fill=(255, 120, 140))
    ink = (35, 35, 60)
    ey = cy - 44
    circ(d, cx - 30, cy - 24, 7, (255, 170, 190))
    circ(d, cx + 30, cy - 24, 7, (255, 170, 190))
    if mood == "closed":
        for sx in (-1, 1):
            d.line([P(cx + sx * 17 - 8), P(ey - 4), P(cx + sx * 17 + 8), P(ey)], fill=ink, width=P(4))
            d.line([P(cx + sx * 17 - 8), P(ey + 4), P(cx + sx * 17 + 8), P(ey)], fill=ink, width=P(4))
    elif mood == "happy":
        for sx in (-1, 1):
            d.arc([P(cx + sx * 17 - 9), P(ey - 4), P(cx + sx * 17 + 9), P(ey + 12)], 200, 340, fill=ink, width=P(4))
    else:
        blink = (t % 3.1) < 0.13
        for sx in (-1, 1):
            ell(d, cx + sx * 17, ey, 7, 2 if blink else 10, ink)
            if not blink:
                circ(d, cx + sx * 17 + 2, ey - 4, 3, (255, 255, 255))
    if mood == "worried":
        for sx in (-1, 1):
            d.line([P(cx + sx * 17 - 9 * sx), P(ey - 20), P(cx + sx * 17 + 7 * sx), P(ey - 14)], fill=ink, width=P(4))
    op = max(talk, 0.5 if mood == "happy" else 0)
    by = cy - 28
    if op > 0.02:
        d.rectangle([P(cx - 7), P(by + 2), P(cx + 7), P(by + 4 + 8 * op)], fill=(150, 40, 60))
    d.polygon([(P(cx - 12), P(by)), (P(cx + 12), P(by)), (P(cx), P(by + 10))], fill=orange)
    if op > 0.02:
        d.polygon([(P(cx - 9), P(by + 3 + 8 * op)), (P(cx + 9), P(by + 3 + 8 * op)),
                   (P(cx), P(by + 12 + 8 * op))], fill=(230, 120, 30))


def penguin_rot(img, cx, cy, ang_deg, *a, **kw):
    if abs(ang_deg) < 0.5:
        penguin(ImageDraw.Draw(img), cx, cy, *a, **kw)
        return
    global S
    R = 170
    spr = Image.new("RGBA", (P(2 * R), P(2 * R)), (0, 0, 0, 0))
    penguin(ImageDraw.Draw(spr), R, R, *a, **kw)
    spr = spr.rotate(ang_deg, resample=Image.NEAREST)
    img.paste(spr, (P(cx) - P(R), P(cy) - P(R)), spr)


GX, GY = 900, 612


def snowman(d, t, sway, mood, talk, wave=0.0):
    white, edge = (250, 252, 255), (175, 190, 230)
    bx, mx, hx = GX, GX + sway * 0.4, GX + sway
    hy = 362
    # arms
    for sx in (-1, 1):
        a = -0.6 - wave * (0.5 + 0.4 * math.sin(t * 7 + sx))
        x0, y0 = mx + sx * 44, 440
        x1, y1 = x0 + sx * 62 * math.cos(a), y0 + 62 * math.sin(a)
        d.line([P(x0), P(y0), P(x1), P(y1)], fill=(120, 80, 55), width=P(7))
        d.line([P(x0 + sx * 38 * math.cos(a)), P(y0 + 38 * math.sin(a)),
                P(x0 + sx * 38 * math.cos(a) + sx * 6), P(y0 + 38 * math.sin(a) - 20)],
               fill=(120, 80, 55), width=P(5))
    for x, y, r in [(bx, 540, 72), (mx, 442, 54), (hx, hy, 42)]:
        circ(d, x, y, r + 5, edge)
    for x, y, r in [(bx, 540, 72), (mx, 442, 54), (hx, hy, 42)]:
        circ(d, x, y, r, white)
        circ(d, x - r * 0.35, y - r * 0.35, r * 0.25, (255, 255, 255))
    for yy in (425, 455, 520, 555):
        circ(d, mx if yy < 500 else bx, yy, 6, (60, 60, 80))
    # scarf
    d.rounded_rectangle([P(mx - 46), P(hy + 30), P(mx + 46), P(hy + 46)], radius=P(8), fill=(235, 85, 100))
    d.rectangle([P(mx - 36), P(hy + 40), P(mx - 20), P(hy + 82)], fill=(235, 85, 100))
    # hat
    d.pieslice([P(hx - 40), P(hy - 52), P(hx + 40), P(hy + 22)], 180, 360, fill=(140, 110, 230))
    d.rectangle([P(hx - 42), P(hy - 18), P(hx + 42), P(hy - 8)], fill=(110, 85, 200))
    circ(d, hx, hy - 54, 10, (255, 255, 255))
    ink = (50, 50, 70)
    ey = hy + 2
    if mood == "sad":
        for sx in (-1, 1):
            d.arc([P(hx + sx * 14 - 7), P(ey - 2), P(hx + sx * 14 + 7), P(ey + 8)], 20, 160, fill=ink, width=P(3))
        d.arc([P(hx - 11), P(hy + 18), P(hx + 11), P(hy + 30)], 200, 340, fill=ink, width=P(3))
        ell(d, hx + 22, ey + 10, 3.5, 5, (110, 170, 255))
    else:
        if mood == "happy":
            for sx in (-1, 1):
                d.arc([P(hx + sx * 14 - 7), P(ey - 4), P(hx + sx * 14 + 7), P(ey + 8)], 200, 340, fill=ink, width=P(3))
        else:
            for sx in (-1, 1):
                circ(d, hx + sx * 14, ey, 4.5, ink)
        if talk > 0.02:
            ell(d, hx, hy + 24, 8, 2 + 6 * talk, (140, 50, 60))
        else:
            for i in range(5):
                a = math.pi * (0.2 + 0.15 * i)
                circ(d, hx + 14 * math.cos(a), hy + 14 + 9 * math.sin(a), 2.5, ink)
        circ(d, hx - 24, hy + 12, 5, (255, 170, 180))
        circ(d, hx + 24, hy + 12, 5, (255, 170, 180))
    return (hx, hy - 22), (hx + 6, hy + 10)   # bubble anchor, nose point


def star(d, x, y, r, rot_, col):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = rot_ + i * math.pi / 5 - math.pi / 2
        pts.append((P(x + rr * math.cos(a)), P(y + rr * math.sin(a))))
    d.polygon(pts, fill=col)


def arc_path(p0, p1, u, h):
    return lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u) - h * math.sin(math.pi * u)


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
    if t > 5.7:
        return
    text = story.TITLE
    f = font(72)
    total = f.getlength(text) / S
    x = 640 - total / 2
    out = ease((t - 5.0) / 0.6) * -320
    ci = 0
    for i, ch in enumerate(text):
        wch = f.getlength(ch) / S
        u = back((t - 0.4 - i * 0.07) / 0.6)
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
    sz = max(8, 130 * u)
    d.text((P(640), P(120 + 5 * math.sin(t * 4))), "Fin !", font=font(sz),
           fill=(255, 100, 150), anchor="mm", stroke_width=P(8 * u), stroke_fill=(255, 255, 255))


# ---------------------------------------------------------------- frame
GROUND_CY = 524


def tobi_state(t):
    """Return x, y, angle (deg), mood, flap."""
    x, y, ang, mood, flap = -150, GROUND_CY, 0.0, "smile", 0.0
    walking = False
    if t >= 0.5:
        u = (t - 0.5) / 2.5
        x = lerp(-150, 560, ease(u))
        walking = u < 1
    if 6.4 <= t < 9.3:
        u_fall = ease((t - 6.4) / 0.4)
        u_up = ease((t - 8.6) / 0.7)
        k = u_fall * (1 - u_up)
        ang = -82 * k
        y = GROUND_CY + 30 * k
        x += 30 * k
        if 6.7 <= t < 8.8:
            mood = "closed"
    if t >= 11.8:
        u = (t - 11.8) / 2.2
        x = lerp(560, 720, ease(u))
        walking = walking or u < 1
    if 12.6 <= t < 16.0:
        mood = "worried"
    for h0 in (21.5, 33.5):     # hops to give the nose
        if h0 <= t < h0 + 0.9:
            y -= 115 * math.sin(math.pi * (t - h0) / 0.9)
            flap = math.sin(math.pi * (t - h0) / 0.9)
    if 24.4 <= t < 26.4:
        mood = "closed"
    if t >= 34.6:
        mood = "happy"
    if 37.0 <= t < 44.0:
        ph = (t - 37.0) * 1.6
        y -= 45 * abs(math.sin(math.pi * ph))
        flap = 0.5 + 0.5 * math.sin(2 * math.pi * ph)
        ang = 10 * math.sin(math.pi * ph)
    if t >= 44.0:
        u = (t - 44.0) / 1.4
        x = lerp(720, 600, ease(u))
        walking = u < 1
    if walking:
        ang += 9 * math.sin(t * 11)
        y -= 6 * abs(math.sin(t * 11))
    return x, y, ang, mood, flap


def scene(t, with_sun=True):
    img = SKY.copy()
    d = ImageDraw.Draw(img)
    stars(d, t, STARS)
    au = clamp01((t - 36.6) / 2.0)
    if au > 0:
        aurora(img, t, ease(au))
    img.paste(HILLS, (0, 0), HILLS)
    d = ImageDraw.Draw(img)
    snow(d, t)

    x, y, ang, mood, flap = tobi_state(t)

    # snowman
    sway = 0.0
    wave = 0.0
    if t >= 34.6:
        sway = 10 * math.sin(2 * math.pi * 0.8 * (t - 34.6)) * min(1, (t - 34.6) / 0.6)
        wave = min(1, (t - 34.6) / 0.6)
    smood = "sad" if t < 22.5 else ("happy" if (t < 24.2 or t >= 34.6) else "smile")
    head, nose = snowman(d, t, sway, smood, talking("flocon", t), wave)

    # bird
    bp = None
    if 28.5 <= t < 31.0:
        u = ease((t - 28.5) / 2.5)
        bp = (lerp(1250, 630, u), lerp(120, 440, u) - 60 * math.sin(math.pi * u)), True
    elif 31.0 <= t < 32.6:
        bp = (630, 440 + 6 * math.sin(t * 6)), True
    elif 32.6 <= t < 34.0:
        u = ease((t - 32.6) / 1.4)
        bp = arc_path((630, 440), (998, 378), u, 120), True
    elif t >= 34.0:
        hop = 14 * abs(math.sin(math.pi * 1.6 * (t - 37))) if 37 <= t < 44 else 0
        aw = 0
        if t >= 34.6:
            aw = 0  # arm moves a little: keep bird on its tip approx.
        bp = (998 + sway * 0.4, 378 - hop), (37 <= t < 44)

    # carrot
    cp = None
    if 28.5 <= t < 32.2 and bp:
        cp = (bp[0][0] - 10, bp[0][1] + 22, math.pi / 2)
    elif 32.2 <= t < 32.6:
        u = ease((t - 32.2) / 0.4)
        cp = (lerp(620, x - 62, u), lerp(462, y + 10, u), lerp(math.pi / 2, -0.3, u))
    elif 32.6 <= t < 33.9:
        cp = (x - 62, y + 10 - 30 * flap, -0.3)
    elif 33.9 <= t < 34.5:
        u = ease((t - 33.9) / 0.6)
        p = arc_path((x - 62, y + 10), (nose[0] - 4, nose[1]), u, 60)
        cp = (p[0], p[1], lerp(-0.3, 0.1, u))
    elif t >= 34.5:
        cp = (nose[0] - 4, nose[1], 0.1)

    # fish
    fp = None
    if 20.0 <= t < 21.9:
        fp = (x + 64, y + 12 - 30 * flap, -0.4 + 0.15 * math.sin(t * 9))
    elif 21.9 <= t < 22.5:
        u = ease((t - 21.9) / 0.6)
        p = arc_path((x + 64, y + 12), (nose[0] + 20, nose[1]), u, 50)
        fp = (p[0], p[1], lerp(-0.4, 0, u))
    elif 22.5 <= t < 24.0:
        fp = (nose[0] + 20, nose[1] + 2, 0.35 * math.sin((t - 22.5) * 18))
    elif 24.0 <= t < 24.5:
        u = (t - 24.0) / 0.5
        fp = (nose[0] + 20 - 60 * u, lerp(nose[1], 600, u * u), u * 4)
    elif 24.5 <= t < 26.6:
        fp = (820, 600 - 25 * abs(math.sin((t - 24.5) * 7)), 0.5 * math.sin((t - 24.5) * 14))
    elif 26.6 <= t < 28.2:
        u = (t - 26.6) / 1.6
        p = arc_path((820, 600), (1260, 640), u, 220)
        fp = (p[0], p[1], -1.0 + 2 * u)

    penguin_rot(img, x, y, ang, t, mood, talking("tobi", t), flap)
    d = ImageDraw.Draw(img)
    if fp:
        fish(d, *fp)
    if cp:
        carrot(d, *cp)
    if bp:
        bird(d, bp[0][0], bp[0][1], t, bp[1])

    # sparkles after the nose is placed
    if 34.5 < t < 40:
        g = (t - 34.5) / 5.5
        for i in range(8):
            a = i * math.pi / 4 + t * 0.8
            rr = 70 + 80 * g
            sz = 13 * math.sin(math.pi * min(1, g * 1.3)) * (0.8 + 0.3 * math.sin(t * 8 + i))
            if sz > 1:
                star(d, nose[0] + rr * math.cos(a), nose[1] + rr * math.sin(a), sz, t * 2 + i,
                     (255, 220, 60) if i % 2 else (255, 255, 255))
    return img, x, y, head


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
                ax, ay = (x + 60, y - 80) if side == "right" else (x - 60, y - 80)
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
