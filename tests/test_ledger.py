from __future__ import annotations

from typing import Any

import pytest

from pipeline.config import AppConfig
from pipeline.ledger import BudgetExceeded, Ledger, cost_summary


def ledger(cfg: AppConfig, sf: Any, run_id: str = "r1", **budget: float) -> Ledger:
    ch = cfg.channel("whatif")
    if budget:
        ch = ch.model_copy(update={"budget": ch.budget.model_copy(update=budget)})
    return Ledger(sf, ch, run_id, cfg.prices)


def test_cap_per_video(cfg: AppConfig, sf: Any) -> None:
    lg = ledger(cfg, sf, per_video_usd=1.0)
    lg.check_cap(0.9)
    lg.record("script", "llm:x", 100, 0.8)
    assert lg.spent_run() == pytest.approx(0.8)
    with pytest.raises(BudgetExceeded, match="This video"):
        lg.check_cap(0.3)


def test_cap_per_month_spans_runs(cfg: AppConfig, sf: Any) -> None:
    ledger(cfg, sf, "a", per_month_usd=2.0).record("script", "llm:x", 1, 1.5)
    with pytest.raises(BudgetExceeded, match="This month"):
        ledger(cfg, sf, "b", per_month_usd=2.0).check_cap(0.6)
    summary = cost_summary(sf, "whatif")
    assert summary["total"] == pytest.approx(1.5) and summary["by_run"] == {"a": pytest.approx(1.5)}


def test_tts_free_tier_then_paid(cfg: AppConfig, sf: Any) -> None:
    lg = ledger(cfg, sf)
    assert lg.tts_cost(400_000) == 0.0
    lg.record("tts", "tts:azure", 450_000, 0.0)
    # 50K free chars left: 100K more bills 50K at $16 per million
    assert lg.tts_cost(100_000) == pytest.approx(0.8)


def test_llm_cost_counts_cache_tokens(cfg: AppConfig, sf: Any) -> None:
    lg = ledger(cfg, sf)

    class Usage:
        input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens = (
            1_000_000,
            100_000,
            0,
            0,
        )

    usd = lg.record_llm("script", "claude-sonnet-5-5", Usage())
    p = cfg.prices.llm["claude-sonnet-5-5"]
    assert usd == pytest.approx(p["input_per_mtok"] + 0.1 * p["output_per_mtok"])
    assert lg.llm_cost("unknown-model", 10, 10) == 0.0
