"""Load and validate every config file at start-up. A typo fails loudly, with the file name."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml
from pydantic import BaseModel, ValidationError

from .paths import project_root
from .schemas import ChannelConfig, StyleBible


class ConfigError(Exception):
    """A config file is missing, malformed or inconsistent."""


class LLMModels(BaseModel):
    provider: str = "anthropic"
    strong: str
    small: str
    max_tokens: dict[str, int] = {}


class TTSModels(BaseModel):
    provider: str = "azure"


class ImageModels(BaseModel):
    provider: str = "openai"
    model: str = "gpt-image-1"
    quality: str = "medium"


class ModelsConfig(BaseModel):
    llm: LLMModels
    tts: TTSModels = TTSModels()
    image: ImageModels = ImageModels()


class Prices(BaseModel):
    llm: dict[str, dict[str, float]] = {}
    tts: dict[str, dict[str, float]] = {}
    image: dict[str, dict[str, float]] = {}
    estimates: dict[str, float] = {}


@dataclass
class AppConfig:
    root: Path
    platforms: dict[str, dict[str, dict[str, Any]]]
    channels: dict[str, ChannelConfig]
    styles: dict[str, StyleBible]
    models: ModelsConfig
    prices: Prices
    warnings: list[str] = field(default_factory=list)

    def channel(self, channel_id: str) -> ChannelConfig:
        if channel_id not in self.channels:
            raise ConfigError(f"unknown channel {channel_id!r}; known channels: {sorted(self.channels)}")
        return self.channels[channel_id]

    def style(self, channel_id: str) -> StyleBible:
        return self.styles[self.channel(channel_id).id]


def _load_yaml(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError as e:
        raise ConfigError(f"missing config file: {path}") from e
    except yaml.YAMLError as e:
        raise ConfigError(f"{path}: invalid YAML: {e}") from e


def _validate[T: BaseModel](model: type[T], data: Any, path: Path) -> T:
    try:
        return model.model_validate(data)
    except ValidationError as e:
        problems = "; ".join(f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors())
        raise ConfigError(f"{path}: {problems}") from e


def load_config(root: Path | None = None) -> AppConfig:
    root = root or project_root()
    cfg_dir = root / "config"

    platforms = _load_yaml(cfg_dir / "platforms.yaml")
    if not isinstance(platforms, dict) or not platforms:
        raise ConfigError(f"{cfg_dir / 'platforms.yaml'}: must be a mapping of platform -> formats")

    models = _validate(ModelsConfig, _load_yaml(cfg_dir / "models.yaml"), cfg_dir / "models.yaml")
    prices = _validate(Prices, _load_yaml(cfg_dir / "prices.yaml"), cfg_dir / "prices.yaml")

    channels: dict[str, ChannelConfig] = {}
    styles: dict[str, StyleBible] = {}
    channel_files = sorted((cfg_dir / "channels").glob("*.yaml"))
    if not channel_files:
        raise ConfigError(f"no channel files found in {cfg_dir / 'channels'}")

    for path in channel_files:
        ch = _validate(ChannelConfig, _load_yaml(path), path)
        if ch.id != path.stem:
            raise ConfigError(f"{path}: id {ch.id!r} must match the file name {path.stem!r}")
        if ch.id in channels:
            raise ConfigError(f"{path}: duplicate channel id {ch.id!r}")
        for d in ch.destinations:
            if d.platform not in platforms:
                raise ConfigError(
                    f"{path}: destination platform {d.platform!r} is not in platforms.yaml "
                    f"(known: {sorted(platforms)})"
                )
            for f in d.formats:
                if f not in platforms[d.platform]:
                    raise ConfigError(
                        f"{path}: platform {d.platform!r} has no rules for format {f!r} in platforms.yaml"
                    )
                if f not in ch.formats:
                    raise ConfigError(
                        f"{path}: destination {d.account!r} uses format {f!r}, "
                        f"but the channel only makes {ch.formats}"
                    )
        try:
            ZoneInfo(ch.schedule.timezone)
        except Exception as e:
            raise ConfigError(f"{path}: unknown timezone {ch.schedule.timezone!r}") from e
        style_path = cfg_dir / ch.style
        styles[ch.id] = _validate(StyleBible, _load_yaml(style_path), style_path)
        channels[ch.id] = ch

    return AppConfig(
        root=root, platforms=platforms, channels=channels, styles=styles, models=models, prices=prices
    )


def load_backlog(root: Path, channel_id: str) -> list[str]:
    path = root / "config" / "channels" / channel_id / "backlog.md"
    if not path.exists():
        return []
    return [
        ln.strip()
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.startswith("#")
    ]


_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def next_slot(channel: ChannelConfig, fmt: str, after: datetime) -> datetime | None:
    """First posting slot for this format strictly after `after` (naive UTC). Returns a tz-aware datetime
    in the channel's timezone, or None if the channel has no slots for the format."""
    slots: list[str] = getattr(channel.schedule, fmt, [])
    if not slots:
        return None
    tz = ZoneInfo(channel.schedule.timezone)
    after_local = after.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
    best: datetime | None = None
    for day_offset in range(0, 9):
        day = (after_local + timedelta(days=day_offset)).date()
        for slot in slots:
            dname, hm = slot.split(" ")
            if _DAYS[day.weekday()] != dname:
                continue
            hh, mm = (int(x) for x in hm.split(":"))
            cand = datetime(day.year, day.month, day.day, hh, mm, tzinfo=tz)
            if cand > after_local and (best is None or cand < best):
                best = cand
        if best is not None:
            return best
    return best
