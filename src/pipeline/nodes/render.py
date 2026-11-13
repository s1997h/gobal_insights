"""Render: Remotion draws the picture from scenes + timing + words; FFmpeg adds ducked music and loudness."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from ..adapters.audio import duration_sec, mix_final
from ..checks import SHORT_HARD_LIMIT_SEC
from ..context import PipelineError, RunContext
from ..db import AssetRow, session_scope
from ..render_util import remotion, style_props
from ..schemas import RenderedAsset, ScriptDoc
from ..state import RunState
from ..util import read_json, sha, write_json

COMPOSITION = {"long": "Long", "short": "Short"}


def _pick_music(ctx: RunContext, seed: str) -> Path | None:
    tracks = [ctx.cfg.root / t for t in ctx.style.music.tracks]
    tracks = [t for t in tracks if t.exists()]
    if not tracks:
        return None
    return tracks[int(sha(seed), 16) % len(tracks)]


def render_node(ctx: RunContext, state: RunState) -> dict[str, Any]:
    p = ctx.paths
    p.final_dir.mkdir(parents=True, exist_ok=True)
    stats: dict[str, Any] = (
        read_json(p.render_dir / "stats.json") if (p.render_dir / "stats.json").exists() else {}
    )
    for fmt in ctx.channel.formats:
        doc = ScriptDoc.model_validate(read_json(p.script(fmt)))
        props = {
            "run_id": ctx.run_id,
            "format": fmt,
            "scenes": [s.model_dump() for s in doc.scenes],
            "timing": read_json(p.timing(fmt)),
            "words": read_json(p.words(fmt)),
            "images": read_json(p.image_map(fmt)) if p.image_map(fmt).exists() else {},
            "style": style_props(ctx),
        }
        props_path = p.render_dir / f"{fmt}.props.json"
        write_json(props_path, props)
        digest = sha(
            props_path.read_text(encoding="utf-8"), ctx.style.music.volume, str(_pick_music(ctx, ctx.run_id))
        )
        done = p.render_dir / f"{fmt}.done"
        final = p.final(fmt)
        if final.exists() and done.exists() and done.read_text() == digest:
            ctx.log(f"render[{fmt}]: unchanged, reusing {final.name}")
            continue

        raw = p.render_dir / f"{fmt}.silent.mp4"
        frames = round(float(props["timing"]["total_sec"]) * 30)  # type: ignore[index]
        ctx.log(f"render[{fmt}]: Remotion, {frames} frames ...")
        t0 = time.time()
        remotion(
            ctx,
            [
                "render",
                "src/index.ts",
                COMPOSITION[fmt],
                str(raw),
                f"--props={props_path}",
                f"--public-dir={p.run_dir}",
                "--muted",
                "--pixel-format=yuv420p",
                "--color-space=bt709",
            ],
            p.render_dir / f"{fmt}.log",
        )
        render_s = time.time() - t0
        t1 = time.time()
        mix_final(raw, p.narration(fmt), final, _pick_music(ctx, ctx.run_id), ctx.style.music.volume)
        mix_s = time.time() - t1
        dur = duration_sec(final)
        if fmt == "short" and dur > SHORT_HARD_LIMIT_SEC + 1:
            raise PipelineError(f"Rendered Short is {dur:.1f}s; it must be under 60s")
        done.write_text(digest)
        stats[fmt] = {
            "render_sec": round(render_s, 1),
            "mix_sec": round(mix_s, 1),
            "frames": frames,
            "fps_rendered": round(frames / render_s, 1) if render_s else None,
            "duration_sec": round(dur, 2),
        }
        write_json(p.render_dir / "stats.json", stats)
        with session_scope(ctx.sf) as s:
            asset = RenderedAsset(run_id=ctx.run_id, format=fmt, path=str(final), duration_sec=dur)  # type: ignore[arg-type]
            row = s.query(AssetRow).filter_by(run_id=ctx.run_id, format=fmt).one_or_none()
            if row is None:
                s.add(AssetRow(**asset.model_dump()))
            else:
                row.path, row.duration_sec = asset.path, asset.duration_sec
        ctx.log(
            f"render[{fmt}]: done in {render_s:.0f}s ({frames / max(render_s, 0.1):.1f} fps), {dur:.1f}s long -> {final.name}"
        )
    return {}
