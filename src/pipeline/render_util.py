"""Calling Remotion: props files, font staging and the CLI wrapper shared by the render and package nodes."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .context import PipelineError, RunContext

_WEIGHTS = {"Regular": "400", "Medium": "500", "SemiBold": "600", "Bold": "700", "ExtraBold": "800"}


def stage_fonts(ctx: RunContext) -> list[dict[str, str]]:
    """Copy bundled font files for the style's font into the run folder (Remotion's public dir)."""
    src = ctx.cfg.root / "assets" / "fonts"
    dst = ctx.paths.fonts_dir
    dst.mkdir(parents=True, exist_ok=True)
    out: list[dict[str, str]] = []
    family = ctx.style.font
    for path in sorted(src.glob(f"{family}-*")):
        if path.suffix.lower() not in (".otf", ".ttf", ".woff2", ".woff"):
            continue
        weight = _WEIGHTS.get(path.stem.split("-", 1)[1])
        if not weight:
            continue
        shutil.copyfile(path, dst / path.name)
        out.append({"file": f"fonts/{path.name}", "weight": weight})
    return out


def style_props(ctx: RunContext) -> dict[str, object]:
    s = ctx.style
    return {
        "palette": s.palette.model_dump(),
        "font": s.font,
        "fonts": stage_fonts(ctx),
        "captions": {
            "max_words_per_line": s.captions.max_words_per_line,
            "highlight": s.highlight_hex(),
            "position": s.captions.position,
        },
        "channel_name": ctx.channel.name,
    }


def remotion(ctx: RunContext, args: list[str], log_path: Path, *, render: bool = True) -> None:
    npx = shutil.which("npx")
    if not npx:
        raise PipelineError(
            "npx not found. Install Node.js 20+ (https://nodejs.org) and run `npm ci` in the render folder."
        )
    render_dir = ctx.cfg.root / "render"
    if not (render_dir / "node_modules").exists():
        raise PipelineError(f"Run `npm ci` in {render_dir} first (Remotion is not installed).")
    cmd = [npx, "remotion", *args, "--log=warn"]
    chrome = os.environ.get("PIPELINE_CHROME")
    if chrome:
        cmd.append(f"--browser-executable={chrome}")
    conc = os.environ.get("RENDER_CONCURRENCY")
    if conc and render:
        cmd.append(f"--concurrency={conc}")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(cmd, cwd=render_dir, stdout=log, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        tail = log_path.read_text(encoding="utf-8", errors="replace")[-1800:]
        raise PipelineError(f"Remotion failed (exit {proc.returncode}). Log: {log_path}\n{tail}")
