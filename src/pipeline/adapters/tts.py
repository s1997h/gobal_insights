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
from typing import Protocol
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
        key = sha(self.name, voice, f"{rate:.3f}", text)
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
        ssml = (
            f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">'
            f'<voice name="{voice}"><prosody rate="{pct:+d}%">{escape(text)}</prosody></voice></speak>'
        )
        result = synth.speak_ssml_async(ssml).get()
        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            details = result.cancellation_details
            raise RuntimeError(f"Azure TTS failed: {details.reason} {details.error_details}")
        # release the file handle before the caller renames the file (matters on Windows)
        del synth
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


def build_tts(provider: str, offline: bool) -> TTS:
    if offline or provider == "fake":
        return FakeTTS()
    if provider == "azure":
        return AzureTTS()
    raise ValueError(f"unknown tts provider {provider!r}")


def write_silence(path: Path, ms: float) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(b"\x00\x00" * int(SAMPLE_RATE * ms / 1000))
