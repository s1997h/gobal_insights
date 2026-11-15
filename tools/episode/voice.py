"""Voice every shot, then write narration.wav, timing.json and words.json.

usage: python3 tools/episode/voice.py shots.json outdir [--provider kokoro|openai|elevenlabs] [--voice NAME] [--speed 0.9]

Keys come from the environment (.env): ELEVENLABS_API_KEY or OPENAI_API_KEY. Kokoro needs its model files
in KOKORO_DIR (see KokoroTTS in src/pipeline/adapters/tts.py).

Pacing is varied the way a person reads: short punchy shots a little slower, dense fact shots a
little quicker, a longer beat after a punchline or a question, and a real pause between chapters.
"""

import argparse
import hashlib
import json
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pipeline.adapters.tts import SAMPLE_RATE, ElevenLabsTTS, KokoroTTS, OpenAITTS  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("shots")
ap.add_argument("out")
ap.add_argument("--provider", default="kokoro")
ap.add_argument("--voice", default=None)
ap.add_argument("--speed", type=float, default=0.9)
a = ap.parse_args()

out = Path(a.out)
out.mkdir(parents=True, exist_ok=True)
doc = json.loads(Path(a.shots).read_text())
shots = doc["shots"]
CHAPTER_STARTS = {c[0] for c in doc.get("chapters", [])}
if a.provider == "kokoro":
    tts, voice = KokoroTTS(), a.voice or "af_heart"
elif a.provider == "openai":
    tts, voice = OpenAITTS(), a.voice or "coral"
elif a.provider == "elevenlabs":
    tts, voice = ElevenLabsTTS(), a.voice
    if not voice:
        sys.exit("--voice <ElevenLabs voice id> is required")
else:
    sys.exit(f"unknown provider {a.provider}")


def pace(text: str, sid: str) -> float:
    n = len(text.split())
    r = a.speed
    if n <= 8:
        r -= 0.04  # let short lines land
    elif n >= 30:
        r += 0.03  # dense facts move a little faster
    if text.rstrip().endswith("?"):
        r -= 0.01
    jitter = (int(hashlib.md5(sid.encode()).hexdigest()[:4], 16) / 65535 - 0.5) * 0.02
    return round(r + jitter, 3)


def tail_ms(i: int) -> float:
    text = shots[i]["n"].rstrip()
    last = text.split(". ")[-1]
    nxt = shots[i + 1]["id"] if i + 1 < len(shots) else None
    if nxt in CHAPTER_STARTS:
        return 750.0
    if text.endswith("?"):
        return 480.0
    if len(last.split()) <= 4:
        return 520.0  # punchline
    return 300.0


parts, words, spans = [], [], []
offset = 0.0
for i, s in enumerate(shots):
    rate = pace(s["n"], s["id"])
    res = tts.synth(s["n"], voice, rate, out / "cache")
    with wave.open(str(res.wav_path), "rb") as w:
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    ms = max(res.duration_ms + tail_ms(i), float(s.get("min", 0)) * 1000)
    want = round(ms / 1000 * SAMPLE_RATE)
    pcm = np.concatenate([pcm, np.zeros(max(0, want - len(pcm)), dtype="<i2")])[:want]
    parts.append(pcm)
    for wd in res.words:
        words.append(
            {
                "word": wd.word,
                "start_ms": wd.start_ms + offset,
                "end_ms": wd.end_ms + offset,
                "scene_id": s["id"],
            }
        )
    spans.append({"id": s["id"], "start_ms": offset, "end_ms": offset + ms, "speech_ms": res.duration_ms})
    offset += ms
    print(
        f"{i + 1}/{len(shots)} {s['id']} rate {rate} {ms / 1000:.1f}s (total {offset / 1000:.0f}s)",
        flush=True,
    )

with wave.open(str(out / "narration.wav"), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SAMPLE_RATE)
    w.writeframes(np.concatenate(parts).tobytes())
(out / "timing.json").write_text(json.dumps({"total_sec": offset / 1000, "scenes": spans}, indent=1))
(out / "words.json").write_text(json.dumps(words))
n = sum(len(s["n"].split()) for s in shots)
speech = sum(sp["speech_ms"] for sp in spans) / 60000
print(f"TOTAL {offset / 1000:.1f}s = {offset / 60000:.2f} min; speech pace {n / speech:.0f} wpm")
