"""Voice: synthesize each scene (cached), pad to the scene length, join, and write words.json + timing.json.

A scene lasts the longer of its narration plus a 0.3 s tail, or its min_sec. Narration drives timing.
"""

from __future__ import annotations

import wave
from typing import Any

import numpy as np

from ..adapters.tts import SAMPLE_RATE
from ..checks import SHORT_HARD_LIMIT_SEC
from ..context import PipelineError, RunContext
from ..schemas import SceneSpan, ScriptDoc, Timing, WordTiming
from ..state import RunState
from ..util import read_json, write_json

TAIL_MS = 300.0


def _read_pcm(path: Any) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        if w.getframerate() != SAMPLE_RATE or w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise PipelineError(f"{path}: expected 24 kHz mono 16-bit WAV, got {w.getparams()}")
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")


def tts_node(ctx: RunContext, state: RunState) -> dict[str, Any]:
    p = ctx.paths
    voice, rate = ctx.style.narrator.voice, ctx.style.narrator.rate
    cache_dir = ctx.cfg.root / "cache" / "tts"
    for fmt in ctx.channel.formats:
        doc = ScriptDoc.model_validate(read_json(p.script(fmt)))
        parts: list[np.ndarray] = []
        words: list[WordTiming] = []
        spans: list[SceneSpan] = []
        offset_ms = 0.0
        new_chars = 0
        spoken_words = 0
        speech_ms = 0.0
        for scene in doc.scenes:
            chars = len(scene.narration)
            est = ctx.ledger.tts_cost(chars, ctx.tts.name)
            if est > 0:
                ctx.ledger.check_cap(est)
            res = ctx.tts.synth(scene.narration, voice, rate, cache_dir)
            if not res.cached:
                ctx.ledger.record(
                    "tts", f"tts:{ctx.tts.name}", float(chars), ctx.ledger.tts_cost(chars, ctx.tts.name)
                )
                new_chars += chars
            scene_ms = max(res.duration_ms + TAIL_MS, scene.min_sec * 1000.0)
            pcm = _read_pcm(res.wav_path)
            want = round(scene_ms / 1000 * SAMPLE_RATE)
            if len(pcm) < want:
                pcm = np.concatenate([pcm, np.zeros(want - len(pcm), dtype="<i2")])
            parts.append(pcm[:want])
            for w in res.words:
                words.append(
                    WordTiming(
                        word=w.word,
                        start_ms=w.start_ms + offset_ms,
                        end_ms=w.end_ms + offset_ms,
                        scene_id=scene.id,
                    )
                )
            spans.append(SceneSpan(id=scene.id, start_ms=offset_ms, end_ms=offset_ms + scene_ms))
            spoken_words += len(scene.narration.split())
            speech_ms += res.duration_ms
            offset_ms += scene_ms

        timing = Timing(total_sec=offset_ms / 1000, scenes=spans)
        out = p.narration(fmt)
        out.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(out), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(np.concatenate(parts).astype("<i2").tobytes())
        write_json(p.words(fmt), [w.model_dump() for w in words])
        write_json(p.timing(fmt), timing.model_dump())

        measured_wpm = spoken_words / (speech_ms / 60000) if speech_ms else 0
        ctx.log(
            f"tts[{fmt}]: {timing.total_sec:.1f}s, {len(doc.scenes)} scenes, {new_chars} new chars"
            + (
                f", measured pace {measured_wpm:.0f} wpm (style says {ctx.style.narrator.wpm})"
                if ctx.tts.name != "fake"
                else ""
            )
        )
        if fmt == "short" and timing.total_sec > SHORT_HARD_LIMIT_SEC + 0.5:
            raise PipelineError(
                f"The Short is {timing.total_sec:.1f}s; it must be under 60s. Cut narration, or set narrator.wpm in the style "
                f"to the measured pace ({measured_wpm:.0f}) so scripts are sized correctly, then run again."
            )
    return {}
