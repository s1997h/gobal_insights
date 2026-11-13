"""SQLite (later PostgreSQL) tables. One config change (PIPELINE_DB_URL) moves to Postgres."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .util import utcnow


class Base(DeclarativeBase):
    pass


class RunRow(Base):
    __tablename__ = "runs"
    run_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    channel_id: Mapped[str] = mapped_column(String(40), index=True)
    topic: Mapped[str | None] = mapped_column(Text, nullable=True)
    story_shape: Mapped[str | None] = mapped_column(String(60), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="created")
    options: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class AssetRow(Base):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.run_id"), index=True)
    format: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(Text)
    duration_sec: Mapped[float] = mapped_column(Float)
    __table_args__ = (UniqueConstraint("run_id", "format", name="uq_asset_run_format"),)


class PostRow(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.run_id"), index=True)
    channel_id: Mapped[str] = mapped_column(String(40), index=True)
    platform: Mapped[str] = mapped_column(String(30))
    account: Mapped[str] = mapped_column(String(60))
    format: Mapped[str] = mapped_column(String(10))
    remote_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="manual_pending")
    publish_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    path: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Nothing posts twice: one row per run, platform, account and format.
    __table_args__ = (UniqueConstraint("run_id", "platform", "account", "format", name="uq_post"),)


class CostRow(Base):
    __tablename__ = "cost_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(80), index=True)
    channel_id: Mapped[str] = mapped_column(String(40), index=True)
    step: Mapped[str] = mapped_column(String(40))
    provider: Mapped[str] = mapped_column(String(40))
    units: Mapped[float] = mapped_column(Float, default=0.0)
    usd: Mapped[float] = mapped_column(Float, default=0.0)
    at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class MetricRow(Base):
    """Filled by the analytics job once publishing is plugged in."""

    __tablename__ = "metrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True)
    day: Mapped[int] = mapped_column(Integer)
    views: Mapped[int] = mapped_column(Integer, default=0)
    avg_view_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    ctr: Mapped[float | None] = mapped_column(Float, nullable=True)
    likes: Mapped[int | None] = mapped_column(Integer, nullable=True)


class EmbeddingRow(Base):
    __tablename__ = "video_embeddings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(80), unique=True)
    channel_id: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(Text)
    story_shape: Mapped[str | None] = mapped_column(String(60), nullable=True)
    vector: Mapped[list[float]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


def get_engine(root: Path, url: str | None = None) -> Engine:
    url = url or os.environ.get("PIPELINE_DB_URL") or f"sqlite:///{root / 'pipeline.db'}"
    return create_engine(url, future=True)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)


SessionFactory = Callable[[], Session]


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)


@contextmanager
def session_scope(sf: SessionFactory) -> Iterator[Session]:
    s = sf()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
