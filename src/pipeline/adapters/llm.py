"""LLM adapter. Forces a structured answer through one tool whose input schema is a Pydantic model.

On a validation error (or a failed code check) the error goes back to the model, at most twice.
Every call records a CostEvent. FakeLLM produces valid, deterministic output offline for tests and dry runs.
"""

from __future__ import annotations

import json
import os
import random
import re
from collections.abc import Callable
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from ..config import LLMModels
from ..ledger import Ledger
from ..schemas import (
    CriticReport,
    PackageDraft,
    ScriptPair,
    TopicProposal,
)

T = TypeVar("T", bound=BaseModel)
Check = Callable[[Any], list[str]]


class LLMOutputError(RuntimeError):
    pass


class LLM(Protocol):
    name: str

    def generate(
        self,
        tier: str,
        step: str,
        system: str,
        prompt: str,
        schema: type[T],
        *,
        check: Check | None = None,
        hints: dict[str, Any] | None = None,
    ) -> T: ...


class AnthropicLLM:
    name = "anthropic"

    def __init__(self, models: LLMModels, ledger: Ledger, client: Any = None):
        self.models = models
        self.ledger = ledger
        if client is None:
            import anthropic

            key = os.environ.get("ANTHROPIC_API_KEY")
            if not key:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY is not set (put it in .env). Use --offline to run without keys."
                )
            client = anthropic.Anthropic(api_key=key)
        self.client = client

    def generate(
        self,
        tier: str,
        step: str,
        system: str,
        prompt: str,
        schema: type[T],
        *,
        check: Check | None = None,
        hints: dict[str, Any] | None = None,
    ) -> T:
        tiers = self.models.tiers("anthropic")
        model = tiers.strong if tier == "strong" else tiers.small
        max_tokens = self.models.budget(step, "anthropic")
        tool = {
            "name": "submit",
            "description": "Return the result",
            "input_schema": schema.model_json_schema(),
        }
        msgs: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        last_error = ""
        for _attempt in range(3):  # first try plus at most two fixes
            self.ledger.check_cap(self.ledger.estimate(step))
            r = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                tools=[tool],
                tool_choice={"type": "tool", "name": "submit"},
                messages=msgs,
            )
            self.ledger.record_llm(step, model, r.usage)
            call = next((b for b in r.content if b.type == "tool_use"), None)
            if call is None:
                raise LLMOutputError(f"{step}: the model returned no tool call")
            try:
                obj = schema.model_validate(call.input)
                problems = check(obj) if check else []
                if not problems:
                    return obj
                last_error = "\n".join(f"- {p}" for p in problems)
            except ValidationError as e:
                last_error = str(e)
            msgs += [
                {"role": "assistant", "content": r.content},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": call.id,
                            "is_error": True,
                            "content": f"Invalid result:\n{last_error}\nFix every item and call submit again with the full result.",
                        }
                    ],
                },
            ]
        raise LLMOutputError(f"{step}: {schema.__name__} still invalid after 3 tries:\n{last_error}")


class _Usage:
    """OpenAI-style usage mapped onto the fields the ledger reads."""

    def __init__(self, usage: Any):
        self.input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        # completion_tokens already includes any reasoning tokens, which are billed as output
        self.output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)


def azure_v1_url(endpoint: str) -> str:
    """https://<resource>.openai.azure.com (or .services.ai.azure.com) -> .../openai/v1/"""
    e = endpoint.strip().rstrip("/")
    if e.endswith("/openai/v1"):
        return e + "/"
    if e.endswith("/openai"):
        return e + "/v1/"
    return e + "/openai/v1/"


class AzureOpenAILLM:
    """A model deployed in Azure AI Foundry, called through the OpenAI-compatible v1 API.

    Works with Azure OpenAI deployments (GPT family) and Foundry models that speak the same
    chat-completions format. The structured answer is forced through one function, "submit",
    whose parameters are the Pydantic schema; invalid answers go back to the model at most twice.
    """

    name = "azure_openai"

    def __init__(self, models: LLMModels, ledger: Ledger, client: Any = None):
        self.models = models
        self.tiers = models.tiers("azure_openai")
        self.ledger = ledger
        if client is None:
            from openai import OpenAI

            endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            key = os.environ.get("AZURE_OPENAI_API_KEY")
            if not endpoint or not key:
                raise RuntimeError(
                    "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set (put them in .env). "
                    "Use --offline to run without keys."
                )
            client = OpenAI(base_url=azure_v1_url(endpoint), api_key=key, max_retries=4, timeout=900)
        self.client = client

    def _create(self, step: str, model: str, msgs: list[dict[str, Any]], tool: dict[str, Any]) -> Any:
        import openai

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": msgs,
            "tools": [tool],
            "tool_choice": {"type": "function", "function": {"name": "submit"}},
            "max_completion_tokens": self.models.budget(step, "azure_openai"),
        }
        effort = self.tiers.effort(step)
        if effort:
            kwargs["reasoning_effort"] = effort
        try:
            return self.client.chat.completions.create(**kwargs)
        except openai.RateLimitError as e:
            raise LLMOutputError(
                f"{step}: Azure rate limit on deployment {model!r}. Its tokens-per-minute quota is too low for "
                f"this step (it needs about {kwargs['max_completion_tokens'] + 8000:,} tokens in one minute). "
                "Raise the deployment's TPM in Foundry > Deployments, or set llm.provider: anthropic in "
                "config/models.yaml."
            ) from e
        except openai.NotFoundError as e:
            raise LLMOutputError(
                f"{step}: deployment {model!r} was not found at AZURE_OPENAI_ENDPOINT. Check the deployment "
                "names under llm.azure_openai in config/models.yaml."
            ) from e
        except openai.AuthenticationError as e:
            raise LLMOutputError(
                f"{step}: Azure rejected the key. Check AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT."
            ) from e
        except openai.BadRequestError as e:
            hint = (
                " If the error mentions reasoning_effort, delete that line under llm.azure_openai in "
                "config/models.yaml (this model does not reason)."
                if "reasoning" in str(e)
                else ""
            )
            raise LLMOutputError(f"{step}: Azure rejected the request: {e}.{hint}") from e

    def generate(
        self,
        tier: str,
        step: str,
        system: str,
        prompt: str,
        schema: type[T],
        *,
        check: Check | None = None,
        hints: dict[str, Any] | None = None,
    ) -> T:
        model = self.tiers.strong if tier == "strong" else self.tiers.small
        tool = {
            "type": "function",
            "function": {
                "name": "submit",
                "description": "Return the result",
                "parameters": schema.model_json_schema(),
            },
        }
        msgs: list[dict[str, Any]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        last_error = ""
        for _attempt in range(3):  # first try plus at most two fixes
            self.ledger.check_cap(self.ledger.estimate(step))
            r = self._create(step, model, msgs, tool)
            self.ledger.record_llm(step, model, _Usage(r.usage))
            choice = r.choices[0]
            if choice.finish_reason == "length":
                raise LLMOutputError(
                    f"{step}: the answer was cut off at the token limit. Raise llm.azure_openai.max_tokens.{step} "
                    "in config/models.yaml, or lower reasoning_effort."
                )
            calls = choice.message.tool_calls or []
            if not calls:
                raise LLMOutputError(f"{step}: the model returned no function call")
            call = calls[0]
            try:
                obj = schema.model_validate(json.loads(call.function.arguments))
                problems = check(obj) if check else []
                if not problems:
                    return obj
                last_error = "\n".join(f"- {p}" for p in problems)
            except json.JSONDecodeError as e:
                last_error = f"the arguments were not valid JSON ({e})"
            except ValidationError as e:
                last_error = str(e)
            msgs += [
                {
                    "role": "assistant",
                    "content": choice.message.content,
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {"name": "submit", "arguments": call.function.arguments},
                        }
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": f"Invalid result:\n{last_error}\nFix every item and call submit again with the full result.",
                },
            ]
        raise LLMOutputError(f"{step}: {schema.__name__} still invalid after 3 tries:\n{last_error}")


# --------------------------------------------------------------------------------------------
# Offline fake: deterministic, valid output shaped by `hints` that the nodes pass in.
# --------------------------------------------------------------------------------------------
_BANK = [
    "Picture the very first minute. Nothing looks different yet, but everything has already changed.",
    "Your phone buzzes once, then again, then a third time before you can reach it.",
    "You take a slow breath and try to work out what to do first.",
    "Most people expect a dramatic moment. What you actually get is a quiet, strange stillness.",
    "By the end of the hour you have made three decisions you would never have predicted.",
    "Your body notices before your mind does, and it starts sending small warning signals.",
    "You tell yourself it is fine, and for a while that is almost true.",
    "The numbers are surprising, because small effects stack up faster than you would think.",
    "You look around the room and everything seems the same, yet you see it differently now.",
    "A friend asks what is wrong, and you realise you do not have a simple answer.",
    "Then comes the part nobody warns you about: the slow, steady pressure of ordinary days.",
    "You start planning around it, the way you plan around weather or traffic.",
    "Someone you trust gives you advice, and half of it turns out to be wrong.",
    "You notice a pattern, and the pattern is more useful than any single moment.",
    "The second day feels longer than the first, and the third feels longer still.",
    "You make a small mistake, and it teaches you more than a dozen small wins.",
    "The change is not a cliff. It is a slope, and you only see it when you look back.",
    "You learn which things were never as important as they seemed.",
    "A stranger could not tell anything is different, and that is the strangest part.",
    "You keep going, because stopping would cost more than continuing.",
    "The easy answer is never the whole answer, and you start to enjoy that.",
    "You count what you have, and the total is bigger than you expected.",
    "You count what you have lost, and the total is smaller than you feared.",
    "There is a moment of real doubt, and you decide to take it seriously.",
    "You write it all down, and the page makes the problem look manageable.",
    "A small habit holds everything together, quietly, without any fanfare.",
    "You find out how much of the effect is real and how much is only a story you tell.",
    "The turning point arrives on an ordinary afternoon, with no music and no warning.",
    "You see what the research says, and it is both simpler and stranger than you assumed.",
    "In the end the biggest surprise is how normal it all begins to feel.",
]
_CHAPTERS = [
    "The setup",
    "The first hit",
    "The knock-on effects",
    "The new normal",
    "The long run",
    "The takeaway",
]


def _topic_phrase(topic: str) -> str:
    return re.sub(r"^what if you\s+", "", topic.strip().rstrip("?"), flags=re.I)


def _fake_scenes(h: dict[str, Any], fmt: str) -> list[dict[str, Any]]:
    topic: str = h["topic"]
    shape: str = h.get("story_shape", "first_24_hours")
    target: int = int(h["long_words"] if fmt == "long" else h["short_words"])
    allow_stills = bool(h.get("allow_stills")) and not bool(h.get("no_stills"))
    max_stills = int(h.get("max_stills_long" if fmt == "long" else "max_stills_short", 0))
    per_scene = 32 if fmt == "long" else 20
    n_scenes = max(4, round(target / per_scene))
    rng = random.Random(f"{topic}|{fmt}")
    bank = list(_BANK)
    rng.shuffle(bank)
    phrase = _topic_phrase(topic)
    topic_lines = [
        f"Imagine you {phrase}, starting right now.",
        f"Everything about this question, {topic.rstrip('?').lower()}, comes down to what happens next.",
        f"So here is how it plays out when you {phrase}.",
    ]
    sentences = [topic_lines[0], *bank]
    if fmt == "short":
        sentences = [f"You {phrase}, and the first ten seconds already surprise you."] + bank
    words_left = target
    scenes: list[dict[str, Any]] = []
    si = 0
    stills_used = 0
    moods = ["neutral", "shocked", "worried", "happy"]
    cycle = ["you_reaction", "diagram", "number_counter", "compare", "captions_only", "still"]
    for i in range(n_scenes):
        remaining_scenes = n_scenes - i
        goal = max(8, round(words_left / remaining_scenes))
        parts: list[str] = []
        got = 0
        while got < goal:
            s = sentences[si % len(sentences)]
            if si == 6 and fmt == "long":
                s = topic_lines[1]
            if si == 12 and fmt == "long":
                s = topic_lines[2]
            si += 1
            parts.append(s)
            got += len(s.split())
        text = " ".join(parts)
        if i == n_scenes - 1:
            toks = text.split()
            if len(toks) > words_left:
                text = " ".join(toks[: max(8, words_left)])
                if not text.endswith((".", "!", "?")):
                    text = text.rstrip(",;") + "."
        words_left -= len(text.split())
        # visual
        kind = "title_card" if i == 0 else cycle[(i - 1) % len(cycle)]
        if kind == "still" and (not allow_stills or stills_used >= max_stills):
            kind = "you_reaction"
        if kind == "compare" and fmt == "short":
            kind = "number_counter"
        if kind == "still":
            stills_used += 1
            visual: dict[str, Any] = {
                "type": "still",
                "prompt": f"a calm illustrated scene about: {phrase}, moment {i + 1}",
            }
        else:
            props: dict[str, Any]
            if kind == "title_card":
                props = {"title": topic.rstrip("?") + "?", "subtitle": shape.replace("_", " ")}
            elif kind == "you_reaction":
                props = {"mood": moods[i % 4]}
            elif kind == "diagram":
                props = {"nodes": ["The start", "First change", "Knock-on effect", "New normal"]}
            elif kind == "number_counter":
                props = {
                    "from": 0,
                    "to": 10 * (i + 1),
                    "label": "hours in" if i % 2 else "percent more",
                    "suffix": "",
                }
            elif kind == "compare":
                props = {
                    "left": {
                        "label": "What people expect",
                        "points": ["Instant drama", "A clear before and after"],
                    },
                    "right": {"label": "What happens", "points": ["Slow change", "Small surprises"]},
                }
            else:
                props = {}
            visual = {"type": "template", "template": kind, "props": props}
        sc: dict[str, Any] = {
            "id": f"s{i + 1:02d}",
            "narration": text,
            "visual": visual,
            "on_screen_text": (f"Hour {i + 1}" if i % 3 == 1 else None),
            "min_sec": 4.0 if i == 0 else 3.0,
        }
        if (
            fmt == "long"
            and (i == 0 or i % max(1, n_scenes // 5) == 0)
            and i // max(1, n_scenes // 5) < len(_CHAPTERS)
        ):
            sc["chapter"] = _CHAPTERS[i // max(1, n_scenes // 5)] if i else "Intro"
        scenes.append(sc)
    return scenes


class FakeLLM:
    name = "fake"

    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger

    def generate(
        self,
        tier: str,
        step: str,
        system: str,
        prompt: str,
        schema: type[T],
        *,
        check: Check | None = None,
        hints: dict[str, Any] | None = None,
    ) -> T:
        h = hints or {}
        obj: BaseModel
        if schema is TopicProposal:
            backlog = list(h.get("backlog") or ["What if you stopped sleeping for 72 hours"])
            shapes = list(h.get("shapes") or ["first_24_hours"])
            start = int(h.get("start_shape_index", 0))
            while len(backlog) < 3:
                backlog.append(f"{backlog[0]} (part {len(backlog) + 1})")
            obj = TopicProposal.model_validate(
                {
                    "candidates": [
                        {
                            "title": backlog[i],
                            "angle": f"A grounded, step-by-step look at what really changes: angle {i + 1}",
                            "story_shape": shapes[(start + i) % len(shapes)],
                            "hook_idea": f"You {_topic_phrase(backlog[i])}, and the first surprise arrives within a minute.",
                        }
                        for i in range(3)
                    ]
                }
            )
        elif schema is ScriptPair:
            obj = ScriptPair.model_validate(
                {"long": {"scenes": _fake_scenes(h, "long")}, "short": {"scenes": _fake_scenes(h, "short")}}
            )
        elif schema is CriticReport:
            fail = int(h.get("attempt", 1)) <= int(h.get("fail_first", 0))
            obj = CriticReport.model_validate(
                {
                    "passed": not fail,
                    "hook_score": 4 if fail else 8,
                    "fixes": ["Open with a sharper, more concrete first sentence."] if fail else [],
                    "claims": [
                        {
                            "text": "Offline fake critic: no real claim checking was done.",
                            "source": "none (fake provider)",
                        }
                    ],
                    "notes": "FAKE CRITIC. Run without --offline for a real review.",
                }
            )
        elif schema is PackageDraft:
            topic = str(h.get("topic", "What if you tried something new"))
            base = topic.rstrip("?")
            titles = [f"{base}?", f"The truth about: {base}", f"{base} (hour by hour)"]
            titles = [t if len(t) <= 70 else t[:67].rsplit(" ", 1)[0] + "..." for t in titles]
            obj = PackageDraft.model_validate(
                {
                    "titles": titles,
                    "thumbnail_text": "WHAT IF YOU?",
                    "thumbnail_mood": "shocked",
                    "description": f"{base}? Here is a calm, step-by-step look at what would really happen. Offline placeholder text.",
                    "tags": [
                        "what if",
                        "explained",
                        "science",
                        "thought experiment",
                        "what happens if",
                        "curiosity",
                    ],
                    "short_title": f"{base}?"[:80],
                    "short_description": f"{base}? In under a minute.",
                    "instagram_caption": f"{base}? Here is what would really happen.",
                    "hashtags": ["#whatif", "#explained", "#curious"],
                }
            )
        elif hasattr(schema, "offline_example"):
            # schemas outside this module bring their own deterministic stand-in (see pipeline.episode.schemas)
            obj = schema.offline_example(h)  # type: ignore[attr-defined]
        else:  # pragma: no cover
            raise NotImplementedError(f"FakeLLM cannot produce {schema.__name__}")
        result = schema.model_validate(obj.model_dump())
        if check:
            problems = check(result)
            if problems:
                raise LLMOutputError("FakeLLM output failed code checks: " + "; ".join(problems))
        return result


def build_llm(provider: str, models: LLMModels, ledger: Ledger, offline: bool) -> LLM:
    if offline or provider == "fake":
        return FakeLLM(ledger)
    if provider == "anthropic":
        return AnthropicLLM(models, ledger)
    if provider == "azure_openai":
        return AzureOpenAILLM(models, ledger)
    raise ValueError(f"unknown llm provider {provider!r}")
