"""The cartoon-episode command: director, engagement gate, captions, and the whole run with fakes."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from pipeline.adapters.tts import SynthResult
from pipeline.context import PipelineError, RunContext
from pipeline.db import RunRow, session_scope
from pipeline.episode import produce
from pipeline.episode.audit import audit, hook_score
from pipeline.episode.caps import caption_tokens, srt
from pipeline.episode.director import direct, direct_hook
from pipeline.episode.run import chapter_lines, pick_topic, run_episode, write_script
from pipeline.episode.schemas import Beat, EpisodeCritique, EpisodeScript
from pipeline.schemas import WordTiming
from pipeline.util import read_json

from .conftest import MakeCtx, needs_ffmpeg


def _words(text: str) -> list[dict[str, Any]]:
    return [{"word": w, "start_ms": i * 300.0, "end_ms": i * 300.0 + 250} for i, w in enumerate(text.split())]


# ------------------------------------------------------------------------------------------ director
def test_director_places_everything_on_screen() -> None:
    script = EpisodeScript.offline_example({"target_words": 400})
    assert script.problems(400) == []
    shots, chapters = direct(script)
    assert len(shots) == len(script.beats)
    assert chapters[0][0] == shots[0]["id"]
    for shot, beat in zip(shots, script.beats, strict=True):
        assert shot["n"] == beat.say and shot["set"]
        for a in shot.get("actors", []):
            assert 0 < a["x"] < 1920 and a["y"] == 1000
        for pr in shot.get("props", []):
            assert 0 <= pr["x"] <= 1920
    assert shots[-1]["ov"]["t"] == "end"
    # a new chapter arrives with a wipe; the very first shot does not
    assert "tr" not in shots[0]
    assert any(s.get("tr") == "wipe" for s in shots[1:])


def test_clock_carries_forward_and_flashbacks_drop_it() -> None:
    script = EpisodeScript.model_validate(
        {
            "promise": "p",
            "payoff_beat": 2,
            "comment_prompt": "c",
            "beats": [
                {"say": "You wake up.", "view": "scene", "set": "bedroom", "people": [{}], "clock": "8:00 AM", "chapter": "Morning"},
                {"say": "You walk out.", "view": "scene", "set": "street", "people": [{"pose": "walk"}]},
                {"say": "Years ago, it happened before.", "view": "scene", "set": "bank_front", "people": [{}], "past": True},
                {"say": "Back to you.", "view": "object", "object": "wallet"},
                {"say": "It is trust.", "view": "title", "big": "TRUST"},
                {"say": "Tell me.", "view": "end", "label": "Next one"},
            ],
        }
    )  # fmt: skip
    shots, _ = direct(script)
    assert [s.get("clock") for s in shots] == ["8:00 AM", "8:00 AM", None, "8:00 AM", "8:00 AM", None]
    assert shots[2]["tod"] == "sepia"
    assert shots[1]["actors"][0]["walk"][1] == shots[1]["actors"][0]["x"]


def test_beat_problems_name_the_field() -> None:
    assert "source" in " ".join(Beat(say="x", view="stat", big="86%", label="of cash").problems(3))
    assert "6 characters" in " ".join(
        Beat(say="x", view="stat", big="1,234,567", label="l", source="s").problems(3)
    )
    assert Beat(say="x", view="scene", set="bazaar", scene_prop="queue").problems(1) == []
    assert "clock" in " ".join(Beat(say="x", view="object", object="wallet", clock="9am").problems(1))


def test_direct_hook_makes_one_plain_shot() -> None:
    shot = direct_hook(
        Beat(say="Your payment just failed. Now what?", view="object", object="phone_fail"), "h1"
    )
    assert shot["id"] == "h1" and "tr" not in shot and shot["props"][0]["t"] == "pay_phone"


# --------------------------------------------------------------------------------------------- audit
def test_hook_score_prefers_a_concrete_question_to_you() -> None:
    good = hook_score(
        "At eight tomorrow morning your payment fails, and so does everyone else's. What do you do?"
    )
    bad = hook_score(
        "Money is an interesting concept that has existed for a very long time in human history."
    )
    assert good["total"] > bad["total"] + 20


def test_audit_asks_for_specific_rewrites() -> None:
    flat = EpisodeScript.model_validate(
        {
            "promise": "p",
            "payoff_beat": 1,
            "comment_prompt": "c",
            "beats": [{"say": "Money is a system of exchange used by people.", "view": "title", "big": "MONEY", "chapter": "Intro"}] * 7
            + [{"say": "That is all.", "view": "end", "label": "Next"}],
        }
    )  # fmt: skip
    fixes = " ".join(audit(flat)["fixes"])
    assert "first 15 seconds" in fixes and "'you'" in fixes and "End on one ask" in fixes
    assert audit(EpisodeScript.offline_example({"target_words": 160}))["hook"]["total"] >= 50


# ------------------------------------------------------------------------------------------ captions
def test_captions_turn_number_words_into_numerals() -> None:
    toks = caption_tokens(
        _words(
            "In twenty sixteen, eighty-six percent of cash stopped. Eight hundred and twenty-two million payments. One friend."
        )
    )
    text = [t["text"] for t in toks]
    assert "2016," in text and "86%" in text and "822" in text
    assert "One" in text  # a small count stays a word
    assert all(t.get("num") for t in toks if t["text"] in ("2016,", "86%", "822"))


def test_srt_has_increasing_cues() -> None:
    out = srt(_words("You scan the code. Payment failed. And you are not the only one today."))
    assert out.startswith("1\n00:00:00,000 --> ")
    assert out.count("-->") >= 3


def test_script_words_keep_punctuation_and_survive_a_mismatch(tmp_path: Path) -> None:
    def res(tokens: list[str]) -> SynthResult:
        ws = [WordTiming(word=t, start_ms=i * 100.0, end_ms=i * 100.0 + 90) for i, t in enumerate(tokens)]
        return SynthResult(tmp_path / "x.wav", 1000.0, ws, 0, cached=True)

    exact = produce.script_words(
        "Payment failed. Twenty-two times!", res(["Payment", "failed", "Twenty", "two", "times"])
    )
    assert [w["word"] for w in exact] == ["Payment", "failed.", "Twenty-two", "times!"]
    assert exact[2]["start_ms"] == 200.0 and exact[2]["end_ms"] == 390.0
    rough = produce.script_words("Payment failed. Now what?", res(["Payment", "fails"]))
    assert [w["word"] for w in rough] == ["Payment", "failed.", "Now", "what?"]
    assert rough[0]["start_ms"] == 0.0 and rough[-1]["end_ms"] == pytest.approx(190.0)


def test_chapter_lines_follow_youtube_rules() -> None:
    spans = [{"id": f"b{i}", "start_ms": i * 8000.0, "end_ms": (i + 1) * 8000.0} for i in range(10)]
    chapters = [
        ["b0", "Intro"],
        ["b1", "Too soon"],
        ["b3", "The turn"],
        ["b6", "The answer"],
        ["b9", "Outro"],
    ]
    assert chapter_lines(chapters, spans, 80.0) == ["00:00 Intro", "00:24 The turn", "00:48 The answer"]
    assert chapter_lines(chapters[:2], spans, 80.0) == []


# --------------------------------------------------------------------------------------------- topic
def test_topic_comes_from_the_backlog_in_order(make_ctx: MakeCtx, project: Path, sf: Any) -> None:
    (project / "config" / "channels" / "iflab" / "backlog.md").write_text(
        "# comment\nFirst story | its angle\nSecond story\nThird story\n", encoding="utf-8"
    )
    a = pick_topic(make_ctx("r1", "iflab"))
    assert (
        a["chosen"]["title"] == "First story"
        and a["chosen"]["angle"] == "its angle"
        and a["next"] == "Second story"
    )
    with session_scope(sf) as s:
        row = s.get(RunRow, "r1")
        assert row is not None
        row.topic, row.status = "First story", "ready_for_review"
    assert pick_topic(make_ctx("r2", "iflab"))["chosen"]["title"] == "Second story"
    # a failed run does not use its topic up
    with session_scope(sf) as s:
        row = s.get(RunRow, "r2")
        assert row is not None
        row.topic, row.status = "Second story", "failed"
    assert pick_topic(make_ctx("r3", "iflab"))["chosen"]["title"] == "Second story"
    assert pick_topic(make_ctx("r4", "iflab", topic="My own idea"))["source"] == "cli"


def test_an_empty_backlog_says_what_to_do(make_ctx: MakeCtx, project: Path) -> None:
    (project / "config" / "channels" / "iflab" / "backlog.md").write_text("# nothing\n", encoding="utf-8")
    with pytest.raises(PipelineError, match="backlog.md"):
        pick_topic(make_ctx("r1", "iflab"))


# ---------------------------------------------------------------------------------------------- gate
class _SeqLLM:
    """Hands out a flat script first and a good one second; the critic always passes."""

    name = "fake"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(
        self,
        tier: str,
        step: str,
        system: str,
        prompt: str,
        schema: Any,
        *,
        check: Any = None,
        hints: Any = None,
    ) -> Any:
        if schema is EpisodeCritique:
            return EpisodeCritique(hook_score=8, passed=True)
        self.prompts.append(prompt)
        good = EpisodeScript.offline_example({"target_words": 140})
        if len(self.prompts) > 1:
            return good
        flat = good.model_copy(deep=True)
        flat.beats[0].say = "Money is a system of exchange that people have used for a long time."
        return flat


def test_the_gate_sends_fixes_back_to_the_writer(make_ctx: MakeCtx) -> None:
    ctx = make_ctx("r1", "iflab")
    llm = _SeqLLM()
    ctx.llm = llm  # type: ignore[assignment]
    ctx.paths.run_dir.mkdir(parents=True)
    script, gate = write_script(ctx, {"chosen": {"title": "T", "angle": ""}, "next": "N"}, 140)
    assert gate["passed"] and gate["attempts"] == 2
    assert "REWRITE IT TO FIX ALL OF THESE" in llm.prompts[1] and "YOUR LAST DRAFT" in llm.prompts[1]
    assert script.beats[0].say.startswith("What if money stopped")
    # finished steps are read back, not paid for again
    write_script(ctx, {"chosen": {"title": "T", "angle": ""}, "next": "N"}, 140)
    assert len(llm.prompts) == 2


# ----------------------------------------------------------------------------------------- whole run
class EpisodeRemotionStub:
    """Stands in for the Remotion CLI: bundle, chunked render and stills."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(
        self, ctx: RunContext, args: list[str], log_path: Path, *, render: bool = True, on_line: Any = None
    ) -> None:
        self.calls.append(args)
        if args[0] == "bundle":
            out = Path(next(a for a in args if a.startswith("--out-dir=")).split("=", 1)[1])
            out.mkdir(parents=True, exist_ok=True)
            (out / "index.html").write_text("stub")
            return
        out = Path(args[3])
        out.parent.mkdir(parents=True, exist_ok=True)
        if args[0] == "still":
            Image.new("RGB", (320, 180), (255, 178, 56)).save(out)
            return
        a, b = (int(x) for x in next(x for x in args if x.startswith("--frames=")).split("=")[1].split("-"))
        if on_line:  # what the Remotion CLI prints when it is not on a terminal
            n = b - a + 1
            for k in (0, n // 3, 2 * n // 3, n):
                on_line(f"Rendered {k}/{n}, time remaining: 10s\n")
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=black:s=320x180:r=30:d={(b - a + 1) / 30:.4f}",
             "-pix_fmt", "yuv420p", str(out)],
            check=True,
        )  # fmt: skip


@needs_ffmpeg
def test_offline_episode_end_to_end(
    make_ctx: MakeCtx,
    project: Path,
    sf: Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    stub = EpisodeRemotionStub()
    monkeypatch.setattr("pipeline.episode.produce.remotion", stub)
    monkeypatch.setattr("pipeline.episode.produce.CHUNK_FRAMES", 600)  # force more than one chunk
    monkeypatch.setattr("pipeline.episode.produce._BUNDLED", set())
    ctx = make_ctx("20260101-000000-iflab", "iflab", mode="episode", shorts=2)
    run_episode(ctx)

    # every line says how far along the run is, the numbers only go up, and it ends at 100%
    import re

    pcts = [
        int(m.group(1)) for m in re.finditer(r"^\[\d\d:\d\d:\d\d\]\s+(\d+)% ", capsys.readouterr().err, re.M)
    ]
    assert len(pcts) > 10 and pcts == sorted(pcts) and pcts[-1] == 100

    with session_scope(sf) as s:
        row = s.get(RunRow, ctx.run_id)
        assert row is not None and row.status == "ready_for_review"
        assert row.topic and "Kodak" in row.topic
    out = project / "out" / "iflab" / ctx.run_id
    for rel in ("youtube/video.mp4", "youtube/thumbnail.png", "youtube/description.txt", "youtube/captions.srt",
                "youtube/UPLOAD.md", "shorts/short1.mp4", "shorts/short1-cover.jpg", "shorts/short2.mp4",
                "shorts/POSTING.md", "REVIEW.md"):  # fmt: skip
        assert (out / rel).exists(), rel
    review = (out / "REVIEW.md").read_text()
    assert "OFFLINE REHEARSAL" in review and "| Claim |" in review
    posting = (out / "shorts" / "POSTING.md").read_text()
    assert "#shorts" in posting and posting.count("## short") == 2
    assert "Sun" in (out / "youtube" / "UPLOAD.md").read_text()

    # the long video was rendered in chunks and joined; picture and sound are the same length
    renders = [c for c in stub.calls if c[0] == "render" and c[2] == "Episode"]
    assert len(renders) >= 2
    timing = read_json(ctx.paths.run_dir / "audio" / "timing.json")
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out / "youtube" / "video.mp4")],
        capture_output=True, text=True, check=True,
    )  # fmt: skip
    assert abs(float(probe.stdout) - timing["total_sec"]) < 0.3
    # every Short fits the platform limit and has captions with numerals handled
    for k in (1, 2):
        props = read_json(ctx.paths.run_dir / "shorts" / f"s{k}" / "short.props.json")
        assert props["timing"]["total_sec"] <= 58 and props["caps"] and len(props["title"]) >= 2
        assert props["shots"][0]["id"] == f"h{k}"

    # resuming a finished run renders nothing and asks the model nothing
    before = len(stub.calls)
    run_episode(ctx)
    assert [c[0] for c in stub.calls[before:]] in ([], ["bundle"])


@needs_ffmpeg
def test_a_failed_render_is_recorded_and_resumes(
    make_ctx: MakeCtx, sf: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    stub = EpisodeRemotionStub()
    boom = {"left": 1}

    def flaky(ctx: RunContext, args: list[str], log_path: Path, *, render: bool = True, **kw: Any) -> None:
        if args[0] == "render" and boom["left"]:
            boom["left"] -= 1
            raise PipelineError("simulated renderer crash")
        stub(ctx, args, log_path, render=render, **kw)

    monkeypatch.setattr("pipeline.episode.produce.remotion", flaky)
    monkeypatch.setattr("pipeline.episode.produce._BUNDLED", set())
    ctx = make_ctx("20260101-000001-iflab", "iflab", mode="episode", shorts=1)
    with pytest.raises(PipelineError):
        run_episode(ctx)
    with session_scope(sf) as s:
        row = s.get(RunRow, ctx.run_id)
        assert row is not None and row.status == "failed" and "simulated" in (row.error or "")
    run_episode(ctx)
    with session_scope(sf) as s:
        row = s.get(RunRow, ctx.run_id)
        assert row is not None and row.status == "ready_for_review"


# ------------------------------------------------------------------------- story, hooks and labels
def _story(beats: list[dict[str, Any]], **kw: Any) -> EpisodeScript:
    end = {"say": "What would you have done? Tell me.", "view": "end", "label": "Next"}
    base = {
        "hero": "Kodak",
        "stakes": "s",
        "hooks": ["a", "b", "c"],
        "promise": "p",
        "payoff_beat": 2,
        "comment_prompt": "c",
    }
    pad = [{"say": "But nobody bought it.", "view": "object", "object": "wallet"}] * max(0, 5 - len(beats))
    return EpisodeScript.model_validate({**base, **kw, "beats": [*beats, *pad, end]})


_LAB = {"say": "It's 1975. An engineer at Kodak holds a camera with no film.", "view": "scene", "set": "lab",
        "people": [{"who": "leo", "pose": "hold"}], "chapter": "The camera", "where": "Rochester, 1975", "sign": "Kodak"}  # fmt: skip


def test_script_labels_never_reach_the_screen() -> None:
    bad = _story(
        [
            _LAB,
            {
                "say": "Here is the promise.",
                "view": "title",
                "big": "PROMISE",
                "label": "what you want to know",
            },
            {
                "say": "Act one.",
                "view": "title",
                "big": "ACT ONE",
                "label": "who owns it?",
                "chapter": "Act one",
            },
            {"say": "So they hid it.", "view": "title", "big": "FILM IS DEAD", "label": "the takeaway"},
        ]
    )
    text = " ".join(bad.problems(bad.words()))
    assert (
        "'PROMISE'" in text
        and "'ACT ONE'" in text
        and "chapter 'Act one'" in text
        and "'the takeaway'" in text
    )
    assert "FILM IS DEAD" not in text


def test_the_first_beat_must_be_a_real_moment() -> None:
    mystery = {
        "say": "Why did Kodak hide its own camera?",
        "view": "object",
        "object": "mystery",
        "chapter": "c",
    }
    empty = {
        "say": "Kodak hid its own camera.",
        "view": "scene",
        "set": "office",
        "people": [{}],
        "chapter": "c",
    }
    assert "beat 1 must drop the viewer into the story" in _story([mystery, _LAB]).problems(30)[0]
    assert "empty room" in _story([empty, _LAB]).problems(30)[0]
    ok = _story([_LAB, mystery])
    assert not [x for x in ok.problems(ok.words()) if "beat 1" in x]
    assert any("`hero`" in x for x in _story([_LAB, mystery], hero="").problems(30))
    assert any("`hooks`" in x for x in _story([_LAB, mystery], hooks=["one"]).problems(30))


def test_audit_catches_a_slideshow() -> None:
    stand = {"view": "scene", "set": "office", "people": [{"who": "you", "pose": "think"}]}
    beats = [_LAB] + [
        {**stand, "say": "The company did not change and it is clear that sales were not growing at all."}
        for _ in range(9)
    ]
    fixes = " ".join(audit(_story(beats))["fixes"])
    assert "one person standing still" in fixes
    assert "scenes in a row use the same place" in fixes
    assert "written for the page" in fixes
    assert "list of facts" in fixes
    good = audit(EpisodeScript.offline_example({"target_words": 1275}))
    assert good["fixes"] == [] and good["different_places"] >= 4


def test_a_named_company_counts_as_a_hook_subject() -> None:
    named = hook_score(
        "In 1975 an engineer at Kodak built a camera that needed no film, and was told to hide it."
    )
    vague = hook_score(
        "Companies sometimes fail because they do not adapt to changes in technology over time."
    )
    assert named["total"] >= vague["total"] + 15


def test_director_draws_company_scenes_and_keeps_text_in_bounds() -> None:
    s = _story(
        [
            _LAB,
            {"say": "Sales fell.", "view": "scene", "set": "boardroom", "people": [{"who": "maya", "pose": "point"}],
             "scene_prop": "chart_down", "prop_text": "Film sales", "sign": "Kodak"},
            {"say": "It filed for bankruptcy.", "view": "stat", "big": "2012", "label": "bankruptcy", "source": "Kodak, 2012"},
            {"say": "Eighty percent.", "view": "stat", "big": "80%", "label": "share", "source": "x, 2000"},
            {"say": "The screen says paid.", "view": "object", "object": "phone_ok", "prop_text": "975 images"},
            {"say": "One person thinks.", "view": "scene", "set": "office", "people": [{"who": "leo", "pose": "think"}]},
        ]
    )  # fmt: skip
    shots, _ = direct(s)
    assert shots[0]["where"] == "Rochester, 1975" and shots[0]["setopt"]["sign"] == "Kodak"
    board = shots[1]
    assert board["setopt"] == {"sign": "Film sales", "down": True} and board["props"] == []
    easel = direct(_story([{**_LAB, "scene_prop": "chart_down", "prop_text": "Film sales"}]))[0][0]["props"][
        0
    ]
    assert easel["t"] == "chart_board" and easel["down"] and easel["label"] == "Film sales"
    assert "count" not in shots[2]["ov"] and shots[3]["ov"]["count"] is True  # a year is never counted up to
    assert shots[4]["props"][0]["amount"] == "20"  # words on a payment screen fall back to a plain amount
    assert any("digits only" in x for x in s.problems(s.words()))
    assert shots[5]["props"][0]["t"] == "desk"  # a lone figure in an office gets a desk to work at


def test_stock_openings_never_pass_as_hooks() -> None:
    story = hook_score(
        "Nineteen seventy-five. A young engineer at Kodak holds a camera with no film in it, and his bosses tell him to keep quiet."
    )
    assert story["total"] >= 75
    for stock in (
        "Have you ever wondered why big companies fail?",
        "Today we look at the story of Kodak and digital disruption.",
        "What is disruption? Let's find out.",
        "In this video you'll learn why Kodak failed.",
    ):
        assert hook_score(stock)["total"] <= 35, stock
    assert hook_score("Kodak was a big company that made film for cameras for many years.")["total"] < 58


def test_end_card_drops_a_repeated_next() -> None:
    s = _story([_LAB])
    s.beats[-1].label = "Next: How IKEA makes money"
    shots, _ = direct(s)
    assert shots[-1]["ov"]["next"] == "How IKEA makes money"


# ------------------------------------------------------------------- tools, voices and progress
def test_a_missing_ffmpeg_stops_the_run_before_anything_is_paid_for(
    make_ctx: MakeCtx, sf: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = __import__("shutil").which
    monkeypatch.setattr("pipeline.episode.run.shutil.which", lambda t: None if t == "ffmpeg" else real(t))
    ctx = make_ctx("20260101-000002-iflab", "iflab", mode="episode")
    with pytest.raises(PipelineError, match="winget install"):
        run_episode(ctx)
    assert not ctx.paths.script("long").exists()
    with session_scope(sf) as s:
        row = s.get(RunRow, ctx.run_id)
        assert row is not None and row.status == "failed" and "ffmpeg was not found" in (row.error or "")


def test_ffmpeg_helper_names_the_missing_program() -> None:
    from pipeline.adapters.audio import FFmpegError, run

    with pytest.raises(FFmpegError, match="no-such-ffmpeg was not found"):
        run(["no-such-ffmpeg", "-version"])


def test_the_narrator_walks_the_fallback_list(make_ctx: MakeCtx, tmp_path: Path) -> None:
    ctx = make_ctx("20260101-000003-iflab", "iflab", mode="episode")
    real = ctx.tts
    asked: list[str] = []

    class Picky:
        name = "fake"

        def synth(self, text: str, voice: str, rate: float, cache_dir: Path) -> SynthResult:
            asked.append(voice)
            if voice != "en-IN-NeerjaNeural":
                raise RuntimeError(f"Unsupported voice {voice}")
            return real.synth(text, voice, rate, cache_dir)

    ctx.tts = Picky()  # type: ignore[assignment]
    ctx.style.narrator.voice = "en-IN-Aarti:DragonHDOmniLatestNeural"
    ctx.style.narrator.fallback_voice = ["en-IN-AartiNeural", "en-IN-NeerjaNeural"]
    n = produce.Narrator(ctx)
    n.say("Kodak built it first.")
    assert asked == ["en-IN-Aarti:DragonHDOmniLatestNeural", "en-IN-AartiNeural", "en-IN-NeerjaNeural"]
    assert n.voice == "en-IN-NeerjaNeural"
    n.say("Then it waited.")  # the chosen voice sticks for the rest of the video
    assert asked[-1] == "en-IN-NeerjaNeural" and len(asked) == 4


def test_expressiveness_goes_only_to_voices_that_take_it() -> None:
    from pipeline.adapters.tts import AzureTTS

    tts = AzureTTS(key="k", region="eastus")
    assert tts.voice_params("en-us-Andrew:DragonHDLatestNeural") == ""  # nothing set in the style file
    tts.temperature = 0.9
    assert tts.voice_params("en-us-Andrew:DragonHDLatestNeural") == "temperature=0.9"
    assert tts.voice_params("en-IN-Aarti:DragonHDOmniLatestNeural") == "temperature=0.9;top_p=0.9"
    assert tts.voice_params("en-IN-NeerjaNeural") == ""
    assert tts.cache_extra("en-IN-NeerjaNeural") == "" and tts.cache_extra("x:DragonHDLatestNeural")


def test_progress_never_goes_backwards(make_ctx: MakeCtx, capsys: pytest.CaptureFixture[str]) -> None:
    ctx = make_ctx("20260101-000004-iflab", "iflab", mode="episode")
    ctx.log("before")
    ctx.stage(25, 68)
    ctx.advance(0.5)
    ctx.log("half")
    ctx.advance(0.2)  # a resumed step reporting less must not move the number back
    ctx.stage(10, 20)
    ctx.log("later")
    err = capsys.readouterr().err
    assert "] before" in err and "]  46% half" in err and "]  46% later" in err
