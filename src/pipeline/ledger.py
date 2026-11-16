"""Cost ledger. Every paid step records a CostEvent; check_cap runs *before* a paid call."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import func, select

from .config import Prices
from .db import CostRow, SessionFactory, session_scope
from .schemas import ChannelConfig, CostEvent
from .util import utcnow


class BudgetExceeded(RuntimeError):
    def __init__(self, channel_id: str, run_id: str, est_usd: float, detail: str = ""):
        super().__init__(
            f"budget cap would be exceeded for channel {channel_id!r} (run {run_id}) by a ${est_usd:.2f} step. {detail}".strip()
        )


def month_start() -> Any:
    return utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)


class Ledger:
    def __init__(self, sf: SessionFactory, channel: ChannelConfig, run_id: str, prices: Prices):
        self.sf = sf
        self.channel = channel
        self.run_id = run_id
        self.prices = prices

    # --- reads ---
    def spent_run(self) -> float:
        with session_scope(self.sf) as s:
            return float(
                s.scalar(
                    select(func.coalesce(func.sum(CostRow.usd), 0.0)).where(CostRow.run_id == self.run_id)
                )
                or 0.0
            )

    def spent_month(self) -> float:
        with session_scope(self.sf) as s:
            return float(
                s.scalar(
                    select(func.coalesce(func.sum(CostRow.usd), 0.0)).where(
                        CostRow.channel_id == self.channel.id, CostRow.at >= month_start()
                    )
                )
                or 0.0
            )

    def month_units(self, provider: str) -> float:
        with session_scope(self.sf) as s:
            return float(
                s.scalar(
                    select(func.coalesce(func.sum(CostRow.units), 0.0)).where(
                        CostRow.provider == provider, CostRow.at >= month_start()
                    )
                )
                or 0.0
            )

    # --- guard ---
    def check_cap(self, est_usd: float) -> None:
        spent_video = self.spent_run()
        spent_month = self.spent_month()
        b = self.channel.budget
        if spent_video + est_usd > b.per_video_usd:
            raise BudgetExceeded(
                self.channel.id,
                self.run_id,
                est_usd,
                f"This video has spent ${spent_video:.2f} of its ${b.per_video_usd:.2f} cap.",
            )
        if spent_month + est_usd > b.per_month_usd:
            raise BudgetExceeded(
                self.channel.id,
                self.run_id,
                est_usd,
                f"This month has spent ${spent_month:.2f} of the ${b.per_month_usd:.2f} cap.",
            )

    # --- writes ---
    def record(self, step: str, provider: str, units: float, usd: float) -> None:
        ev = CostEvent(
            run_id=self.run_id, channel_id=self.channel.id, step=step, provider=provider, units=units, usd=usd
        )
        with session_scope(self.sf) as s:
            s.add(CostRow(**ev.model_dump()))

    def llm_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        p = self.prices.llm.get(model)
        if not p:
            return 0.0
        return input_tokens / 1e6 * p.get("input_per_mtok", 0.0) + output_tokens / 1e6 * p.get(
            "output_per_mtok", 0.0
        )

    def record_llm(self, step: str, model: str, usage: Any) -> float:
        inp = int(getattr(usage, "input_tokens", 0) or 0)
        # cache reads/writes are billed too; count them as input so the ledger errs high
        inp += int(getattr(usage, "cache_creation_input_tokens", 0) or 0) + int(
            getattr(usage, "cache_read_input_tokens", 0) or 0
        )
        out = int(getattr(usage, "output_tokens", 0) or 0)
        usd = self.llm_cost(model, inp, out)
        self.record(step, f"llm:{model}", float(inp + out), usd)
        return usd

    def tts_cost(self, chars: int, provider: str = "azure") -> float:
        # adapter names can carry a version or settings suffix ("kokoro2", "openai-1a2b3c4d")
        base = provider.split("-")[0].rstrip("0123456789")
        p = self.prices.tts.get(provider) or self.prices.tts.get(base, {})
        free = p.get("free_chars_per_month", 0.0)
        already = self.month_units(f"tts:{provider}")
        billable = max(0.0, (already + chars) - max(free, already))
        return billable / 1e6 * p.get("usd_per_million_chars", 0.0)

    def estimate(self, step: str) -> float:
        return self.prices.estimates.get(step, 0.05)


def cost_summary(sf: SessionFactory, channel_id: str | None = None) -> dict[str, Any]:
    """Month-to-date spend grouped by step and by run, for `pipeline costs`."""
    with session_scope(sf) as s:
        q = select(CostRow).where(CostRow.at >= month_start())
        if channel_id:
            q = q.where(CostRow.channel_id == channel_id)
        rows = list(s.scalars(q))
    by_step: dict[str, float] = defaultdict(float)
    by_run: dict[str, float] = defaultdict(float)
    for r in rows:
        by_step[r.step] += r.usd
        by_run[r.run_id] += r.usd
    return {"total": sum(by_step.values()), "by_step": dict(by_step), "by_run": dict(by_run)}
