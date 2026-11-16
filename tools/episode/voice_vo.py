"""Voice every shot like a recorded voice-over, then write narration.wav, timing.json and words.json.

usage: python3 tools/episode/voice_vo.py shots.json outdir [--blend af_heart:0.42,hf_alpha:0.46,bf_emma:0.12] [--lang en-gb]

Free and local (Kokoro, model files in KOKORO_DIR). Differences from voice.py:
- the voice is a blend of Kokoro voices (the default is a lightly Indian-English narrator);
- each sentence is spoken on its own, so questions and punchlines can be slower and lists quicker;
- pitch moves a little from sentence to sentence, the way a person's does;
- pauses depend on what was just said (longer after a question and before a punchline).
The mix adds microphone colour and room tone (see make.sh, style "vo").
"""

import argparse
import hashlib
import json
import os
import re
import wave
from pathlib import Path

import numpy as np
from kokoro_onnx import Kokoro
from scipy.signal import resample_poly

SR = 24000
ap = argparse.ArgumentParser()
ap.add_argument("shots")
ap.add_argument("out")
ap.add_argument("--blend", default="af_heart:0.42,hf_alpha:0.46,bf_emma:0.12")
ap.add_argument("--lang", default="en-gb")
ap.add_argument("--speed", type=float, default=0.93)
a = ap.parse_args()

out = Path(a.out)
cache = out / "cache_vo"
cache.mkdir(parents=True, exist_ok=True)
doc = json.loads(Path(a.shots).read_text())
shots = doc["shots"]
CHAPTER_STARTS = {c[0] for c in doc.get("chapters", [])}
kdir = Path(os.environ.get("KOKORO_DIR", Path.home() / ".cache/videopipe/kokoro"))
tts = Kokoro(str(kdir / "kokoro-v1.0.onnx"), str(kdir / "voices-v1.0.bin"))
style = sum(tts.get_voice_style(n) * float(w) for n, w in (x.split(":") for x in a.blend.split(",")))


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.?!])\s+(?=[A-Z\"'])", text.strip())
    return [p for p in parts if p.strip()]


def h(s: str) -> float:
    return int(hashlib.md5(s.encode()).hexdigest()[:6], 16) / 0xFFFFFF  # 0..1, stable


def plan(sents: list[str]) -> list[tuple[float, float, float]]:
    """(speed, pitch, pause after in seconds) for each sentence of one shot."""
    res = []
    for i, s in enumerate(sents):
        n = len(s.split())
        last = i == len(sents) - 1
        speed = a.speed
        pitch = 1 + (h(s) - 0.5) * 0.024
        if s.endswith("?"):
            speed, pitch = speed - 0.04, pitch + 0.008
        if n <= 3:
            speed -= 0.05
        elif n >= 18:
            speed += 0.02
        if last and len(sents) > 1 and n <= 6:  # punchline
            speed, pitch = speed - 0.06, pitch - 0.02
        nxt = sents[i + 1] if not last else ""
        if last:
            pause = 0.0
        elif n <= 3 and len(nxt.split()) <= 3:
            pause = 0.19  # a quick list
        elif s.endswith("?"):
            pause = 0.5
        elif i == len(sents) - 2 and len(nxt.split()) <= 6:
            pause = 0.52  # beat before the punchline
        else:
            pause = 0.33
        res.append((round(speed, 3), round(pitch, 4), round(pause * (0.9 + 0.2 * h(s + "p")), 3)))
    return res


def trim(x: np.ndarray) -> np.ndarray:
    idx = np.where(np.abs(x) > 0.008)[0]
    return x[max(0, idx[0] - 300) : idx[-1] + 1400] if len(idx) else x


def speak(text: str, speed: float, pitch: float) -> np.ndarray:
    key = hashlib.md5(f"{a.blend}|{a.lang}|{speed}|{pitch}|{text}".encode()).hexdigest()[:16]
    f = cache / f"{key}.npy"
    if f.exists():
        return np.load(f)
    x, _ = tts.create(text, voice=style, speed=speed / pitch, lang=a.lang)
    x = trim(x)
    if abs(pitch - 1) > 1e-3:
        x = resample_poly(x, 1000, int(round(1000 * pitch)))
    n = int(0.012 * SR)
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    x = x.astype(np.float32)
    np.save(f, x)
    return x


def tail(i: int) -> float:
    text = shots[i]["n"].rstrip()
    nxt = shots[i + 1]["id"] if i + 1 < len(shots) else None
    if nxt in CHAPTER_STARTS:
        return 0.8
    if text.endswith("?"):
        return 0.5
    if len(sentences(text)[-1].split()) <= 4:
        return 0.52
    return 0.32


parts, words, spans = [], [], []
offset = 0.0  # seconds
for i, s in enumerate(shots):
    sents = sentences(s["n"])
    t0 = offset
    speech_end = offset
    for sent, (speed, pitch, pause) in zip(sents, plan(sents), strict=True):
        x = speak(sent, speed, pitch)
        dur = len(x) / SR
        toks = sent.split()
        wts = np.array([len(t.strip(".,;:!?\"'")) + 2 for t in toks], dtype=float)
        edges = np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
        voiced = dur - 1400 / SR  # the trim keeps a short tail
        for j, tok in enumerate(toks):
            words.append({"word": tok, "start_ms": (offset + edges[j] * voiced) * 1000, "end_ms": (offset + edges[j + 1] * voiced) * 1000, "scene_id": s["id"]})
        parts += [x, np.zeros(int(SR * pause), dtype=np.float32)]
        offset += dur + int(SR * pause) / SR
        speech_end = offset - int(SR * pause) / SR
    want = max(speech_end - t0 + tail(i), float(s.get("min", 0)))
    pad = max(0, int(round((t0 + want - offset) * SR)))
    parts.append(np.zeros(pad, dtype=np.float32))
    offset += pad / SR
    spans.append({"id": s["id"], "start_ms": t0 * 1000, "end_ms": offset * 1000, "speech_ms": (speech_end - t0) * 1000})
    print(f"{i + 1}/{len(shots)} {s['id']} {offset - t0:.1f}s (total {offset:.0f}s)", flush=True)

cat = np.concatenate(parts)
peak = float(np.max(np.abs(cat)))
print(f"raw peak {peak:.2f}")
if peak > 0.9:
    cat = cat * (0.9 / peak)
pcm = (cat * 32767).astype("<i2")
with wave.open(str(out / "narration.wav"), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
total = len(pcm) / SR
(out / "timing.json").write_text(json.dumps({"total_sec": total, "scenes": spans}, indent=1))
(out / "words.json").write_text(json.dumps(words))
n = sum(len(s["n"].split()) for s in shots)
print(f"TOTAL {total:.1f}s = {total / 60:.2f} min; {n} words")
