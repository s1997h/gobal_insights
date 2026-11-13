"""Package agent: titles, thumbnail text, description, tags, captions. Chapters and limits are handled in code."""

from __future__ import annotations

import json
from typing import Any

from ..checks import build_chapters, chapters_text, lint_package
from ..context import RunContext
from ..prompts import banned_text, render_prompt
from ..render_util import remotion, style_props
from ..schemas import PackageDraft, PostMeta, ScriptDoc, Timing
from ..state import RunState
from ..util import read_json, write_json


def build_metas(
    ctx: RunContext, draft: PackageDraft, chapters: list[tuple[float, str]], thumbnail: str | None
) -> dict[str, dict[str, Any]]:
    """PostMeta per 'platform-format' key, using each platform's own limits from platforms.yaml."""
    yt = ctx.cfg.platforms.get("youtube", {})
    metas: dict[str, dict[str, Any]] = {}
    disclosure = ctx.style.disclosure
    long_desc = draft.description.strip()
    if chapters:
        long_desc += "\n\nChapters:\n" + chapters_text(chapters)
    if disclosure:
        long_desc += f"\n\n{disclosure}"
    for dest in ctx.channel.destinations:
        for fmt in dest.formats:
            key = f"{dest.platform}-{fmt}"
            if key in metas:
                continue
            if dest.platform == "youtube" and fmt == "long":
                meta = PostMeta(
                    title=draft.titles[0], description=long_desc, tags=draft.tags, thumbnail_path=thumbnail
                )
            elif dest.platform == "youtube":
                tag = str(yt.get("short", {}).get("tag", "#Shorts"))
                desc = f"{draft.short_description.strip()}\n\n{tag}"
                if disclosure:
                    desc += f"\n\n{disclosure}"
                meta = PostMeta(title=draft.short_title, description=desc, tags=draft.tags)
            else:
                caption = draft.instagram_caption.strip() + "\n\n" + " ".join(draft.hashtags)
                meta = PostMeta(title=draft.short_title, caption=caption.strip())
            metas[key] = meta.model_dump()
    return metas


def package_node(ctx: RunContext, state: RunState) -> dict[str, Any]:
    p = ctx.paths
    long_doc = ScriptDoc.model_validate(read_json(p.script("long")))
    short_doc = ScriptDoc.model_validate(read_json(p.script("short")))
    timing = Timing.model_validate(read_json(p.timing("long")))
    topic = state.get("topic_title") or long_doc.video_id

    if p.package.exists():
        draft = PackageDraft.model_validate(read_json(p.package)["draft"])
    else:
        system = render_prompt(
            ctx.cfg.root,
            "package",
            channel_name=ctx.channel.name,
            voice_rules=ctx.style.voice_rules,
            banned_phrases=banned_text(ctx.style),
        )
        chapters_for_prompt = [s.chapter for s in long_doc.scenes if s.chapter]
        prompt = json.dumps(
            {
                "TOPIC": topic,
                "LONG HOOK": long_doc.scenes[0].narration,
                "LONG CHAPTERS": chapters_for_prompt,
                "SHORT HOOK": short_doc.scenes[0].narration,
                "NARRATION (long, first 12 scenes)": [s.narration for s in long_doc.scenes[:12]],
            },
            indent=2,
        )

        def check(d: PackageDraft) -> list[str]:
            return lint_package(d, ctx.cfg.platforms, ctx.channel)

        ctx.log("package: writing titles, description and captions")
        draft = ctx.llm.generate(
            "small", "package", system, prompt, PackageDraft, check=check, hints={"topic": topic}
        )

    chapters = build_chapters(long_doc, timing)
    thumb_path = None
    if "long" in ctx.channel.formats:
        thumb = p.thumbnail
        props = {
            "text": draft.thumbnail_text.upper(),
            "mood": draft.thumbnail_mood,
            "style": style_props(ctx),
        }
        props_path = p.render_dir / "thumbnail.props.json"
        write_json(props_path, props)
        ctx.log("package: rendering the thumbnail")
        thumb.parent.mkdir(parents=True, exist_ok=True)
        remotion(
            ctx,
            [
                "still",
                "src/index.ts",
                "Thumbnail",
                str(thumb),
                f"--props={props_path}",
                f"--public-dir={p.run_dir}",
            ],
            p.render_dir / "thumbnail.log",
            render=False,
        )
        thumb_path = str(thumb)

    metas = build_metas(ctx, draft, chapters, thumb_path)
    write_json(
        p.package,
        {
            "draft": draft.model_dump(),
            "chapters": [{"at_sec": t, "title": title} for t, title in chapters],
            "metas": metas,
        },
    )
    if not chapters:
        ctx.log("package: video too short for 3 chapters of 10s+; chapters omitted")
    return {}
