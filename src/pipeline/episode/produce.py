"""Voice, picture and sound for a directed episode: the mechanical half of `pipeline episode`.

Everything here is resumable. Voice clips are cached by text, video is rendered in chunks that are
renamed only when Remotion exits cleanly, and nothing is re-made when its inputs did not change.
"""

from __future__ import annotations

import math
import re
import shutil
import wave
from pathlib import Path
from typing import Any

import numpy as np

from ..adapters.audio import run as ffmpeg
from ..adapters.tts import SAMPLE_RATE, SynthResult
from ..context import PipelineError, RunContext
from ..nodes.tts import _read_pcm
from ..render_util import remotion
from ..util import read_json, sha, write_json
from .sound import build_tracks

FPS = 30
CHUNK_FRAMES = 2400  # 80 s of video per Remotion call: bounded memory, and a crash loses one chunk
Shot = dict[str, Any]

# Silence left after a shot's last word, in seconds.
TAIL = 0.32
TAIL_QUESTION = 0.52  # a question needs a beat to land
TAIL_CARD = 0.5  # numbers and lists stay up long enough to read
TAIL_CHAPTER_END = 0.8  # a breath before the next chapter


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def script_words(text: str, res: SynthResult) -> list[dict[str, Any]]:
    """Word timings that carry the script's own spelling and punctuation.

    Voice engines report bare words ("failed") while captions need the script's tokens ("failed.").
    Tokens are matched to the engine's words in order; if they do not line up (the engine split or
    merged something), the script tokens share the spoken span in proportion to their length.
    """
    tokens = text.split()
    spoken = [w for w in res.words if _norm(w.word)]
    out: list[dict[str, Any]] = []
    j = 0
    for tok in tokens:
        want = _norm(tok)
        if not want:  # a lone dash or similar: attach to the previous word
            if out:
                out[-1]["word"] += f" {tok}"
            continue
        got, k = "", j
        while k < len(spoken) and len(got) < len(want):
            got += _norm(spoken[k].word)
            k += 1
        if got != want:
            out = []
            break
        out.append({"word": tok, "start_ms": spoken[j].start_ms, "end_ms": spoken[k - 1].end_ms})
        j = k
    if out and j == len(spoken):
        return out
    start = spoken[0].start_ms if spoken else 0.0
    end = spoken[-1].end_ms if spoken else res.duration_ms
    real = [t for t in tokens if _norm(t)] or tokens
    weights = np.array([len(_norm(t)) + 2 for t in real], dtype=float)
    edges = start + np.concatenate([[0.0], np.cumsum(weights)]) / weights.sum() * (end - start)
    return [
        {"word": t, "start_ms": float(edges[i]), "end_ms": float(edges[i + 1])} for i, t in enumerate(real)
    ]


class Narrator:
    """The channel's voice, with the cost ledger and a fallback voice for regions that lack the first choice."""

    def __init__(self, ctx: RunContext):
        self.ctx = ctx
        n = ctx.style.narrator
        self.voice, self.rate = n.voice, n.rate
        self.fallback = n.fallback_voice
        self.cache = ctx.cfg.root / "cache" / "tts"
        self.new_chars = 0
        self.spoke = False  # once a clip exists in one voice, the video never switches to another

    def _price_key(self) -> str:
        return "azure_hd" if self.ctx.tts.name == "azure" and "HD" in self.voice else self.ctx.tts.name

    def say(self, text: str) -> SynthResult:
        ctx = self.ctx
        est = ctx.ledger.tts_cost(len(text), self._price_key())
        if est > 0:
            ctx.ledger.check_cap(est)
        try:
            res = ctx.tts.synth(text, self.voice, self.rate, self.cache)
        except Exception as e:  # noqa: BLE001 - any engine error on the first choice tries the fallback once
            if self.spoke or not self.fallback or self.fallback == self.voice:
                raise PipelineError(
                    f"The voice {self.voice!r} failed: {e}. Check AZURE_SPEECH_REGION (HD voices exist only in "
                    "some regions) or set narrator.fallback_voice in the channel's style file."
                ) from e
            ctx.log(f"voice: {self.voice} failed ({str(e)[:160]}); using {self.fallback} for this episode")
            self.voice, self.fallback = self.fallback, None
            res = ctx.tts.synth(text, self.voice, self.rate, self.cache)
        self.spoke = True
        if not res.cached:
            key = self._price_key()
            ctx.ledger.record("tts", f"tts:{key}", float(len(text)), ctx.ledger.tts_cost(len(text), key))
            self.new_chars += len(text)
        return res


def _tail(shot: Shot, next_is_chapter: bool) -> float:
    if next_is_chapter:
        return TAIL_CHAPTER_END
    if shot["n"].rstrip().endswith("?"):
        return TAIL_QUESTION
    if shot.get("ov"):
        return TAIL_CARD
    return TAIL


def voice(
    narrator: Narrator, shots: list[Shot], out: Path, chapter_ids: set[str] | None = None
) -> dict[str, Any]:
    """Voice every shot and join the clips. Writes narration.wav, timing.json and words.json into `out`."""
    out.mkdir(parents=True, exist_ok=True)
    chapter_ids = chapter_ids or set()
    parts: list[np.ndarray] = []
    words: list[dict[str, Any]] = []
    spans: list[dict[str, Any]] = []
    offset = 0.0
    speech_ms = 0.0
    for i, shot in enumerate(shots):
        res = narrator.say(shot["n"])
        nxt = shots[i + 1]["id"] if i + 1 < len(shots) else None
        ms = max(res.duration_ms + _tail(shot, nxt in chapter_ids) * 1000, float(shot.get("min", 0)) * 1000)
        ms = math.ceil(ms / 1000 * FPS) / FPS * 1000  # whole frames, so picture and sound never drift
        pcm = _read_pcm(res.wav_path)
        want = round(ms / 1000 * SAMPLE_RATE)
        if len(pcm) < want:
            pcm = np.concatenate([pcm, np.zeros(want - len(pcm), dtype="<i2")])
        parts.append(pcm[:want])
        for w in script_words(shot["n"], res):
            words.append(
                {"word": w["word"], "start_ms": w["start_ms"] + offset, "end_ms": w["end_ms"] + offset}
            )
        spans.append({"id": shot["id"], "start_ms": offset, "end_ms": offset + ms})
        speech_ms += res.duration_ms
        offset += ms
    with wave.open(str(out / "narration.wav"), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(np.concatenate(parts).astype("<i2").tobytes())
    timing = {"total_sec": offset / 1000, "scenes": spans}
    write_json(out / "timing.json", timing)
    write_json(out / "words.json", words)
    spoken = sum(len(s["n"].split()) for s in shots)
    return {**timing, "words": words, "wpm": spoken / (speech_ms / 60000) if speech_ms else 0.0}


def mix(audio_dir: Path, shots: list[Shot], timing: dict[str, Any], music_volume: float) -> Path:
    """Narration + ducked music + sound effects -> mix.m4a at about -14 LUFS with true peaks kept under 0 dB."""
    out = audio_dir / "mix.m4a"
    music, sfx = build_tracks(shots, timing, audio_dir)
    flt = (
        "[0:a]aresample=48000,highpass=f=80,equalizer=f=200:t=q:w=1:g=2,equalizer=f=3200:t=q:w=1.2:g=1.5,"
        "deesser=i=0.4,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=140:makeup=2,"
        "pan=stereo|c0=c0|c1=c0,asplit=2[voice][sc];"
        f"[1:a]volume={music_volume}[m];[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[duck];"
        "[2:a]volume=0.6[fx];[voice][duck][fx]amix=inputs=3:duration=first:normalize=0,"
        "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=192000,alimiter=limit=0.6:attack=1:release=60:level=false,"
        "aresample=48000,lowpass=f=19000[a]"
    )
    tmp = audio_dir / "mix.tmp.m4a"
    ffmpeg(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio_dir / "narration.wav"), "-i", str(music), "-i", str(sfx),
         "-filter_complex", flt, "-map", "[a]", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2", str(tmp)]
    )  # fmt: skip
    tmp.replace(out)
    return out


_BUNDLED: set[Path] = set()


def bundle(ctx: RunContext, work: Path) -> Path:
    """Build the renderer once per process. Every later render and still reuses it."""
    out = work / "bundle"
    if out in _BUNDLED and (out / "index.html").exists():
        return out
    public = work / "public"
    (public / "fonts").mkdir(parents=True, exist_ok=True)
    for f in (ctx.cfg.root / "assets" / "fonts").glob("*.otf"):
        shutil.copyfile(f, public / "fonts" / f.name)
    shutil.rmtree(out, ignore_errors=True)
    ctx.log("render: bundling the renderer ...")
    remotion(
        ctx,
        ["bundle", "src/index.ts", f"--out-dir={out}", f"--public-dir={public}"],
        work / "bundle.log",
        render=False,
    )
    _BUNDLED.add(out)
    return out


def render_video(
    ctx: RunContext, bundled: Path, comp: str, props: dict[str, Any], work: Path, name: str
) -> Path:
    """Render `comp` with `props` to work/<name>.silent.mp4, in chunks, skipping chunks already done."""
    work.mkdir(parents=True, exist_ok=True)
    props_path = work / f"{name}.props.json"
    write_json(props_path, props)
    digest = sha(props_path.read_text(encoding="utf-8"))
    out = work / f"{name}.silent.mp4"
    stamp = work / f"{name}.digest"
    chunks = work / f"{name}.chunks"
    if out.exists() and stamp.exists() and stamp.read_text() == digest:
        return out
    if not stamp.exists() or stamp.read_text() != digest:
        shutil.rmtree(chunks, ignore_errors=True)
        out.unlink(missing_ok=True)
        stamp.write_text(digest)
    chunks.mkdir(parents=True, exist_ok=True)
    total = max(FPS, math.ceil(float(props["timing"]["total_sec"]) * FPS))
    files: list[Path] = []
    for i, a in enumerate(range(0, total, CHUNK_FRAMES)):
        b = min(total, a + CHUNK_FRAMES) - 1
        part = chunks / f"c{i:03d}.mp4"
        files.append(part)
        if part.exists():
            continue
        tmp = chunks / f"c{i:03d}.tmp.mp4"
        ctx.log(f"render[{name}]: frames {a}-{b} of {total}")
        remotion(
            ctx,
            ["render", str(bundled), comp, str(tmp), f"--props={props_path}", f"--frames={a}-{b}", "--codec=h264",
             "--crf=18", "--pixel-format=yuv420p", "--color-space=bt709", "--muted"],
            work / f"{name}.render.log",
        )  # fmt: skip
        tmp.replace(part)
    if len(files) == 1:
        shutil.copyfile(files[0], out)
    else:
        listing = work / f"{name}.concat.txt"
        listing.write_text("".join(f"file '{f.as_posix()}'\n" for f in files), encoding="utf-8")
        tmp = work / f"{name}.silent.tmp.mp4"
        ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(listing),
                "-c",
                "copy",
                str(tmp),
            ]
        )
        tmp.replace(out)
    return out


def mux(video: Path, audio: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.stem + ".tmp.mp4")
    ffmpeg(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(audio), "-map", "0:v", "-map", "1:a",
         "-c", "copy", "-shortest", "-movflags", "+faststart", str(tmp)]
    )  # fmt: skip
    tmp.replace(out)
    return out


def still(
    ctx: RunContext, bundled: Path, comp: str, props: dict[str, Any], out: Path, frame: int = 0
) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    props_path = out.with_suffix(".props.json")
    write_json(props_path, props)
    args = ["still", str(bundled), comp, str(out), f"--props={props_path}", f"--frame={frame}"]
    if out.suffix.lower() in (".jpg", ".jpeg"):
        args += ["--image-format=jpeg", "--jpeg-quality=92"]
    remotion(ctx, args, out.with_suffix(".log"), render=False)
    props_path.unlink(missing_ok=True)
    out.with_suffix(".log").unlink(missing_ok=True)
    return out


def load_voice(audio_dir: Path) -> dict[str, Any] | None:
    """A finished voice step, or None."""
    t, w = audio_dir / "timing.json", audio_dir / "words.json"
    if t.exists() and w.exists() and (audio_dir / "narration.wav").exists():
        return {**read_json(t), "words": read_json(w)}
    return None
