"""Make the music bed and the sound-effects track for the episode, both 48 kHz stereo WAV.

usage: python3 tools/episode/sound.py shots.json audio/timing.json outdir
Sound effects are written in shots.json as "name@fraction" (fraction of that shot's length).
Everything is synthesized here, so there is nothing to license.
"""

import json
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def tone(freq, dur, tau=0.25, harm=(1.0, 0.0, 0.0), vol=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = sum(a * np.sin(2 * np.pi * freq * (k + 1) * t) for k, a in enumerate(harm))
    return vol * sig * env_exp(n, tau) * np.minimum(1, np.arange(n) / (0.004 * SR))


def noise(dur):
    return rng.standard_normal(int(dur * SR))


def lowpass(x, cutoff):
    # one-pole low-pass, good enough for SFX
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def sfx(name):
    if name == "pop":
        n = int(0.09 * SR)
        t = np.arange(n) / SR
        f = 500 + 1400 * t / 0.09
        return 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.03)
    if name == "whoosh":
        x = noise(0.55)
        e = np.sin(np.linspace(0, np.pi, len(x))) ** 2
        return 0.35 * lowpass(x, 1400) * e * 3
    if name == "ding":
        return tone(1568, 0.9, 0.35, (1, 0.35, 0.12), 0.32) + tone(2349, 0.9, 0.25, (1,), 0.12)
    if name == "buzz":
        out = np.zeros(int(0.75 * SR))
        for k in range(3):
            n = int(0.16 * SR)
            t = np.arange(n) / SR
            b = 0.35 * np.sign(np.sin(2 * np.pi * 155 * t)) * (0.6 + 0.4 * np.sin(2 * np.pi * 31 * t))
            b = lowpass(b, 900) * np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (0.01 * SR))
            s = int(k * 0.24 * SR)
            out[s : s + n] += b
        return out
    if name == "tick":
        return tone(2600, 0.05, 0.008, (1,), 0.5)
    if name == "buzzer":
        n = int(0.38 * SR)
        t = np.arange(n) / SR
        b = 0.3 * np.sign(np.sin(2 * np.pi * 110 * t))
        return lowpass(b, 1200) * np.minimum(1, (n - np.arange(n)) / (0.04 * SR))
    if name == "drawer":
        x = lowpass(noise(0.32), 500) * 2.2 * np.linspace(0.3, 1, int(0.32 * SR))
        thump = tone(85, 0.25, 0.06, (1, 0.3), 0.8)
        return np.concatenate([x, thump])
    if name == "thud":
        return tone(65, 0.4, 0.09, (1, 0.4), 0.9) + 0.4 * lowpass(noise(0.4), 300) * env_exp(
            int(0.4 * SR), 0.05
        )
    if name == "alarm":
        out = np.zeros(int(1.6 * SR))
        for k in range(8):
            s = int(k * 0.2 * SR)
            b = tone(2093, 0.1, 0.5, (1, 0.3), 0.22)
            out[s : s + len(b)] += b
        return out
    if name == "ring":
        n = int(1.2 * SR)
        t = np.arange(n) / SR
        f = np.where(np.sin(2 * np.pi * 18 * t) > 0, 1320, 1660)
        return 0.18 * np.sin(2 * np.pi * np.cumsum(f) / SR) * (t < 1.0)
    if name == "flip":
        out = np.zeros(int(1.4 * SR))
        for k in range(10):
            s = int(k * 0.12 * SR)
            b = 0.25 * lowpass(noise(0.05), 3000) * env_exp(int(0.05 * SR), 0.015)
            out[s : s + len(b)] += b
        return out
    if name == "chop":
        return (
            0.5 * lowpass(noise(0.08), 4000) * env_exp(int(0.08 * SR), 0.02)
            + tone(180, 0.12, 0.03, (1,), 0.5)[: int(0.08 * SR)]
        )
    raise ValueError(name)


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


def music(total_sec):
    """A light, playful loop: plucked arpeggios over I-V-vi-IV, soft bass and a shaker. 100 BPM."""
    bpm = 100
    beat = 60 / bpm
    n = int(total_sec * SR) + SR
    L = np.zeros(n)
    R = np.zeros(n)
    chords = [[60, 64, 67, 72], [55, 59, 62, 67], [57, 60, 64, 69], [53, 57, 60, 65]]  # C G Am F
    bass = [36, 43, 45, 41]
    pattern = [0, 2, 1, 3, 2, 1, 3, 2]  # eighth-note arpeggio
    bar = 4 * beat
    nbars = int(total_sec / bar) + 2
    pluck_cache = {}
    for b in range(nbars):
        ch = chords[b % 4]
        t0 = b * bar
        for e in range(8):
            m = ch[pattern[e]] + (12 if (b // 8) % 2 and e % 4 == 3 else 0)
            key = m
            if key not in pluck_cache:
                pluck_cache[key] = tone(midi(m), 0.6, 0.18, (1, 0.25, 0.08), 0.16)
            p = pluck_cache[key]
            s = int((t0 + e * beat / 2) * SR)
            pan = 0.35 + 0.3 * (e % 2)
            if s + len(p) < n:
                L[s : s + len(p)] += p * (1 - pan)
                R[s : s + len(p)] += p * pan
        bn = tone(midi(bass[b % 4]), bar, 0.9, (1, 0.5, 0.2), 0.22)
        s = int(t0 * SR)
        if s + len(bn) < n:
            L[s : s + len(bn)] += bn
            R[s : s + len(bn)] += bn
        for q in range(8):  # shaker on eighths, accent on the off-beat
            sh = 0.05 * (1.6 if q % 2 else 1) * noise(0.04) * env_exp(int(0.04 * SR), 0.01)
            s = int((t0 + q * beat / 2) * SR)
            if s + len(sh) < n:
                L[s : s + len(sh)] += sh * 0.8
                R[s : s + len(sh)] += sh
        if b % 2 == 0:  # soft kick on 1 and 3
            for q in (0, 2):
                kk = tone(55, 0.25, 0.07, (1,), 0.35)
                s = int((t0 + q * beat) * SR)
                if s + len(kk) < n:
                    L[s : s + len(kk)] += kk
                    R[s : s + len(kk)] += kk
    out = np.stack([L, R], 1)[: int(total_sec * SR)]
    fade = int(3 * SR)
    out[:fade] *= np.linspace(0, 1, fade)[:, None]
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return out / (np.abs(out).max() + 1e-9) * 0.7


def write(path, stereo):
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    shots = json.loads(Path(sys.argv[1]).read_text())["shots"]
    timing = json.loads(Path(sys.argv[2]).read_text())
    out = Path(sys.argv[3])
    total = timing["total_sec"]
    fx = np.zeros((int(total * SR) + 2 * SR, 2))
    cache = {}
    for shot, span in zip(shots, timing["scenes"], strict=True):
        a, b = span["start_ms"] / 1000, span["end_ms"] / 1000
        for item in shot.get("sfx", []):
            name, frac = item.split("@")
            if name not in cache:
                cache[name] = sfx(name)
            s = int((a + float(frac) * (b - a)) * SR)
            snd = cache[name]
            fx[s : s + len(snd)] += snd[:, None] * np.array([1.0, 1.0])
    fx = fx[: int(total * SR)]
    write(out / "sfx.wav", fx * 0.9)
    write(out / "music.wav", music(total))
    print("wrote", out / "sfx.wav", out / "music.wav", f"{total:.1f}s")
