"""Export: until publishers are plugged in, every destination gets a ready-to-upload folder.

out/<channel>/<run_id>/<platform>-<format>/{video.mp4, thumbnail.png, meta.json, UPLOAD.md}
Each folder is also a `posts` row with status manual_pending, unique per (run, platform, account, format),
so re-running never creates duplicates. A real publisher later takes over rows in this state.
"""

from __future__ import annotations

import shutil
from datetime import UTC, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from ..checks import chapters_text, embed, outline_text
from ..config import next_slot
from ..context import RunContext
from ..db import EmbeddingRow, PostRow, session_scope
from ..ledger import cost_summary
from ..schemas import ScriptDoc
from ..state import RunState
from ..util import read_json, utcnow, write_json

# Posts in these states don't hold a posting slot: offline rehearsals and rejected runs.
FREE_SLOT_STATUSES = ("rehearsal", "rejected")


def _slot_for(ctx: RunContext, fmt: str) -> Any:
    """Next free posting slot for this channel and format, after any slot already suggested."""
    with session_scope(ctx.sf) as s:
        last = s.scalar(
            select(func.max(PostRow.publish_at)).where(
                PostRow.channel_id == ctx.channel.id,
                PostRow.format == fmt,
                PostRow.status.not_in(FREE_SLOT_STATUSES),
            )
        )
    after = max(utcnow() + timedelta(hours=2), last) if last else utcnow() + timedelta(hours=2)
    return next_slot(ctx.channel, fmt, after)


def _upload_md(
    ctx: RunContext,
    platform: str,
    fmt: str,
    meta: dict[str, Any],
    titles: list[str],
    when: str,
    has_thumb: bool,
) -> str:
    if platform == "youtube":
        steps = [
            "Open YouTube Studio as the channel's account and click Create > Upload videos.",
            "Choose `video.mp4` from this folder.",
            "Paste the title and description below. Add the tags under Show more.",
        ]
        if fmt == "long" and has_thumb:
            steps.append(
                "Upload `thumbnail.png` as the custom thumbnail (the channel must be phone-verified)."
            )
        steps += [
            'Audience: choose "No, it\'s not made for kids".',
            "Altered content: answer honestly. This channel's narration is an AI voice and its art is AI-assisted; "
            "Studio's help text explains when disclosure is required.",
            f"Visibility: Schedule, and pick the suggested time below ({when}).",
        ]
        body = (
            f"## Title\n\n```\n{meta['title']}\n```\n\n"
            + (
                f"Other title options: {' | '.join(t for t in titles if t != meta['title'])}\n\n"
                if fmt == "long"
                else ""
            )
            + f"## Description\n\n```\n{meta['description']}\n```\n\n## Tags\n\n```\n{', '.join(meta['tags'])}\n```\n"
        )
    else:
        steps = [
            "Open the Instagram app (or instagram.com) as the account and create a new Reel.",
            "Choose `video.mp4` from this folder.",
            "Paste the caption below.",
            f"Share now or schedule for the suggested time ({when}).",
        ]
        body = f"## Caption\n\n```\n{meta['caption']}\n```\n"
    numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
    return f"# Upload: {platform} {fmt}\n\nSuggested publish time: **{when}**\n\n## Steps\n\n{numbered}\n\n{body}"


def _review_md(ctx: RunContext, state: RunState, folders: list[Path]) -> str:
    p = ctx.paths
    pkg = read_json(p.package)
    crit = read_json(p.critic)["final"] if p.critic.exists() else None
    stats = read_json(p.render_dir / "stats.json") if (p.render_dir / "stats.json").exists() else {}
    cost = cost_summary(ctx.sf, ctx.channel.id)
    run_cost = ctx.ledger.spent_run()
    lines = [
        f"# Review: {state.get('topic_title', ctx.run_id)}",
        "",
        f"Run `{ctx.run_id}` on channel **{ctx.channel.name}**. Story shape: `{state.get('story_shape', 'n/a')}`.",
        "",
        "Nothing is published by this pipeline yet. Review, then upload by hand from the folders below.",
        "",
        "## Title options",
        "",
        *[f"{i}. {t}" for i, t in enumerate(pkg["draft"]["titles"], 1)],
        "",
        f"Thumbnail text: **{pkg['draft']['thumbnail_text']}**",
        "",
        "## Check before you post",
        "",
    ]
    if crit:
        r = crit["report"]
        lines += [
            f"Critic: {'passed' if crit['passed'] else 'FAILED'}, hook {r['hook_score']}/10. {r.get('notes', '')}",
            "",
            "**Facts to verify yourself.** The sources below come from the model's own knowledge, not a live search. "
            "Check every number before you post.",
            "",
            "| Claim | Source given |",
            "|---|---|",
            *[f"| {c['text'].replace('|', '/')} | {c['source'].replace('|', '/')} |" for c in r["claims"]],
            "",
        ]
        if crit.get("variety_issues"):
            lines += ["Variety notes: " + "; ".join(crit["variety_issues"]), ""]
    else:
        lines += ["Hand-written scripts: the critic did not run. Check facts, hook and safety yourself.", ""]
    lines += ["## Files", ""]
    for fmt in ctx.channel.formats:
        s = stats.get(fmt, {})
        lines.append(
            f"- {fmt}: `{p.final(fmt)}` ({s.get('duration_sec', '?')}s, rendered in {s.get('render_sec', '?')}s)"
        )
    lines += ["", "## Upload folders", "", *[f"- `{f}`" for f in folders], "", "## Cost", ""]
    lines += [
        f"- This run: ${run_cost:.3f} (cap ${ctx.channel.budget.per_video_usd:.2f})",
        f"- This month: ${cost['total']:.2f} (cap ${ctx.channel.budget.per_month_usd:.2f})",
        "",
    ]
    if pkg["chapters"]:
        lines += [
            "## Chapters (already in the description)",
            "",
            "```",
            chapters_text([(c["at_sec"], c["title"]) for c in pkg["chapters"]]),
            "```",
            "",
        ]
    lines += [
        f'When you are happy: `pipeline approve {ctx.run_id}`. To discard: `pipeline reject {ctx.run_id} --reason "..."`.',
        "",
    ]
    return "\n".join(lines)


def export_node(ctx: RunContext, state: RunState) -> dict[str, Any]:
    p = ctx.paths
    pkg = read_json(p.package)
    metas = pkg["metas"]
    titles = pkg["draft"]["titles"]
    out_run = p.out_root / ctx.channel.id / ctx.run_id
    folders: list[Path] = []
    for dest in ctx.channel.destinations:
        for fmt in dest.formats:
            key = f"{dest.platform}-{fmt}"
            folder = out_run / key
            folder.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p.final(fmt), folder / "video.mp4")
            has_thumb = dest.platform == "youtube" and fmt == "long" and p.thumbnail.exists()
            if has_thumb:
                shutil.copyfile(p.thumbnail, folder / "thumbnail.png")
            meta = dict(metas[key])
            with session_scope(ctx.sf) as s:
                row = s.scalar(
                    select(PostRow).where(
                        PostRow.run_id == ctx.run_id,
                        PostRow.platform == dest.platform,
                        PostRow.account == dest.account,
                        PostRow.format == fmt,
                    )
                )
                if row is None:
                    slot = _slot_for(ctx, fmt)
                    row = PostRow(
                        run_id=ctx.run_id,
                        channel_id=ctx.channel.id,
                        platform=dest.platform,
                        account=dest.account,
                        format=fmt,
                        status="rehearsal" if ctx.options.get("offline") else "manual_pending",
                        path=str(folder),
                        publish_at=slot.astimezone(UTC).replace(tzinfo=None) if slot else None,
                    )
                    s.add(row)
                    s.flush()
                publish_at = row.publish_at
            tz = ctx.channel.schedule.timezone
            when = (
                publish_at.replace(tzinfo=UTC).astimezone(ZoneInfo(tz)).strftime("%a %d %b %Y, %H:%M")
                + f" ({tz})"
                if publish_at
                else "any time"
            )
            write_json(
                folder / "meta.json",
                {
                    **meta,
                    "title_options": titles if fmt == "long" else [],
                    "suggested_publish_at": when,
                    "account": dest.account,
                },
            )
            (folder / "UPLOAD.md").write_text(
                _upload_md(ctx, dest.platform, fmt, meta, titles, when, has_thumb), encoding="utf-8"
            )
            folders.append(folder)

    # remember this video's outline so the critic can compare future scripts against it
    long_doc = ScriptDoc.model_validate(read_json(p.script("long")))
    vec = embed(outline_text(state.get("topic_title", ""), state.get("angle", ""), long_doc))
    with session_scope(ctx.sf) as s:
        if s.scalar(select(EmbeddingRow).where(EmbeddingRow.run_id == ctx.run_id)) is None:
            s.add(
                EmbeddingRow(
                    run_id=ctx.run_id,
                    channel_id=ctx.channel.id,
                    title=state.get("topic_title", long_doc.video_id),
                    story_shape=state.get("story_shape"),
                    vector=vec,
                )
            )

    p.review.write_text(_review_md(ctx, state, folders), encoding="utf-8")
    shutil.copyfile(p.review, out_run / "REVIEW.md")
    ctx.set_status("ready_for_review")
    ctx.log(f"export: ready for review -> {out_run}")
    return {}
