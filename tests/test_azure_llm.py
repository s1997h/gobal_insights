"""The Azure OpenAI adapter, against a stub client shaped like the OpenAI SDK's responses."""

from __future__ import annotations

import json
from types import SimpleNamespace as NS
from typing import Any

import httpx
import openai
import pytest

from pipeline.adapters.llm import AzureOpenAILLM, LLMOutputError, azure_v1_url, build_llm
from pipeline.config import AppConfig, LLMModels
from pipeline.ledger import Ledger
from pipeline.schemas import CriticReport

GOOD = {"passed": True, "hook_score": 8, "fixes": [], "claims": [], "notes": ""}


def reply(args: dict[str, Any] | str, finish: str = "tool_calls") -> Any:
    raw = args if isinstance(args, str) else json.dumps(args)
    call = NS(id="call_1", type="function", function=NS(name="submit", arguments=raw))
    msg = NS(content=None, tool_calls=[call])
    return NS(
        choices=[NS(message=msg, finish_reason=finish)], usage=NS(prompt_tokens=1000, completion_tokens=500)
    )


class StubClient:
    def __init__(self, *results: Any):
        self.results = list(results)
        self.calls: list[dict[str, Any]] = []
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        r = self.results.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def make(cfg: AppConfig, sf: Any, client: StubClient) -> AzureOpenAILLM:
    ledger = Ledger(sf, cfg.channel("whatif"), "r1", cfg.prices)
    return AzureOpenAILLM(cfg.models.llm, ledger, client=client)


def test_endpoint_formats() -> None:
    assert azure_v1_url("https://x.openai.azure.com") == "https://x.openai.azure.com/openai/v1/"
    assert azure_v1_url("https://x.services.ai.azure.com/") == "https://x.services.ai.azure.com/openai/v1/"
    assert azure_v1_url("https://x.openai.azure.com/openai/v1/") == "https://x.openai.azure.com/openai/v1/"


def test_forced_function_call_and_cost(cfg: AppConfig, sf: Any) -> None:
    client = StubClient(reply(GOOD))
    llm = make(cfg, sf, client)
    out = llm.generate("strong", "critic", "sys", "prompt", CriticReport)
    assert out.hook_score == 8
    sent = client.calls[0]
    assert sent["model"] == "gpt-5-mini"
    assert sent["tool_choice"] == {"type": "function", "function": {"name": "submit"}}
    assert sent["reasoning_effort"] == "medium"  # per step: the critic thinks harder than topic/package
    assert sent["max_completion_tokens"] == 16000  # the azure_openai override for critic
    assert sent["messages"][0] == {"role": "system", "content": "sys"}
    # 1000 in at $0.25/M + 500 out at $2/M
    assert llm.ledger.spent_run() == pytest.approx(0.00125)


def test_invalid_answer_goes_back_once(cfg: AppConfig, sf: Any) -> None:
    client = StubClient(reply({"passed": True, "hook_score": 99}), reply(GOOD))
    out = make(cfg, sf, client).generate("small", "critic", "s", "p", CriticReport)
    assert out.passed and len(client.calls) == 2
    follow_up = client.calls[1]["messages"]
    assert follow_up[-2]["role"] == "assistant" and follow_up[-2]["tool_calls"][0]["id"] == "call_1"
    assert follow_up[-1]["role"] == "tool" and "hook_score" in follow_up[-1]["content"]


def test_cut_off_answer_is_a_clear_error(cfg: AppConfig, sf: Any) -> None:
    client = StubClient(reply('{"passed": tr', finish="length"))
    with pytest.raises(LLMOutputError, match="token limit"):
        make(cfg, sf, client).generate("strong", "script", "s", "p", CriticReport)


def test_rate_limit_explains_the_quota(cfg: AppConfig, sf: Any) -> None:
    resp = httpx.Response(
        429, request=httpx.Request("POST", "https://x.openai.azure.com/openai/v1/chat/completions")
    )
    client = StubClient(openai.RateLimitError("Too many requests", response=resp, body=None))
    with pytest.raises(LLMOutputError, match="tokens-per-minute"):
        make(cfg, sf, client).generate("strong", "script", "s", "p", CriticReport)


def test_no_reasoning_effort_when_unset(cfg: AppConfig, sf: Any) -> None:
    models = cfg.models.llm.model_copy(deep=True)
    assert models.azure_openai is not None
    models.azure_openai.reasoning_effort = None
    client = StubClient(reply(GOOD))
    ledger = Ledger(sf, cfg.channel("whatif"), "r1", cfg.prices)
    AzureOpenAILLM(models, ledger, client=client).generate("strong", "critic", "s", "p", CriticReport)
    assert "reasoning_effort" not in client.calls[0]


def test_missing_keys_are_reported(cfg: AppConfig, sf: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    ledger = Ledger(sf, cfg.channel("whatif"), "r1", cfg.prices)
    with pytest.raises(RuntimeError, match="AZURE_OPENAI_ENDPOINT"):
        build_llm("azure_openai", cfg.models.llm, ledger, offline=False)


def test_legacy_models_layout_still_loads() -> None:
    m = LLMModels.model_validate(
        {"provider": "anthropic", "strong": "a", "small": "b", "max_tokens": {"script": 5}}
    )
    assert m.tiers().strong == "a" and m.budget("script") == 5 and m.budget("other") == 8000
