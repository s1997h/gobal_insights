"""Small helpers with no pipeline dependencies."""

from __future__ import annotations

import hashlib
import json
import os
import re
import wave
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utcnow() -> datetime:
    """Naive UTC now. SQLite drops tzinfo, so the whole code base stores naive UTC."""
    return datetime.now(UTC).replace(tzinfo=None)


def slugify(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len].strip("-") or "untitled"


def sha(*parts: object) -> str:
    return hashlib.sha256("\x1f".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:24]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def count_words(text: str) -> int:
    return len(text.split())


def wav_duration_ms(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate() * 1000.0


def load_env(root: Path) -> None:
    """Load .env from the project root if python-dotenv is available. Never overrides real env vars."""
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover
        return
    load_dotenv(root / ".env", override=False)


def fmt_timestamp(seconds: float) -> str:
    """YouTube chapter timestamp: 00:00 or 1:02:03."""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"
