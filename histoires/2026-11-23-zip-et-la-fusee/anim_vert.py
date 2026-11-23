import math, random, sys
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


def make_top_sky(bot):
    """Ciel étoilé du panneau du haut, raccordé à la couleur du ciel du monde en haut de la fenêtre."""
    am.S = am.SCENE_S
    img = Image.new("RGB", (int(VW * am.S), int(TOP * am.S)))
    d = ImageDraw.Draw(img)
    top = (12, 10, 40)
    h = img.height
    for y in range(h):
        u = int(y / h * 6) / 6
        d.line([(0, y), (img.width, y)], fill=lerpc(top, bot, u))
    return img


_SKIES = {}


def top_sky(wy0):
    bot = am.sky_col(wy0)
    if bot not in _SKIES:
        _SKIES[bot] = make_top_sky(bot)
    return _SKIES[bot].copy()


TOP_STARS = [(random.Random(i).uniform(0, VW), random.Random(i + 300).uniform(0, TOP),
              random.Random(i + 700).uniform(0, 6.28)) for i in range(70)]
TOP_FW = [(23.6, 200, 230), (24.2, 520, 170), (24.8, 330, 300), (25.6, 600, 260), (26.2, 150, 150),
          (26.9, 450, 220)]


def top_decor(d, t):
    am.stars(d, t, VW, TOP, TOP_STARS)
    am.ringed_planet(d, 600, 120, 34)
    am.moon(d, 110, 90, 20)
    g = (t % 7.0) / 0.9                                   # étoile filante
    if g < 1:
        x, y = lerp(80, 560, g), lerp(40, 190, g)
        for i in range(6):
            am.circ(d, x - i * 16, y - i * 5, 5 - i * 0.7, (255, 250, 200))
    if t > 23.0:
        for i, (f0, fx, fy) in enumerate(TOP_FW):
            am.firework(d, fx, fy, (t - f0) / 1.3, am.FW_COLS[(i + 2) % len(am.FW_COLS)])



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
    wy0 = int(am.cam_y(t) / 4) * 4 if hasattr(am, "cam_y") else WY0
    world = world.crop((int(x0 * s), int(wy0 * s), int((x0 + WIN) * s), int((wy0 + VW * (VH - TOP) / VW / ZOOM) * s)))
    top = top_sky(wy0)
    d = ImageDraw.Draw(top)
    top_decor(d, t)
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
            bubble_v(d, text, (ax - x0) * ZOOM, TOP + (ay - wy0) * ZOOM, u)
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
