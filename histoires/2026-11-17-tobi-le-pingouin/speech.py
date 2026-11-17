import random, re

from story import LINES


def syllables(text):
    """Rough French syllable split: one per vowel group, pauses at punctuation."""
    out = []
    for word in re.findall(r"[\wÀ-ÿ'-]+|[!?.,…]+", text):
        if re.match(r"[!?.,…]", word):
            out.append(None)
            continue
        n = max(1, len(re.findall(r"[aeiouyàâéèêëîïôûù]+", word.lower())))
        if word.lower().endswith("e") and n > 1:
            n -= 1
        out.extend(["s"] * n)
    return out


def schedule():
    """List of syllables: (speaker, t0, dur, pitch_factor, vowel)."""
    res, spans = [], []
    for li, (who, t0, text, side) in enumerate(LINES):
        rng = random.Random(li * 7 + 1)
        t = t0
        sylls = syllables(text)
        for i, s in enumerate(sylls):
            if s is None:
                t += 0.16
                continue
            dur = rng.uniform(0.11, 0.15)
            last = i == len(sylls) - 1 or sylls[i + 1] is None
            pf = rng.uniform(0.92, 1.12) * (1.12 if "!" in text and last else 1.0)
            res.append((who, t, dur * (1.4 if last else 1), pf, rng.randrange(5)))
            t += dur * (1.4 if last else 1) + 0.035
        spans.append((who, t0, t, text, side))
    return res, spans


SYLL, SPANS = schedule()


def talking(who, t):
    """Mouth openness 0..1 for a speaker at time t."""
    for w, t0, dur, _, _ in SYLL:
        if w == who and t0 <= t <= t0 + dur:
            u = (t - t0) / dur
            return 1 - abs(2 * u - 1) ** 2
    return 0.0
