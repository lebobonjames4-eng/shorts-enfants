import math, sys
from PIL import Image, ImageDraw
import anim_pixel as am
import story
from anim_pixel import (P, font, ease, back, lerp, lerpc, circ, ell, bubbles, SPANS)

VW, VH, TOP = 720, 1280, 560     # vertical canvas in scene units; top panel height
CROP_X = 400                     # world x shown at left edge


def make_top_sky():
    am.S = am.SCENE_S
    img = Image.new("RGB", (int(VW * am.S), int(TOP * am.S)))
    d = ImageDraw.Draw(img)
    top, bot = (150, 225, 248), am.WATER_TOP
    h = img.height
    for y in range(h):
        u = int(y / h * 5) / 5
        d.line([(0, y), (img.width, y)], fill=lerpc(top, bot, u))
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for x0 in (120, 380, 640):
        od.polygon([(P(x0), 0), (P(x0 + 80), 0), (P(x0 - 60), P(TOP)), (P(x0 - 180), P(TOP))],
                   fill=(255, 255, 255, 30))
    img.paste(ov, (0, 0), ov)
    return img


def surface(d, t):
    pts = [(P(x), P(38 + 8 * math.sin(x / 45 + t * 2))) for x in range(0, VW + 20, 10)]
    d.polygon([(0, 0)] + pts + [(P(VW), 0)], fill=(205, 245, 255))
    d.line(pts, fill=(255, 255, 255), width=P(6))


def little_fish(d, x, y, col, face=1):
    ell(d, x, y, 26, 15, col)
    d.polygon([(P(x - face * 20), P(y)), (P(x - face * 42), P(y - 14)), (P(x - face * 42), P(y + 14))], fill=col)
    circ(d, x + face * 12, y - 3, 3.5, (40, 40, 70))


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
    world = world.crop((int(CROP_X * s), 0, int((CROP_X + VW) * s), world.height))
    top = TOP_SKY.copy()
    d = ImageDraw.Draw(top)
    surface(d, t)
    for base, cy, sp, col, fc in [(100, 170, 40, (255, 235, 120), 1), (650, 520, -30, (140, 230, 210), -1)]:
        little_fish(d, (base + t * sp) % 900 - 90, cy + 10 * math.sin(t * 2 + base), col, fc)
    bubbles(d, t, 20, 700, 60, TOP + 40, 6, 77)
    if t > 24.3:
        bubbles(d, t, 20, 700, 60, TOP + 60, int(14 * ease((t - 24.3) / 1.0)), 900, party=1.0, t0=24.3)
    img = Image.new("RGB", (int(VW * s), int(VH * s)))
    img.paste(top, (0, 0))
    img.paste(world, (0, int(TOP * s)))

    am.S = am.TEXT_S
    img = img.resize((int(VW * am.S), int(VH * am.S)), Image.NEAREST)
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    for who, t0, t1, text, side in SPANS:
        if t0 - 0.1 <= t <= t1 + 0.9:
            u = min(back((t - t0 + 0.1) / 0.3), ease((t1 + 0.9 - t) / 0.2))
            if who == story.HERO:
                ax, ay = x, y - 80
            elif who == "star":
                ax, ay = am.STAR_HEAD
            else:
                ax, ay = head[0], head[1] - 58
            bubble_v(d, text, ax - CROP_X, ay + TOP, u)
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
