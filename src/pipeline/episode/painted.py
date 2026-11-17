"""The painted look's director: beats -> shots on painted backgrounds with big-head characters who talk.

Same contract as director.py (one shot per beat, the model never places anything), plus what makes the
style work on screen:
- every place is a painted background (assets/backgrounds/<set>.jpg), and cards and story objects are
  drawn over the last place, so the viewer never leaves the story for a blank studio;
- a character who speaks gets the camera: a close-up on their face (shot, reverse shot), and the shot
  remembers who it is (`spk`) so produce.voice can move their mouth while their line plays;
- long lines get a cut-in partway through (`cam2`), so the picture changes about every four seconds.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .director import GROUND, _actor, _card, _object
from .schemas import STORY_OBJS, Beat, Person

Shot = dict[str, Any]

# script role -> drawn character (render/src/cartoon/Cast.tsx)
CAST = {
    "you": "eng", "you_old": "eng_old", "boss": "boss", "exec_a": "exec1", "exec_b": "exec2", "exec_c": "exec3",
    "woman": "joy", "anchor": "anchor", "expert": "vince", "rival": "fuji", "young_a": "techa", "young_b": "techb",
    "kid_a": "kid1", "kid_b": "kid2", "maya": "maya", "leo": "leo", "zoe": "zoe", "sam": "sam", "ana": "ana",
}  # fmt: skip
# script role -> voice role (style narrator.voice / narrator.cast)
VOICE = {
    "narrator": "narrator", "you": "narrator", "you_old": "narrator",
    "boss": "man", "exec_a": "man", "exec_b": "man", "exec_c": "man", "expert": "man", "young_a": "man",
    "leo": "man", "sam": "man",
    "woman": "woman", "anchor": "woman", "rival": "woman", "young_b": "woman", "maya": "woman", "zoe": "woman",
    "ana": "woman",
}  # fmt: skip
BACKGROUNDS = ("lab", "living", "conf", "exec", "shop", "factory", "office", "startup", "street")
_ALIAS = {
    "boardroom": "conf", "stage": "conf", "store": "shop", "kirana": "shop", "bazaar": "street", "cafe": "street",
    "park": "street", "bank_front": "street", "pub": "street", "bedroom": "living", "kitchen": "living",
    "garage": "lab", "datacentre": "office", "studio": "office",
}  # fmt: skip
_X = {1: [960], 2: [700, 1250], 3: [540, 960, 1380]}
COUCH = {"x": 960, "y": 655, "s": 0.7}
TV_CLOSE = {"t": "tv_pixels", "x": 1005, "y": 800, "s": 1.3}
_DRAWER_ITEMS = {"prototype": "cam", "report": "memo", "memo": "memo", "idea": "bulb"}


def background(name: str | None) -> str:
    n = name or "office"
    return n if n in BACKGROUNDS else _ALIAS.get(n, "office")


def voice_role(speaker: str) -> str:
    return VOICE.get(speaker, "narrator")


def _close(x: float, z0: float = 1.5, z1: float = 1.62) -> list[float]:
    return [z0, z1, x, 610]


def _people(b: Beat, place: str) -> list[dict[str, Any]]:
    people = list(b.people)[:3]
    xs = _X.get(len(people), _X[3])
    out: list[dict[str, Any]] = []
    for i, p in enumerate(people):
        if place == "living" and p.pose == "sit" and not any(a.get("y") == COUCH["y"] for a in out):
            a = _actor(Person(who=p.who, pose="sit", mood=p.mood), int(COUCH["x"]))
            a.update(y=COUCH["y"], s=COUCH["s"])
        else:
            pose = "stand" if p.pose == "sit" else p.pose
            a = _actor(Person(who=p.who, pose=pose, mood=p.mood), xs[i], i)
            if place == "living":
                a["s"] = 0.85
        if len(people) > 1:
            a["face"] = 1 if i < len(people) - 1 else -1
        a["who"] = CAST.get(p.who, p.who)
        a.pop("glow", None)  # a screen glow sits over a big-head character's face
        out.append(a)
    return out


def _scene(b: Beat, i: int, place: str, new_place: bool) -> Shot:
    actors = _people(b, place)
    s: Shot = {"set": f"img:{place}", "actors": actors}
    words = len(b.say.split())
    roles = [p.who for p in b.people[:3]]
    spk = roles.index(b.speaker) if b.speaker in roles else None
    lead = actors[spk if spk is not None else 0]["x"] if actors else 960
    if spk is not None:
        s["spk"] = spk
        if words > 14 and len(actors) > 1:  # two-shot, then in on the speaker
            s.update(cam=[1.1, 1.16, 960, 620], cam2=_close(lead), cut=0.4)
        else:
            s["cam"] = _close(lead, 1.5 + 0.05 * (i % 3), 1.62 + 0.05 * (i % 3))
    elif new_place or not actors:
        s["cam"] = [1.0, 1.08, 960, 600]
        if words > 18 and actors:
            s.update(cam2=_close(lead, 1.35, 1.45), cut=0.5)
    else:
        s["cam"] = [[1.2, 1.32, lead, 620], [1.05, 1.1, 960, 600], [1.45, 1.55, lead, 610]][i % 3]
        if words > 18:
            s.update(cam2=[1.05, 1.1, 960, 600] if i % 3 != 1 else _close(lead, 1.35, 1.45), cut=0.5)
    props: list[dict[str, Any]] = []
    if b.scene_prop == "desk" and actors:
        props.append({"t": "worktable", "x": actors[0]["x"], "y": GROUND + 20, "s": 1.05, "front": True})
    elif b.scene_prop == "tv":
        props.append({"t": "tv_pixels", "x": 1500, "y": GROUND + 20, "s": 1.2, "from": 0.05, "to": 0.6})
        for a in actors:
            a["x"] = min(a["x"], 1100)
    if props:
        s["props"] = props
    return s


def _story_object(b: Beat, place: str) -> Shot:
    o = b.object
    s: Shot = {"set": f"img:{place}", "cam": [1.0, 1.06, 960, 540]}
    if o == "napkin":
        default = ["Product", "Customers", "Repeat sales", "Profit"]
        labels = [x.split("|")[0][:16] for x in (b.items or default)][:4]
        while len(labels) < 4:
            labels.append(default[len(labels)])
        spec: dict[str, Any] = {"t": "napkin", "x": 960, "y": 500, "s": 1.18, "labels": labels,
                                "tags": ["GO", "$", "$", "$"], "end": (b.prop_text or "PROFIT")[:12].upper(), "plain": True}  # fmt: skip
        if b.broken:
            spec["broken"] = 0.55
        s.update(props=[spec], sfx=["pop@0.05"] + (["buzzer@0.56"] if b.broken else []))
    elif o == "drawer":
        items = [_DRAWER_ITEMS.get(x.strip().lower(), "memo") for x in (b.items or ["prototype"])][:3]
        spec = {"t": "drawer", "x": 960, "y": 1020, "s": 0.92, "open": [0.0, 0.12],
                "items": [{"k": k, **({"at": 0.25} if j == len(items) - 1 and j > 0 else {})} for j, k in enumerate(items)],
                "label": (b.prop_text or "LATER")[:10].upper()}  # fmt: skip
        if not b.ok:
            spec["shut"] = 0.82
        s.update(
            cam=[1.0, 1.06, 960, 700], props=[spec], sfx=["drawer@0.03"] + ([] if b.ok else ["drawer@0.82"])
        )
    elif o == "memo":
        s["props"] = [{"t": "memo", "x": 960, "y": 560, "s": 1.05, "head": (b.prop_text or "REPORT")[:22],
                       "sub": (b.sub or "")[:40], "lines": b.items[:2], **({"stamp": b.label[:14]} if b.label else {})}]  # fmt: skip
        s["sfx"] = ["flip@0.05"]
    elif o == "old_tv":
        s.update(cam=[1.6, 1.75, 960, 520], props=[{**TV_CLOSE, "from": 0.05, "to": 0.6, "static": not b.ok}],
                 sfx=["static@0.55"] if not b.ok else ["ding@0.6"])  # fmt: skip
    elif o == "prototype":
        s.update(
            cam=[1.2, 1.3, 960, 720],
            props=[{"t": "worktable", "x": 960, "y": GROUND + 20, "s": 1.15, "front": True},
                   {"t": "proto_cam", "x": 960, "y": GROUND + 20 - 242, "s": 0.8, "front": True}],
            fx=[{"t": "sparkle", "x": 960, "y": 640, "from": 0.05}], sfx=["ding@0.1"],
        )  # fmt: skip
    elif o == "news":
        s.update(
            cam=[1.0, 1.06, 700, 520],
            props=[{"t": "news_bg", "x": 960, "y": 540, "box": (b.label or "BREAKING")[:12].upper(),
                    **({"stamp": b.sub[:16].upper()} if b.sub else {})},
                   {"t": "news_fg", "x": 960, "y": 540, "front": True, "head": (b.prop_text or "BREAKING NEWS")[:46].upper(),
                    "ticker": "   •   ".join(b.items) + "   •"}],
            actors=[{"who": "anchor", "pose": "stand", "expr": "neutral", "x": 640, "y": 960, "s": 1.35}],
            sfx=["ding@0.02"],
        )  # fmt: skip
        if b.speaker == "anchor":
            s["spk"] = 0
    elif o == "gadget":
        s["props"] = [{"t": "digicam", "x": 960, "y": 560, "s": 1.15, "label": (b.prop_text or "")[:12].upper(),
                       **({"tag": b.sub[:9], "at": 0.4} if b.sub else {})}]  # fmt: skip
        s["sfx"] = ["pop@0.05"]
    elif o == "website":
        s.update(
            cam=[1.0, 1.08, 1200, 560],
            props=[{"t": "photo_app", "x": 1250, "y": 520, "s": 0.95, "label": (b.prop_text or "")[:16].upper(),
                    **({"badge": b.sub[:20].upper()} if b.sub else {})}],
            actors=[{"who": CAST.get(b.people[0].who if b.people else "young_a", "techa"), "pose": "phone",
                     "expr": b.people[0].mood if b.people else "happy", "x": 520, "y": GROUND, "hold": "phone"}],
            sfx=["pop@0.1"],
        )  # fmt: skip
    return s


def _over_place(shot: Shot, place: str) -> Shot:
    """A card or a money object from the flat director, moved onto the current painted place."""
    shot["set"] = f"img:{place}"
    for a in shot.get("actors", []):
        a["who"] = CAST.get(a["who"], a["who"])
    return shot


def shot_for(b: Beat, i: int, place: str, new_place: bool) -> Shot:
    if b.view == "scene":
        s = _scene(b, i, place, new_place)
    elif b.view == "object" and b.object in STORY_OBJS:
        s = _story_object(b, place)
    elif b.view == "object":
        s = _over_place(_object(b), place)
    else:
        s = _over_place(_card(b), place)
    s["chibi"] = True
    s["voice"] = voice_role(b.speaker)
    return s


def thumbnail_shot(script_beats: list[Beat], mood: str) -> Shot:
    """The thumbnail's picture: the story's first place, the hero reacting, the person who said no, the object."""
    first = next((b for b in script_beats if b.view == "scene"), None)
    place = background(first.set if first else "lab")
    other = next(
        (p.who for b in script_beats for p in b.people if p.who not in ("you", "you_old", "kid_a", "kid_b")),
        "exec_c",
    )
    obj = next(
        (
            b.object
            for b in script_beats
            if b.view == "object" and b.object in ("prototype", "gadget", "website")
        ),
        None,
    )
    props: list[dict[str, Any]] = []
    if obj == "prototype":
        props = [{"t": "worktable", "x": 1180, "y": GROUND + 20, "s": 1.0, "front": True},
                 {"t": "proto_cam", "x": 1180, "y": GROUND + 20 - 210, "s": 0.8, "front": True}]  # fmt: skip
    elif obj == "gadget":
        props = [{"t": "digicam", "x": 1150, "y": 560, "s": 0.9}]
    elif obj == "website":
        props = [{"t": "photo_app", "x": 1150, "y": 520, "s": 0.85}]
    return {
        "id": "thumb", "n": "", "set": f"img:{place}", "chibi": True, "cam": [1.08, 1.08, 1500, 1000], "props": props,
        "actors": [{"who": "eng", "pose": "scared", "expr": mood, "x": 1500, "y": GROUND, "face": -1, "s": 1.05},
                   {"who": CAST.get(other, "exec3"), "pose": "point", "expr": "smug", "x": 1780, "y": GROUND, "face": -1, "s": 1.05}],
        "fx": [{"t": "sparkle", "x": 1180, "y": 640, "from": 0}] if props else [],
    }  # fmt: skip


def thumbnail_words(picture: Path, out: Path, top: str, bottom: str, font: Path) -> Path:
    """Words on the left of the picture, dark behind them so they hold at feed size. 1280 x 720 PNG."""
    from PIL import Image, ImageDraw, ImageFont

    im = Image.open(picture).convert("RGB")
    w, h = im.size
    shade = Image.new("L", (w, h))
    d = ImageDraw.Draw(shade)
    for x in range(w):
        d.line([(x, 0), (x, h)], fill=int(max(0, 170 * (1 - x / (w * 0.55)))))
    im = Image.composite(Image.new("RGB", (w, h), (25, 14, 8)), im, shade)
    lines = [(x, (255, 250, 240)) for x in top.upper().split()] + [
        (x, (255, 213, 74)) for x in bottom.upper().split()
    ]
    lines = lines[:3]
    size = min(250, int(1000 / max(1, max(len(t) for t, _ in lines)) * 1.45))
    y = (h - len(lines) * size * 1.0) / 2 - 20
    for text, color in lines:
        f = ImageFont.truetype(str(font), size)
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text(
            (70, y), text, font=f, fill=color, stroke_width=int(size * 0.09), stroke_fill=(16, 16, 20)
        )
        layer = layer.rotate(3, center=(70, y), resample=Image.Resampling.BICUBIC)
        im.paste(layer, (0, 0), layer)
        y += size * 1.0
    out.parent.mkdir(parents=True, exist_ok=True)
    im.resize((1280, 720), Image.Resampling.LANCZOS).save(out)
    return out
