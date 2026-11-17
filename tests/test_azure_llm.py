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
        self.responses = NS(create=self._respond)
        self.responses_calls: list[dict[str, Any]] = []

    def _respond(self, **kwargs: Any) -> Any:
        self.responses_calls.append(kwargs)
        r = self.results.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

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
    out = llm.generate("small", "critic", "sys", "prompt", CriticReport)
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
        make(cfg, sf, client).generate("small", "script", "s", "p", CriticReport)


def test_rate_limit_explains_the_quota(cfg: AppConfig, sf: Any) -> None:
    resp = httpx.Response(
        429, request=httpx.Request("POST", "https://x.openai.azure.com/openai/v1/chat/completions")
    )
    client = StubClient(openai.RateLimitError("Too many requests", response=resp, body=None))
    with pytest.raises(LLMOutputError, match="tokens-per-minute"):
        make(cfg, sf, client).generate("small", "script", "s", "p", CriticReport)


def test_no_reasoning_effort_when_unset(cfg: AppConfig, sf: Any) -> None:
    models = cfg.models.llm.model_copy(deep=True)
    assert models.azure_openai is not None
    models.azure_openai.reasoning_effort = None
    client = StubClient(reply(GOOD))
    ledger = Ledger(sf, cfg.channel("whatif"), "r1", cfg.prices)
    AzureOpenAILLM(models, ledger, client=client).generate("small", "critic", "s", "p", CriticReport)
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


def response(args: dict[str, Any] | str, status: str = "completed", rid: str = "resp_1") -> Any:
    raw = args if isinstance(args, str) else json.dumps(args)
    call = NS(type="function_call", name="submit", arguments=raw, call_id="call_9")
    return NS(id=rid, status=status, incomplete_details=None, output=[NS(type="reasoning"), call],
              usage=NS(input_tokens=1000, output_tokens=500))  # fmt: skip


def test_gpt_6_1_sol_goes_through_the_responses_api(cfg: AppConfig, sf: Any) -> None:
    client = StubClient(response({"passed": "yes"}), response(GOOD, rid="resp_2"))
    out = make(cfg, sf, client).generate("strong", "script", "sys", "prompt", CriticReport)
    assert out.hook_score == 8 and not client.calls  # nothing went to Chat Completions
    first, fix = client.responses_calls
    assert first["model"] == "gpt-6.1-sol" and first["instructions"] == "sys"
    assert (
        first["tool_choice"] == {"type": "function", "name": "submit"}
        and first["tools"][0]["strict"] is False
    )
    assert first["reasoning"] == {"effort": "high"} and first["max_output_tokens"] == 64000
    # the fix carries on from the stored response, so the reasoning stays with its function call
    assert fix["previous_response_id"] == "resp_1"
    assert fix["input"][0]["type"] == "function_call_output" and fix["input"][0]["call_id"] == "call_9"


def test_a_deployment_that_needs_responses_is_switched(cfg: AppConfig, sf: Any) -> None:
    resp = httpx.Response(
        400, request=httpx.Request("POST", "https://x.openai.azure.com/openai/v1/chat/completions")
    )
    refusal = openai.BadRequestError(
        "Tool calling is not supported with Chat Completions for this model. Use the Responses API.",
        response=resp,
        body=None,
    )
    client = StubClient(refusal, response(GOOD), response(GOOD))
    llm = make(cfg, sf, client)
    assert llm.generate("small", "critic", "s", "p", CriticReport).hook_score == 8
    assert llm.generate("small", "critic", "s", "p", CriticReport).hook_score == 8
    assert len(client.calls) == 1 and len(client.responses_calls) == 2  # remembered after the first refusal


def test_an_answer_stopped_at_the_limit_is_a_clear_error(cfg: AppConfig, sf: Any) -> None:
    client = StubClient(response('{"passed": tr', status="incomplete"))
    with pytest.raises(LLMOutputError, match="stopped early"):
        make(cfg, sf, client).generate("strong", "script", "s", "p", CriticReport)
