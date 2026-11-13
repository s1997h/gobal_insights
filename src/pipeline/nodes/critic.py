"""Critic: a model reviews claims, hook, style and safety; code does the variety check against recent videos."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select

from ..checks import cosine, embed, outline_text, variety_issues
from ..context import RunContext
from ..db import EmbeddingRow, session_scope
from ..prompts import banned_text, render_prompt
from ..schemas import CriticReport, ScriptDoc
from ..state import RunState
from ..util import read_json, write_json

MIN_HOOK_SCORE = 6
MAX_SCRIPT_ATTEMPTS = 3  # the first draft plus at most two rewrites


def load_history(ctx: RunContext, n: int = 20) -> list[tuple[str, str | None, list[float]]]:
    with session_scope(ctx.sf) as s:
        rows = s.scalars(
            select(EmbeddingRow)
            .where(EmbeddingRow.channel_id == ctx.channel.id, EmbeddingRow.run_id != ctx.run_id)
            .order_by(EmbeddingRow.created_at.desc())
            .limit(n)
        )
        return [(r.title, r.story_shape, list(r.vector)) for r in rows]


def _compact(doc: ScriptDoc) -> list[str]:
    return [f"{s.id} [{s.visual.template or s.visual.type}] {s.narration}" for s in doc.scenes]


def critic_node(ctx: RunContext, state: RunState) -> dict[str, Any]:
    p = ctx.paths
    attempt = int(state.get("attempts", 1))
    long_doc = ScriptDoc.model_validate(read_json(p.script("long")))
    short_doc = ScriptDoc.model_validate(read_json(p.script("short")))
    history = load_history(ctx)

    system = render_prompt(
        ctx.cfg.root,
        "critic",
        channel_name=ctx.channel.name,
        voice_rules=ctx.style.voice_rules,
        banned_phrases=banned_text(ctx.style),
    )
    prompt = json.dumps(
        {
            "TOPIC": state.get("topic_title"),
            "LONG SCRIPT": _compact(long_doc),
            "SHORT SCRIPT": _compact(short_doc),
            "RECENT VIDEOS (newest first)": [{"title": t, "story_shape": s} for t, s, _ in history],
        },
        indent=2,
    )
    ctx.log(f"critic: reviewing attempt {attempt}")
    report = ctx.llm.generate(
        "strong",
        "critic",
        system,
        prompt,
        CriticReport,
        hints={"attempt": attempt, "fail_first": int(ctx.options.get("fake_critic_fail_first", 0))},
    )

    vec = embed(outline_text(state.get("topic_title", ""), state.get("angle", ""), long_doc))
    v_issues = variety_issues(vec, state.get("story_shape"), history)
    fixes = list(report.fixes) + v_issues
    if report.hook_score < MIN_HOOK_SCORE:
        fixes.append(
            f"hook score {report.hook_score}/10 is below {MIN_HOOK_SCORE}; write a sharper, more concrete first sentence"
        )
    passed = report.passed and not v_issues and report.hook_score >= MIN_HOOK_SCORE and not report.fixes

    prev = read_json(p.critic) if p.critic.exists() else {"attempts": []}
    prev["attempts"].append(
        {
            "attempt": attempt,
            "passed": passed,
            "report": report.model_dump(),
            "variety_issues": v_issues,
            "max_similarity": max((cosine(vec, h[2]) for h in history), default=0.0),
        }
    )
    prev["final"] = prev["attempts"][-1]
    write_json(p.critic, prev)

    if passed:
        ctx.log(f"critic: passed (hook {report.hook_score}/10)")
        return {"route": "pass", "fixes": []}
    if attempt < MAX_SCRIPT_ATTEMPTS:
        ctx.log(f"critic: failed with {len(fixes)} fix(es); rewriting")
        return {"route": "retry", "fixes": fixes}
    ctx.log("critic: failed after the allowed rewrites; stopping for a human")
    ctx.set_status("needs_review", error="critic failed after rewrites: " + "; ".join(fixes)[:900])
    return {"route": "human", "fixes": fixes}


def route_after_critic(state: RunState) -> str:
    return state.get("route", "pass")
