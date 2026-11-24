import math, sys
from PIL import Image, ImageDraw
import anim_pixel as am
import story
from anim_pixel import (P, font, ease, back, lerp, lerpc, sun, plain_cloud, SPANS)

VW, VH, TOP = 720, 1280, 560     # vertical canvas in scene units; top panel height
CROP_X = 400                     # world x shown at left edge (si anim_pixel n'a pas de cam(t))
ZOOM = 1.5                       # le monde est agrandi 1,5x : les personnages sont GRANDS sur un téléphone
WY0 = 240                        # haut du monde montré (unités monde) ; le bas (720) touche le bas de l'écran
WIN = VW / ZOOM                  # largeur de monde visible : 480 unités


def cam_x0(t, x=None, head=None):
    """Bord gauche de la fenêtre (unités monde). Définis cam(t) dans anim_pixel.py pour suivre l'action ;
    sinon la caméra se centre entre le héros et l'ami."""
    if hasattr(am, "cam"):
        c = am.cam(t)
    elif x is not None and head is not None:
        c = (x + head[0]) / 2
    else:
        c = CROP_X + WIN / 2
    x0 = min(max(c - WIN / 2, 0), am.W - WIN)
    return int(x0 / 4) * 4       # arrondi au pixel : pas de tremblement


def world_sky_col():
    """Couleur du ciel du monde à la hauteur WY0, pour raccorder le panneau du haut."""
    am.S = am.SCENE_S
    img = am.scene(0, with_sun=False)[0]
    y = int(WY0 * am.SCENE_S)
    cols = [img.getpixel((x, y)) for x in range(0, img.width, 7)]
    return max(set(cols), key=cols.count)


def make_top_sky():
    am.S = am.SCENE_S
    img = Image.new("RGB", (int(VW * am.S), int(TOP * am.S)))
    d = ImageDraw.Draw(img)
    bot = world_sky_col()
    top = tuple(max(0, int(c * 0.8)) for c in bot)
    h = img.height
    for y in range(h):
        u = int(y / h * 5) / 5
        d.line([(0, y), (img.width, y)], fill=lerpc(top, bot, u))
    return img


TOP_SKY = make_top_sky()


def text_line(d, text, cx, y, sz, col, stroke=6):
    d.text((P(cx), P(y)), text, font=font(sz), fill=col, anchor="ms",
           stroke_width=P(stroke), stroke_fill=(255, 255, 255))


def title_v(d, t):
    if t > story.TITLE_OUT + 0.7:
        return
    out = ease((t - story.TITLE_OUT) / 0.6) * -520
    ci = 0
    ys = [300, 390, 460][:len(story.TITLE_LINES)]
    for li, ((text, sz), ybase) in enumerate(zip(story.TITLE_LINES, ys)):
        f = font(sz)
        x = 360 - f.getlength(text) / am.S / 2
        for i, ch in enumerate(text):
            k = i + sum(len(tl[0]) for tl in story.TITLE_LINES[:li])
            u = back((t + 0.2 - k * 0.03) / 0.4)
            if ch != " " and u > 0:
                yy = lerp(-160, ybase, u) + out + 6 * math.sin(t * 3 + k * 0.6)
                d.text((P(x), P(yy)), ch, font=f, fill=am.TITLE_COLS[ci % 6], anchor="ls",
                       stroke_width=P(7), stroke_fill=(255, 255, 255))
            if ch != " ":
                ci += 1
            x += f.getlength(ch) / am.S


def wrap(text, f, maxw):
    lines, cur = [], ""
    for w in text.split(" "):
        test = (cur + " " + w).strip()
        if f.getlength(test) / am.S <= maxw or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def caption_v(d, text, t0, t1, t):
    if not (t0 <= t <= t1):
        return
    u = min(ease((t - t0) / 0.4), ease((t1 - t) / 0.3))
    f = font(42)
    lines = wrap(text, f, 600)
    lh = 54
    bw = max(f.getlength(l) / am.S for l in lines) + 60
    bh = lh * len(lines) + 30
    x0 = 360 - bw / 2
    y0 = 500 - bh + (1 - u) * -60
    if u <= 0.01:
        return
    d.rounded_rectangle([P(x0 + 4), P(y0 + 6), P(x0 + bw + 4), P(y0 + bh + 6)], radius=P(30),
                        fill=(40, 90, 170))
    d.rounded_rectangle([P(x0), P(y0), P(x0 + bw), P(y0 + bh)], radius=P(30), fill=(255, 255, 255))
    for i, l in enumerate(lines):
        d.text((P(360), P(y0 + 15 + lh * i + lh / 2)), l, font=f, fill=(90, 60, 140), anchor="mm")


def bubble_v(d, text, ax, ay, u):
    """Bubble centered above anchor (ax, ay), tail pointing down."""
    f = font(26)
    w = f.getlength(text) / am.S + 36
    off = (1 - u) * 18
    y1 = ay - 18 + off
    y0 = y1 - 56
    x0 = min(max(ax - w / 2, 10), VW - 10 - w)
    ol = (90, 60, 140)
    tail = [(P(ax), P(ay + off * 0.3)), (P(ax - 14), P(y1 - 4)), (P(ax + 14), P(y1 - 4))]
    d.rounded_rectangle([P(x0 - 3), P(y0 - 3), P(x0 + w + 3), P(y1 + 3)], radius=P(28), fill=ol)
    d.polygon([(a, b + P(3)) for a, b in tail], fill=ol)
    d.rounded_rectangle([P(x0), P(y0), P(x0 + w), P(y1)], radius=P(26), fill=(255, 255, 255))
    d.polygon(tail, fill=(255, 255, 255))
    d.text((P(x0 + w / 2), P((y0 + y1) / 2)), text, font=f, fill=ol, anchor="mm")


def fin_v(d, t):
    if t < story.DURATION - 2.7:
        return
    u = back((t - story.DURATION + 2.7) / 0.7)
    d.text((P(360), P(330 + 6 * math.sin(t * 4))), "The End!", font=font(max(8, 110 * u)),
           fill=(255, 100, 150), anchor="mm", stroke_width=P(9 * u), stroke_fill=(255, 255, 255))


def frame(t):
    am.S = am.SCENE_S
    world, x, y, head = am.scene(t, with_sun=False)
    s = am.SCENE_S
    x0 = cam_x0(t, x, head)
    world = world.crop((int(x0 * s), int(WY0 * s), int((x0 + WIN) * s), world.height))
    top = TOP_SKY.copy()
    d = ImageDraw.Draw(top)
    for base, cy, k, sp in [(200, 300, 0.8, 9), (700, 420, 0.6, 13)]:
        plain_cloud(d, (base + t * sp) % 1000 - 150, cy, k)
    sun(d, t)
    am.S = am.TEXT_S
    ts = am.TEXT_S
    img = Image.new("RGB", (int(VW * ts), int(VH * ts)))
    img.paste(top.resize((int(VW * ts), int(TOP * ts)), Image.NEAREST), (0, 0))
    k = int(round(ZOOM * ts / s))
    img.paste(world.resize((world.width * k, world.height * k), Image.NEAREST), (0, int(TOP * ts)))
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    for who, t0, t1, text, side in SPANS:
        if t0 - 0.1 <= t <= t1 + 0.9:
            u = min(back((t - t0 + 0.1) / 0.3), ease((t1 + 0.9 - t) / 0.2))
            if who in getattr(am, "ANCHORS", {}):
                ax, ay = am.ANCHORS[who]
            elif who == story.HERO:
                ax, ay = x, y - 62
            else:
                ax, ay = head[0], head[1] - 58
            bubble_v(d, text, (ax - x0) * ZOOM, TOP + (ay - WY0) * ZOOM, u)
    title_v(d, t)
    for text, c0, c1 in story.CAPTIONS:
        caption_v(d, text, c0, c1, t)
    fin_v(d, t)
    am.S = am.SCENE_S
    return img.resize((1080, 1920), Image.NEAREST)


if __name__ == "__main__":
    if sys.argv[1] == "still":
        for tt in sys.argv[2:]:
            frame(float(tt)).save(f"vstill_{tt}.png")
    else:
        out = sys.stdout.buffer
        for n in range(int(sys.argv[2]), int(sys.argv[3])):
            out.write(frame(n / 30).tobytes())
