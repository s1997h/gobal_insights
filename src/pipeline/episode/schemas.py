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
    "lab", "factory", "boardroom", "store", "garage", "stage",
    "conf", "exec", "shop", "startup",
]  # fmt: skip
BIZ_SETS = {"lab", "factory", "boardroom", "store", "garage", "stage"}
Who = Literal[
    "you", "maya", "leo", "zoe", "sam", "ana",
    # the painted look's cast (see PAINTED_GUIDE)
    "you_old", "boss", "exec_a", "exec_b", "exec_c", "woman", "anchor", "expert", "rival",
    "young_a", "young_b", "kid_a", "kid_b",
]  # fmt: skip
Pose = Literal[
    "stand", "walk", "wave", "scared", "point", "phone", "hold", "read", "think", "cheer", "shrug", "slump",
    "sit", "stretch", "reach",
]  # fmt: skip
Mood = Literal[
    "neutral", "happy", "worried", "shocked", "bored", "joy", "sad", "smug", "deadpan", "grin", "angry"
]  # fmt: skip
View = Literal["scene", "object", "stat", "title", "list", "checklist", "duo", "bars", "end"]
SceneProp = Literal[
    "none", "chai_stall", "atm", "petrol_pump", "auto", "veg_cart", "shutter", "queue", "tv", "sign", "desk",
    "product", "chart_up", "chart_down",
]  # fmt: skip
Obj = Literal[
    "phone_fail", "phone_ok", "wallet", "banknote", "ledger", "mystery",
    "balance", "balance_locked", "cheque", "pins", "calendar",
    # story objects (painted look)
    "napkin", "drawer", "memo", "old_tv", "prototype", "news", "gadget", "website",
]  # fmt: skip
STORY_OBJS = {"napkin", "drawer", "memo", "old_tv", "prototype", "news", "gadget", "website"}

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
- scene: people in a place. Fields: set, people (1-3), scene_prop (optional), prop_text (words on the prop), sign (a name on the wall), where (place and year tag).
- object: one big object on the plain studio background. Fields: object, prop_text, items; people (0-1).
- stat: one big number on a card. Fields: big (max 6 characters, e.g. "86%", "5.2M"), label, sub (optional), source (required).
- title: two or three punchy words FROM THE STORY ("FILM IS DEAD"), never a label for a part of the script. Fields: big (max 12 characters), label (a short second line).
- list: 2-4 short items popping in. Fields: items (each max 20 characters), ok (true = ticks, false = crosses).
- checklist: 2-4 lines being ticked. Fields: items (each max 30 characters).
- duo: two things compared. Fields: label (the question), left {big, label}, right {big, label}; big max 6 characters.
- bars: a bar chart. Fields: label (chart title), bars (2-4, each {name, value 0-100, text}), source (required).
- end: the closing card. Fields: label (the next video's title)."""

PAINTED_GUIDE = """\
The video is drawn as painted backgrounds with big-head cartoon characters whose mouths move when they talk.

Who speaks each beat: `speaker`. "narrator" (the default) tells the story. Anyone else is a character saying
their line out loud: they must be in that beat's `people` (or be the anchor of a `news` object). The narrator's
voice also plays "you", so the viewer hears themselves talk. Dialogue beats are short: one or two sentences,
max 25 words, in quotes-free spoken English ("Could we build a camera with no film?").

Cast (`people[].who`), each with one voice:
- you: the viewer as a young adult (narrator's voice). you_old: the viewer, decades later (narrator's voice).
- boss: a manager with a mustache and tie. exec_a, exec_b, exec_c: senior executives in suits. expert: an analyst
  with glasses. (all: an older man's voice)
- woman: a colleague in a lab coat. anchor: a TV news anchor. rival: a woman in a green suit who leads a rival.
  young_a, young_b: young founders or customers. kid_a, kid_b: children. (all: a woman's voice; kids never speak)
Never use a real person's name for a cast member's lines; real people appear only in the narration.

Places (`set`), each a painted room: lab (workshop/research lab), living (living room at night, a sofa and TV),
conf (wood-panelled conference room), exec (an executive's office with a big desk), shop (a camera/electronics
shop counter), factory (a production floor), office (an open office with computers), startup (a loft with a
photo wall), street (a city street with shops). Pick the closest; the same place can appear many times.

Story objects (`view: object`), drawn big over the last place:
- napkin: a business model sketched on a napkin, as a chain of 4 steps. items: the steps ("Cheap camera",
  "Film", "Chemicals", "Prints"); prop_text: who gets the money ("KODAK"). broken: true crosses it out.
- drawer: the running gag of what gets hidden. items: what is inside, from prototype, report, idea (the last one
  drops in during this beat); prop_text: the label on the drawer (default "LATER"); ok: true leaves it open.
- memo: an internal report. prop_text: its title; sub: small print; items: up to 2 lines "BAD NEWS|Digital
  could replace film"; label: a stamp ("CONFIDENTIAL").
- old_tv: an old TV painting a photo in line by line. ok: false shows static where the face should be.
- prototype: the invention on a workbench, glowing. prop_text: optional label.
- news: a TV news broadcast. prop_text: the headline; items: ticker lines; label: the company in the graphic
  box; sub: a stamp on it ("BANKRUPT"). speaker: anchor reads the news.
- gadget: a product (a camera, a phone). prop_text: the brand; sub: a price tag ("$20,000", "-$60").
- website: an app or website on a phone. prop_text: its name; sub: a badge ("75 MILLION USERS")."""


# Words that name a part of the script instead of something in the story. They must never reach the screen.
_SCAFFOLD = re.compile(
    r"^(the )?(hook|promise|pay-?off|answer|take-?aways?|check|checklist|intro(duction)?|outro|conclusion|summary|recap|"
    r"setup|context|background|twist|reveal|lesson|question|cold open|the end)$"
    r"|^(act|part|chapter|question|step|lesson|section)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|i{1,3}|iv|v)\b",
    re.I,
)


def scaffold(text: str | None) -> bool:
    """True when on-screen text is script scaffolding ("ACT ONE", "PAYOFF") rather than story."""
    return bool(text) and bool(_SCAFFOLD.search((text or "").strip().strip(":.!?")))


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
    speaker: Who | Literal["narrator"] = Field(
        default="narrator",
        description="Who says `say`: the narrator, or a character on screen saying their line out loud.",
    )
    broken: bool = Field(default=False, description="napkin only: cross out the business model.")
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
    sign: str | None = Field(
        default=None,
        description="A company or product name written on the wall, banner or screen of a lab, factory, boardroom, store, garage or stage. Max 14 characters.",
    )
    where: str | None = Field(
        default=None,
        description='Place and year shown as a tag when the story moves, e.g. "Rochester, 1975". Max 28 characters.',
    )
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
        elif v == "object":
            if not self.object:
                p.append(f"beat {n}: an object beat needs `object`")
            elif self.object in ("phone_fail", "phone_ok", "balance", "balance_locked") and self.prop_text:
                if not re.fullmatch(r"[\d,. ]{1,10}", self.prop_text.strip()):
                    p.append(
                        f'beat {n}: `prop_text` on a {self.object} is the amount on its screen, digits only (e.g. "20"); '
                        f"got {self.prop_text!r}"
                    )
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
            for x in (self.big, self.label):
                if scaffold(x):
                    p.append(
                        f"beat {n}: {x!r} names a part of the script. Put words from the story on screen instead "
                        "(a name, a number, what just happened), or use a scene"
                    )
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
        if scaffold(self.chapter):
            p.append(
                f"beat {n}: chapter {self.chapter!r} is a script label. Name what happens in it "
                '("The camera nobody wanted", "1975: the first warning")'
            )
        if self.where and len(self.where) > 28:
            p.append(f'beat {n}: `where` is {len(self.where)} characters; max 28 (e.g. "Rochester, 1975")')
        if self.sign and len(self.sign) > 14:
            p.append(f"beat {n}: `sign` is {len(self.sign)} characters; max 14")
        if self.clock and not re.fullmatch(r"(1[0-2]|[1-9]):[0-5]\d (AM|PM)", self.clock):
            p.append(f'beat {n}: clock {self.clock!r} must look like "9:30 AM"')
        if self.speaker != "narrator":
            if self.speaker in ("kid_a", "kid_b"):
                p.append(f"beat {n}: kids never speak; give the line to the narrator or an adult")
            elif v == "object" and self.object == "news":
                if self.speaker != "anchor":
                    p.append(f"beat {n}: only the anchor speaks over a `news` object")
            elif v != "scene":
                p.append(
                    f"beat {n}: {self.speaker} speaks, so the beat must be a `scene` with them in `people`"
                )
            elif self.speaker not in {x.who for x in self.people}:
                p.append(f"beat {n}: {self.speaker} speaks, so put them in `people`")
            if w > 25:
                p.append(f"beat {n}: a spoken line is {w} words; keep dialogue to 25 words or split it")
        if v == "object" and self.object in ("napkin", "drawer", "memo") and len(self.items) > 4:
            p.append(f"beat {n}: a {self.object} takes at most 4 items")
        return p


class Claim(BaseModel):
    text: str = Field(description="One factual claim made in the narration, with its number.")
    source: str = Field(description="Who published it and when. Say 'unsure' if you are not certain.")


class EpisodeScript(BaseModel):
    hero: str = Field(
        default="",
        description='Who the story follows: a real named person, a company, or "you" for a what-if. One name.',
    )
    stakes: str = Field(default="", description="What the hero stands to lose or win, in one sentence.")
    hooks: list[str] = Field(
        default_factory=list,
        max_length=6,
        description="Five different candidate first lines, each a different angle. Beat 1 speaks the strongest.",
    )
    promise: str = Field(description="The open question planted in the first 20 seconds, in one sentence.")
    payoff_beat: int = Field(ge=1, description="1-based number of the beat that answers the promise.")
    comment_prompt: str = Field(description="The one question viewers are asked to answer in the comments.")
    beats: list[Beat] = Field(min_length=6)
    claims: list[Claim] = Field(default_factory=list)

    def words(self) -> int:
        return sum(len(b.say.split()) for b in self.beats)

    def problems(self, target_words: int, painted: bool = False) -> list[str]:
        p: list[str] = []
        for i, b in enumerate(self.beats, 1):
            p += b.problems(i)
        if painted:
            talk = sum(1 for b in self.beats if b.speaker != "narrator")
            want = max(4, len(self.beats) // 8)
            if talk < want:
                p.append(
                    f"only {talk} beats are spoken by characters; write at least {want} short dialogue beats "
                    "(set `speaker` to someone in the scene) so the story plays out instead of being described"
                )
        w = self.words()
        if not 0.7 * target_words <= w <= 1.3 * target_words:
            p.append(f"the script is {w} words; write about {target_words}")
        first = self.beats[0]
        if first.view not in ("scene", "object") or first.object == "mystery":
            p.insert(
                0,
                "beat 1 must drop the viewer into the story: a `scene` with people in a real place at a real moment, "
                "or an `object` that is not `mystery`",
            )
        elif first.view == "scene" and first.set in ("studio", "office") and first.scene_prop == "none":
            p.insert(
                0,
                "beat 1 is a person in an empty room. Open where the story happens (a lab, a shop, a street) with a prop or a second person",
            )
        if not self.hero.strip():
            p.append("`hero` is empty: say who the story follows")
        if len(self.hooks) < 3:
            p.append("`hooks` needs five candidate first lines, each a different angle")
        titles = sum(1 for b in self.beats if b.view == "title")
        if titles > max(2, len(self.beats) // 12):
            p.append(
                f"{titles} title cards is too many; keep at most {max(2, len(self.beats) // 12)} and turn the rest into scenes"
            )
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
            {"say": f"{topic}? Payment failed. And you're not the only one.", "view": "object", "object": "phone_fail",
             "people": [{"who": "you", "pose": "scared", "mood": "shocked"}], "chapter": "The day it stops", "prop_text": "20", "where": "Your street, 8 AM"},
            {"say": "Eight o'clock. You're at the tea stall, and your phone won't pay.", "view": "scene", "set": "bazaar",
             "people": [{"who": "you", "pose": "phone", "mood": "worried"}], "scene_prop": "chai_stall", "clock": "8:00 AM",
             "chapter": "8 AM: the first failure"},
            {"say": "Card machine's down. Cash only today.", "view": "scene", "set": "cafe", "speaker": "boss",
             "people": [{"who": "you", "pose": "phone", "mood": "worried"}, {"who": "boss", "pose": "shrug", "mood": "deadpan"}]},
            {"say": "Cash? Who carries cash?", "view": "scene", "set": "cafe", "speaker": "you",
             "people": [{"who": "you", "pose": "shrug", "mood": "shocked"}, {"who": "boss", "pose": "stand", "mood": "deadpan"}]},
            {"say": "Then I hope you're good at washing dishes.", "view": "scene", "set": "cafe", "speaker": "boss",
             "people": [{"who": "you", "pose": "stand", "mood": "sad"}, {"who": "boss", "pose": "point", "mood": "smug"}]},
            {"say": "No apps. No cards. No machines.", "view": "list", "items": ["No apps", "No cards", "No machines"]},
            {"say": "Is everyone's phone broken?", "view": "scene", "set": "park", "speaker": "woman",
             "people": [{"who": "woman", "pose": "phone", "mood": "worried"}, {"who": "you", "pose": "shrug", "mood": "worried"}]},
            {"say": "By tonight, the most valuable thing on your street will be a notebook.", "view": "object", "object": "mystery"},
            {"say": "Offline placeholder fact: about half of payments went through that day.", "view": "stat", "big": "50%",
             "label": "of payments went through", "source": "Offline placeholder, 2026"},
            {"say": "So you run to the cash machine. So did everyone else.", "view": "scene", "set": "street",
             "people": [{"who": "sam", "pose": "stand", "mood": "worried"}], "scene_prop": "atm", "prop_text": "OUT OF SERVICE"},
            {"say": "But in a boardroom across town, somebody saw this coming. They chose to wait.", "view": "scene", "set": "boardroom",
             "people": [{"who": "maya", "pose": "point", "mood": "worried"}, {"who": "leo", "pose": "shrug", "mood": "neutral"}],
             "sign": "PAYMENTS", "scene_prop": "chart_down", "prop_text": "Trust", "where": "Head office, 2019", "past": True},
            {"say": "Who still gets served? The regular, or the stranger?", "view": "duo", "label": "Who gets served?",
             "left": {"big": "10 yrs", "label": "The regular"}, "right": {"big": "Day 1", "label": "The stranger"}},
            {"say": "The shopkeeper pulls out a notebook, and writes down your name.", "view": "scene", "set": "kirana",
             "people": [{"who": "you", "pose": "stand", "mood": "happy"}, {"who": "sam", "pose": "read", "mood": "happy"}],
             "clock": "2:00 PM", "chapter": "2 PM: the notebook"},
            {"say": "That notebook is the answer. It's trust, written down.", "view": "object", "object": "ledger",
             "items": ["Mrs Rao|64", "You|240", "Flat 302|118"]},
            {"say": "Offline placeholder chart: payments lost in one afternoon.", "view": "bars", "label": "Payments lost",
             "bars": [{"name": "Cards", "value": 55, "text": "55%"}, {"name": "Shops", "value": 80, "text": "80%"}],
             "source": "Offline placeholder, 2026"},
            {"say": "Three things to do tonight. Keep a little cash. Know your shopkeeper. Count your wallet.", "view": "checklist",
             "items": ["Keep a little cash", "Know your shopkeeper", "Count your wallet"], "chapter": "What to do"},
            {"say": "So the shop stays open, and the shelves keep moving.", "view": "scene", "set": "store",
             "people": [{"who": "ana", "pose": "hold", "mood": "happy"}, {"who": "you", "pose": "cheer", "mood": "joy"}], "sign": "Corner shop"},
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
                "hero": "you",
                "stakes": "A whole day with no way to pay for anything.",
                "hooks": [
                    f"{topic}? Payment failed. And you are not the only one.",
                    "At eight this morning your phone stops paying, and so does everyone else's.",
                    "By tonight, a notebook is worth more than your bank account. Why?",
                ],
                "promise": "Why is a notebook the most valuable thing on your street by tonight?",
                "payoff_beat": 10 if len(beats) <= 16 else round(len(beats) * 0.6),
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
    keyword: str = Field(
        default="",
        description="The 2-4 word phrase a person would type into YouTube search to find this video.",
    )
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
            keyword=" ".join(topic.lower().split()[:4]),
            titles=[f"{topic}?"[:60], f"{topic} (hour by hour)"[:60], f"The day {topic.lower()}"[:60]],
            thumb_top="OFFLINE",
            thumb_bottom="TEST",
            description=(
                f"{topic}? {' '.join(topic.lower().split()[:4])}: this is the offline placeholder description, written by the fake provider so that a "
                "rehearsal run can finish without any API keys.\n\nNothing here was researched. Do not upload it."
            ),
            tags=["what if", "money", "explained", "economics", "animated", "the if lab"],
            hashtags=["#WhatIf", "#Money"],
            pinned_comment="How many days would you last?",
        )
