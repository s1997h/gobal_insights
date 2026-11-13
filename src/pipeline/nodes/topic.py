"""Topic agent: three candidates from the backlog, preferring the story shape used least recently."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from ..config import load_backlog
from ..context import RunContext
from ..db import RunRow, session_scope
from ..prompts import render_prompt, story_shapes_text
from ..schemas import TopicCandidate, TopicProposal
from ..state import RunState
from ..util import read_json, slugify, write_json


def recent_runs(ctx: RunContext, n: int = 30) -> list[tuple[str, str | None]]:
    """(topic, story_shape) of this channel's recent runs, newest first, excluding the current run."""
    with session_scope(ctx.sf) as s:
        rows = s.scalars(
            select(RunRow)
            .where(
                RunRow.channel_id == ctx.channel.id, RunRow.run_id != ctx.run_id, RunRow.topic.is_not(None)
            )
            .order_by(RunRow.created_at.desc())
            .limit(n)
        )
        return [(r.topic or "", r.story_shape) for r in rows]


def least_recent_shape(shape_ids: list[str], recent_shapes: list[str | None]) -> str:
    def last_use(sid: str) -> int:
        return recent_shapes.index(sid) if sid in recent_shapes else 10_000

    return max(shape_ids, key=lambda sid: (last_use(sid), -shape_ids.index(sid)))


def topic_node(ctx: RunContext, state: RunState) -> dict[str, Any]:
    p = ctx.paths
    shape_ids = [s.id for s in ctx.style.story_shapes]
    recent = recent_runs(ctx)
    if p.topic.exists():
        data = read_json(p.topic)
    else:
        override = ctx.options.get("topic")
        if override:
            shape = ctx.options.get("shape") or least_recent_shape(shape_ids, [s for _, s in recent])
            chosen = TopicCandidate(
                title=str(override),
                angle=str(
                    ctx.options.get("angle") or "A grounded, concrete walk through what really happens"
                ),
                story_shape=shape,
                hook_idea="",
            )
            data = {"candidates": [chosen.model_dump()], "chosen": chosen.model_dump(), "source": "cli"}
        else:
            used = {t for t, _ in recent}
            backlog = [b for b in load_backlog(ctx.cfg.root, ctx.channel.id) if b not in used]
            ctx.log(f"topic: asking the topic agent ({len(backlog)} unused backlog ideas)")
            start = shape_ids.index(least_recent_shape(shape_ids, [s for _, s in recent]))
            system = render_prompt(
                ctx.cfg.root,
                "topic",
                channel_name=ctx.channel.name,
                story_shapes=story_shapes_text(ctx.style),
            )
            prompt = json.dumps(
                {
                    "BACKLOG": backlog[:60],
                    "RECENT TOPICS (do not repeat)": [t for t, _ in recent[:15]],
                    "RECENT SHAPES (newest first)": [s for _, s in recent[:10]],
                },
                indent=2,
            )

            def check(obj: TopicProposal) -> list[str]:
                errs = [
                    f"unknown story_shape {c.story_shape!r}; use one of {shape_ids}"
                    for c in obj.candidates
                    if c.story_shape not in shape_ids
                ]
                if len({c.title.lower() for c in obj.candidates}) < 3:
                    errs.append("the three candidates must have different titles")
                return errs

            proposal = ctx.llm.generate(
                "small",
                "topic",
                system,
                prompt,
                TopicProposal,
                check=check,
                hints={"backlog": backlog, "shapes": shape_ids, "start_shape_index": start},
            )
            chosen = proposal.candidates[0]
            data = {
                "candidates": [c.model_dump() for c in proposal.candidates],
                "chosen": chosen.model_dump(),
                "source": "agent",
            }
        write_json(p.topic, data)

    chosen = data["chosen"]
    ctx.set_status("running", topic=chosen["title"], story_shape=chosen["story_shape"])
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    video_id = (
        f"{date}-{slugify(chosen['title'].removeprefix('What if you ').removeprefix('what if you '), 36)}"
    )
    ctx.log(f"topic: {chosen['title']}  [{chosen['story_shape']}]")
    return {
        "video_id": video_id,
        "topic_title": chosen["title"],
        "angle": chosen.get("angle", ""),
        "story_shape": chosen["story_shape"],
        "attempts": 0,
        "fixes": [],
    }
