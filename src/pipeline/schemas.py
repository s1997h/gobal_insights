"""Pydantic contracts shared by every stage (agents, TTS, renderer, export)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .util import utcnow

Format = Literal["long", "short"]
FORMATS: tuple[str, ...] = ("long", "short")
MOODS: tuple[str, ...] = ("neutral", "shocked", "happy", "worried")

SLOT_RE = re.compile(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun) ([01]\d|2[0-3]):[0-5]\d$")

# --- Scene templates ---------------------------------------------------------
# name -> (one-line description for the script prompt, props example)
TEMPLATE_SPECS: dict[str, tuple[str, str]] = {
    "title_card": (
        "Big title on screen. Use for the opening and for chapter starts.",
        '{"title": "What if you won the lottery?", "subtitle": "Hour by hour"}',
    ),
    "you_reaction": (
        "The YOU character reacts. mood is one of: neutral, shocked, happy, worried.",
        '{"mood": "shocked"}',
    ),
    "diagram": (
        "2 to 5 labelled boxes joined by arrows (a chain of cause and effect).",
        '{"nodes": ["Win", "Tell family", "Calls begin", "New phone number"]}',
    ),
    "number_counter": (
        "A big number counting up or down. Use for the key statistic.",
        '{"from": 0, "to": 1000000, "prefix": "$", "label": "in your account"}',
    ),
    "compare": (
        "Two columns side by side, each with a label and 2 to 4 short points.",
        '{"left": {"label": "Lump sum", "points": ["Cash now", "Taxed up front"]}, '
        '"right": {"label": "Annuity", "points": ["Paid over years", "Steadier"]}}',
    ),
    "captions_only": (
        "No picture; the captions carry the scene. Use sparingly for a pause or a punchline.",
        "{}",
    ),
}
TEMPLATES: frozenset[str] = frozenset(TEMPLATE_SPECS)


class Destination(BaseModel):
    platform: str  # checked against known platforms at load time
    account: str  # key for the token in Key Vault (later); a config never holds a secret
    formats: list[Format]


class Budget(BaseModel):
    per_video_usd: float = 8.0
    per_month_usd: float = 150.0


class Schedule(BaseModel):
    timezone: str = "Asia/Kolkata"
    long: list[str] = []
    short: list[str] = []

    @field_validator("long", "short")
    @classmethod
    def _slots(cls, v: list[str]) -> list[str]:
        for s in v:
            if not SLOT_RE.match(s):
                raise ValueError(f"bad slot {s!r}; expected like 'Mon 19:00'")
        return v


class VisualPolicy(BaseModel):
    stills: bool = True
    hero_clips: bool = False
    max_stills_long: int = 12
    max_stills_short: int = 4


class ChannelConfig(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    name: str
    style: str
    language: str = "en"
    formats: list[Format]
    schedule: Schedule
    budget: Budget = Budget()
    visuals: VisualPolicy = VisualPolicy()
    destinations: list[Destination] = Field(min_length=1)


# --- Style bible -------------------------------------------------------------
class Palette(BaseModel):
    bg: str
    gold: str
    teal: str
    ink: str


class CaptionStyle(BaseModel):
    max_words_per_line: int = 4
    highlight: str = "gold"  # a palette key
    position: Literal["lower_third", "center"] = "lower_third"


class Narrator(BaseModel):
    provider: str = "azure"
    voice: str
    fallback_voice: str | None = None  # used for the whole video when `voice` fails (e.g. not in this region)
    rate: float = 1.0
    wpm: int = 150  # measured narration pace; used to size scripts


class LongSpec(BaseModel):
    ratio: str = "16:9"
    target_minutes: float = 9


class ShortSpec(BaseModel):
    ratio: str = "9:16"
    target_seconds: float = 55


class FormatSpecs(BaseModel):
    long: LongSpec = LongSpec()
    short: ShortSpec = ShortSpec()


class MusicStyle(BaseModel):
    volume: float = 0.22
    tracks: list[str] = []


class StoryShape(BaseModel):
    id: str
    name: str
    description: str


class StyleBible(BaseModel):
    palette: Palette
    font: str = "Inter"
    captions: CaptionStyle = CaptionStyle()
    narrator: Narrator
    formats: FormatSpecs = FormatSpecs()
    banned_phrases: list[str] = []
    voice_rules: str = ""
    image_suffix: str = ""
    disclosure: str = ""
    music: MusicStyle = MusicStyle()
    story_shapes: list[StoryShape] = Field(min_length=1)

    @model_validator(mode="after")
    def _highlight_is_palette_key(self) -> StyleBible:
        if self.captions.highlight not in type(self.palette).model_fields:
            raise ValueError(f"captions.highlight must be a palette key, got {self.captions.highlight!r}")
        return self

    def highlight_hex(self) -> str:
        return str(getattr(self.palette, self.captions.highlight))

    def target_words(self, fmt: str, scale: float = 1.0) -> int:
        wpm = self.narrator.wpm
        if fmt == "long":
            minutes = self.formats.long.target_minutes
        else:
            minutes = self.formats.short.target_seconds / 60
        return max(12, round(minutes * wpm * scale))


# --- Scripts -----------------------------------------------------------------
class Visual(BaseModel):
    type: Literal["template", "still", "hero_clip"]
    template: str | None = None
    props: dict[str, Any] = {}
    prompt: str | None = None
    max_sec: float | None = None

    @model_validator(mode="after")
    def _consistent(self) -> Visual:
        if self.type == "template":
            if self.template not in TEMPLATES:
                raise ValueError(f"unknown template {self.template!r}; use one of {sorted(TEMPLATES)}")
        elif not self.prompt:
            raise ValueError(f"visual type {self.type!r} needs a prompt")
        return self


class Scene(BaseModel):
    id: str
    narration: str = Field(min_length=1)
    visual: Visual
    on_screen_text: str | None = None
    min_sec: float = 3.0
    chapter: str | None = None  # set on the scene that starts a YouTube chapter (long only)


class ScriptDraft(BaseModel):
    """What the script agent returns for one format (code adds ids)."""

    scenes: list[Scene] = Field(min_length=3)


class ScriptPair(BaseModel):
    long: ScriptDraft
    short: ScriptDraft


class ScriptDoc(BaseModel):
    video_id: str
    channel_id: str
    format: Format
    scenes: list[Scene] = Field(min_length=3)

    @model_validator(mode="after")
    def _unique_ids(self) -> ScriptDoc:
        ids = [s.id for s in self.scenes]
        if len(ids) != len(set(ids)):
            raise ValueError("scene ids must be unique")
        return self


# --- Agent outputs -----------------------------------------------------------
class TopicCandidate(BaseModel):
    title: str = Field(description="The topic as a 'What if you ...' line")
    angle: str = Field(description="The specific angle that makes this video different")
    story_shape: str = Field(description="id of one story shape from the list provided")
    hook_idea: str = Field(description="A concrete first sentence idea, no greeting")


class TopicProposal(BaseModel):
    candidates: list[TopicCandidate] = Field(min_length=3, max_length=3)


class Claim(BaseModel):
    text: str
    source: str = Field(description="A named source, or 'common knowledge'")


class CriticReport(BaseModel):
    passed: bool
    hook_score: int = Field(ge=0, le=10)
    fixes: list[str] = []
    claims: list[Claim] = []
    notes: str = ""


class PackageDraft(BaseModel):
    titles: list[str] = Field(
        min_length=3, max_length=3, description="Three title options for the long video"
    )
    thumbnail_text: str = Field(description="Four words at most")
    thumbnail_mood: Literal["neutral", "shocked", "happy", "worried"] = "shocked"
    description: str = Field(description="2 to 4 sentences for the long video, no chapters, no hashtags")
    tags: list[str] = Field(description="8 to 15 tags")
    short_title: str
    short_description: str = Field(description="1 to 2 sentences for the Short")
    instagram_caption: str = Field(description="Caption for the Reel, without hashtags")
    hashtags: list[str] = Field(max_length=5, description="Up to five, each starting with #")


# --- Timing, assets, posts, costs -------------------------------------------
class WordTiming(BaseModel):
    word: str
    start_ms: float
    end_ms: float
    scene_id: str | None = None


class SceneSpan(BaseModel):
    id: str
    start_ms: float
    end_ms: float


class Timing(BaseModel):
    total_sec: float
    scenes: list[SceneSpan]


class PostMeta(BaseModel):
    title: str
    description: str = ""
    tags: list[str] = []
    caption: str = ""  # Instagram
    thumbnail_path: str | None = None


class RenderedAsset(BaseModel):
    run_id: str
    format: Format
    path: str
    duration_sec: float


class CostEvent(BaseModel):
    run_id: str
    channel_id: str
    step: str
    provider: str
    units: float = 0.0
    usd: float = 0.0
    at: datetime = Field(default_factory=utcnow)
