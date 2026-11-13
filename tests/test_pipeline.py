"""The graph end to end with fake providers and a stub renderer (real FFmpeg mixing)."""

from __future__ import annotations

from datetime import UTC
from typing import Any

import pytest
from sqlalchemy import select
from typer.testing import CliRunner

from pipeline.cli import app
from pipeline.db import PostRow, RunRow, session_scope
from pipeline.ledger import BudgetExceeded
from pipeline.runner import execute
from pipeline.schemas import Timing, WordTiming
from pipeline.util import read_json, wav_duration_ms

from .conftest import REPO, MakeCtx, RemotionStub, needs_ffmpeg

pytestmark = needs_ffmpeg


def status(sf: Any, run_id: str) -> str:
    with session_scope(sf) as s:
        row = s.get(RunRow, run_id)
        assert row is not None
        return row.status


def count_llm_calls(ctx: Any) -> list[str]:
    calls: list[str] = []
    orig = ctx.llm.generate

    def wrapped(tier: str, step: str, *a: Any, **k: Any) -> Any:
        calls.append(step)
        return orig(tier, step, *a, **k)

    ctx.llm.generate = wrapped
    return calls


def test_offline_run_reaches_review(make_ctx: MakeCtx, sf: Any, remotion_stub: RemotionStub) -> None:
    ctx = make_ctx()
    execute(ctx, {"run_id": ctx.run_id})
    assert status(sf, ctx.run_id) == "ready_for_review"
    p = ctx.paths

    for fmt in ("long", "short"):
        timing = Timing.model_validate(read_json(p.timing(fmt)))
        spans = timing.scenes
        assert spans[0].start_ms == 0
        assert all(a.end_ms == pytest.approx(b.start_ms) for a, b in zip(spans, spans[1:], strict=False))
        assert wav_duration_ms(p.narration(fmt)) == pytest.approx(timing.total_sec * 1000, abs=5)
        words = [WordTiming.model_validate(w) for w in read_json(p.words(fmt))]
        assert all(a.start_ms <= b.start_ms for a, b in zip(words, words[1:], strict=False))
        assert p.final(fmt).exists()

    out = p.out_root / "whatif" / ctx.run_id
    for folder in ("youtube-long", "youtube-short", "instagram-short"):
        assert (out / folder / "video.mp4").exists() and (out / folder / "UPLOAD.md").exists()
        assert read_json(out / folder / "meta.json")["title"]
    assert (out / "youtube-long" / "thumbnail.png").exists()
    assert "#Shorts" in read_json(out / "youtube-short" / "meta.json")["description"]
    with session_scope(sf) as s:
        posts = list(s.scalars(select(PostRow).where(PostRow.run_id == ctx.run_id)))
    assert {(r.platform, r.format, r.status) for r in posts} == {
        ("youtube", "long", "rehearsal"),
        ("youtube", "short", "rehearsal"),
        ("instagram", "short", "rehearsal"),
    }
    assert all(r.publish_at is not None for r in posts)


def test_critic_retry_then_pass(make_ctx: MakeCtx, sf: Any, remotion_stub: RemotionStub) -> None:
    ctx = make_ctx(fake_critic_fail_first=1)
    execute(ctx, {"run_id": ctx.run_id})
    report = read_json(ctx.paths.critic)
    assert [a["passed"] for a in report["attempts"]] == [False, True]
    assert status(sf, ctx.run_id) == "ready_for_review"


def test_critic_gives_up_after_two_rewrites(make_ctx: MakeCtx, sf: Any, remotion_stub: RemotionStub) -> None:
    ctx = make_ctx(fake_critic_fail_first=9)
    execute(ctx, {"run_id": ctx.run_id})
    assert len(read_json(ctx.paths.critic)["attempts"]) == 3
    assert status(sf, ctx.run_id) == "needs_review"
    assert not remotion_stub.calls  # nothing rendered


def test_resume_after_crash_skips_finished_steps(
    make_ctx: MakeCtx, sf: Any, remotion_stub: RemotionStub
) -> None:
    ctx = make_ctx()
    calls = count_llm_calls(ctx)
    remotion_stub.fail_on = "Long"
    with pytest.raises(RuntimeError, match="simulated"):
        execute(ctx, {"run_id": ctx.run_id})
    assert status(sf, ctx.run_id) == "failed"
    assert calls == ["topic", "script", "critic"]
    execute(ctx, None)  # resume
    assert calls == ["topic", "script", "critic", "package"]
    assert status(sf, ctx.run_id) == "ready_for_review"


def test_budget_cap_stops_before_paid_step(make_ctx: MakeCtx, sf: Any, remotion_stub: RemotionStub) -> None:
    ctx = make_ctx()
    ctx.cfg.prices.tts["fake"] = {"usd_per_million_chars": 100_000.0, "free_chars_per_month": 0.0}
    ctx.ledger.channel = ctx.channel.model_copy(
        update={"budget": ctx.channel.budget.model_copy(update={"per_video_usd": 0.01})}
    )
    with pytest.raises(BudgetExceeded):
        execute(ctx, {"run_id": ctx.run_id})
    with session_scope(sf) as s:
        row = s.get(RunRow, ctx.run_id)
        assert row is not None and row.status == "failed" and (row.error or "").startswith("budget")
    assert not ctx.paths.narration("long").exists()


def test_build_from_hand_written_scripts(project: Any, remotion_stub: RemotionStub) -> None:
    res = CliRunner().invoke(
        app,
        [
            "build",
            "--channel",
            "whatif",
            "--long",
            str(REPO / "examples/long.json"),
            "--short",
            str(REPO / "examples/short.json"),
            "--offline",
        ],
    )
    assert res.exit_code == 0, res.output
    assert "ready_for_review" in res.output
    pkg = read_json(next((project / "runs").iterdir()) / "package.json")
    assert [c["title"] for c in pkg["chapters"]][0] == "Intro" and len(pkg["chapters"]) >= 3


def test_dry_run_and_bad_channel(project: Any) -> None:
    runner = CliRunner()
    assert runner.invoke(app, ["run", "--channel", "whatif", "--dry-run"]).exit_code == 0
    assert runner.invoke(app, ["run", "--channel", "nope", "--dry-run"]).exit_code != 0


@pytest.mark.slow
@pytest.mark.skipif(
    not __import__("os").environ.get("RUN_RENDER_TESTS"), reason="set RUN_RENDER_TESTS=1 (needs Node, Chrome)"
)
def test_real_render(make_ctx: MakeCtx, sf: Any) -> None:
    """A real Remotion render of a quick offline run (a few minutes on a laptop)."""
    import json
    import subprocess

    ctx = make_ctx()
    execute(ctx, {"run_id": ctx.run_id})
    assert status(sf, ctx.run_id) == "ready_for_review"
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_name,pix_fmt,channels,width,height",
            "-of",
            "json",
            str(ctx.paths.final("short")),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    streams = json.loads(probe.stdout)["streams"]
    video = next(s for s in streams if s["codec_name"] == "h264")
    audio = next(s for s in streams if s["codec_name"] == "aac")
    assert (video["width"], video["height"], video["pix_fmt"]) == (1080, 1920, "yuv420p")
    assert audio["channels"] == 2


def test_rehearsals_and_rejects_do_not_hold_posting_slots(make_ctx: MakeCtx, sf: Any) -> None:
    from pipeline.nodes.export import _slot_for

    ctx = make_ctx()
    first = _slot_for(ctx, "long")
    with session_scope(sf) as s:
        for i, status_ in enumerate(("rehearsal", "rejected")):
            s.add(
                PostRow(
                    run_id=f"r{i}",
                    channel_id="whatif",
                    platform="youtube",
                    account="yt_whatif",
                    format="long",
                    status=status_,
                    path="x",
                    publish_at=first.astimezone(UTC).replace(tzinfo=None),
                )
            )
    assert _slot_for(ctx, "long") == first
    with session_scope(sf) as s:
        s.add(
            PostRow(
                run_id="real",
                channel_id="whatif",
                platform="youtube",
                account="yt_whatif",
                format="long",
                status="manual_pending",
                path="x",
                publish_at=first.astimezone(UTC).replace(tzinfo=None),
            )
        )
    assert _slot_for(ctx, "long") > first
