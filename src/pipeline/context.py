"""RunContext: everything a node needs, built once per run and bound into the graph."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .adapters.image import ImageGen
from .adapters.llm import LLM
from .adapters.tts import TTS
from .config import AppConfig
from .db import SessionFactory, session_scope
from .ledger import Ledger
from .paths import RunPaths
from .schemas import ChannelConfig, StyleBible


class PipelineError(RuntimeError):
    """A step failed in a way that needs a human or a config change."""


@dataclass
class RunContext:
    cfg: AppConfig
    channel: ChannelConfig
    style: StyleBible
    paths: RunPaths
    sf: SessionFactory
    ledger: Ledger
    llm: LLM
    tts: TTS
    image: ImageGen
    options: dict[str, Any] = field(default_factory=dict)

    @property
    def run_id(self) -> str:
        return self.paths.run_id

    @property
    def quick(self) -> bool:
        return bool(self.options.get("quick"))

    @property
    def no_stills(self) -> bool:
        return bool(self.options.get("no_stills"))

    @property
    def scale(self) -> float:
        """Length scale for the long video; quick runs make a ~1 minute video to test cheaply."""
        return 0.11 if self.quick else 1.0

    def scale_for(self, fmt: str) -> float:
        if not self.quick:
            return 1.0
        return 0.11 if fmt == "long" else 0.5

    def log(self, msg: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{stamp}] {msg}", file=sys.stderr, flush=True)

    def set_status(self, status: str, error: str | None = None, **fields: Any) -> None:
        from .db import RunRow

        with session_scope(self.sf) as s:
            row = s.get(RunRow, self.run_id)
            if row is None:
                return
            row.status = status
            row.error = error
            for k, v in fields.items():
                setattr(row, k, v)
