"""What the model writes for a cartoon episode, and the checks that keep it drawable.

The model never places anything on screen. It picks a `view` and fills a few fields; the director
(director.py) turns each beat into a concrete shot. Every field is flat and optional so the same
schema works across model providers; `problems()` says what is missing in plain words, which the
model adapter feeds back for a retry.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field

SetName = Literal[
    "studio", "bazaar", "kirana", "datacentre", "pub", "bank_front",
    "bedroom", "living", "street", "cafe", "park", "office", "kitchen",
]  # fmt: skip
Who = Literal["you", "maya", "leo", "zoe", "sam", "ana"]
Pose = Literal[
    "stand", "walk", "wave", "scared", "point", "phone", "hold", "read", "think", "cheer", "shrug", "slump"
]
Mood = Literal["neutral", "happy", "worried", "shocked", "bored", "joy", "sad"]
View = Literal["scene", "object", "stat", "title", "list", "checklist", "duo", "bars", "end"]
SceneProp = Literal[
    "none", "chai_stall", "atm", "petrol_pump", "auto", "veg_cart", "shutter", "queue", "tv", "sign", "desk"
]
Obj = Literal[
    "phone_fail", "phone_ok", "wallet", "banknote", "ledger", "mystery",
    "balance", "balance_locked", "cheque", "pins", "calendar",
]  # fmt: skip

ThumbObj = Literal[
    "phone_fail",
    "phone_ok",
    "wallet",
    "banknote",
    "ledger",
    "mystery",
    "balance_locked",
    "cheque",
    "calendar",
]

VIEW_GUIDE = """\
- scene: people in a place. Fields: set, people (1-3), scene_prop (optional), prop_text (words on the prop).
- object: one big object on the plain studio background. Fields: object, prop_text, items; people (0-1).
- stat: one big number on a card. Fields: big (max 6 characters, e.g. "86%", "5.2M"), label, sub (optional), source (required).
- title: two or three punchy words. Fields: big (max 12 characters), label (a short second line).
- list: 2-4 short items popping in. Fields: items (each max 20 characters), ok (true = ticks, false = crosses).
- checklist: 2-4 lines being ticked. Fields: items (each max 30 characters).
- duo: two things compared. Fields: label (the question), left {big, label}, right {big, label}; big max 6 characters.
- bars: a bar chart. Fields: label (chart title), bars (2-4, each {name, value 0-100, text}), source (required).
- end: the closing card. Fields: label (the next video's title)."""


class Person(BaseModel):
    who: Who = "you"
    pose: Pose = "stand"
    mood: Mood = "neutral"


class Pair(BaseModel):
    big: str
    label: str


class Bar(BaseModel):
    name: str
    value: float = Field(ge=0, le=100)
    text: str


class Beat(BaseModel):
    say: str = Field(min_length=1, description="The narration for this shot. One to three short sentences.")
    view: View
    chapter: str | None = Field(
        default=None, description="Set on the first beat of a new chapter: its title."
    )
    clock: str | None = Field(
        default=None,
        description='For hour-by-hour stories, the time on the clock, e.g. "9:30 AM". Carries forward.',
    )
    past: bool = Field(
        default=False, description="True for a flashback to a real historical event (drawn in sepia)."
    )
    set: SetName | None = None
    people: list[Person] = Field(default_factory=list, max_length=3)
    scene_prop: SceneProp = "none"
    object: Obj | None = None
    prop_text: str | None = None
    big: str | None = None
    label: str | None = None
    sub: str | None = None
    source: str | None = Field(
        default=None, description="Who published the number, and the year. Never a URL."
    )
    items: list[str] = Field(default_factory=list, max_length=7)
    ok: bool = False
    left: Pair | None = None
    right: Pair | None = None
    bars: list[Bar] = Field(default_factory=list, max_length=4)

    def problems(self, n: int) -> list[str]:
        p: list[str] = []
        w = len(self.say.split())
        if w > 36:
            p.append(f"beat {n}: narration is {w} words; split it into two beats (max 36)")
        v = self.view
        if v == "scene":
            if not self.set:
                p.append(f"beat {n}: a scene needs `set`")
            if not self.people and self.scene_prop in ("none", "sign"):
                p.append(f"beat {n}: a scene needs 1-3 `people`")
        elif v == "object" and not self.object:
            p.append(f"beat {n}: an object beat needs `object`")
        elif v == "stat":
            if not self.big or not self.label:
                p.append(f"beat {n}: a stat needs `big` and `label`")
            elif len(self.big) > 6:
                p.append(f"beat {n}: stat `big` is {self.big!r}; keep it to 6 characters (e.g. 86%, 5.2M)")
            if not self.source:
                p.append(f"beat {n}: a stat needs `source` (who published it, and the year)")
        elif v == "title":
            if not self.big:
                p.append(f"beat {n}: a title needs `big`")
            elif len(self.big) > 12:
                p.append(f"beat {n}: title `big` is {len(self.big)} characters; max 12")
        elif v in ("list", "checklist"):
            lim = 20 if v == "list" else 30
            if not 2 <= len(self.items) <= 4:
                p.append(f"beat {n}: a {v} needs 2-4 `items`")
            p += [
                f"beat {n}: item {it!r} is too long (max {lim} characters)"
                for it in self.items
                if len(it) > lim
            ]
        elif v == "duo":
            if not self.left or not self.right:
                p.append(f"beat {n}: a duo needs `left` and `right`")
            else:
                p += [
                    f"beat {n}: duo `big` {x.big!r} is too long (max 6 characters)"
                    for x in (self.left, self.right)
                    if len(x.big) > 6
                ]
        elif v == "bars":
            if not 2 <= len(self.bars) <= 4:
                p.append(f"beat {n}: bars needs 2-4 `bars`")
            if not self.source:
                p.append(f"beat {n}: bars needs `source`")
        elif v == "end" and not self.label:
            p.append(f"beat {n}: the end card needs `label` (the next video's title)")
        if self.clock and not re.fullmatch(r"(1[0-2]|[1-9]):[0-5]\d (AM|PM)", self.clock):
            p.append(f'beat {n}: clock {self.clock!r} must look like "9:30 AM"')
        return p


class Claim(BaseModel):
    text: str = Field(description="One factual claim made in the narration, with its number.")
    source: str = Field(description="Who published it and when. Say 'unsure' if you are not certain.")


class EpisodeScript(BaseModel):
    promise: str = Field(description="The open question planted in the first 20 seconds, in one sentence.")
    payoff_beat: int = Field(ge=1, description="1-based number of the beat that answers the promise.")
    comment_prompt: str = Field(description="The one question viewers are asked to answer in the comments.")
    beats: list[Beat] = Field(min_length=6)
    claims: list[Claim] = Field(default_factory=list)

    def words(self) -> int:
        return sum(len(b.say.split()) for b in self.beats)

    def problems(self, target_words: int) -> list[str]:
        p: list[str] = []
        for i, b in enumerate(self.beats, 1):
            p += b.problems(i)
        w = self.words()
        if not 0.7 * target_words <= w <= 1.3 * target_words:
            p.append(f"the script is {w} words; write about {target_words}")
        if not self.beats[0].chapter:
            p.append("beat 1 must set `chapter` (the first chapter's title)")
        if self.beats[-1].view != "end":
            p.append("the last beat must have view `end`")
        if not 1 <= self.payoff_beat <= len(self.beats):
            p.append("payoff_beat must be a beat number")
        return p[:12]

    @classmethod
    def offline_example(cls, hints: dict[str, Any]) -> EpisodeScript:
        """A deterministic stand-in script for --offline runs and tests. Not real writing."""
        topic = str(hints.get("topic", "What if money stopped working for one day")).rstrip("?")
        target = int(hints.get("target_words", 160))
        base: list[dict[str, Any]] = [
            {"say": f"{topic}? Payment failed. And you are not the only one.", "view": "object", "object": "phone_fail",
             "people": [{"who": "you", "pose": "scared", "mood": "shocked"}], "chapter": "The day it stops", "prop_text": "20"},
            {"say": "No apps. No cards. No machines.", "view": "list", "items": ["No apps", "No cards", "No machines"]},
            {"say": "By tonight, the most valuable thing on your street will be a notebook.", "view": "object", "object": "mystery"},
            {"say": "Eight o'clock. You are at the tea stall, and your phone will not pay.", "view": "scene", "set": "bazaar",
             "people": [{"who": "you", "pose": "phone", "mood": "worried"}], "scene_prop": "chai_stall", "clock": "8:00 AM",
             "chapter": "8 AM: the first failure"},
            {"say": "Offline placeholder fact: about half of payments went through that day.", "view": "stat", "big": "50%",
             "label": "of payments went through", "source": "Offline placeholder, 2026"},
            {"say": "So you run to the cash machine. So did everyone else.", "view": "scene", "set": "bazaar",
             "people": [{"who": "sam", "pose": "stand", "mood": "worried"}], "scene_prop": "atm", "prop_text": "OUT OF SERVICE"},
            {"say": "Who still gets served? The regular, or the stranger?", "view": "duo", "label": "Who gets served?",
             "left": {"big": "10 yrs", "label": "The regular"}, "right": {"big": "Day 1", "label": "The stranger"}},
            {"say": "The shopkeeper pulls out a notebook, and writes down your name.", "view": "scene", "set": "kirana",
             "people": [{"who": "you", "pose": "stand", "mood": "happy"}, {"who": "sam", "pose": "read", "mood": "happy"}],
             "clock": "2:00 PM", "chapter": "2 PM: the notebook"},
            {"say": "That notebook is the answer. It is trust, written down.", "view": "object", "object": "ledger",
             "items": ["Mrs Rao|64", "You|240", "Flat 302|118"]},
            {"say": "Offline placeholder chart: payments lost in one afternoon.", "view": "bars", "label": "Payments lost",
             "bars": [{"name": "Cards", "value": 55, "text": "55%"}, {"name": "Shops", "value": 80, "text": "80%"}],
             "source": "Offline placeholder, 2026"},
            {"say": "Three things to do tonight. Keep a little cash. Know your shopkeeper. Count your wallet.", "view": "checklist",
             "items": ["Keep a little cash", "Know your shopkeeper", "Count your wallet"], "chapter": "What to do"},
            {"say": "It is trust.", "view": "title", "big": "TRUST", "label": "who owes what"},
        ]  # fmt: skip
        beats: list[dict[str, Any]] = []
        i = 0
        while sum(len(b["say"].split()) for b in beats) < target * 0.9:
            b = dict(base[i % len(base)])
            if i >= len(base) and "chapter" in b:
                b["chapter"] = f"{b['chapter']} ({i // len(base) + 1})"
            beats.append(b)
            i += 1
        beats.append(
            {
                "say": "How many days would you last? Tell me your number.",
                "view": "end",
                "label": "What if everyone got free money?",
            }
        )
        return cls.model_validate(
            {
                "promise": "Why is a notebook the most valuable thing on your street by tonight?",
                "payoff_beat": 9 if len(beats) <= 16 else round(len(beats) * 0.6),
                "comment_prompt": "How many days would you last on the cash in your wallet?",
                "beats": beats,
                "claims": [
                    {
                        "text": "Offline placeholder: no real facts were checked.",
                        "source": "none (fake provider)",
                    }
                ],
            }
        )


class EpisodeCritique(BaseModel):
    hook_score: int = Field(ge=1, le=10, description="How hard the first 15 seconds pull, 1-10.")
    passed: bool
    fixes: list[str] = Field(
        default_factory=list, description="Concrete rewrites, most important first. Max 6."
    )
    risky_claims: list[str] = Field(
        default_factory=list, description="Claims a human should check before posting."
    )

    @classmethod
    def offline_example(cls, hints: dict[str, Any]) -> EpisodeCritique:
        return cls(hook_score=8, passed=True, risky_claims=["FAKE CRITIC: nothing was checked."])


class ShortPick(BaseModel):
    first_beat: int = Field(ge=1)
    last_beat: int = Field(ge=1)
    hook: Beat = Field(description="A NEW opening beat written for someone who has not seen the long video.")
    title_lines: list[str] = Field(
        min_length=2, max_length=3, description="On-screen title, each line max 20 characters."
    )
    highlight: list[str] = Field(
        default_factory=list, description="One or two words from the title to colour."
    )
    youtube_title: str
    instagram_caption: str
    hashtags: list[str] = Field(default_factory=list, max_length=5)


class ShortsPlan(BaseModel):
    shorts: list[ShortPick] = Field(min_length=1)

    @classmethod
    def offline_example(cls, hints: dict[str, Any]) -> ShortsPlan:
        n, beats = int(hints.get("count", 4)), int(hints.get("beats", 12))
        span = max(2, min(4, (beats - 1) // max(1, n)))
        picks = []
        for i in range(n):
            a = 1 + i * span
            if a + span - 1 > beats - 1:
                break
            picks.append(
                {
                    "first_beat": a,
                    "last_beat": a + span - 1,
                    "hook": {
                        "say": f"Offline hook {i + 1}: what happens next?",
                        "view": "object",
                        "object": "phone_fail",
                    },
                    "title_lines": ["When money stops", "who gets served?"],
                    "highlight": ["money"],
                    "youtube_title": f"Offline short {i + 1}",
                    "instagram_caption": "Offline placeholder caption.",
                    "hashtags": ["#whatif", "#money"],
                }
            )
        return cls.model_validate({"shorts": picks})


class EpisodePackage(BaseModel):
    titles: list[str] = Field(
        min_length=3, max_length=3, description="Three title options, each max 60 characters."
    )
    thumb_top: str = Field(description="First thumbnail word (white). Never repeats a title word.")
    thumb_bottom: str = Field(description="Second thumbnail word or two (red). Three words in total at most.")
    thumb_object: ThumbObj = "phone_fail"
    thumb_mood: Literal["shocked", "joy", "worried"] = "shocked"
    description: str = Field(
        description="Two short paragraphs. The first 150 characters must work as the search snippet."
    )
    tags: list[str] = Field(min_length=6, max_length=15)
    hashtags: list[str] = Field(min_length=2, max_length=3)
    pinned_comment: str

    @classmethod
    def offline_example(cls, hints: dict[str, Any]) -> EpisodePackage:
        topic = str(hints.get("topic", "What if money stopped working for one day")).rstrip("?")
        return cls(
            titles=[f"{topic}?"[:60], f"{topic} (hour by hour)"[:60], f"The day {topic.lower()}"[:60]],
            thumb_top="OFFLINE",
            thumb_bottom="TEST",
            description=(
                f"{topic}? This is the offline placeholder description, written by the fake provider so that a "
                "rehearsal run can finish without any API keys.\n\nNothing here was researched. Do not upload it."
            ),
            tags=["what if", "money", "explained", "economics", "animated", "the if lab"],
            hashtags=["#WhatIf", "#Money"],
            pinned_comment="How many days would you last?",
        )
