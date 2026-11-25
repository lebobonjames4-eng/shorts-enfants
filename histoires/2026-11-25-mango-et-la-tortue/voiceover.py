"""Voix off : une conteuse à la voix jeune et enjouée lit chaque phrase de story.CAPTIONS (Piper, hors ligne).

Utilisé par audio_mix.py. Installer d'abord la voix avec ../../tts_setup.sh.
Si Piper est absent ou échoue, renvoie None : la vidéo se fait quand même, sans voix off
(audio_mix.py affiche « VOIX OFF ABSENTE »).
"""
import os, subprocess, wave
import numpy as np
import story

TTS_DIR = os.environ.get("TTS_DIR", os.path.expanduser("~/.cache/tts"))
PIPER = os.path.join(TTS_DIR, "piper", "piper")
MODEL = os.path.join(TTS_DIR, "en-us-libritts-high.onnx")
SPEAKER = getattr(story, "NARRATOR", 552)            # conteuse : voix claire et vivante (LibriTTS n° 552)
PITCH = getattr(story, "NARRATION_PITCH", 3)         # demi-tons en plus : voix plus jeune, « dessin animé »
SPEED = getattr(story, "NARRATION_SPEED", 1.1)       # > 1 = plus lent (enfants)
R = 2 ** (PITCH / 12)
DELAY = 0.25                                         # la voix commence 0,25 s après l'apparition du bandeau


def synth(text, path):
    # on synthétise R fois plus lent puis on rejoue R fois plus vite : même durée, voix plus aiguë
    subprocess.run([PIPER, "-m", MODEL, "--speaker", str(SPEAKER), "--length_scale", str(SPEED * R),
                    "--noise_scale", "0.75", "--noise_w", "0.9", "--sentence_silence", "0.3",
                    "-f", path], input=text.encode(), check=True, capture_output=True)
    w = wave.open(path)
    sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    w.close()
    nz = np.nonzero(np.abs(a) > 0.01)[0]              # enlève les silences au début et à la fin
    if len(nz):
        a = a[max(0, nz[0] - int(0.03 * sr)): nz[-1] + int(0.08 * sr)]
    return a, sr * R


def narration(SR, N):
    """Piste de voix off (numpy, SR Hz, N échantillons) ou None si indisponible."""
    if not (os.path.exists(PIPER) and os.path.exists(MODEL)):
        return None
    track = np.zeros(N)
    os.makedirs("tts", exist_ok=True)
    try:
        for i, (text, t0, t1) in enumerate(story.CAPTIONS):
            a, sr = synth(text, f"tts/n{i}.wav")
            x = np.linspace(0, len(a) - 1, int(len(a) * SR / sr))   # rééchantillonnage
            a = np.interp(x, np.arange(len(a)), a)
            dur = len(a) / SR
            room = t1 - t0 - DELAY
            if dur > room + 0.6:
                print(f"ATTENTION voix off trop longue : « {text} » dure {dur:.1f} s pour {room:.1f} s de bandeau")
            i0 = int((t0 + DELAY) * SR)
            n = min(len(a), N - i0)
            track[i0:i0 + n] += a[:n]
    except Exception as e:                                          # pas de voix off plutôt que pas de vidéo
        print("Piper a échoué :", e)
        return None
    return track / max(1e-9, np.abs(track).max())
