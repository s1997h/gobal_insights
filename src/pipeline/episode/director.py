"""The director: turns the model's beats into concrete shots for the Remotion `Episode` composition.

The model says *what* is on screen ("a scene in the bazaar with a worried shopper at the ATM");
this module decides *where* everything goes, how the camera moves, which sound plays and how the
shot arrives. Keeping placement in code means a bad model output can never put a character off
screen or a card over a face.
"""

from __future__ import annotations

import re
from typing import Any

from .schemas import BIZ_SETS, Beat, EpisodeScript, Person

GROUND = 1000
Shot = dict[str, Any]

# scene props that stand on the right of the frame: (x, extra spec)
_RIGHT_PROPS: dict[str, tuple[int, dict[str, Any]]] = {
    "chai_stall": (1400, {"front": True}),
    "atm": (1540, {}),
    "petrol_pump": (1200, {"s": 0.9}),
    "auto": (1340, {"s": 1.2}),
    "veg_cart": (1500, {}),
    "shutter": (1280, {"s": 0.92, "close": 0.12}),
    "sign": (1400, {}),
    "product": (1450, {}),
    "chart_up": (1480, {}),
    "chart_down": (1480, {"down": True}),
}
_COUNTER_X = {"kirana": 1470, "pub": 1400}


def _pipes(text: str | None, per_line: int = 12, lines: int = 3) -> str:
    """Wrap sign text into at most `lines` short lines joined with '|' (the props' line break)."""
    words = (text or "").replace("|", " ").replace("/", " ").upper().split()
    out: list[str] = []
    cur = ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > per_line:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        out.append(cur)
    return "|".join(out[:lines])


def _actor(p: Person, x: int, i: int = 0, **extra: Any) -> dict[str, Any]:
    a: dict[str, Any] = {"who": p.who, "pose": p.pose, "expr": p.mood, "x": x, "y": GROUND, **extra}
    if p.pose == "phone":
        a.update(hold="phone", glow=True)
    elif p.pose == "read":
        a["hold"] = "book"
    elif p.pose == "walk":
        a["walk"] = [x - 380 if i % 2 == 0 else x + 380, x]
    return a


def _narrator(b: Beat, x: int, pose: str, mood: str) -> dict[str, Any]:
    p = b.people[0] if b.people else Person(who="you", pose=pose, mood=mood)  # type: ignore[arg-type]
    if p.pose in ("walk", "phone", "read"):  # a card is on screen; keep the narrator simple
        p = Person(who=p.who, pose=pose, mood=p.mood)  # type: ignore[arg-type]
    return _actor(p, x)


def _split(item: str) -> list[str]:
    for sep in ("|", ":", " - "):
        if sep in item:
            a, b = item.split(sep, 1)
            return [a.strip(), b.strip()]
    return [item.strip(), ""]


def _scene(b: Beat, i: int) -> Shot:
    place = b.set or "street"
    s: Shot = {"set": place}
    people = list(b.people)
    prop = b.scene_prop
    props: list[dict[str, Any]] = []

    if prop == "tv":
        lines = [x[:26] for x in (b.items or [(b.prop_text or "Breaking news")])][:3]
        s.update(set="living", setopt={"time": "evening"}, tod="night", cam=[1.0, 1.08, 1100, 560])
        who = people[0] if people else Person()
        s["actors"] = [{"who": who.who, "pose": "sit_look", "expr": who.mood, "x": 330, "y": GROUND}]
        s["props"] = [
            {"t": "couch", "x": 330, "y": GROUND},
            {"t": "tv", "x": 1250, "y": 880, "s": 0.95, "lines": lines, "ticker": (b.sub or "") + "   •   "},
        ]
        return s
    if prop == "desk":
        who = people[0] if people else Person()
        s.update(set="office", cam=[1.0, 1.05])
        s["actors"] = [{"who": who.who, "pose": "sit_desk", "expr": who.mood, "x": 520, "y": GROUND}]
        s["props"] = [{"t": "desk", "x": 680, "y": GROUND, "front": True}]
        return s
    if prop == "queue":
        lead = people[0] if people else Person(mood="worried")  # type: ignore[arg-type]
        q: dict[str, Any] = {
            "t": "queue",
            "x": 330,
            "y": GROUND,
            "n": 5,
            "gap": 190,
            "pose": lead.pose,
            "expr": lead.mood,
        }
        if lead.pose == "phone":
            q["glow"] = True
        s["props"] = [q]
        s["cam"] = [1.0, 1.06, 800, 700]
        return s

    if place in BIZ_SETS:
        s["setopt"] = {"sign": (b.sign or "")[:14], "down": prop == "chart_down"}
        if place == "boardroom" and prop in ("chart_up", "chart_down"):
            # the boardroom's wall screen is the chart; a second one on an easel would repeat it
            s["setopt"]["sign"] = (b.prop_text or b.sign or "")[:14]
            prop = "none"
    elif place in ("studio", "office") and prop == "none" and len(people) == 1:
        # one person in an empty room reads as a slide; give them something to do
        return _scene(b.model_copy(update={"scene_prop": "desk"}), i) if place == "office" else {
            **s, "actors": [_actor(people[0], 960)], "props": [], "cam": [1.0, 1.1, 960, 520] if i % 2 == 0 else [1.1, 1.0, 960, 520],
        }  # fmt: skip
    counter = _COUNTER_X.get(place)
    if counter is not None:  # the last person stands behind the counter
        if len(people) >= 2:
            keeper, rest = people[-1], people[:-1]
            slots = [640] if len(rest) == 1 else [330, 720]
            s["actors"] = [
                _actor(keeper, counter),
                *[_actor(p, x, k) for k, (p, x) in enumerate(zip(rest, slots, strict=False))],
            ]
        else:
            s["actors"] = [_actor(p, 640) for p in people]
        if place == "kirana":
            props.append({"t": "goods", "x": 1300, "y": 742, "s": 1.1, "front": True})
        if prop == "sign":
            props.append(
                {
                    "t": "sign_board",
                    "x": 520,
                    "y": 520,
                    "hang": True,
                    "text": _pipes(b.prop_text, 18),
                    "s": 0.8,
                }
            )
        s["props"] = props
        s["cam"] = [1.0, 1.08, 1100, 600] if i % 2 == 0 else [1.06, 1.0, 1100, 600]
        return s

    if place == "bank_front":  # the sign hangs on the bank's own door; people stand clear of it
        s["setopt"] = {"sign": _pipes(b.prop_text, 12, 1)[:12] if prop == "sign" else ""}
        slots = {1: [600], 2: [560, 1380], 3: [400, 640, 1400]}.get(len(people), [])
        s["actors"] = [_actor(p, x, k) for k, (p, x) in enumerate(zip(people, slots, strict=False))]
        s["props"] = []
        s["cam"] = [1.0, 1.06, 960, 560]
        return s

    if prop in _RIGHT_PROPS:
        x, extra = _RIGHT_PROPS[prop]
        spec: dict[str, Any] = {
            "t": {"atm": "atm_booth", "sign": "sign_board"}.get(prop, prop),
            "x": x,
            "y": GROUND,
            **extra,
        }
        text = _pipes(b.prop_text)
        if prop in ("chart_up", "chart_down"):
            spec.update(t="chart_board", label=(b.prop_text or "")[:14])
        elif prop == "product":
            spec["label"] = (b.prop_text or b.sign or "")[:12]
        if prop == "atm":
            spec["screen"] = text or "OUT OF|SERVICE"
        elif prop == "petrol_pump" and text:
            spec["board"] = text.replace("|", " ")
        elif prop in ("auto", "chai_stall") and text:
            spec["sign"] = text.replace("|", " ")[:12]
        elif prop == "shutter":
            spec["note"] = text or "CLOSED"
        elif prop == "sign":
            spec["text"] = text or "CLOSED"
        props.append(spec)
        slots = {1: [520], 2: [330, 760], 3: [250, 600, 950]}.get(len(people), [])
        s["cam"] = [1.0, 1.08, 1100, 680]
    else:
        slots = {1: [960], 2: [640, 1280], 3: [420, 960, 1500]}.get(len(people), [])
        s["cam"] = [1.0, 1.06] if i % 2 == 0 else [1.05, 1.0]
    s["actors"] = [_actor(p, x, k) for k, (p, x) in enumerate(zip(people, slots, strict=False))]
    s["props"] = props
    return s


def _object(b: Beat) -> Shot:
    s: Shot = {"set": "studio", "cam": [1.0, 1.08]}
    solo = not b.people
    x = 960 if solo else 1330
    if not solo:
        s["actors"] = [_actor(b.people[0], 500)]
    o, text = b.object, (b.prop_text or "").strip()
    sfx: list[str] = []
    if o in ("phone_fail", "phone_ok"):
        ok = o == "phone_ok"
        spec: dict[str, Any] = {
            "t": "pay_phone",
            "x": x,
            "y": 560,
            "s": 1.05,
            "at": 0.22,
            "ok": ok,
            "tilt": 0 if solo else -4,
        }
        spec["amount"] = text[:8] if re.fullmatch(r"[\d,. ]{1,8}", text) else "20"
        if b.label:
            spec["to"] = b.label[:16]
        s["props"] = [spec]
        if ok:
            sfx = ["ding@0.22"]
        else:
            s["shake"] = [0.22, 0.3]
            sfx = ["buzzer@0.22"]
    elif o == "wallet":
        s["props"] = [{"t": "wallet", "x": x, "y": 500, "s": 1.0, **({"label": text[:8]} if text else {})}]
        sfx = ["drawer@0.05"]
    elif o == "banknote":
        s["props"] = [{"t": "note", "x": x, "y": 520, "s": 1.15, "glow": True, "val": text[:4] or "100"}]
        sfx = ["ding@0.12"]
    elif o in ("ledger", "mystery"):
        lines = [_split(it) for it in b.items[:7]]
        s["props"] = [
            {"t": "khata", "x": x, "y": 560, "s": 0.95 if solo else 0.7, "glow": o == "mystery" or len(lines) > 4,
             **({"mystery": True} if o == "mystery" else {"lines": lines or [["You", ""]], "from": 0.08, "to": 0.7})}
        ]  # fmt: skip
        sfx = ["whoosh@0.5"] if o == "mystery" else ["tick@0.15", "tick@0.4"]
    elif o in ("balance", "balance_locked"):
        spec = {
            "t": "balance",
            "x": x,
            "y": 540,
            "s": 1.2 if solo else 0.9,
            "amount": text[:10] if re.fullmatch(r"[\d,. ]{1,10}", text) else "42,318",
        }
        if o == "balance_locked":
            spec["at"] = 0.4
            sfx = ["thud@0.4"]
        s["props"] = [spec]
    elif o == "cheque":
        s["props"] = [{"t": "cheque", "x": x, "y": 540, "s": 1.7, **({"val": text[:6]} if text else {})}]
        sfx = ["flip@0.1"]
    elif o == "pins":
        s.pop("actors", None)
        s["props"] = [{"t": "city_pins", "x": 960, "y": 470, "items": [_split(it) for it in b.items[:4]]}]
        sfx = [f"pop@{0.08 + k * 0.16:.2f}" for k in range(min(4, len(b.items)))]
    elif o == "calendar":
        s["props"] = [{"t": "calendar", "x": x, "y": 540, "s": 1.5, "flip": [1, 2]}]
        sfx = ["flip@0.5"]
    s["sfx"] = sfx
    return s


def _card(b: Beat) -> Shot:
    s: Shot = {"set": "studio", "cam": [1.0, 1.05]}
    v = b.view
    if v == "stat":
        ov: dict[str, Any] = {"t": "stat", "big": b.big, "label": b.label, "pos": "right"}
        if b.sub:
            ov["sub"] = b.sub
        if b.source:
            ov["src"] = f"Source: {b.source}"
        # count up to a percentage or a quantity, never to a year
        if b.big and b.big.rstrip("%").isdigit() and not re.fullmatch(r"(1[5-9]|20)\d\d", b.big):
            ov["count"] = True
        s.update(actors=[_narrator(b, 430, "point", "neutral")], ov=ov, sfx=["pop@0.25"])
    elif v == "title":
        big = (b.big or "").upper()
        wide = len(big) > 8
        s["ov"] = {
            "t": "title",
            "title": big,
            "pos": "center" if wide else "right",
            **({"sub": b.label} if b.label else {}),
        }
        if not wide:
            s["actors"] = [_narrator(b, 470, "think", "happy")]
        s["sfx"] = ["whoosh@0.2"]
    elif v == "list":
        s.update(
            actors=[_narrator(b, 480, "think", "neutral")],
            ov={"t": "rules", "items": b.items, "pos": "right", "ok": b.ok},
            sfx=[f"pop@{0.05 + k * 0.15:.2f}" for k in range(len(b.items))],
        )
    elif v == "checklist":
        n = len(b.items)
        s.update(
            ov={"t": "checklist", "items": b.items, "pos": "center"},
            sfx=[f"tick@{0.12 + k * (0.8 / n):.2f}" for k in range(n)],
        )
    elif v == "duo" and b.left and b.right:
        s.update(
            ov={"t": "duo", "head": b.label or "", "a": b.left.model_dump(), "b": b.right.model_dump(), "pos": "center",
                **({"src": f"Source: {b.source}"} if b.source else {})},
            sfx=["pop@0.15", "pop@0.6"],
        )  # fmt: skip
    elif v == "bars":
        s.update(
            ov={"t": "bars", "title": b.label or "", "max": 100, "pos": "center", "src": f"Source: {b.source}",
                "bars": [{"l": x.name[:14], "v": x.value, "txt": x.text[:6], "hot": k == len(b.bars) - 1} for k, x in enumerate(b.bars)]},
            sfx=[f"pop@{0.3 + k * 0.2:.2f}" for k in range(len(b.bars))],
        )  # fmt: skip
    elif v == "end":
        s.update(
            actors=[{"who": "you", "pose": "wave", "expr": "joy", "x": 960, "y": GROUND}],
            fx=[{"t": "coins", "x": 960, "y": 620, "from": 0.3}],
            ov={
                "t": "end",
                "pos": "center",
                "next": re.sub(r"^\s*(next( up| video)?)\s*[:\-–]\s*", "", b.label or "", flags=re.I)[:60],
            },
            sfx=["ding@0.3"],
            min=5.5,
        )
    return s


def direct(script: EpisodeScript, prefix: str = "b") -> tuple[list[Shot], list[list[str]]]:
    """Beats -> (shots, chapters). Chapters are [shot id, title] pairs for YouTube and for pacing."""
    shots: list[Shot] = []
    chapters: list[list[str]] = []
    clock: str | None = None
    for i, b in enumerate(script.beats):
        sid = f"{prefix}{i + 1:03d}"
        shot = _scene(b, i) if b.view == "scene" else _object(b) if b.view == "object" else _card(b)
        if b.clock is not None:
            clock = b.clock or None
        timeline = clock if not b.past and b.view != "end" else None
        shot = {"id": sid, "n": b.say, **shot}
        if timeline:
            shot["clock"] = timeline
        if b.past:
            shot["tod"] = "sepia"
        if b.where and b.view == "scene":
            shot["where"] = b.where[:28]
        if b.chapter or i == 0:
            chapters.append([sid, b.chapter or "Intro"])
            if i > 0:
                shot["tr"] = "wipe"
        if len(b.say.split()) <= 6:
            shot["min"] = max(float(shot.get("min", 0)), 2.8)
        shots.append(shot)
    return shots, chapters


def direct_hook(beat: Beat, sid: str) -> Shot:
    """One extra shot for the start of a Short."""
    one = EpisodeScript.model_construct(promise="", payoff_beat=1, comment_prompt="", beats=[beat], claims=[])
    shot = direct(one, prefix="h")[0][0]
    shot["id"] = sid
    shot.pop("tr", None)
    return shot
