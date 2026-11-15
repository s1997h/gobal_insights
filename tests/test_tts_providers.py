"""The voice adapters that need no network: word alignment, ElevenLabs timestamps, OpenAI with a stub client."""

import base64
import shutil
import wave

import numpy as np
import pytest

from pipeline.adapters.tts import SAMPLE_RATE, ElevenLabsTTS, OpenAITTS, align_words, chars_to_words


def _speechy(parts_ms: list[tuple[str, float]]) -> np.ndarray:
    """("on"/"off", ms) segments -> a signal with tone where 'on'."""
    out = []
    for kind, ms in parts_ms:
        n = int(SAMPLE_RATE * ms / 1000)
        t = np.arange(n) / SAMPLE_RATE
        out.append(0.3 * np.sin(2 * np.pi * 220 * t) if kind == "on" else np.zeros(n))
    return np.concatenate(out).astype(np.float32)


def test_align_words_puts_sentence_breaks_in_the_pauses():
    sig = _speechy([("off", 50), ("on", 1000), ("off", 400), ("on", 600), ("off", 50)])
    words = align_words(sig, "One two three four. Five six.")
    assert [w.word for w in words] == ["One", "two", "three", "four.", "Five", "six."]
    five = words[4]
    assert 1050 + 150 < five.start_ms < 1050 + 400 + 50  # starts inside or just after the pause
    assert words[3].end_ms <= five.start_ms
    assert all(w.end_ms > w.start_ms for w in words)


def test_align_words_single_sentence_spans_voiced_part():
    sig = _speechy([("off", 200), ("on", 800), ("off", 200)])
    words = align_words(sig, "Hello there friend.")
    assert words[0].start_ms == pytest.approx(200, abs=20)
    assert words[-1].end_ms == pytest.approx(1000, abs=20)


def test_chars_to_words():
    al = {
        "characters": list("Hi you."),
        "character_start_times_seconds": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
        "character_end_times_seconds": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
    }
    w = chars_to_words(al)
    assert [x.word for x in w] == ["Hi", "you."]
    assert w[1].start_ms == pytest.approx(300) and w[1].end_ms == pytest.approx(700)


class _Resp:
    def __init__(self, raw: bytes):
        self.raw = raw

    def read(self) -> bytes:
        return self.raw


class _Speech:
    def __init__(self):
        self.calls = []

    def create(self, **kw):
        self.calls.append(kw)
        pcm = (_speechy([("off", 100), ("on", 700), ("off", 100)]) * 32767).astype("<i2")
        return _Resp(pcm.tobytes())


class _Client:
    def __init__(self):
        self.audio = type("A", (), {})()
        self.audio.speech = _Speech()


def test_openai_tts_with_stub(tmp_path):
    client = _Client()
    tts = OpenAITTS(client=client)
    res = tts.synth("A short line.", "coral", 1.0, tmp_path)
    kw = client.audio.speech.calls[0]
    assert kw["model"] == "gpt-4o-mini-tts" and kw["voice"] == "coral" and kw["response_format"] == "pcm"
    assert "narrating" in kw["instructions"]
    with wave.open(str(res.wav_path)) as w:
        assert w.getframerate() == SAMPLE_RATE and w.getnchannels() == 1
    assert 700 <= res.duration_ms <= 800  # trimmed to the voice plus a little padding
    assert [x.word for x in res.words] == ["A", "short", "line."]
    again = tts.synth("A short line.", "coral", 1.0, tmp_path)
    assert again.cached and len(client.audio.speech.calls) == 1


def test_openai_needs_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        OpenAITTS()


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_elevenlabs_with_stub(tmp_path):
    import subprocess

    mp3 = tmp_path / "t.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=220:d=0.6", str(mp3)], check=True
    )
    seen = {}

    def fake_post(url, body):
        seen["url"], seen["body"] = url, body
        return {
            "audio_base64": base64.b64encode(mp3.read_bytes()).decode(),
            "alignment": {
                "characters": list("Hi you."),
                "character_start_times_seconds": [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3],
                "character_end_times_seconds": [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.5],
            },
        }

    tts = ElevenLabsTTS(key="k", http=fake_post)
    res = tts.synth("Hi you.", "VOICE123", 0.9, tmp_path / "cache")
    assert "VOICE123" in seen["url"] and seen["body"]["voice_settings"]["speed"] == 0.9
    assert [w.word for w in res.words] == ["Hi", "you."]
    assert res.duration_ms == pytest.approx(600, abs=60)


def test_elevenlabs_needs_key(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ELEVENLABS_API_KEY"):
        ElevenLabsTTS()
