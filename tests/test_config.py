from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
import yaml

from pipeline.config import ConfigError, load_backlog, load_config, next_slot


def _edit_channel(root: Path, fn) -> None:  # type: ignore[no-untyped-def]
    path = root / "config" / "channels" / "whatif.yaml"
    data = yaml.safe_load(path.read_text())
    fn(data)
    path.write_text(yaml.safe_dump(data))


def test_real_config_loads(project: Path) -> None:
    cfg = load_config(project)
    ch = cfg.channel("whatif")
    assert ch.name == "What IF You..."
    assert {(d.platform, f) for d in ch.destinations for f in d.formats} == {
        ("youtube", "long"),
        ("youtube", "short"),
        ("instagram", "short"),
    }
    assert cfg.style("whatif").narrator.wpm == 150
    assert load_backlog(project, "whatif")


def test_unknown_platform_fails(project: Path) -> None:
    _edit_channel(
        project,
        lambda d: d["destinations"].append({"platform": "tiktok", "account": "t", "formats": ["short"]}),
    )
    with pytest.raises(ConfigError, match="tiktok"):
        load_config(project)


def test_format_without_platform_rules_fails(project: Path) -> None:
    _edit_channel(
        project,
        lambda d: d["destinations"].__setitem__(
            1, {"platform": "instagram", "account": "ig", "formats": ["long"]}
        ),
    )
    with pytest.raises(ConfigError):
        load_config(project)


def test_channel_id_must_match_filename(project: Path) -> None:
    _edit_channel(project, lambda d: d.update(id="other"))
    with pytest.raises(ConfigError, match="file name"):
        load_config(project)


def test_bad_slot_and_timezone_fail(project: Path) -> None:
    _edit_channel(project, lambda d: d["schedule"].update(long=["Monday 7pm"]))
    with pytest.raises(ConfigError):
        load_config(project)


def test_unknown_timezone_fails(project: Path) -> None:
    _edit_channel(project, lambda d: d["schedule"].update(timezone="Mars/Olympus"))
    with pytest.raises(ConfigError, match="timezone"):
        load_config(project)


def test_next_slot_is_strictly_after_and_in_channel_timezone(project: Path) -> None:
    ch = load_config(project).channel("whatif")
    # Fri 13 Nov 2026 12:00 UTC is 17:30 IST: the next long slot is Fri 19:00 IST, the next short is Sat 13:00 IST
    after = datetime(2026, 11, 13, 12, 0)
    long_slot = next_slot(ch, "long", after)
    short_slot = next_slot(ch, "short", after)
    assert long_slot is not None and short_slot is not None
    assert (long_slot.strftime("%a %H:%M"), long_slot.utcoffset().total_seconds()) == ("Fri 19:00", 19800)  # type: ignore[union-attr]
    assert short_slot.strftime("%a %d %H:%M") == "Sat 14 13:00"
    # exactly at the slot: move to the following one
    at_slot = datetime(2026, 11, 13, 13, 30)  # 19:00 IST
    nxt = next_slot(ch, "long", at_slot)
    assert nxt is not None and nxt.strftime("%a %H:%M") == "Mon 19:00"


def test_next_slot_without_schedule(project: Path) -> None:
    ch = load_config(project).channel("whatif")
    ch = ch.model_copy(update={"schedule": ch.schedule.model_copy(update={"short": []})})
    assert next_slot(ch, "short", datetime(2026, 1, 1)) is None


def test_unknown_llm_provider_fails(project: Path) -> None:
    path = project / "config" / "models.yaml"
    data = yaml.safe_load(path.read_text())
    data["llm"]["provider"] = "mystery"
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ConfigError, match="llm.provider"):
        load_config(project)


def test_provider_without_model_names_fails(project: Path) -> None:
    path = project / "config" / "models.yaml"
    data = yaml.safe_load(path.read_text())
    data["llm"]["provider"] = "azure_openai"
    del data["llm"]["azure_openai"]
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ConfigError, match="azure_openai"):
        load_config(project)
