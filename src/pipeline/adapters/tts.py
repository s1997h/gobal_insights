"""Text to speech with word timings. One scene at a time, cached under a hash of provider, voice, rate and text,
so an edited script only re-voices the scenes that changed.

Output is 24 kHz 16-bit mono WAV (no MP3 encoder delay, so word timings stay exact).
"""

from __future__ import annotations

import hashlib
import math
import os
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from xml.sax.saxutils import escape

import numpy as np

from ..schemas import WordTiming
from ..util import read_json, sha, wav_duration_ms, write_json

SAMPLE_RATE = 24000


@dataclass
class SynthResult:
    wav_path: Path
    duration_ms: float
    words: list[WordTiming]
    chars: int
    cached: bool


class TTS(Protocol):
    name: str

    def synth(self, text: str, voice: str, rate: float, cache_dir: Path) -> SynthResult: ...


class _CachedTTS:
    name = "base"

    def _synth_to(self, text: str, voice: str, rate: float, out_wav: Path) -> list[WordTiming]:
        raise NotImplementedError

    def synth(self, text: str, voice: str, rate: float, cache_dir: Path) -> SynthResult:
        cache_dir.mkdir(parents=True, exist_ok=True)
        extra = getattr(self, "voice_params", "") if "HD" in voice else ""
        key = sha(self.name, voice, f"{rate:.3f}", text, *([extra] if extra else []))
        wav, meta = cache_dir / f"{key}.wav", cache_dir / f"{key}.json"
        if wav.exists() and meta.exists():
            words = [WordTiming.model_validate(w) for w in read_json(meta)["words"]]
            return SynthResult(wav, wav_duration_ms(wav), words, len(text), cached=True)
        tmp = wav.with_suffix(".tmp.wav")
        words = self._synth_to(text, voice, rate, tmp)
        os.replace(tmp, wav)
        write_json(
            meta, {"text": text, "voice": voice, "rate": rate, "words": [w.model_dump() for w in words]}
        )
        return SynthResult(wav, wav_duration_ms(wav), words, len(text), cached=False)


class AzureTTS(_CachedTTS):
    """Azure Neural TTS. Word-boundary events give the word timings that drive the captions."""

    name = "azure"

    # extra `parameters` for HD voices (e.g. "temperature=0.9"); set by the caller, part of the cache key
    voice_params: str = ""

    def __init__(self, key: str | None = None, region: str | None = None):
        self.key = key or os.environ.get("AZURE_SPEECH_KEY")
        self.region = region or os.environ.get("AZURE_SPEECH_REGION")
        if not self.key or not self.region:
            raise RuntimeError(
                "AZURE_SPEECH_KEY and AZURE_SPEECH_REGION are not set (put them in .env). "
                "Use --offline to run without keys."
            )

    def _synth_to(self, text: str, voice: str, rate: float, out_wav: Path) -> list[WordTiming]:
        import azure.cognitiveservices.speech as speechsdk

        cfg = speechsdk.SpeechConfig(subscription=self.key, region=self.region)
        cfg.speech_synthesis_voice_name = voice
        cfg.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm)
        synth = speechsdk.SpeechSynthesizer(
            speech_config=cfg, audio_config=speechsdk.audio.AudioOutputConfig(filename=str(out_wav))
        )
        words: list[WordTiming] = []

        def on_word(e: speechsdk.SessionEventArgs) -> None:  # type: ignore[name-defined]
            if e.boundary_type == speechsdk.SpeechSynthesisBoundaryType.Word:
                start = e.audio_offset / 10_000  # 100-ns ticks to ms
                words.append(
                    WordTiming(word=e.text, start_ms=start, end_ms=start + e.duration.total_seconds() * 1000)
                )

        synth.synthesis_word_boundary.connect(on_word)
        pct = round((rate - 1.0) * 100)
        lang = voice.split("-")[0] + "-" + voice.split("-")[1] if voice.count("-") >= 2 else "en-US"
        # HD voices pace themselves and accept only part of SSML, so send no <prosody> at the normal rate
        body = escape(text) if pct == 0 else f'<prosody rate="{pct:+d}%">{escape(text)}</prosody>'
        params = self.voice_params if "HD" in voice else ""

        def speak(p: str, engine: Any = synth) -> Any:
            attr = f' parameters="{escape(p)}"' if p else ""
            return engine.speak_ssml_async(
                f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">'
                f'<voice name="{voice}"{attr}>{body}</voice></speak>'
            ).get()

        result = speak(params)
        if params and result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            # this voice does not take the parameters: drop them for the rest of the run and say it plainly
            words.clear()
            type(self).voice_params = self.voice_params = ""
            result = speak("")
        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            details = result.cancellation_details
            raise RuntimeError(f"Azure TTS failed: {details.reason} {details.error_details}")
        # release the file handle before the caller renames the file (matters on Windows)
        del synth
        if not words:  # this voice sent no word events: estimate the timings from the audio itself
            with wave.open(str(out_wav), "rb") as w:
                sig = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768
            return align_words(sig, text)
        return words


class FakeTTS(_CachedTTS):
    """Offline stand-in: a short tone burst per word, with believable timings. For tests and dry runs only."""

    name = "fake"

    def _synth_to(self, text: str, voice: str, rate: float, out_wav: Path) -> list[WordTiming]:
        words: list[WordTiming] = []
        chunks: list[np.ndarray] = []
        t_ms = 0.0
        for tok in text.split():
            dur = (0.16 + 0.05 * len(tok.strip(".,;:!?\"'"))) / max(rate, 0.5)
            n = int(SAMPLE_RATE * dur)
            ts = np.arange(n) / SAMPLE_RATE
            f0 = 150 + int(hashlib.md5(tok.encode()).hexdigest()[:2], 16) % 90
            env = np.hanning(n) ** 0.6
            sig = 0.20 * env * (np.sin(2 * math.pi * f0 * ts) + 0.4 * np.sin(2 * math.pi * 2 * f0 * ts))
            chunks.append(sig)
            words.append(WordTiming(word=tok, start_ms=t_ms, end_ms=t_ms + dur * 1000))
            t_ms += dur * 1000
            gap = 0.04
            if tok.endswith((",", ";", ":")):
                gap += 0.22
            elif tok.endswith((".", "!", "?")):
                gap += 0.42
            gap /= max(rate, 0.5)
            chunks.append(np.zeros(int(SAMPLE_RATE * gap)))
            t_ms += gap * 1000
        audio = np.concatenate(chunks) if chunks else np.zeros(SAMPLE_RATE // 4)
        pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2")
        with wave.open(str(out_wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(pcm.tobytes())
        return words


def _sentences(text: str) -> list[str]:
    import re

    return [p for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p]


def _voiced_span(sig: np.ndarray, sr: int = SAMPLE_RATE) -> tuple[int, int]:
    """First and last sample of actual speech (models pad each clip with a little silence)."""
    win = sr // 100  # 10 ms
    n = len(sig) // win
    if n == 0:
        return 0, len(sig)
    rms = np.sqrt(np.mean(sig[: n * win].astype(np.float64).reshape(n, win) ** 2, axis=1))
    thr = max(1e-4, 0.06 * float(rms.max()))
    loud = np.nonzero(rms > thr)[0]
    if len(loud) == 0:
        return 0, len(sig)
    return int(loud[0] * win), int(min(len(sig), (loud[-1] + 1) * win))


def align_words(sig: np.ndarray, text: str, sr: int = SAMPLE_RATE) -> list[WordTiming]:
    """Word timings for a clip that has no timestamps of its own.

    Sentence boundaries are put at the longest pauses inside the voiced part (one fewer than the number of
    sentences); words inside a sentence share its time by length. Exact enough for captions.
    """
    sents = _sentences(text) or [text]
    a, b = _voiced_span(sig, sr)
    win = sr // 100
    seg = sig[a:b].astype(np.float64)
    n = len(seg) // win
    bounds = [a, b]
    if len(sents) > 1 and n > 4:
        rms = np.sqrt(np.mean(seg[: n * win].reshape(n, win) ** 2, axis=1))
        quiet = rms < max(1e-4, 0.05 * float(rms.max()))
        runs: list[tuple[int, int, int]] = []  # (length, start, end) in windows
        i = 0
        while i < n:
            if quiet[i]:
                j = i
                while j < n and quiet[j]:
                    j += 1
                runs.append((j - i, i, j))
                i = j
            else:
                i += 1
        best = sorted(runs, reverse=True)[: len(sents) - 1]
        cuts = sorted(a + ((st + en) // 2) * win for _, st, en in best)
        if len(cuts) == len(sents) - 1:
            bounds = [a, *cuts, b]
        else:  # not enough pauses: split by text length
            w = np.array([len(x) for x in sents], dtype=float)
            edges = np.concatenate([[0], np.cumsum(w)]) / w.sum()
            bounds = [int(a + e * (b - a)) for e in edges]
    words: list[WordTiming] = []
    for k, sent in enumerate(sents):
        s0, s1 = bounds[k], bounds[k + 1]
        toks = sent.split()
        if not toks:
            continue
        weights = np.array([len(t.strip(".,;:!?\"'")) + 2 for t in toks], dtype=float)
        edges = np.concatenate([[0], np.cumsum(weights)]) / weights.sum()
        for j, tok in enumerate(toks):
            words.append(
                WordTiming(
                    word=tok,
                    start_ms=(s0 + edges[j] * (s1 - s0)) / sr * 1000,
                    end_ms=(s0 + edges[j + 1] * (s1 - s0)) / sr * 1000,
                )
            )
    return words


def _write_pcm(out_wav: Path, audio: np.ndarray) -> None:
    pcm = audio if audio.dtype == np.dtype("<i2") else (np.clip(audio, -1, 1) * 32767).astype("<i2")
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.tobytes())


def _trim(sig: np.ndarray, pad_ms: float = 40) -> np.ndarray:
    a, b = _voiced_span(sig)
    pad = int(SAMPLE_RATE * pad_ms / 1000)
    return sig[max(0, a - pad) : min(len(sig), b + pad)]


class KokoroTTS(_CachedTTS):
    """Kokoro-82M, a free voice model that runs on the CPU: no account, no key, no network after download.

    Voices are names like "af_heart" (American female) or "am_michael" (American male); rate maps to speed.
    A whole scene is voiced in one pass so sentences flow into each other the way a person reads; word
    timings come from align_words().

    Model files (download once, about 350 MB) go in KOKORO_DIR, default ~/.cache/videopipe/kokoro:
      https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
      https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
    """

    name = "kokoro2"

    def __init__(self, model_dir: str | None = None):
        d = Path(model_dir or os.environ.get("KOKORO_DIR") or Path.home() / ".cache" / "videopipe" / "kokoro")
        model, voices = d / "kokoro-v1.0.onnx", d / "voices-v1.0.bin"
        if not model.exists() or not voices.exists():
            raise RuntimeError(
                f"Kokoro model files not found in {d}. Download kokoro-v1.0.onnx and voices-v1.0.bin "
                "(links in the KokoroTTS docstring) or set KOKORO_DIR."
            )
        from kokoro_onnx import Kokoro

        self._k = Kokoro(str(model), str(voices))

    def _synth_to(self, text: str, voice: str, rate: float, out_wav: Path) -> list[WordTiming]:
        sig, sr = self._k.create(text, voice=voice, speed=rate, lang="en-us")
        if sr != SAMPLE_RATE:
            raise RuntimeError(f"Kokoro returned {sr} Hz; expected {SAMPLE_RATE}")
        sig = _trim(np.asarray(sig, dtype=np.float32))
        _write_pcm(out_wav, sig)
        return align_words(sig, text)


NARRATOR_INSTRUCTIONS = (
    "You are narrating a calm, curious explainer video. Speak like a real person telling a friend a "
    "fascinating story: warm, lightly amused, never salesy. Vary your pace naturally, slow down a little "
    "for surprising numbers, let short punchlines land with a beat of silence, and sound like you are "
    "smiling slightly on the funny lines. American English."
)


class OpenAITTS(_CachedTTS):
    """OpenAI gpt-4o-mini-tts: steerable with plain-English instructions, about $0.015 a minute.

    Needs OPENAI_API_KEY. Voices: alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer, verse.
    OPENAI_TTS_INSTRUCTIONS overrides the default narrator direction.
    """

    name = "openai"

    def __init__(self, client: object | None = None, model: str = "gpt-4o-mini-tts"):
        if client is None:
            if not os.environ.get("OPENAI_API_KEY"):
                raise RuntimeError("OPENAI_API_KEY is not set (put it in .env).")
            from openai import OpenAI

            client = OpenAI(max_retries=4, timeout=300)
        self.client = client
        self.model = model
        self.instructions = os.environ.get("OPENAI_TTS_INSTRUCTIONS") or NARRATOR_INSTRUCTIONS
        self.name = f"openai-{sha(self.instructions)[:8]}"

    def _synth_to(self, text: str, voice: str, rate: float, out_wav: Path) -> list[WordTiming]:
        resp = self.client.audio.speech.create(  # type: ignore[attr-defined]
            model=self.model,
            voice=voice,
            input=text,
            instructions=self.instructions,
            response_format="pcm",  # 24 kHz, 16-bit, mono
            speed=rate,
        )
        raw = resp.read() if hasattr(resp, "read") else bytes(resp.content)
        sig = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768
        sig = _trim(sig)
        _write_pcm(out_wav, sig)
        return align_words(sig, text)


class ElevenLabsTTS(_CachedTTS):
    """ElevenLabs: the most human-sounding option, with exact character timestamps.

    Needs ELEVENLABS_API_KEY and a voice id from your ElevenLabs Voice Library (narrator.voice in the style).
    A paid plan (Starter or higher) is needed to use the audio commercially. rate maps to speed (0.7-1.2).
    """

    name = "elevenlabs"
    URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps"

    def __init__(self, key: str | None = None, model: str | None = None, http: object | None = None):
        self.key = key or os.environ.get("ELEVENLABS_API_KEY")
        if not self.key:
            raise RuntimeError("ELEVENLABS_API_KEY is not set (put it in .env).")
        self.model = model or os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
        self.http = http

    def _post(self, url: str, body: dict) -> dict:
        if self.http is not None:
            return self.http(url, body)  # type: ignore[operator]
        import httpx

        r = httpx.post(
            url,
            json=body,
            headers={"xi-api-key": str(self.key)},
            params={"output_format": "mp3_44100_128"},
            timeout=300,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"ElevenLabs error {r.status_code}: {r.text[:300]}")
        return r.json()

    def _synth_to(self, text: str, voice: str, rate: float, out_wav: Path) -> list[WordTiming]:
        import base64
        import subprocess
        import tempfile

        body = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": 0.4,
                "similarity_boost": 0.75,
                "style": 0.2,
                "use_speaker_boost": True,
                "speed": max(0.7, min(1.2, rate)),
            },
        }
        data = self._post(self.URL.format(voice=voice), body)
        mp3 = base64.b64decode(data["audio_base64"])
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(mp3)
            src = f.name
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    src,
                    "-ac",
                    "1",
                    "-ar",
                    str(SAMPLE_RATE),
                    "-c:a",
                    "pcm_s16le",
                    str(out_wav),
                ],
                check=True,
            )
        finally:
            os.unlink(src)
        return chars_to_words(data.get("alignment") or {})


def chars_to_words(al: dict) -> list[WordTiming]:
    """ElevenLabs character alignment -> word timings."""
    chars = al.get("characters") or []
    starts = al.get("character_start_times_seconds") or []
    ends = al.get("character_end_times_seconds") or []
    words: list[WordTiming] = []
    cur, t0, t1 = "", 0.0, 0.0
    for c, a, b in zip(chars, starts, ends, strict=False):
        if c.isspace():
            if cur:
                words.append(WordTiming(word=cur, start_ms=t0 * 1000, end_ms=t1 * 1000))
            cur = ""
            continue
        if not cur:
            t0 = a
        cur += c
        t1 = b
    if cur:
        words.append(WordTiming(word=cur, start_ms=t0 * 1000, end_ms=t1 * 1000))
    return words


def build_tts(provider: str, offline: bool) -> TTS:
    if offline or provider == "fake":
        return FakeTTS()
    if provider == "azure":
        return AzureTTS()
    if provider == "kokoro":
        return KokoroTTS()
    if provider == "openai":
        return OpenAITTS()
    if provider == "elevenlabs":
        return ElevenLabsTTS()
    raise ValueError(f"unknown tts provider {provider!r}")


def write_silence(path: Path, ms: float) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(b"\x00\x00" * int(SAMPLE_RATE * ms / 1000))
