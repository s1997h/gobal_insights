"""Script agent: a long script and a separate Short, validated by code before anything else sees them."""

from __future__ import annotations

import json
import math
from typing import Any

from ..checks import MAX_SCENE_NARRATION_SEC, validate_script
from ..context import RunContext
from ..prompts import banned_text, render_prompt, template_catalog
from ..schemas import ScriptDoc, ScriptDraft, ScriptPair
from ..state import RunState
from ..util import read_json, write_json


def _range(target: int, scale: float) -> tuple[int, int]:
    tol = 0.10 if scale >= 1.0 else 0.25
    return math.floor(target * (1 - tol)), math.ceil(target * (1 + tol))


def make_doc(ctx: RunContext, video_id: str, fmt: str, draft: ScriptDraft) -> ScriptDoc:
    return ScriptDoc(video_id=video_id, channel_id=ctx.channel.id, format=fmt, scenes=draft.scenes)  # type: ignore[arg-type]


def script_node(ctx: RunContext, state: RunState) -> dict[str, Any]:
    p = ctx.paths
    fixes = state.get("fixes") or []
    attempts = int(state.get("attempts", 0))
    video_id = state["video_id"]

    if not fixes and p.script("long").exists() and p.script("short").exists():
        ctx.log("script: reusing the scripts already on disk")
        return {"attempts": max(attempts, 1), "fixes": []}

    style, ch = ctx.style, ctx.channel
    lw, sw = (
        style.target_words("long", ctx.scale_for("long")),
        style.target_words("short", ctx.scale_for("short")),
    )
    (llo, lhi), (slo, shi) = _range(lw, ctx.scale_for("long")), _range(sw, ctx.scale_for("short"))
    stills_on = ch.visuals.stills and not ctx.no_stills
    stills_rule = (
        f"Use at most {ch.visuals.max_stills_long} stills in the long script and {ch.visuals.max_stills_short} in the short; stills are optional."
        if stills_on
        else "Stills are OFF for this video: use only templates."
    )
    system = render_prompt(
        ctx.cfg.root,
        "script",
        channel_name=ch.name,
        voice_rules=style.voice_rules,
        banned_phrases=banned_text(style),
        template_catalog=template_catalog(),
        max_scene_words=round(style.narrator.wpm * MAX_SCENE_NARRATION_SEC / 60),
        long_words=lw,
        long_lo=llo,
        long_hi=lhi,
        long_scenes=max(4, round(lw / 32)),
        short_words=sw,
        short_lo=slo,
        short_hi=shi,
        short_scenes=max(4, round(sw / 20)),
        stills_rule=stills_rule,
    )
    shape = next((s for s in style.story_shapes if s.id == state["story_shape"]), style.story_shapes[0])
    topic = read_json(p.topic)["chosen"]
    payload: dict[str, Any] = {
        "TOPIC": topic["title"],
        "ANGLE": topic.get("angle", ""),
        "HOOK IDEA": topic.get("hook_idea", ""),
        "STORY SHAPE": {"id": shape.id, "name": shape.name, "how_to_use_it": shape.description},
    }
    if fixes:
        payload["FIX THESE PROBLEMS FROM THE PREVIOUS DRAFT"] = fixes
    prompt = json.dumps(payload, indent=2)

    def check(pair: ScriptPair) -> list[str]:
        errs: list[str] = []
        for fmt, draft in (("long", pair.long), ("short", pair.short)):
            try:
                doc = make_doc(ctx, video_id, fmt, draft)
            except ValueError as e:  # duplicate scene ids etc.
                errs.append(f"[{fmt}] {e}")
                continue
            errs += validate_script(doc, style, ch, scale=ctx.scale_for(fmt), no_stills=ctx.no_stills)
        return errs

    ctx.log(f"script: writing long ({lw} words) and short ({sw} words), attempt {attempts + 1}")
    pair = ctx.llm.generate(
        "strong",
        "script",
        system,
        prompt,
        ScriptPair,
        check=check,
        hints={
            "topic": topic["title"],
            "angle": topic.get("angle", ""),
            "story_shape": shape.id,
            "long_words": lw,
            "short_words": sw,
            "allow_stills": stills_on,
            "no_stills": ctx.no_stills,
            "max_stills_long": ch.visuals.max_stills_long,
            "max_stills_short": ch.visuals.max_stills_short,
        },
    )
    for fmt, draft in (("long", pair.long), ("short", pair.short)):
        write_json(p.script(fmt), make_doc(ctx, video_id, fmt, draft).model_dump())
    return {"attempts": attempts + 1, "fixes": []}
