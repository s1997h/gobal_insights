"""The painted look: places, talking characters, cast voices, story objects."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.adapters.tts import FakeTTS
from pipeline.episode import painted, produce
from pipeline.episode.director import direct, direct_hook
from pipeline.episode.schemas import Beat, EpisodeScript

from .conftest import MakeCtx

ROOT = Path(__file__).resolve().parents[1]


def _script() -> EpisodeScript:
    return EpisodeScript.offline_example({"target_words": 400})


def test_every_painted_shot_stands_in_a_painted_place() -> None:
    shots, _ = direct(_script(), look="painted")
    for s in shots:
        assert s["set"].startswith("img:"), s
        assert s["set"][4:] in painted.BACKGROUNDS
        assert (ROOT / "assets" / "backgrounds" / f"{s['set'][4:]}.jpg").exists()
        assert s["chibi"] is True
        for a in s.get("actors", []):
            assert 0 <= a["x"] <= 1920


def test_a_speaking_character_gets_the_camera_and_their_voice() -> None:
    shots, _ = direct(_script(), look="painted")
    spoken = [s for s in shots if "spk" in s]
    assert spoken, "the example script has dialogue"
    for s in spoken:
        who = s["actors"][s["spk"]]["who"]
        assert who in painted.CAST.values()
        x = s["actors"][s["spk"]]["x"]
        cam = s.get("cam2") or s["cam"]
        assert cam[2] == x and cam[0] >= 1.3  # a close-up on the speaker's face
    roles = {s["voice"] for s in shots}
    assert {"narrator", "man", "woman"} <= roles


def test_the_flat_look_is_unchanged() -> None:
    shots, _ = direct(_script())
    assert not any(s["set"].startswith("img:") for s in shots)
    assert not any("chibi" in s for s in shots)


def test_dialogue_rules_name_the_problem() -> None:
    b = Beat(say="Could we build it?", view="scene", set="lab", speaker="boss", people=[{"who": "you"}])
    assert any("put them in `people`" in p for p in b.problems(3))
    card = Beat(say="Ten years.", view="stat", big="10", label="years", source="x", speaker="boss")
    assert any("must be a `scene`" in p for p in card.problems(4))
    kid = Beat(say="Hi.", view="scene", set="living", speaker="kid_a", people=[{"who": "kid_a"}])
    assert any("kids never speak" in p for p in kid.problems(5))
    script = _script()
    for b in script.beats:
        b.speaker = "narrator"
    assert any("dialogue beats" in p for p in script.problems(400, painted=True))


def test_story_objects_draw_over_the_last_place() -> None:
    beats = [
        Beat(say="Rochester.", view="scene", set="boardroom", people=[{"who": "exec_a"}]),
        Beat(say="A napkin.", view="object", object="napkin", items=["Camera", "Film", "Prints"], prop_text="Kodak", broken=True),
        Beat(say="Into the drawer.", view="object", object="drawer", items=["prototype", "report"]),
        Beat(say="Kodak has filed.", view="object", object="news", speaker="anchor", prop_text="Kodak files", label="KODAK"),
        Beat(say="The photo.", view="object", object="old_tv"),
        Beat(say="Ten years.", view="stat", big="10", label="years", source="Forbes, 2012"),
    ]  # fmt: skip
    script = EpisodeScript.model_construct(
        promise="", payoff_beat=1, comment_prompt="", beats=beats, claims=[]
    )
    shots, _ = direct(script, look="painted")
    assert {s["set"] for s in shots} == {"img:conf"}  # boardroom is drawn as the conference room
    napkin = shots[1]["props"][0]
    assert (
        napkin["t"] == "napkin"
        and len(napkin["labels"]) == 4
        and napkin["end"] == "KODAK"
        and "broken" in napkin
    )
    drawer = shots[2]["props"][0]
    assert (
        [i["k"] for i in drawer["items"]] == ["cam", "memo"]
        and drawer["items"][1]["at"] > 0
        and "shut" in drawer
    )
    assert shots[3]["spk"] == 0 and shots[3]["actors"][0]["who"] == "anchor" and shots[3]["voice"] == "woman"
    assert shots[4]["props"][0]["static"] is True
    assert shots[5]["ov"]["t"] == "stat"


def test_a_short_hook_uses_the_painted_look() -> None:
    hook = Beat(say="Kodak hid it.", view="scene", set="lab", people=[{"who": "you", "pose": "point"}])
    s = direct_hook(hook, "h1", "painted")
    assert s["set"] == "img:lab" and s["chibi"] and s["id"] == "h1"


def test_cast_roles_pick_their_own_voice(make_ctx: MakeCtx) -> None:
    ctx = make_ctx()
    ctx.style.narrator.cast = {"man": "voice-man", "woman": "voice-woman"}
    seen: list[str] = []

    class Spy(FakeTTS):
        def synth(self, text: str, voice: str, rate: float, cache_dir: Path) -> Any:
            seen.append(voice)
            return super().synth(text, voice, rate, cache_dir)

    ctx.tts = Spy()
    n = produce.Narrator(ctx)
    n.say("One.", "man")
    n.say("Two.", "woman")
    n.say("Three.")
    n.say("Four.", "nobody")
    assert seen == ["voice-man", "voice-woman", n.voice, n.voice]


def test_mouths_move_only_while_the_line_plays() -> None:
    shots: list[dict[str, Any]] = [{"id": "a", "n": "x", "spk": 1}, {"id": "b", "n": "y"}]
    timing = {
        "scenes": [{"id": "a", "start_ms": 0, "end_ms": 3000}, {"id": "b", "start_ms": 3000, "end_ms": 5000}]
    }
    words = [
        {"word": "Could", "start_ms": 200, "end_ms": 500},
        {"word": "we?", "start_ms": 600, "end_ms": 1400},
        {"word": "No.", "start_ms": 3100, "end_ms": 3500},
    ]
    produce.mouths(shots, timing, words)
    assert shots[0]["speak"] == [{"a": 1, "s": 0.2, "e": 1.45}]
    assert "speak" not in shots[1]
    caps = produce.captions(words)
    assert caps[0] == {"w": "Could", "s": 0.2, "e": 0.5}
