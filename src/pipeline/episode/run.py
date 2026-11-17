"""`pipeline episode`: one topic in, one cartoon video + Shorts + thumbnail + upload kit out.

    topic -> script (model) -> engagement gate (code audit + model critic, up to two rewrites)
          -> director (code) -> voice -> sound -> render -> Shorts -> package -> export

Each step writes its result into runs/<run_id>/ and is skipped when that file exists, so
`pipeline resume <run_id>` continues from the step that failed without paying twice.
"""

from __future__ import annotations

import copy
import json
import re
import shutil
from datetime import UTC, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select

from ..adapters.audio import duration_sec, missing_tool
from ..adapters.llm import LLMOutputError
from ..config import load_backlog, next_slot
from ..context import PipelineError, RunContext
from ..db import AssetRow, RunRow, session_scope
from ..ledger import BudgetExceeded
from ..prompts import banned_text, render_prompt
from ..util import fmt_timestamp, read_json, slugify, utcnow, write_json
from . import produce
from .audit import audit, hook_score
from .caps import caption_tokens, srt
from .director import direct, direct_hook
from .schemas import PAINTED_GUIDE, VIEW_GUIDE, EpisodeCritique, EpisodePackage, EpisodeScript, ShortsPlan

MAX_REWRITES = 3
SHORT_MAX_SEC = 58.0
DONE_STATUSES = ("ready_for_review", "approved")
Shot = dict[str, Any]


# --------------------------------------------------------------------------------------------- topic
def pick_topic(ctx: RunContext) -> dict[str, Any]:
    """--topic wins; otherwise the first backlog line that no finished run has used.

    A backlog line is `Title` or `Title | angle`. The line after it becomes the "next video" on the end card.
    """
    path = ctx.paths.topic
    if path.exists():
        return dict(read_json(path))
    lines = [ln.split("|", 1) for ln in load_backlog(ctx.cfg.root, ctx.channel.id)]
    backlog = [(p[0].strip(), p[1].strip() if len(p) > 1 else "") for p in lines]
    with session_scope(ctx.sf) as s:
        rows = s.scalars(
            select(RunRow).where(
                RunRow.channel_id == ctx.channel.id,
                RunRow.run_id != ctx.run_id,
                RunRow.status.in_(DONE_STATUSES),
            )
        )
        used = {(r.topic or "").lower() for r in rows}
    unused = [b for b in backlog if b[0].lower() not in used]
    override = ctx.options.get("topic")
    if override:
        title, angle, source = str(override), str(ctx.options.get("angle") or ""), "cli"
        rest = [b for b in unused if b[0].lower() != title.lower()]
    elif unused:
        (title, angle), rest, source = unused[0], unused[1:], "backlog"
    else:
        raise PipelineError(
            f"Every topic in config/channels/{ctx.channel.id}/backlog.md has been made. Add new lines to that "
            "file, or pass --topic."
        )
    data = {
        "chosen": {"title": title, "angle": angle, "story_shape": "episode", "hook_idea": ""},
        "candidates": [],
        "source": source,
        "next": rest[0][0] if rest else "",
    }
    write_json(path, data)
    return data


# -------------------------------------------------------------------------------------------- script
def _generate(ctx: RunContext, *args: Any, **kw: Any) -> Any:
    """One extra fresh attempt when the model cannot produce a valid answer (the adapter already retries twice)."""
    try:
        return ctx.llm.generate(*args, **kw)
    except LLMOutputError as e:
        ctx.log(f"model: invalid answer, asking once more from scratch ({str(e)[:200]})")
        return ctx.llm.generate(*args, **kw)


def _banned(script: EpisodeScript, phrases: list[str]) -> list[str]:
    out = []
    for i, b in enumerate(script.beats, 1):
        low = b.say.lower()
        out += [f"beat {i}: remove the phrase {p!r}" for p in phrases if p.lower() in low]
    return out


# Lines from the worked example in prompts/episode_painted.md. Another story must invent its own.
EXAMPLE_LINES = (
    "what's in your drawer",
    "needs work",
    "that's cute",
    "nice toaster",
    "don't tell anyone about it",
)


def _copied(s: EpisodeScript, title: str) -> list[str]:
    if "kodak" in title.lower():
        return []
    out = []
    for i, b in enumerate(s.beats, 1):
        hit = next((x for x in EXAMPLE_LINES if x in b.say.lower().replace("’", "'")), None)
        if hit:
            out.append(
                f"beat {i} copies the Kodak example ({hit!r}). Invent a line, gag or question that belongs to this story"
            )
    return out


def write_script(ctx: RunContext, topic: dict[str, Any], target: int) -> tuple[EpisodeScript, dict[str, Any]]:
    """Draft, audit, critique; rewrite with the fixes at most MAX_REWRITES times. Returns (script, gate report)."""
    p = ctx.paths
    gate_path = p.run_dir / "gate.json"
    if p.script("long").exists() and gate_path.exists():
        return EpisodeScript.model_validate(read_json(p.script("long"))), dict(read_json(gate_path))
    title = topic["chosen"]["title"]
    painted = ctx.style.look == "painted"
    shapes = "\n".join(f"- {s.name}: {s.description}" for s in ctx.style.story_shapes)
    common = {
        "channel_name": ctx.channel.name,
        "voice_rules": ctx.style.voice_rules.strip(),
        "view_guide": VIEW_GUIDE,
    }
    system = render_prompt(
        ctx.cfg.root,
        "episode_script",
        **common,
        banned_phrases=banned_text(ctx.style),
        story_shapes=shapes,
        target_words=target,
        lo=round(target * 0.9),
        hi=round(target * 1.1),
        beats=max(8, round(target / 17)),
        chapters="one or two" if target < 400 else "six to nine",
        look_guide=render_prompt(ctx.cfg.root, "episode_painted", painted_guide=PAINTED_GUIDE)
        if painted
        else "",
    )
    critic_system = render_prompt(ctx.cfg.root, "episode_critic", **common)

    def check(s: EpisodeScript) -> list[str]:
        return (s.problems(target, painted) + _banned(s, ctx.style.banned_phrases) + _copied(s, title))[:12]

    fixes: list[str] = []
    draft: EpisodeScript | None = None
    best: tuple[int, EpisodeScript, list[str], int] | None = None  # (open fixes, draft, fixes, attempt)
    history: list[dict[str, Any]] = []
    for attempt in range(1, MAX_REWRITES + 2):
        ask: dict[str, Any] = {
            "TOPIC": title,
            "ANGLE": topic["chosen"].get("angle") or "(your choice: find the most surprising true angle)",
            "NEXT VIDEO (for the end card label)": topic.get("next") or "A new story every week",
        }
        if draft is not None:
            ask["YOUR LAST DRAFT"] = draft.model_dump(exclude_defaults=True)
            ask["REWRITE IT TO FIX ALL OF THESE"] = fixes
            ask["HOW TO REWRITE"] = (
                "Apply every fix above; where a fix gives replacement text, use it word for word. Keep the beats that "
                f"work. The new draft must be about {target} words: if your last draft was short, add scenes and "
                "spoken exchanges, never filler."
            )
        ctx.advance((attempt - 1) / (MAX_REWRITES + 1))
        ctx.log(f"script: draft {attempt} ({target} words wanted)")
        draft = _generate(
            ctx, "strong", "script", system, json.dumps(ask, indent=1, ensure_ascii=False), EpisodeScript,
            check=check, hints={"topic": title, "target_words": target},
        )  # fmt: skip
        assert draft is not None
        report = audit(draft)
        words = report["words"]
        if not 0.88 * target <= words <= 1.12 * target:
            report["fixes"].append(
                f"The script is {words} words. Write {target} (between {round(target * 0.9)} and {round(target * 1.1)})."
            )
        critic: EpisodeCritique = _generate(
            ctx, "strong", "critic", critic_system,
            json.dumps({"TOPIC": title, "SCRIPT": draft.model_dump(exclude_defaults=True), "CODE AUDIT": report}, ensure_ascii=False),
            EpisodeCritique, hints={},
        )  # fmt: skip
        fixes = report["fixes"] + ([] if critic.passed else critic.fixes[:6])
        history.append(
            {"attempt": attempt, "audit": report, "critic": critic.model_dump(), "open_fixes": fixes}
        )
        write_json(p.run_dir / f"script_draft{attempt}.json", draft.model_dump(exclude_defaults=True))
        ctx.log(
            f"gate: draft {attempt}: {words} words, hook {report['hook']['total']}/100, critic {critic.hook_score}/10, "
            f"{len(fixes)} fix(es) open"
        )
        if best is None or len(fixes) < best[0]:
            best = (len(fixes), draft, fixes, attempt)
        if not fixes:
            break
    assert draft is not None and best is not None
    if best[1] is not draft:  # a rewrite can make things worse: ship the draft with the fewest open fixes
        ctx.log(f"gate: keeping draft {best[3]} ({best[0]} open fix(es)), the best of {len(history)}")
    _, draft, fixes, kept = best
    gate = {
        "passed": not fixes,
        "attempts": len(history),
        "open_fixes": fixes,
        **history[kept - 1],
        "history": history,
    }
    write_json(p.script("long"), draft.model_dump())
    write_json(gate_path, gate)
    return draft, gate


# -------------------------------------------------------------------------------------------- shorts
def plan_shorts(
    ctx: RunContext, script: EpisodeScript, spans: list[dict[str, Any]], wps: float, count: int
) -> ShortsPlan:
    path = ctx.paths.run_dir / "shorts" / "plan.json"
    if path.exists():
        return ShortsPlan.model_validate(read_json(path))
    last_ok = len(script.beats) - 1  # the end card never goes into a Short
    secs = [(s["end_ms"] - s["start_ms"]) / 1000 for s in spans]
    lo, hi = (5.0, 52.0) if ctx.quick else (18.0, 52.0)

    def check(plan: ShortsPlan) -> list[str]:
        errs: list[str] = []
        if len(plan.shorts) != count:
            errs.append(f"return exactly {count} shorts (got {len(plan.shorts)})")
        taken: set[int] = set()
        for k, sp in enumerate(plan.shorts, 1):
            if not 1 <= sp.first_beat <= sp.last_beat <= last_ok:
                errs.append(f"short {k}: beats must run from first_beat to last_beat within 1..{last_ok}")
                continue
            span = set(range(sp.first_beat, sp.last_beat + 1))
            if span & taken:
                errs.append(f"short {k}: overlaps another short; use different beats")
            taken |= span
            est = sum(secs[sp.first_beat - 1 : sp.last_beat]) + len(sp.hook.say.split()) / wps + 0.5
            if not lo <= est <= hi:
                errs.append(
                    f"short {k}: about {est:.0f} seconds with its hook; it must be {lo:.0f} to {hi:.0f}"
                )
            errs += [f"short {k} hook, {e}" for e in sp.hook.problems(0)]
            if sp.hook.view == "end":
                errs.append(f"short {k}: the hook cannot be an end card")
            errs += [
                f"short {k}: title line {ln!r} is over 20 characters" for ln in sp.title_lines if len(ln) > 20
            ]
            if len(sp.youtube_title) > 90:
                errs.append(f"short {k}: youtube_title is over 90 characters")
        return errs[:12]

    beats = [
        {"beat": i + 1, "seconds": round(secs[i], 1), "say": b.say, "view": b.view, **({"chapter": b.chapter} if b.chapter else {})}
        for i, b in enumerate(script.beats[:last_ok])
    ]  # fmt: skip
    system = render_prompt(
        ctx.cfg.root, "episode_shorts", channel_name=ctx.channel.name, view_guide=VIEW_GUIDE, count=count
    )
    plan: ShortsPlan = _generate(
        ctx, "strong", "shorts", system,
        json.dumps({"HOW MANY": count, "PAYOFF BEAT": script.payoff_beat, "BEATS": beats}, ensure_ascii=False),
        ShortsPlan, check=check, hints={"count": count, "beats": last_ok},
    )  # fmt: skip
    write_json(path, plan.model_dump())
    return plan


def make_shorts(
    ctx: RunContext, script: EpisodeScript, shots: list[Shot], long_voice: dict[str, Any],
    narrator: produce.Narrator, bundled: Path, count: int, span: tuple[float, float] = (70.0, 94.0),
) -> list[dict[str, Any]]:  # fmt: skip
    count = min(count, max(1, (len(script.beats) - 1) // 3))
    wps = max(1.5, float(long_voice.get("wpm") or 156) / 60)
    lo, hi = span
    ctx.stage(lo, lo + 2)
    plan = plan_shorts(ctx, script, long_voice["scenes"], wps, count)
    made: list[dict[str, Any]] = []
    each = (hi - lo - 2) / max(1, len(plan.shorts))
    for k, sp in enumerate(plan.shorts, 1):
        start = lo + 2 + (k - 1) * each
        ctx.stage(start, start + 0.2 * each)
        work = ctx.paths.run_dir / "shorts" / f"s{k}"
        final = ctx.paths.final_dir / f"short{k}.mp4"
        cover = ctx.paths.final_dir / f"short{k}-cover.jpg"
        picked = [direct_hook(sp.hook, f"h{k}", ctx.style.look)]
        for s in shots[sp.first_beat - 1 : sp.last_beat]:
            c = copy.deepcopy(s)
            c["tr"] = "punch"
            picked.append(c)
        v = produce.voice(narrator, picked, work / "audio")
        while v["total_sec"] > SHORT_MAX_SEC and len(picked) > 2:
            picked.pop()
            v = produce.voice(narrator, picked, work / "audio")
        if v["total_sec"] > SHORT_MAX_SEC + 1.5:
            ctx.log(f"short {k}: {v['total_sec']:.0f}s is too long for a Short; skipped")
            continue
        timing = {"total_sec": v["total_sec"], "scenes": v["scenes"]}
        produce.mouths(picked, timing, v["words"])
        props = {
            "shots": picked,
            "timing": timing,
            "words": v["words"],
            "caps": caption_tokens(v["words"]),
            "title": sp.title_lines,
            "highlight": sp.highlight,
            "brand": ctx.channel.name,
        }
        ctx.stage(start + 0.2 * each, start + 0.95 * each)
        silent = produce.render_video(ctx, bundled, "EpisodeShort", props, work, "short", label=f"short {k}")
        if not final.exists() or final.stat().st_mtime < silent.stat().st_mtime:
            produce.mux(silent, produce.mix(work / "audio", picked, timing, ctx.style.music.volume), final)
            produce.still(
                ctx, bundled, "EpisodeShort", props, cover, frame=min(45, int(v["total_sec"] * 30) - 1)
            )
        tags = [h if h.startswith("#") else f"#{h}" for h in sp.hashtags][:5]
        made.append(
            {"n": k, "file": final, "cover": cover, "sec": round(v["total_sec"], 1), "title": sp.youtube_title.strip(),
             "caption": sp.instagram_caption.strip(), "hashtags": tags, "beats": [sp.first_beat, sp.last_beat]}
        )  # fmt: skip
        ctx.log(f"short {k}: {v['total_sec']:.1f}s -> {final.name}")
    return made


# ------------------------------------------------------------------------------------------- package
def _caps_words(title: str) -> int:
    return sum(1 for w in re.findall(r"[A-Za-z]{3,}", title) if w.isupper())


def write_package(ctx: RunContext, topic: str, script: EpisodeScript) -> EpisodePackage:
    path = ctx.paths.package
    if path.exists():
        return EpisodePackage.model_validate(read_json(path))

    def check(pk: EpisodePackage) -> list[str]:
        errs = [f"title {t!r} is {len(t)} characters; max 60" for t in pk.titles if len(t) > 60]
        errs += [f"title {t!r} has more than two ALL-CAPS words" for t in pk.titles if _caps_words(t) > 2]
        if len(set(t.lower() for t in pk.titles)) < 3:
            errs.append("the three titles must be different")
        thumb = f"{pk.thumb_top} {pk.thumb_bottom}".split()
        if not 1 <= len(thumb) <= 3:
            errs.append("the thumbnail takes one to three words in total")
        for part in (pk.thumb_top, pk.thumb_bottom):
            if len(part) > 10:
                errs.append(f"thumbnail text {part!r} is over 10 characters")
        title_words = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", pk.titles[0])}
        errs += [
            f"thumbnail word {w!r} repeats the first title; use different words"
            for w in thumb
            if w.lower() in title_words
        ]
        if len(pk.description) < 120:
            errs.append("the description needs at least 120 characters")
        kw = [w for w in re.findall(r"[a-z0-9']+", pk.keyword.lower()) if len(w) > 2]
        if not 2 <= len(pk.keyword.split()) <= 5:
            errs.append("`keyword` is the 2-4 word phrase people type into search for this video")
        else:
            missing = [w for w in kw if w not in pk.titles[0].lower()]
            if missing:
                errs.append(
                    f"the first title must contain the search phrase {pk.keyword!r}; missing {missing}"
                )
            if any(w not in pk.description[:160].lower() for w in kw):
                errs.append(
                    f"the first 150 characters of the description must contain the search phrase {pk.keyword!r}"
                )
        return errs

    system = render_prompt(ctx.cfg.root, "episode_package", channel_name=ctx.channel.name)
    ask = {
        "TOPIC": topic,
        "HERO": script.hero,
        "PROMISE": script.promise,
        "COMMENT QUESTION": script.comment_prompt,
        "NARRATION": " ".join(b.say for b in script.beats),
    }
    pk: EpisodePackage = _generate(
        ctx,
        "small",
        "package",
        system,
        json.dumps(ask, ensure_ascii=False),
        EpisodePackage,
        check=check,
        hints={"topic": topic},
    )
    write_json(path, pk.model_dump())
    return pk


def chapter_lines(chapters: list[list[str]], spans: list[dict[str, Any]], total: float) -> list[str]:
    """YouTube chapters: first at 00:00, at least three, each at least 10 seconds. Otherwise none."""
    start = {s["id"]: s["start_ms"] / 1000 for s in spans}
    marks = [
        (0.0 if i == 0 else start[sid], title) for i, (sid, title) in enumerate(chapters) if sid in start
    ]
    kept: list[tuple[float, str]] = []
    for t, title in marks:
        if kept and t - kept[-1][0] < 10:
            continue
        kept.append((t, title))
    if kept and total - kept[-1][0] < 10:
        kept.pop()
    return [f"{fmt_timestamp(t)} {title}" for t, title in kept] if len(kept) >= 3 else []


def _sources(script: EpisodeScript) -> list[str]:
    seen: list[str] = []
    for src in [b.source for b in script.beats if b.source] + [c.source for c in script.claims]:
        s = (src or "").strip()
        if s and not re.search(r"unsure|placeholder|^none\b", s.lower()) and s not in seen:
            seen.append(s)
    return seen


def _slots(ctx: RunContext, fmt: str, n: int, after: Any) -> list[Any]:
    out = []
    for _ in range(n):
        slot = next_slot(ctx.channel, fmt, after)
        if slot is None:
            break
        out.append(slot)
        after = slot.astimezone(UTC).replace(tzinfo=None)
    return out


# -------------------------------------------------------------------------------------------- export
def export(
    ctx: RunContext, topic: str, script: EpisodeScript, gate: dict[str, Any], pk: EpisodePackage,
    chapters: list[list[str]], long_voice: dict[str, Any], shorts: list[dict[str, Any]], narrator: produce.Narrator,
) -> Path:  # fmt: skip
    p = ctx.paths
    out = p.out_root / ctx.channel.id / ctx.run_id
    yt, sh = out / "youtube", out / "shorts"
    yt.mkdir(parents=True, exist_ok=True)
    sh.mkdir(parents=True, exist_ok=True)
    total = float(long_voice["total_sec"])
    offline = ctx.llm.name == "fake" or ctx.tts.name == "fake"

    chaps = chapter_lines(chapters, long_voice["scenes"], total)
    sources = _sources(script)
    desc = pk.description.strip()
    if chaps:
        desc += "\n\nChapters\n" + "\n".join(chaps)
    if sources:
        desc += "\n\nSources\n" + "\n".join(f"- {s}" for s in sources)
    if ctx.style.disclosure:
        desc += f"\n\n{ctx.style.disclosure}"
    desc += "\n\n" + " ".join(h if h.startswith("#") else f"#{h}" for h in pk.hashtags)

    shutil.copyfile(p.final("long"), yt / "video.mp4")
    shutil.copyfile(p.thumbnail, yt / "thumbnail.png")
    (yt / "description.txt").write_text(desc + "\n", encoding="utf-8")
    (yt / "captions.srt").write_text(srt(long_voice["words"]), encoding="utf-8")

    now = utcnow() + timedelta(hours=2)
    long_slot = (_slots(ctx, "long", 1, now) or [None])[0]
    after_long = long_slot.astimezone(UTC).replace(tzinfo=None) if long_slot else now
    short_slots = _slots(ctx, "short", len(shorts), after_long)
    when = long_slot.strftime("%a %d %b, %H:%M %Z") if long_slot else "your next free slot"
    upload = [
        f"# Upload: {pk.titles[0]}",
        "",
        f"Suggested time: **{when}**",
        "",
        "1. YouTube Studio > Create > Upload video > `video.mp4`.",
        "2. Title (pick one):",
        *[f"   - {t}" for t in pk.titles],
        "3. Description: paste `description.txt` (chapters and sources are inside).",
        "4. Thumbnail: `thumbnail.png`.",
        "5. Subtitles > Upload file > With timing > `captions.srt`.",
        f"6. Tags: {', '.join(pk.tags)}",
        "7. Altered content: answer Yes if asked whether the video uses AI-made voice or visuals.",
        "8. After it is live, pin this comment:",
        "",
        f"   > {pk.pinned_comment.strip()}",
        "",
    ]
    (yt / "UPLOAD.md").write_text("\n".join(upload), encoding="utf-8")

    posting = [
        "# Shorts and Reels",
        "",
        "Post each file to YouTube Shorts, then the same file as an Instagram Reel.",
        "",
    ]
    for i, s in enumerate(shorts):
        shutil.copyfile(s["file"], sh / f"short{s['n']}.mp4")
        shutil.copyfile(s["cover"], sh / f"short{s['n']}-cover.jpg")
        slot = short_slots[i].strftime("%a %d %b, %H:%M %Z") if i < len(short_slots) else "next free slot"
        posting += [
            f"## short{s['n']}.mp4 ({s['sec']:.0f} s)",
            "",
            f"- YouTube Shorts, {slot}",
            f"  - Title: {s['title']} #shorts",
            "  - Related video: link the long video.",
            "- Instagram Reel (cover: the matching `-cover.jpg`)",
            f"  - Caption: {s['caption']}",
            f"  - Hashtags: {' '.join(s['hashtags'])}",
            "",
        ]
    (sh / "POSTING.md").write_text("\n".join(posting), encoding="utf-8")

    a = gate["audit"]
    review = [
        f"# Review before posting: {topic}",
        "",
        *(["> OFFLINE REHEARSAL: fake script and beep voice. Do not upload.", ""] if offline else []),
        f"- Length: {fmt_timestamp(total)} ({a['words']} words, {len(script.beats)} shots)",
        "- Voice: offline beeps (no real voice was used)"
        if ctx.tts.name == "fake"
        else f"- Voice: {narrator.voice}, measured pace {long_voice.get('wpm') or 0:.0f} words a minute "
        f"(narrator.wpm in the style file is {ctx.style.narrator.wpm}; set it to the measured figure)",
        f"- Engagement gate: {'passed' if gate['passed'] else 'NOT passed'} after {gate['attempts']} draft(s). "
        f"Opening line {a['hook']['total']}/100, critic {gate['critic']['hook_score']}/10.",
        f"- Hero: {script.hero or '(not set)'}. At stake: {script.stakes or '(not set)'}",
        f'- First line: "{script.beats[0].say}"',
        *[
            f'  - other candidate ({hook_score(h)["total"]}/100): "{h}"'
            for h in script.hooks
            if h.strip() != script.beats[0].say.strip()
        ],
        f"- Story: {a.get('story_turns_per_minute', 0)} turns a minute, {a.get('different_places', 0)} places, "
        f"{a.get('avg_words_per_sentence', 0)} words a sentence.",
        f"- Promise: {script.promise} Answered at beat {script.payoff_beat} ({a['payoff_at_fraction']:.0%} of the way in).",
        f"- Shorts made: {len(shorts)}",
        "",
    ]
    if gate["open_fixes"]:
        review += ["## Still open after the rewrites", "", *[f"- {f}" for f in gate["open_fixes"]], ""]
    review += [
        "## Check these by hand",
        "",
        "1. Listen to the whole video once. The code cannot hear a mispronounced name or number.",
        "2. Check every claim below against its source. The model can be wrong, and it can misremember a source.",
        "3. Watch the first 30 seconds as a stranger would. Would you stay?",
        "",
        "## Claims",
        "",
        "| Claim | Source the model gave |",
        "|---|---|",
        *[f"| {c.text.replace('|', '/')} | {c.source.replace('|', '/')} |" for c in script.claims],
        "",
    ]
    if gate["critic"].get("risky_claims"):
        review += ["## The critic flagged these", "", *[f"- {c}" for c in gate["critic"]["risky_claims"]], ""]
    review += [
        "## Files",
        "",
        f"- `{yt}`: video, thumbnail, description, captions, UPLOAD.md",
        f"- `{sh}`: Shorts, covers, POSTING.md",
        "",
    ]
    text = "\n".join(review)
    p.review.write_text(text, encoding="utf-8")
    (out / "REVIEW.md").write_text(text, encoding="utf-8")
    return out


# ----------------------------------------------------------------------------------------------- run
def preflight() -> None:
    """Fail in the first second, before any paid step, when a program the run needs at the end is missing."""
    missing = [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]
    if missing:
        raise PipelineError(missing_tool(" and ".join(missing)))


def _run(ctx: RunContext) -> None:
    p = ctx.paths
    p.run_dir.mkdir(parents=True, exist_ok=True)
    p.final_dir.mkdir(parents=True, exist_ok=True)
    ctx.stage(0, 2)
    preflight()
    topic = pick_topic(ctx)
    title = topic["chosen"]["title"]
    ctx.set_status("running", topic=title, story_shape="episode")
    ctx.log(f"topic: {title}  [{topic['source']}]")

    target = ctx.style.target_words("long", ctx.scale)
    ctx.stage(2, 16)
    script, gate = write_script(ctx, topic, target)

    shots, chapters = direct(script, look=ctx.style.look)
    write_json(p.run_dir / "shots.json", {"title": title, "shots": shots, "chapters": chapters})

    ctx.stage(16, 23)
    narrator = produce.Narrator(ctx)
    audio = p.run_dir / "audio"
    long_voice = produce.load_voice(audio)
    if long_voice is None:
        ctx.log(f"voice: reading {len(shots)} lines with {narrator.voice}")
        long_voice = produce.voice(narrator, shots, audio, {sid for sid, _ in chapters[1:]})
        write_json(audio / "voice.json", {"voice": narrator.voice, "wpm": long_voice["wpm"]})
        ctx.log(
            f"voice: {long_voice['total_sec'] / 60:.1f} min, {narrator.new_chars} new characters, "
            f"{long_voice['wpm']:.0f} words a minute ({narrator.voice})"
        )
    elif (audio / "voice.json").exists():
        meta = read_json(audio / "voice.json")
        narrator.voice, long_voice["wpm"] = meta["voice"], meta["wpm"]
    timing = {"total_sec": long_voice["total_sec"], "scenes": long_voice["scenes"]}

    ctx.stage(23, 25)
    bundled = produce.bundle(ctx, p.render_dir)
    final = p.final("long")
    ctx.stage(25, 68)
    props: dict[str, Any] = {"shots": shots, "timing": timing}
    if ctx.style.look == "painted":  # talking mouths and burnt-in captions
        props["shots"] = produce.mouths(shots, timing, long_voice["words"])
        props["words"] = produce.captions(long_voice["words"])
    silent = produce.render_video(ctx, bundled, "Episode", props, p.render_dir, "long")
    ctx.stage(68, 70)
    if not final.exists() or final.stat().st_mtime < silent.stat().st_mtime:
        ctx.log("sound: mixing voice, music and effects")
        produce.mux(silent, produce.mix(audio, shots, timing, ctx.style.music.volume), final)
    ctx.advance(1)
    dur = duration_sec(final)
    ctx.log(f"render: long video {fmt_timestamp(dur)} -> {final}")

    shorts = make_shorts(ctx, script, shots, long_voice, narrator, bundled, int(ctx.options.get("shorts", 4)))

    ctx.stage(94, 98)
    pk = write_package(ctx, title, script)
    if not p.thumbnail.exists() and ctx.style.look == "painted":
        from . import painted

        raw = produce.still(
            ctx, bundled, "Episode",
            {"shots": [painted.thumbnail_shot(script.beats, pk.thumb_mood)], "timing": {"total_sec": 1, "scenes": [{"id": "thumb", "start_ms": 0, "end_ms": 1000}]}},
            p.thumbnail.with_name("thumb-picture.png"), frame=20,
        )  # fmt: skip
        painted.thumbnail_words(
            raw,
            p.thumbnail,
            pk.thumb_top,
            pk.thumb_bottom,
            ctx.cfg.root / "assets" / "fonts" / "Inter-ExtraBold.otf",
        )
    if not p.thumbnail.exists():
        produce.still(
            ctx, bundled, "MoneyThumb", {"top": pk.thumb_top.upper(), "bottom": pk.thumb_bottom.upper(), "object": pk.thumb_object, "mood": pk.thumb_mood},
            p.thumbnail,
        )  # fmt: skip

    ctx.stage(98, 100)
    out = export(ctx, title, script, gate, pk, chapters, long_voice, shorts, narrator)
    with session_scope(ctx.sf) as s:
        row = s.query(AssetRow).filter_by(run_id=ctx.run_id, format="long").one_or_none()
        if row is None:
            s.add(AssetRow(run_id=ctx.run_id, format="long", path=str(final), duration_sec=dur))
        else:
            row.path, row.duration_sec = str(final), dur
    note = (
        None
        if gate["passed"]
        else f"engagement gate still has {len(gate['open_fixes'])} open fix(es); see REVIEW.md"
    )
    ctx.set_status("ready_for_review", error=note)
    ctx.advance(1)
    ctx.log(f"done: {out}  ({slugify(title)})")


def run_episode(ctx: RunContext) -> None:
    """Run or resume one episode. Failures are recorded on the run row, then re-raised for the CLI to report."""
    try:
        _run(ctx)
    except BudgetExceeded as e:
        ctx.set_status("failed", error=f"budget: {e}")
        raise
    except Exception as e:
        ctx.set_status("failed", error=f"{type(e).__name__}: {e}"[:1500])
        raise
