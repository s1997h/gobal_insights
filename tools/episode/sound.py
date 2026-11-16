"""Make the music bed and the sound-effects track for the episode, both 48 kHz stereo WAV.

usage: python3 tools/episode/sound.py shots.json audio/timing.json outdir
The synthesis lives in src/pipeline/episode/sound.py so the automated `pipeline episode` command shares it.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pipeline.episode.sound import build_tracks  # noqa: E402

if __name__ == "__main__":
    shots = json.loads(Path(sys.argv[1]).read_text())["shots"]
    timing = json.loads(Path(sys.argv[2]).read_text())
    music, fx = build_tracks(shots, timing, Path(sys.argv[3]))
    print("wrote", fx, music, f"{timing['total_sec']:.1f}s")
