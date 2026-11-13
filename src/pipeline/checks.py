"""Deterministic checks that run in code, never in a model: script rules, chapters, package lint, variety."""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Any

from .schemas import MOODS, ChannelConfig, PackageDraft, Scene, ScriptDoc, StyleBible, Timing
from .util import count_words, fmt_timestamp

MAX_SCENE_NARRATION_SEC = 25.0
SHORT_HARD_LIMIT_SEC = 59.0
TITLE_SOFT_MAX = 70  # longer titles get cut off in feeds


# --- script checks -------------------------------------------------------------
def validate_template_props(template: str, props: dict[str, Any]) -> list[str]:
    errs: list[str] = []

    def need_str_list(key: str, lo: int, hi: int) -> None:
        v = props.get(key)
        if not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v):
            errs.append(f"{template}: props.{key} must be a list of non-empty strings")
        elif not lo <= len(v) <= hi:
            errs.append(f"{template}: props.{key} needs {lo} to {hi} items, got {len(v)}")

    if template == "you_reaction":
        mood = props.get("mood", "neutral")
        if mood not in MOODS:
            errs.append(f"you_reaction: props.mood must be one of {list(MOODS)}, got {mood!r}")
    elif template == "diagram":
        need_str_list("nodes", 2, 5)
    elif template == "number_counter":
        if not isinstance(props.get("to"), (int, float)) or isinstance(props.get("to"), bool):
            errs.append("number_counter: props.to must be a number")
        if "from" in props and (
            not isinstance(props["from"], (int, float)) or isinstance(props["from"], bool)
        ):
            errs.append("number_counter: props.from must be a number")
    elif template == "compare":
        for side in ("left", "right"):
            d = props.get(side)
            if not isinstance(d, dict) or not isinstance(d.get("label"), str):
                errs.append(f"compare: props.{side} must be an object with a label")
                continue
            pts = d.get("points")
            if (
                not isinstance(pts, list)
                or not 1 <= len(pts) <= 4
                or not all(isinstance(x, str) for x in pts)
            ):
                errs.append(f"compare: props.{side}.points must be 1 to 4 strings")
    elif template == "title_card":
        for k in ("title", "subtitle"):
            if k in props and not isinstance(props[k], str):
                errs.append(f"title_card: props.{k} must be a string")
    return errs


def scene_seconds(scene: Scene, wpm: int) -> float:
    return max(count_words(scene.narration) / wpm * 60 + 0.3, scene.min_sec)


def estimate_seconds(doc: ScriptDoc, wpm: int) -> float:
    return sum(scene_seconds(s, wpm) for s in doc.scenes)


def validate_script(
    doc: ScriptDoc,
    style: StyleBible,
    channel: ChannelConfig,
    *,
    scale: float = 1.0,
    no_stills: bool = False,
    length: bool = True,
) -> list[str]:
    errs: list[str] = []
    wpm = style.narrator.wpm
    fmt = doc.format

    total_words = sum(count_words(s.narration) for s in doc.scenes)
    target = style.target_words(fmt, scale)
    tol = 0.10 if scale >= 1.0 else 0.25
    lo, hi = math.floor(target * (1 - tol)), math.ceil(target * (1 + tol))
    if length and not lo <= total_words <= hi:
        errs.append(
            f"[{fmt}] narration is {total_words} words; it must be between {lo} and {hi} (target {target}). "
            f"{'Add' if total_words < lo else 'Cut'} about {abs(total_words - target)} words."
        )

    max_words = round(wpm * MAX_SCENE_NARRATION_SEC / 60)
    for s in doc.scenes:
        n = count_words(s.narration)
        if n > max_words:
            errs.append(f"[{fmt}] scene {s.id} has {n} words (max {max_words}); split it into two scenes")
        if s.visual.type == "template":
            errs += [
                f"[{fmt}] scene {s.id}: {e}"
                for e in validate_template_props(str(s.visual.template), s.visual.props)
            ]

    hero = sum(1 for s in doc.scenes if s.visual.type == "hero_clip")
    if hero and not channel.visuals.hero_clips:
        errs.append(
            f"[{fmt}] {hero} hero_clip scene(s); this channel is on the lean tier, so use template or still"
        )

    stills = sum(1 for s in doc.scenes if s.visual.type == "still")
    cap = channel.visuals.max_stills_long if fmt == "long" else channel.visuals.max_stills_short
    if no_stills or not channel.visuals.stills:
        if stills:
            errs.append(f"[{fmt}] {stills} still scene(s); stills are off, so use only templates")
    elif stills > cap:
        errs.append(f"[{fmt}] {stills} still scenes; the cap is {cap}")

    text_blob = " ".join(
        [s.narration for s in doc.scenes] + [s.on_screen_text or "" for s in doc.scenes]
    ).lower()
    for phrase in style.banned_phrases:
        if phrase.lower() in text_blob:
            errs.append(f"[{fmt}] banned phrase used: {phrase!r}")

    if fmt == "short":
        est = estimate_seconds(doc, wpm)
        if est > SHORT_HARD_LIMIT_SEC:
            errs.append(
                f"[short] estimated {est:.0f}s; a Short must stay under 60s. Cut about {est - 55:.0f}s of narration"
            )
    return errs


# --- chapters ------------------------------------------------------------------
def build_chapters(
    doc: ScriptDoc, timing: Timing, *, min_len: float = 10.0, min_count: int = 3
) -> list[tuple[float, str]]:
    """Chapters in code from timing.json. Start at 00:00, at least three, each at least 10 seconds.
    Returns [] when the video is too short to satisfy YouTube's rules."""
    spans = {s.id: s for s in timing.scenes}
    total = timing.total_sec
    cands: list[tuple[float, str]] = []
    for i, sc in enumerate(doc.scenes):
        if sc.chapter and sc.id in spans:
            cands.append((spans[sc.id].start_ms / 1000, sc.chapter.strip()))
        elif i == 0:
            cands.append((0.0, "Intro"))
    if not cands or cands[0][0] > 0.01:
        cands.insert(0, (0.0, "Intro"))
    cands[0] = (0.0, cands[0][1])

    def prune(items: list[tuple[float, str]]) -> list[tuple[float, str]]:
        changed = True
        while changed and len(items) > 1:
            changed = False
            for i in range(len(items) - 1, -1, -1):
                end = items[i + 1][0] if i + 1 < len(items) else total
                if end - items[i][0] < min_len:
                    # a short chapter is absorbed by the one before it; a short first chapter absorbs the next one
                    items.pop(i if i > 0 else 1)
                    changed = True
                    break
        return items

    chapters = prune(list(cands))
    if len(chapters) < min_count:
        if total < min_len * min_count:
            return []
        starts = [s.start_ms / 1000 for s in timing.scenes]
        names = ["Opening", "What unfolds", "Where it ends"]
        chapters = []
        for k in range(min_count):
            target_t = total * k / min_count
            snapped = min(starts, key=lambda t: abs(t - target_t)) if k else 0.0
            if not chapters or snapped > chapters[-1][0]:
                chapters.append((snapped, names[k]))
        chapters = prune(chapters)
        if len(chapters) < min_count:
            return []
    return chapters


def chapters_text(chapters: Sequence[tuple[float, str]]) -> str:
    return "\n".join(f"{fmt_timestamp(t)} {title}" for t, title in chapters)


# --- package lint --------------------------------------------------------------
def lint_package(
    pkg: PackageDraft, platforms: dict[str, dict[str, dict[str, Any]]], channel: ChannelConfig
) -> list[str]:
    errs: list[str] = []
    yt_long = platforms.get("youtube", {}).get("long", {})
    yt_short = platforms.get("youtube", {}).get("short", {})
    ig = platforms.get("instagram", {}).get("short", {})

    titles = [t.strip() for t in pkg.titles]
    if len({t.lower() for t in titles}) < len(titles):
        errs.append("the three titles must be different from each other")
    limit = min(TITLE_SOFT_MAX, int(yt_long.get("title_max", 100)))
    for t in titles:
        if len(t) > limit:
            errs.append(f"title too long ({len(t)} > {limit} chars): {t!r}")
        if not t:
            errs.append("empty title")
    if len(pkg.thumbnail_text.split()) > 4 or not pkg.thumbnail_text.strip():
        errs.append("thumbnail_text must be 1 to 4 words")
    if any(pkg.thumbnail_text.strip().lower() == t.lower() for t in titles):
        errs.append("thumbnail_text must not repeat a title")
    if len(pkg.short_title) > int(yt_short.get("title_max", 100)) - len(str(yt_short.get("tag", ""))) - 1:
        errs.append(f"short_title too long: {pkg.short_title!r}")
    if not 5 <= len(pkg.tags) <= 20 or sum(len(t) for t in pkg.tags) > 450:
        errs.append("tags: give 5 to 20 tags, 450 characters in total at most")
    if len(pkg.description) > int(yt_long.get("desc_max", 5000)) - 1200:
        errs.append("description is too long once chapters and disclosure are added")
    max_tags = min(5, int(ig.get("hashtags_max", 30)))
    if len(pkg.hashtags) > max_tags or any(not h.startswith("#") or " " in h for h in pkg.hashtags):
        errs.append(f"hashtags: up to {max_tags}, each starting with # and with no spaces")
    cap = int(ig.get("caption_max", 2200))
    if len(pkg.instagram_caption) + sum(len(h) + 1 for h in pkg.hashtags) > cap:
        errs.append(f"instagram caption plus hashtags exceeds {cap} characters")
    return errs


# --- variety (embeddings) -------------------------------------------------------
_STOP = frozenset(
    "a an the and or but if of to in on at for with you your it is are was be as by this that from what when how then so".split()
)
HASH_DIM = 512
_FASTEMBED: Any = None
_FASTEMBED_TRIED = False


def _hash_embed(text: str) -> list[float]:
    toks = [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOP]
    vec = [0.0] * HASH_DIM
    feats = [(t, 1.0) for t in toks] + [(f"{a}_{b}", 1.5) for a, b in zip(toks, toks[1:], strict=False)]
    for f, w in feats:
        h = int(hashlib.sha1(f.encode()).hexdigest()[:8], 16)
        vec[h % HASH_DIM] += w if (h >> 16) % 2 == 0 else -w
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def embed(text: str) -> list[float]:
    """fastembed (local model) when installed and its model is available, else a hashing embedder.
    Vectors of different lengths are never compared, so switching later is safe."""
    global _FASTEMBED, _FASTEMBED_TRIED
    if not _FASTEMBED_TRIED:
        _FASTEMBED_TRIED = True
        try:  # pragma: no cover - depends on optional package and network
            from fastembed import TextEmbedding

            _FASTEMBED = TextEmbedding("BAAI/bge-small-en-v1.5")
        except Exception:
            _FASTEMBED = None
    if _FASTEMBED is not None:  # pragma: no cover
        try:
            return [float(x) for x in next(iter(_FASTEMBED.embed([text])))]
        except Exception:
            pass
    return _hash_embed(text)


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def outline_text(title: str, angle: str, doc: ScriptDoc) -> str:
    chapters = [s.chapter for s in doc.scenes if s.chapter]
    firsts = [
        re.split(r"(?<=[.!?])\s", s.narration.strip())[0]
        for s in doc.scenes[:: max(1, len(doc.scenes) // 10)]
    ]
    return " . ".join([title, angle, *chapters, *firsts])


def variety_issues(
    vec: Sequence[float],
    shape: str | None,
    history: Sequence[tuple[str, str | None, Sequence[float]]],
    threshold: float = 0.85,
) -> list[str]:
    """history = [(title, story_shape, vector)] newest first, at most the last 20 videos."""
    issues: list[str] = []
    for title, _shape, other in history[:20]:
        sim = cosine(vec, other)
        if sim > threshold:
            issues.append(
                f"too similar to an earlier video ({title!r}, similarity {sim:.2f} > {threshold}); change the angle and structure"
            )
    if shape and len(history) >= 1 and all(h[1] == shape for h in history[:3]) and len(history[:3]) == 3:
        issues.append(f"story shape {shape!r} was used in each of the last 3 videos; pick a different shape")
    return issues
