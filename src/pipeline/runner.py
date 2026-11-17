"""Create runs, build the context, and execute or resume the graph (with a SQLite checkpointer keyed by run_id)."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver

from .adapters.image import build_image
from .adapters.llm import build_llm
from .adapters.tts import build_tts
from .config import AppConfig
from .context import RunContext
from .db import RunRow, SessionFactory, session_scope
from .graph import build_graph
from .ledger import BudgetExceeded, Ledger
from .paths import RunPaths
from .state import RunState


def new_run_id(channel_id: str) -> str:
    return f"{datetime.now():%Y%m%d-%H%M%S}-{channel_id}"


def create_run(
    sf: SessionFactory, channel_id: str, run_id: str, options: dict[str, Any], status: str = "created"
) -> None:
    with session_scope(sf) as s:
        s.add(RunRow(run_id=run_id, channel_id=channel_id, status=status, options=options))


def build_context(
    cfg: AppConfig, channel_id: str, run_id: str, options: dict[str, Any], sf: SessionFactory
) -> RunContext:
    channel, style = cfg.channel(channel_id), cfg.style(channel_id)
    offline = bool(options.get("offline"))
    ledger = Ledger(sf, channel, run_id, cfg.prices)
    stills_needed = channel.visuals.stills and not options.get("no_stills")
    return RunContext(
        cfg=cfg,
        channel=channel,
        style=style,
        paths=RunPaths(cfg.root, run_id),
        sf=sf,
        ledger=ledger,
        llm=build_llm(cfg.models.llm.provider, cfg.models.llm, ledger, offline),
        tts=build_tts(style.narrator.provider or cfg.models.tts.provider, offline),
        image=build_image(cfg.models.image, offline, stills_needed),
        options=options,
    )


def execute(ctx: RunContext, initial: RunState | None) -> dict[str, Any]:
    """Run the graph. `initial=None` resumes the checkpointed run from the last finished node."""
    db_path = os.environ.get("PIPELINE_CHECKPOINT_DB") or str(Path(ctx.cfg.root) / "checkpoints.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    try:
        app = build_graph(ctx, SqliteSaver(conn))
        config = {"configurable": {"thread_id": ctx.run_id}}
        try:
            result: dict[str, Any] = app.invoke(initial, config)
        except BudgetExceeded as e:
            ctx.set_status("failed", error=f"budget: {e}")
            raise
        except Exception as e:
            ctx.set_status("failed", error=f"{type(e).__name__}: {e}"[:1500])
            raise
        return result
    finally:
        conn.close()
