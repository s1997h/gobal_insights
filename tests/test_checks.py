from __future__ import annotations

from typing import Any

import pytest

from pipeline.checks import (
    build_chapters,
    chapters_text,
    cosine,
    embed,
    lint_package,
    outline_text,
    validate_script,
    validate_template_props,
    variety_issues,
)
from pipeline.config import AppConfig
from pipeline.schemas import PackageDraft, Scene, SceneSpan, ScriptDoc, Timing, Visual


def scene(
    i: int,
    words: int = 20,
    *,
    template: str = "captions_only",
    props: dict[str, Any] | None = None,
    chapter: str | None = None,
    text: str | None = None,
    visual: Visual | None = None,
) -> Scene:
    return Scene(
        id=f"s{i:02}",
        narration=text or " ".join(["word"] * words),
        visual=visual or Visual(type="template", template=template, props=props or {}),
        chapter=chapter,
    )


def doc(fmt: str, scenes: list[Scene]) -> ScriptDoc:
    return ScriptDoc(video_id="v", channel_id="whatif", format=fmt, scenes=scenes)  # type: ignore[arg-type]


# --- script validation ---------------------------------------------------------------------
def test_short_over_60s_fails(cfg: AppConfig) -> None:
    ch, st = cfg.channel("whatif"), cfg.style("whatif")
    long_short = doc("short", [scene(i, 30) for i in range(1, 7)])  # 180 words at 150 wpm = 72 s
    errs = validate_script(long_short, st, ch, length=False)
    assert any("under 60s" in e for e in errs)
    ok = doc("short", [scene(i, 20) for i in range(1, 6)])  # 100 words = 40 s
    assert validate_script(ok, st, ch, length=False) == []


def test_word_count_window(cfg: AppConfig) -> None:
    ch, st = cfg.channel("whatif"), cfg.style("whatif")
    target = st.target_words("short")  # 55 s at 150 wpm = 138 words
    exact = doc("short", [scene(i, target // 5) for i in range(1, 6)])
    assert validate_script(exact, st, ch) == []
    too_short = doc("short", [scene(i, 10) for i in range(1, 6)])
    assert any("must be between" in e for e in validate_script(too_short, st, ch))


def test_scene_too_long_is_flagged(cfg: AppConfig) -> None:
    ch, st = cfg.channel("whatif"), cfg.style("whatif")
    errs = validate_script(doc("long", [scene(1, 80), scene(2), scene(3)]), st, ch, length=False)
    assert any("split it" in e for e in errs)


def test_banned_phrase_and_lean_tier(cfg: AppConfig) -> None:
    ch, st = cfg.channel("whatif"), cfg.style("whatif")
    bad = doc("long", [scene(1, text="Hey guys, welcome back to the channel."), scene(2), scene(3)])
    assert any("banned phrase" in e for e in validate_script(bad, st, ch, length=False))
    hero = Visual(type="hero_clip", prompt="a clip")
    errs = validate_script(doc("long", [scene(1, visual=hero), scene(2), scene(3)]), st, ch, length=False)
    assert any("lean tier" in e for e in errs)


def test_still_caps(cfg: AppConfig) -> None:
    ch, st = cfg.channel("whatif"), cfg.style("whatif")
    still = Visual(type="still", prompt="a door")
    scenes = [scene(i, visual=still) for i in range(1, 7)]
    assert any("cap is 4" in e for e in validate_script(doc("short", scenes), st, ch, length=False))
    assert any(
        "stills are off" in e
        for e in validate_script(doc("long", scenes[:3]), st, ch, length=False, no_stills=True)
    )


@pytest.mark.parametrize(
    ("template", "props", "ok"),
    [
        ("diagram", {"nodes": ["a", "b", "c"]}, True),
        ("diagram", {"nodes": ["only one"]}, False),
        ("diagram", {"nodes": ["a", "b", "c", "d", "e", "f"]}, False),
        ("number_counter", {"to": 10}, True),
        ("number_counter", {"to": "10"}, False),
        ("number_counter", {"from": True, "to": 3}, False),
        ("you_reaction", {"mood": "shocked"}, True),
        ("you_reaction", {"mood": "furious"}, False),
        (
            "compare",
            {"left": {"label": "A", "points": ["x"]}, "right": {"label": "B", "points": ["y", "z"]}},
            True,
        ),
        ("compare", {"left": {"label": "A", "points": []}, "right": {"label": "B", "points": ["y"]}}, False),
        ("compare", {"left": {"label": "A"}}, False),
        ("title_card", {"title": "Hi"}, True),
        ("title_card", {"title": 5}, False),
        ("captions_only", {}, True),
    ],
)
def test_template_props(template: str, props: dict[str, Any], ok: bool) -> None:
    assert (validate_template_props(template, props) == []) is ok


def test_unknown_template_rejected_by_schema() -> None:
    with pytest.raises(ValueError, match="unknown template"):
        Visual(type="template", template="spinning_globe")


# --- chapters ----------------------------------------------------------------------------------
def timing_for(lengths: list[float]) -> Timing:
    spans, t = [], 0.0
    for i, n in enumerate(lengths, 1):
        spans.append(SceneSpan(id=f"s{i:02}", start_ms=t * 1000, end_ms=(t + n) * 1000))
        t += n
    return Timing(total_sec=t, scenes=spans)


def test_chapters_follow_youtube_rules() -> None:
    d = doc(
        "long", [scene(1), scene(2, chapter="Hour one"), scene(3), scene(4, chapter="Hour twelve"), scene(5)]
    )
    chapters = build_chapters(d, timing_for([12, 15, 15, 20, 20]))
    assert chapters[0][0] == 0.0
    assert [c[1] for c in chapters] == ["Intro", "Hour one", "Hour twelve"]
    assert len(chapters) >= 3
    gaps = [b[0] - a[0] for a, b in zip(chapters, chapters[1:], strict=False)]
    assert all(g >= 10 for g in gaps)
    assert chapters_text(chapters).splitlines()[0] == "00:00 Intro"


def test_short_chapters_are_merged_and_tiny_videos_get_none() -> None:
    d = doc("long", [scene(1), scene(2, chapter="A"), scene(3, chapter="B"), scene(4, chapter="C"), scene(5)])
    # chapter B lasts 4 s: it must be merged away, then the fallback keeps three valid chapters
    chapters = build_chapters(d, timing_for([15, 15, 4, 15, 15]))
    assert chapters and all(b[0] - a[0] >= 10 for a, b in zip(chapters, chapters[1:], strict=False))
    assert len(chapters) >= 3
    assert build_chapters(d, timing_for([5, 5, 5, 5, 5])) == []


# --- package lint ---------------------------------------------------------------------------
def good_pkg(**over: Any) -> PackageDraft:
    base: dict[str, Any] = {
        "titles": ["What if you stopped sleeping?", "72 hours without sleep", "Your brain on no sleep"],
        "thumbnail_text": "NO SLEEP",
        "thumbnail_mood": "shocked",
        "description": "A calm look at sleep loss.",
        "tags": ["sleep", "brain", "what if", "science", "explained"],
        "short_title": "72 hours awake?",
        "short_description": "In under a minute.",
        "instagram_caption": "Three days awake.",
        "hashtags": ["#sleep", "#brain"],
    }
    base.update(over)
    return PackageDraft.model_validate(base)


def test_package_lint(cfg: AppConfig) -> None:
    ch = cfg.channel("whatif")
    assert lint_package(good_pkg(), cfg.platforms, ch) == []
    long_title = "x" * 71
    assert any(
        "too long" in e for e in lint_package(good_pkg(titles=[long_title, "b", "c"]), cfg.platforms, ch)
    )
    assert any(
        "different" in e for e in lint_package(good_pkg(titles=["Same", "same", "Other"]), cfg.platforms, ch)
    )
    assert any(
        "1 to 4 words" in e
        for e in lint_package(good_pkg(thumbnail_text="THIS IS FAR TOO MANY WORDS"), cfg.platforms, ch)
    )
    assert any("hashtags" in e for e in lint_package(good_pkg(hashtags=["sleep"]), cfg.platforms, ch))
    assert any("tags" in e for e in lint_package(good_pkg(tags=["a", "b"]), cfg.platforms, ch))


# --- variety --------------------------------------------------------------------------------
def test_embedding_similarity_and_variety() -> None:
    a = embed("What if you stopped sleeping for 72 hours. A grounded look at sleep loss and the brain.")
    same = embed("What if you stopped sleeping for 72 hours. A grounded look at sleep loss and the brain.")
    other = embed("What if you won the lottery tomorrow. Taxes, family calls and a new bank account.")
    assert cosine(a, same) == pytest.approx(1.0)
    assert cosine(a, other) < 0.5
    assert cosine(a, [0.0, 1.0]) == 0.0  # different lengths are never compared
    assert variety_issues(a, "countdown", [("old", "year_by_year", same)])
    assert variety_issues(a, "countdown", [("old", "year_by_year", other)]) == []
    hist = [("a", "countdown", other), ("b", "countdown", other), ("c", "countdown", other)]
    assert any("last 3" in i for i in variety_issues(a, "countdown", hist))
    assert variety_issues(a, "year_by_year", hist) == []


def test_outline_text_mentions_title_and_chapters() -> None:
    d = doc(
        "long",
        [
            scene(1, text="You wake up. It is quiet."),
            scene(2, chapter="Hour one", text="Hour one begins."),
            scene(3),
        ],
    )
    text = outline_text("What if you ...", "angle", d)
    assert "What if you ..." in text and "Hour one" in text
