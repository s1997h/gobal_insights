"""Build the soundtrack from the four vidIQ voice takes and mux it onto the silent picture.

usage: PYTHONPATH=src python3 episodes/kodak-pov/audio.py <dir with chris_a.mp3 chris_b.mp3 bill.mp3 sarah.mp3 hooks.mp3>

Also builds the four Shorts (work/shorts/s<k>) when their silent pictures exist; hooks.mp3 is the
take with their new first lines.

Each line is cut from its take (work/lines.json: src, src_start, dur), levelled so the three voices
sit at the same loudness, and placed at its slot on the timeline (work/audio_plan.json). Music and
sound effects come from the pipeline's synth (sfx named in the shots), and the mix uses the pipeline's
chain: voice EQ and compression, music ducked under the voice, -14 LUFS.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from pipeline.episode.produce import mix
from pipeline.episode.sound import SR, write

HERE = Path(__file__).parent
WORK = HERE / "work"
AUD = WORK / "audio"
FADE = int(0.012 * SR)


def load(path: Path) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def rms_active(x: np.ndarray) -> float:
    """RMS over the louder half of 50 ms windows, so pauses don't drag it down."""
    n = int(0.05 * SR)
    w = x[: len(x) // n * n].reshape(-1, n)
    r = np.sqrt((w**2).mean(axis=1))
    r = np.sort(r)[len(r) // 2 :]
    return float(np.sqrt((r**2).mean()))


def place(plan: dict, takes: dict, gain: dict, out_dir: Path) -> None:
    """Cut every line from its take and lay it on the timeline -> out_dir/narration.wav."""
    total = float(plan["total_sec"])
    voice = np.zeros(int((total + 1) * SR))
    for ln in plan["lines"]:
        take = takes[ln["src"]]
        a = int(ln["src_start"] * SR)
        b = min(len(take), a + int(ln["dur"] * SR))
        seg = take[a:b] * gain[ln["src"]]
        if len(seg) == 0:
            raise SystemExit(f"a line is outside its take {ln['src']}")
        f = min(FADE, len(seg) // 4)
        seg[:f] *= np.linspace(0, 1, f)
        seg[-f:] *= np.linspace(1, 0, f)
        s = int(ln["at"] * SR)
        voice[s : s + len(seg)] += seg
    voice = voice[: int(total * SR)]
    out_dir.mkdir(parents=True, exist_ok=True)
    write(out_dir / "narration.wav", np.stack([voice, voice], axis=1) * (0.89 / np.abs(voice).max()))


def mux(pic: Path, audio: Path, final: Path) -> None:
    final.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(pic), "-i", str(audio), "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(final)],
        check=True,
    )
    print("video:", final)


def main(src_dir: Path) -> None:
    names = ["chris_a", "chris_b", "bill", "sarah"] + (["hooks"] if (src_dir / "hooks.mp3").exists() else [])
    takes = {name: load(src_dir / f"{name}.mp3") for name in names}
    ref = rms_active(takes["chris_a"])
    gain = {k: ref / max(1e-6, rms_active(v)) for k, v in takes.items()}
    print("levelling:", {k: round(g, 2) for k, g in gain.items()})

    plan = json.loads((WORK / "audio_plan.json").read_text())
    props = json.loads((WORK / "props.json").read_text())
    place(plan, takes, gain, AUD)
    out = mix(AUD, props["shots"], props["timing"], music_volume=0.16)
    mux(WORK / "render" / "picture.mp4", out, HERE / "out" / "What If You Invented the Digital Camera.mp4")

    for k in range(1, 5):
        d = WORK / "shorts" / f"s{k}"
        if "hooks" not in takes or not (d / "picture.mp4").exists():
            continue
        plan = json.loads((d / "audio_plan.json").read_text())
        props = json.loads((d / "props.json").read_text())
        place(plan, takes, gain, d / "audio")
        out = mix(d / "audio", props["shots"], props["timing"], music_volume=0.18)
        mux(d / "picture.mp4", out, HERE / "out" / "shorts" / f"short{k}.mp4")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
