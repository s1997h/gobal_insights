"""Where things live on disk."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def project_root() -> Path:
    """The folder that holds config/ and pyproject.toml.

    Order: PIPELINE_ROOT env var, then the current directory and its parents, then the
    folder this package was installed from (editable installs).
    """
    env = os.environ.get("PIPELINE_ROOT")
    if env:
        return Path(env).resolve()
    here = Path.cwd().resolve()
    for p in [here, *here.parents]:
        if (p / "config" / "platforms.yaml").exists():
            return p
    guess = Path(__file__).resolve().parents[2]
    if (guess / "config" / "platforms.yaml").exists():
        return guess
    raise FileNotFoundError(
        "Could not find the project root (a folder with config/platforms.yaml). "
        "Run from the project folder or set PIPELINE_ROOT."
    )


@dataclass(frozen=True)
class RunPaths:
    root: Path
    run_id: str

    @property
    def run_dir(self) -> Path:
        return self.root / "runs" / self.run_id

    # contracts
    def script(self, fmt: str) -> Path:
        return self.run_dir / f"script_{fmt}.json"

    @property
    def topic(self) -> Path:
        return self.run_dir / "topic.json"

    @property
    def critic(self) -> Path:
        return self.run_dir / "critic_report.json"

    @property
    def package(self) -> Path:
        return self.run_dir / "package.json"

    # audio
    def narration(self, fmt: str) -> Path:
        return self.run_dir / "audio" / f"{fmt}.wav"

    def words(self, fmt: str) -> Path:
        return self.run_dir / "audio" / f"{fmt}.words.json"

    def timing(self, fmt: str) -> Path:
        return self.run_dir / "audio" / f"{fmt}.timing.json"

    # visuals
    def images_dir(self, fmt: str) -> Path:
        return self.run_dir / "assets" / fmt

    def image_map(self, fmt: str) -> Path:
        return self.run_dir / "assets" / f"{fmt}.images.json"

    # render
    @property
    def render_dir(self) -> Path:
        return self.run_dir / "render"

    @property
    def final_dir(self) -> Path:
        return self.run_dir / "final"

    def final(self, fmt: str) -> Path:
        return self.final_dir / f"{fmt}.mp4"

    @property
    def thumbnail(self) -> Path:
        return self.final_dir / "thumbnail.png"

    @property
    def review(self) -> Path:
        return self.run_dir / "REVIEW.md"

    @property
    def fonts_dir(self) -> Path:
        return self.run_dir / "fonts"

    @property
    def out_root(self) -> Path:
        return self.root / "out"
