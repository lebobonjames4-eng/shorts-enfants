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
def make_sky():
    img = Image.new("RGB", (int(W * S), int(H * S)))
    d = ImageDraw.Draw(img)
    top, bot = (110, 185, 255), (205, 238, 255)
    h = int(H * S)
    for y in range(h):
        u = int(y / h * 7) / 6
        d.line([(0, y), (int(W * S), y)], fill=lerpc(top, bot, u))
    return img


def make_hills():
    img = Image.new("RGBA", (int(W * S), int(H * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ell(d, 250, 760, 650, 300, (120, 205, 115))
    ell(d, 1100, 780, 620, 310, (100, 192, 105))
    d.rectangle([0, P(600), int(W * S), int(H * S)], fill=(85, 178, 90))
    ell(d, 640, 640, 900, 70, (85, 178, 90))
    rng = random.Random(3)
    cols = [(255, 255, 255), (255, 230, 90), (255, 170, 200), (200, 170, 255)]
    for _ in range(40):
        x, y = rng.uniform(20, 1260), rng.uniform(560, 715)
        if 820 < x < 980 and y < 640:
            continue
        c = rng.choice(cols)
        for k in range(5):
            a = k * 2 * math.pi / 5
            circ(d, x + 5 * math.cos(a), y + 5 * math.sin(a), 4, c)
        circ(d, x, y, 3, (255, 200, 50))
    return img


SKY = make_sky()
HILLS = make_hills()
BASE = SKY.copy()
BASE.paste(HILLS, (0, 0), HILLS)


# ---------------------------------------------------------------- pieces
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


def plain_cloud(d, x, y, k):
    for dx, dy, r in [(-40, 5, 28), (0, -12, 36), (40, 5, 28)]:
        circ(d, x + dx * k, y + dy * k, r * k, (250, 252, 255))
    d.rounded_rectangle([P(x - 62 * k), P(y), P(x + 62 * k), P(y + 32 * k)],
                        radius=P(16 * k), fill=(250, 252, 255))


CLOUD = [(-70, 10, 50), (-25, -25, 62), (35, -15, 55), (75, 15, 42), (0, 20, 55)]


def pico(d, cx, cy, t, mood, tint=0.0, k=1.0, talk=0.0):
    edge = lerpc((175, 205, 240), (140, 160, 200), tint)
    body = lerpc((255, 255, 255), (222, 230, 245), tint)
    for grow, col in ((6, edge), (0, body)):
        for dx, dy, r in CLOUD:
            circ(d, cx + dx * k, cy + dy * k, r * k + grow, col)
        d.rounded_rectangle([P(cx - 115 * k - grow), P(cy - grow), P(cx + 115 * k + grow),
                             P(cy + 64 * k + grow)], radius=P(32 * k + grow), fill=col)
    ink = (45, 45, 80)
    ex = 28
    ey = cy + 14
    circ(d, cx - 54, cy + 38, 12, (255, 175, 195))
    circ(d, cx + 54, cy + 38, 12, (255, 175, 195))
    if mood == "closed":
        for sx in (-1, 1):
            d.arc([P(cx + sx * ex - 10), P(ey - 6), P(cx + sx * ex + 10), P(ey + 12)],
                  200, 340, fill=ink, width=P(4))
    else:
        blink = (t % 3.3) < 0.13
        hy = 2 if blink else 11
        for sx in (-1, 1):
            ell(d, cx + sx * ex, ey, 8, hy, ink)
            if not blink:
                circ(d, cx + sx * ex + 2, ey - 4, 3, (255, 255, 255))
    if mood == "worried":
        for sx in (-1, 1):
            d.line([P(cx + sx * ex - 10 * sx), P(ey - 22), P(cx + sx * ex + 8 * sx), P(ey - 16)],
                   fill=ink, width=P(4))
    if talk > 0.02:
        ell(d, cx, cy + 40, 11, 3 + 11 * talk, (130, 40, 60))
        ell(d, cx, cy + 44 + 6 * talk, 6, 2 + 3 * talk, (240, 110, 130))
    elif mood == "worried":
        ell(d, cx, cy + 42, 7, 9, (120, 40, 60))
    elif mood == "happy":
        d.pieslice([P(cx - 20), P(cy + 20), P(cx + 20), P(cy + 58)], 0, 180, fill=(130, 40, 60))
        ell(d, cx, cy + 48, 9, 5, (240, 110, 130))
    else:
        d.arc([P(cx - 16), P(cy + 24), P(cx + 16), P(cy + 46)], 20, 160, fill=ink, width=P(4))


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


def flower(d, t, droop, sway=0.0, talk=0.0):
    gx, gy = 900, 615
    a = droop * 1.2 + sway
    c = (gx, gy - 100)
    head = (gx - 135 * math.sin(a), gy - 100 - 95 * math.cos(a))
    pts = [bez((gx, gy), c, head, i / 24) for i in range(25)]
    green = lerpc((90, 175, 85), (125, 160, 95), droop)
    d.line([(P(x), P(y)) for x, y in pts], fill=green, width=P(10), joint="curve")
    lp = bez((gx, gy), c, head, 0.3)
    leaf(d, lp, -0.5 + droop * 0.9, 55, 16, green)
    leaf(d, lp, math.pi + 0.5 - droop * 0.9, 55, 16, green)
    hx, hy = head
    pet = lerpc((255, 100, 160), (195, 165, 180), droop)
    spin = sway * 2
    for i in range(8):
        ang = i * math.pi / 4 + spin
        circ(d, hx + 36 * math.cos(ang), hy + 36 * math.sin(ang), 27, pet)
    circ(d, hx, hy, 31, lerpc((255, 210, 60), (215, 195, 130), droop))
    ink = (80, 50, 40)
    if droop > 0.45:
        for sx in (-1, 1):
            d.arc([P(hx + sx * 11 - 7), P(hy - 6), P(hx + sx * 11 + 7), P(hy + 6)],
                  20, 160, fill=ink, width=P(3))
        d.arc([P(hx - 11), P(hy + 9), P(hx + 11), P(hy + 23)], 200, 340, fill=ink, width=P(3))
        ell(d, hx + 17, hy + 10, 3.5, 5, (110, 170, 255))
    else:
        circ(d, hx - 11, hy - 4, 4.5, ink)
        circ(d, hx + 11, hy - 4, 4.5, ink)
        if talk > 0.02:
            ell(d, hx, hy + 10, 8, 2 + 8 * talk, (140, 50, 60))
        else:
            d.pieslice([P(hx - 12), P(hy + 0), P(hx + 12), P(hy + 20)], 0, 180, fill=(140, 50, 60))
        circ(d, hx - 20, hy + 8, 5, (255, 150, 150))
        circ(d, hx + 20, hy + 8, 5, (255, 150, 150))
    return head


def star(d, x, y, r, rot, col):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = rot + i * math.pi / 5 - math.pi / 2
        pts.append((P(x + rr * math.cos(a)), P(y + rr * math.sin(a))))
    d.polygon(pts, fill=col)


def drop(d, x, y):
    circ(d, x, y, 7, (80, 155, 250))
    d.polygon([(P(x - 6.5), P(y - 2)), (P(x + 6.5), P(y - 2)), (P(x), P(y - 18))],
              fill=(80, 155, 250))
    circ(d, x - 2, y + 1, 2, (200, 225, 255))


RAINBOW = [(255, 120, 120), (255, 180, 100), (255, 230, 110),
           (140, 220, 120), (120, 180, 255), (180, 140, 240)]


def rainbow(d, p):
    cx, cy = 640, 760
    for i, col in enumerate(RAINBOW):
        r = 560 - i * 26
        d.arc([P(cx - r), P(cy - r), P(cx + r), P(cy + r)], 180, 180 + 180 * p,
              fill=col, width=P(27))


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
def scene(t, with_sun=True):
    rb = clamp01((t - 20.3) / 2.2)
    if rb > 0:
        img = SKY.copy()
    else:
        img = BASE.copy()
    d = ImageDraw.Draw(img)
    if with_sun:
        sun(d, t)
    for base, y, k, sp in [(300, 90, 0.9, 10), (900, 150, 0.7, 14), (1400, 60, 0.6, 8)]:
        x = (base + t * sp) % 1580 - 150
        plain_cloud(d, x, y, k)
    if rb > 0:
        rainbow(d, ease(rb))
        img.paste(HILLS, (0, 0), HILLS)
        d = ImageDraw.Draw(img)

    # Pico position / mood
    # accroche : Pico est à l'écran dès la 1re image et bouge tout de suite
    u = ease(t / 1.5)
    x, y = lerp(540, 640, u), 300 - 40 * math.sin(math.pi * min(1, t / 1.5))
    if t >= 5.6:
        u = ease((t - 5.6) / 3.4)
        x, y = lerp(640, 790, u), lerp(300, 225, u)
    if t >= 23.5:
        u = ease((t - 23.5) / 2.0)
        x, y = lerp(790, 600, u), lerp(225, 250, u)
    y += 8 * math.sin(2 * math.pi * 0.55 * t)
    mood = "smile"
    if 9.5 <= t < 12.3:
        mood = "worried"
    elif 12.3 <= t < 18.8:
        mood = "closed"
    elif t >= 18.8:
        mood = "happy"
    tint = min(ease((t - 12.0) / 0.6), ease((19.0 - t) / 0.6))
    k = 1.0 + (0.03 * math.sin(t * 9) if 12.5 < t < 18.5 else 0)

    droop = 1 - ease((t - 14.5) / 4.0)
    sway = 0.0
    if t > 18.5:
        sway = 0.09 * math.sin(2 * math.pi * 0.7 * (t - 18.5)) * min(1, (t - 18.5) / 0.8)

    # rain behind flower head? drops drawn before flower so the flower sits in front
    if 12.5 <= t <= 19.2:
        for i in range(130):
            t0 = 12.5 + i * 0.047
            if t < t0:
                break
            r = random.Random(i)
            dx = r.uniform(-85, 85)
            py = y + 60 + (t - t0) * 540
            if py < 612:
                drop(d, x + dx, py)
    head = flower(d, t, droop, sway, talking("flower", t))
    pico(d, x, y, t, mood, tint, k, talking("pico", t))
    if 18.8 < t < 25:
        g = (t - 18.8) / 6.2
        for i in range(8):
            a = i * math.pi / 4 + t * 0.8
            rr = 75 + 70 * g
            sz = 13 * math.sin(math.pi * min(1, g * 1.3)) * (0.8 + 0.3 * math.sin(t * 8 + i))
            if sz > 1:
                star(d, head[0] + rr * math.cos(a), head[1] + rr * math.sin(a), sz, t * 2 + i,
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
