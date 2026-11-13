"""Shared fixtures. Every test works in a throwaway copy of the project: no keys, no network, no real renders."""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from pipeline.config import AppConfig, load_config
from pipeline.context import RunContext
from pipeline.db import get_engine, init_db, make_session_factory
from pipeline.runner import build_context, create_run
from pipeline.util import read_json

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch project root: copied config and prompts, linked assets and renderer."""
    root = tmp_path / "proj"
    root.mkdir()
    shutil.copytree(REPO / "config", root / "config")
    shutil.copytree(REPO / "prompts", root / "prompts")
    (root / "assets").symlink_to(REPO / "assets")
    (root / "render").symlink_to(REPO / "render")
    monkeypatch.setenv("PIPELINE_ROOT", str(root))
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def cfg(project: Path) -> AppConfig:
    return load_config(project)


@pytest.fixture
def sf(project: Path) -> Any:
    engine = get_engine(project)
    init_db(engine)
    return make_session_factory(engine)


class RemotionStub:
    """Stands in for the Remotion CLI: writes a valid black clip (render) or a PNG (still)."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.fail_on: str | None = None  # e.g. "Long": raise when this composition is rendered

    def __call__(self, ctx: RunContext, args: list[str], log_path: Path, *, render: bool = True) -> None:
        self.calls.append(args)
        if self.fail_on and args[2] == self.fail_on:
            self.fail_on = None  # fail once, like a crash
            raise RuntimeError("simulated renderer crash")
        out = Path(args[3])
        out.parent.mkdir(parents=True, exist_ok=True)
        if args[0] == "still":
            Image.new("RGB", (1280, 720), (11, 27, 51)).save(out)
            return
        props = next(a for a in args if a.startswith("--props=")).split("=", 1)[1]
        total = float(read_json(Path(props))["timing"]["total_sec"])
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"color=c=black:s=320x180:r=30:d={total:.2f}",
                "-pix_fmt",
                "yuv420p",
                str(out),
            ],
            check=True,
        )


@pytest.fixture
def remotion_stub(monkeypatch: pytest.MonkeyPatch) -> RemotionStub:
    stub = RemotionStub()
    monkeypatch.setattr("pipeline.nodes.render.remotion", stub)
    monkeypatch.setattr("pipeline.nodes.package.remotion", stub)
    return stub


MakeCtx = Callable[..., RunContext]


@pytest.fixture
def make_ctx(cfg: AppConfig, sf: Any) -> MakeCtx:
    def _make(run_id: str = "20260101-000000-whatif", channel: str = "whatif", **options: Any) -> RunContext:
        opts = {"offline": True, "quick": True, **options}
        create_run(sf, channel, run_id, opts)
        return build_context(cfg, channel, run_id, opts, sf)

    return _make


needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
