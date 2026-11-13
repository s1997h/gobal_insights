"""`pipeline` command line. Every command that touches a channel takes --channel."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Any

import typer
from sqlalchemy import select

from .adapters.audio import generate_beds
from .checks import validate_script
from .config import AppConfig, ConfigError, load_config
from .context import PipelineError
from .db import PostRow, RunRow, get_engine, init_db, make_session_factory, session_scope
from .ledger import BudgetExceeded, cost_summary
from .paths import RunPaths, project_root
from .runner import build_context, create_run, execute, new_run_id
from .schemas import ScriptDoc
from .util import load_env, read_json, write_json

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Multichannel AI video pipeline.")

Channel = Annotated[str, typer.Option("--channel", "-c", help="Channel id, e.g. whatif")]


def _setup() -> tuple[AppConfig, Any]:
    root = project_root()
    load_env(root)
    try:
        cfg = load_config(root)
    except ConfigError as e:
        typer.secho(f"Config error: {e}", fg="red", err=True)
        raise typer.Exit(2) from e
    engine = get_engine(root)
    init_db(engine)
    return cfg, make_session_factory(engine)


def _report(cfg: AppConfig, sf: Any, run_id: str) -> None:
    with session_scope(sf) as s:
        row = s.get(RunRow, run_id)
        assert row is not None
        status, error, channel_id, topic = row.status, row.error, row.channel_id, row.topic
    paths = RunPaths(cfg.root, run_id)
    color = {"ready_for_review": "green", "needs_review": "yellow", "failed": "red"}.get(status, None)
    typer.echo("")
    typer.secho(f"Run {run_id}: {status}", fg=color, bold=True)
    if topic:
        typer.echo(f"Topic: {topic}")
    if error:
        typer.echo(f"Note: {error}")
    if status == "ready_for_review":
        typer.echo(f"Review:  {paths.review}")
        typer.echo(f"Upload folders: {paths.out_root / channel_id / run_id}")
        typer.echo(f"When happy: pipeline approve {run_id}")
    elif status == "needs_review":
        typer.echo(
            f"The critic report is at {paths.critic}. Edit the scripts in {paths.run_dir} or run again."
        )


def _execute(
    cfg: AppConfig, sf: Any, channel: str, run_id: str, options: dict[str, Any], initial: Any
) -> None:
    try:
        ctx = build_context(cfg, channel, run_id, options, sf)
    except RuntimeError as e:
        typer.secho(f"Setup problem: {e}", fg="red", err=True)
        raise typer.Exit(2) from e
    try:
        execute(ctx, initial)
    except BudgetExceeded as e:
        typer.secho(f"Stopped by the spend cap: {e}", fg="red", err=True)
    except PipelineError as e:
        typer.secho(f"Run failed: {e}", fg="red", err=True)
    except Exception as e:  # noqa: BLE001 - show the message, keep the traceback for --verbose users
        typer.secho(f"Run failed: {type(e).__name__}: {e}", fg="red", err=True)
        if os.environ.get("PIPELINE_DEBUG"):
            raise
    _report(cfg, sf, run_id)
    with session_scope(sf) as s:
        failed = (s.get(RunRow, run_id) or RunRow()).status == "failed"
    if failed:
        typer.echo(f"Fix the problem, then: pipeline resume {run_id}")
        raise typer.Exit(1)


@app.command()
def run(
    channel: Channel,
    topic: Annotated[str | None, typer.Option(help="Skip the topic agent and use this topic")] = None,
    shape: Annotated[str | None, typer.Option(help="Story shape id (with --topic)")] = None,
    quick: Annotated[
        bool, typer.Option(help="Make a ~1 minute video and a ~25 s Short to test cheaply")
    ] = False,
    offline: Annotated[
        bool, typer.Option(help="Use fake providers: no API keys, no cost, beep audio")
    ] = False,
    no_stills: Annotated[
        bool, typer.Option(help="Templates only: no AI images, no image API key needed")
    ] = False,
    dry_run: Annotated[bool, typer.Option(help="Load config and create the run row, then stop")] = False,
) -> None:
    """Take a topic to a ready-to-upload video, Short and package."""
    cfg, sf = _setup()
    cfg.channel(channel)
    options = {"topic": topic, "shape": shape, "quick": quick, "offline": offline, "no_stills": no_stills}
    run_id = new_run_id(channel)
    if dry_run:
        create_run(sf, channel, run_id, options, status="dry_run")
        typer.echo(f"dry run: config OK, run {run_id} recorded with status dry_run")
        return
    create_run(sf, channel, run_id, options)
    typer.echo(
        f"Run {run_id} ({channel}){' [offline fakes]' if offline else ''}{' [quick]' if quick else ''}"
    )
    _execute(cfg, sf, channel, run_id, options, {"run_id": run_id})


@app.command()
def build(
    channel: Channel,
    long: Annotated[Path, typer.Option(help="Hand-written long script (JSON)")],
    short: Annotated[Path, typer.Option(help="Hand-written Short script (JSON)")],
    offline: Annotated[bool, typer.Option()] = False,
    no_stills: Annotated[bool, typer.Option()] = False,
) -> None:
    """Skip the agents: voice, render and package from scripts you wrote by hand."""
    cfg, sf = _setup()
    ch, style = cfg.channel(channel), cfg.style(channel)
    run_id = new_run_id(channel)
    options = {"offline": offline, "no_stills": no_stills, "scripts_provided": True}
    paths = RunPaths(cfg.root, run_id)
    docs: dict[str, ScriptDoc] = {}
    for fmt, path in (("long", long), ("short", short)):
        raw = read_json(path)
        raw.setdefault("video_id", path.stem)
        raw["channel_id"], raw["format"] = channel, fmt
        try:
            doc = ScriptDoc.model_validate(raw)
        except ValueError as e:
            typer.secho(f"{path}: {e}", fg="red", err=True)
            raise typer.Exit(2) from e
        errs = validate_script(doc, style, ch, scale=1.0, no_stills=no_stills, length=False)
        if errs:
            typer.secho(f"{path} has problems:\n- " + "\n- ".join(errs), fg="red", err=True)
            raise typer.Exit(2)
        docs[fmt] = doc
    create_run(sf, channel, run_id, options)
    for fmt, doc in docs.items():
        write_json(paths.script(fmt), doc.model_dump())
    title = docs["long"].video_id
    write_json(
        paths.topic,
        {
            "chosen": {"title": title, "angle": "", "story_shape": "n/a", "hook_idea": ""},
            "candidates": [],
            "source": "hand-written",
        },
    )
    state = {
        "run_id": run_id,
        "scripts_provided": True,
        "video_id": docs["long"].video_id,
        "topic_title": title,
        "story_shape": "n/a",
        "angle": "",
    }
    with session_scope(sf) as s:
        row = s.get(RunRow, run_id)
        assert row is not None
        row.topic, row.story_shape = title, "n/a"
    typer.echo(f"Run {run_id} ({channel}) from hand-written scripts")
    _execute(cfg, sf, channel, run_id, options, state)


@app.command()
def resume(run_id: Annotated[str, typer.Argument()]) -> None:
    """Continue a failed or interrupted run from its last finished step. Paid steps are cached."""
    cfg, sf = _setup()
    with session_scope(sf) as s:
        row = s.get(RunRow, run_id)
        if row is None:
            typer.secho(f"no such run: {run_id}", fg="red", err=True)
            raise typer.Exit(2)
        channel, options = row.channel_id, dict(row.options or {})
        row.status, row.error = "running", None
    typer.echo(f"Resuming {run_id}")
    _execute(cfg, sf, channel, run_id, options, None)


@app.command("list")
def list_runs(
    channel: Annotated[str | None, typer.Option("--channel", "-c")] = None, limit: int = 15
) -> None:
    """Recent runs."""
    _, sf = _setup()
    with session_scope(sf) as s:
        q = select(RunRow).order_by(RunRow.created_at.desc()).limit(limit)
        if channel:
            q = q.where(RunRow.channel_id == channel)
        rows = list(s.scalars(q))
    for r in rows:
        typer.echo(f"{r.run_id:34} {r.status:17} {(r.topic or '-')[:60]}")


@app.command()
def costs(channel: Annotated[str | None, typer.Option("--channel", "-c")] = None) -> None:
    """Month-to-date spend by step and by run."""
    cfg, sf = _setup()
    c = cost_summary(sf, channel)
    typer.echo(
        f"This month: ${c['total']:.3f}"
        + (f" of ${cfg.channel(channel).budget.per_month_usd:.0f}" if channel else "")
    )
    for k, v in sorted(c["by_step"].items(), key=lambda kv: -kv[1]):
        typer.echo(f"  {k:10} ${v:.3f}")
    typer.echo("By run:")
    for k, v in sorted(c["by_run"].items(), key=lambda kv: -kv[1])[:10]:
        typer.echo(f"  {k:34} ${v:.3f}")


@app.command()
def review(run_id: Annotated[str, typer.Argument()]) -> None:
    """Print a run's review sheet."""
    cfg, _ = _setup()
    p = RunPaths(cfg.root, run_id).review
    if not p.exists():
        typer.secho("no review sheet yet (the run has not finished)", fg="yellow", err=True)
        raise typer.Exit(1)
    typer.echo(p.read_text(encoding="utf-8"))


@app.command()
def approve(run_id: Annotated[str, typer.Argument()]) -> None:
    """Mark a reviewed run as approved (you upload it by hand for now)."""
    _, sf = _setup()
    with session_scope(sf) as s:
        row = s.get(RunRow, run_id)
        if row is None or row.status != "ready_for_review":
            typer.secho("only runs in status ready_for_review can be approved", fg="red", err=True)
            raise typer.Exit(1)
        row.status = "approved"
    typer.echo(f"{run_id} approved. Upload from out/<channel>/{run_id}/ following each UPLOAD.md.")


@app.command()
def reject(
    run_id: Annotated[str, typer.Argument()],
    reason: Annotated[str, typer.Option(help="Why (kept for later learning)")],
) -> None:
    """Reject a run and record why."""
    _, sf = _setup()
    with session_scope(sf) as s:
        row = s.get(RunRow, run_id)
        if row is None:
            typer.secho("no such run", fg="red", err=True)
            raise typer.Exit(1)
        row.status, row.error = "rejected", reason
        for post in s.scalars(
            select(PostRow).where(PostRow.run_id == run_id, PostRow.status == "manual_pending")
        ):
            post.status = "rejected"
    typer.echo(f"{run_id} rejected: {reason}")


@app.command()
def voices(
    channel: Channel = "whatif",
    offline: Annotated[bool, typer.Option()] = False,
) -> None:
    """Voice the same paragraph in several neural voices so you can pick the narrator."""
    cfg, sf = _setup()
    run_id = "voice-samples"
    ctx = build_context(cfg, channel, run_id, {"offline": offline, "no_stills": True}, sf)
    sample = (
        "You open the email at seven oh two in the morning. The number in the corner has too many zeros. "
        "You read it twice, then a third time, and your coffee goes cold on the desk."
    )
    out_dir = cfg.root / "out" / "voice-samples"
    out_dir.mkdir(parents=True, exist_ok=True)
    for v in [
        "en-US-AndrewNeural",
        "en-US-GuyNeural",
        "en-US-DavisNeural",
        "en-GB-RyanNeural",
        "en-IN-PrabhatNeural",
    ]:
        try:
            res = ctx.tts.synth(sample, v, 1.0, cfg.root / "cache" / "tts")
        except Exception as e:  # noqa: BLE001
            typer.secho(f"{v}: {e}", fg="red", err=True)
            continue
        if not res.cached:
            ctx.ledger.record(
                "tts", f"tts:{ctx.tts.name}", float(res.chars), ctx.ledger.tts_cost(res.chars, ctx.tts.name)
            )
        shutil.copyfile(res.wav_path, out_dir / f"{v}.wav")
        typer.echo(f"{v}: {out_dir / (v + '.wav')}")
    typer.echo("Listen, then set narrator.voice in config/styles/<channel>.yaml.")


@app.command("music-beds")
def music_beds(force: bool = False) -> None:
    """(Re)generate the two synthetic placeholder music beds in assets/music/."""
    root = project_root()
    for p in generate_beds(root / "assets" / "music", force=force):
        typer.echo(str(p))


@app.command()
def doctor() -> None:
    """Check that this machine can run the pipeline."""
    root = project_root()
    load_env(root)
    ok = True

    def line(good: bool, msg: str, fix: str = "") -> None:
        nonlocal ok
        ok = ok and good
        typer.secho(
            f"{'OK ' if good else 'FIX'} {msg}" + (f"  ->  {fix}" if not good and fix else ""),
            fg="green" if good else "red",
        )

    line(sys.version_info >= (3, 12), f"Python {sys.version.split()[0]}", "install Python 3.12+")
    for tool in ("ffmpeg", "ffprobe"):
        line(bool(shutil.which(tool)), f"{tool} found", "install FFmpeg and put it on PATH")
    node = shutil.which("node")
    ver = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip() if node else ""
    line(
        bool(node) and int(ver.lstrip("v").split(".")[0]) >= 20,
        f"Node {ver or 'missing'}",
        "install Node 20+",
    )
    line((root / "render" / "node_modules").exists(), "Remotion installed", "cd render && npm ci")
    chrome = os.environ.get("PIPELINE_CHROME")
    typer.echo(
        f"INFO browser: {'PIPELINE_CHROME=' + chrome if chrome else 'Remotion will download its own headless Chrome on first render'}"
    )
    try:
        llm_provider = load_config(root).models.llm.provider
    except ConfigError:
        llm_provider = "anthropic"
    typer.echo(f"INFO script model provider: {llm_provider} (llm.provider in config/models.yaml)")
    llm_vars = (
        [("AZURE_OPENAI_ENDPOINT", "scripts and critic"), ("AZURE_OPENAI_API_KEY", "scripts and critic")]
        if llm_provider == "azure_openai"
        else [("ANTHROPIC_API_KEY", "scripts and critic")]
    )
    for var, why in [
        *llm_vars,
        ("AZURE_SPEECH_KEY", "voice"),
        ("AZURE_SPEECH_REGION", "voice"),
        ("OPENAI_API_KEY", "AI stills (optional with --no-stills)"),
    ]:
        typer.echo(
            f"{'OK ' if os.environ.get(var) else 'INFO'} {var} {'set' if os.environ.get(var) else 'not set'} ({why})"
        )
    line(
        len(list((root / "assets" / "fonts").glob("Inter-*.otf"))) >= 3,
        "Inter fonts bundled",
        "see assets/fonts/",
    )
    line(
        len(list((root / "assets" / "music").glob("*.mp3"))) >= 1, "music beds present", "pipeline music-beds"
    )
    try:
        cfg = load_config(root)
        line(True, f"config loads ({len(cfg.channels)} channel(s): {', '.join(cfg.channels)})")
    except ConfigError as e:
        line(False, f"config: {e}")
    typer.echo("")
    typer.secho("Ready." if ok else "Fix the items marked FIX.", bold=True)
    raise typer.Exit(0 if ok else 1)


if __name__ == "__main__":  # pragma: no cover
    app()
