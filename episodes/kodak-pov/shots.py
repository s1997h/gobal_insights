"""Shots, timing, captions and the audio plan for the POV version of the Kodak story.

usage: python3 episodes/kodak-pov/shots.py            -> work/props.json, work/audio_plan.json

Told in the second person, like the reference video the user picked: you are the young Kodak engineer
who built the first digital camera in 1975 (Steve Sasson, named at the end). Painted backgrounds,
big-head characters whose mouths move on their lines, and word-by-word captions.

The voices are three ElevenLabs takes made through vidIQ (work/voice_*.json): Chris narrates and plays
"you", Bill plays the Kodak managers, Sarah plays Joy and the news anchor. work/lines.json says where
each of the 94 lines sits in its take (src, src_start, dur). This script lays the lines out on one
timeline with pauses between them, cuts the picture to that timeline, and writes where each line goes
so the mixer can place it.

Facts and sources are the same as the documentary version (episodes/kodak-digital-camera/shots.py).
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
WORK = HERE / "work"
LINES = json.loads((HERE / "data" / "lines.json").read_text())
N = len(LINES)

SRC_MARKET = "Source: Disposable America (Hagley); Knowledge at Wharton, 2012"
SRC_WHARTON = "Source: Knowledge at Wharton, 2012"
SRC_MUI = "Source: Chunka Mui, Forbes, 2012"
SRC_PETA = "Source: PetaPixel, 2018"
SRC_AP = "Source: AP, March 2012"
SRC_FB = "Source: Facebook, April 2012"
SRC_DC = "Source: Rochester Democrat and Chronicle, Jan 2012"
SRC_IEEE = "Source: IEEE Spectrum"

# ---------------------------------------------------------------------------------------- timeline
LEAD = 0.6
END_SEC = 6.0
EXTRA = {  # extra pause after a line: scene changes, jokes landing, the shutter
    1: 0.35, 5: 0.25, 6: 0.9, 8: 0.2, 16: 0.35, 19: 0.3, 22: 0.55, 25: 0.3, 27: 0.7, 28: 0.25,
    29: 0.3, 31: 0.8, 33: 0.5, 43: 0.25, 44: 0.5, 51: 0.45, 52: 0.3, 53: 0.7, 57: 0.25, 61: 0.45,
    62: 0.8, 64: 0.3, 67: 0.2, 69: 0.4, 72: 0.3, 76: 0.7, 79: 0.25, 81: 0.2, 82: 0.4, 83: 0.6,
    86: 0.3, 88: 0.7, 90: 0.6, 91: 0.6, 92: 0.4,
}


def gap_after(i):
    if i == N - 1:
        return 0.8
    same = LINES[i]["who"] == LINES[i + 1]["who"]
    return (0.2 if same else 0.32) + EXTRA.get(i, 0.0)


START = []
_t = LEAD
for _i, _l in enumerate(LINES):
    START.append(round(_t, 3))
    _t += _l["dur"] + gap_after(_i)
END_AT = round(_t, 3)
TOTAL = round(END_AT + END_SEC, 3)


def line_end(i):
    return START[i] + LINES[i]["dur"]


# ------------------------------------------------------------------------- word timing (estimated)
def _weights(tokens):
    w = []
    for tok in tokens:
        x = len(re.sub(r"[^\w]", "", tok)) + 1.6
        if tok[-1] in ".?!":
            x += 3.2
        elif tok[-1] in ",;:":
            x += 1.6
        w.append(x)
    return w


WORDS = []  # per line: [(token, s, e)]
for _i, _l in enumerate(LINES):
    toks = _l["text"].split()
    ws = _weights(toks)
    a, b = START[_i] + 0.04, START[_i] + _l["dur"] - 0.08
    tot = sum(ws)
    acc = a
    row = []
    for tok, w in zip(toks, ws, strict=True):
        d = (b - a) * w / tot
        # punctuation pause belongs after the word, not inside it
        p = 3.2 if tok[-1] in ".?!" else 1.6 if tok[-1] in ",;:" else 0
        speak = d * (w - p) / w
        row.append((tok, round(acc, 3), round(acc + speak, 3)))
        acc += d
    WORDS.append(row)


def at(i, needle=None, off=0.0):
    """Absolute time a word starts in line i (the line's start without a needle)."""
    if needle is None:
        return START[i] + off
    n = needle.lower()
    for tok, s, _e in WORDS[i]:
        if n in tok.lower():
            return s + off
    raise KeyError(f"{needle!r} not in line {i}: {LINES[i]['text']}")


class W:
    """A moment inside a shot, resolved to shot progress (0..1) once the shot's span is known."""

    def __init__(self, i, needle=None, off=0.0):
        self.t = at(i, needle, off)


# caption display: numbers as digits
DISPLAY = [
    ("January nineteenth, twenty twelve.", "January 19, 2012."),
    ("sixty-one,", "61,"),
    ("hundred-and-thirty-one-year-old", "131-year-old"),
    ("thirty-seven years", "37 years"),
    ("Nineteen seventy-four.", "1974."),
    ("twenty-three, fresh", "23, fresh"),
    ("thirty seconds.", "30 seconds."),
    ("eight pounds.", "8 pounds."),
    ("nineteen seventy-five.", "1975."),
    ("Twenty-three seconds.", "23 seconds."),
    ("Nineteen seventy-six.", "1976."),
    ("Fifteen, maybe twenty years.", "15, maybe 20 years."),
    ("Twenty years is", "20 years is"),
    ("nineteen seventy-six,", "1976,"),
    ("ninety percent", "90%"),
    ("eighty percent.", "80%."),
    ("nineteen eighty-one,", "1981,"),
    ("ten years.", "10 years."),
    ("ten-year", "10-year"),
    ("Ten billion dollars", "$10 billion"),
    ("nineteen-nineties,", "1990s,"),
    ("twenty thousand dollars each.", "$20,000 each."),
    ("Twenty thousand?", "$20,000?"),
    ("two thousand and one,", "2001,"),
    ("seventy-five million", "75 million"),
    ("two thousand five,", "2005,"),
    ("sixty dollars", "$60"),
    ("Sixty dollars?", "$60?"),
    ("two thousand, it", "2000, it"),
    ("Ten years later,", "10 years later,"),
    ("ten minutes.", "10 minutes."),
    ("twenty twelve.", "2012."),
    ("eleven hundred", "1,100"),
    ("twenty-three point eight million dollars.", "$23.8 million."),
    ("one billion dollars.", "$1 billion."),
    ("thirteen employees.", "13 employees."),
    ("Thirteen?", "13?"),
    ("nineteen ninety-five.", "1995."),
    ("fifty-seven percent.", "57%."),
    ("fell forty-eight.", "fell 48%."),
    ("twenty-four.", "24."),
]


def caption_words():
    out = []
    for row in WORDS:
        toks = [r[0] for r in row]
        k = 0
        while k < len(row):
            hit = None
            for src, dst in DISPLAY:
                st = src.split()
                if toks[k : k + len(st)] == st:
                    hit = (st, dst.split())
                    break
            if hit:
                st, dt = hit
                s, e = row[k][1], row[k + len(st) - 1][2]
                for j, d in enumerate(dt):
                    out.append({"w": d, "s": round(s + (e - s) * j / len(dt), 3), "e": round(s + (e - s) * (j + 1) / len(dt), 3)})
                k += len(st)
            else:
                out.append({"w": row[k][0], "s": row[k][1], "e": row[k][2]})
                k += 1
    return out


# ------------------------------------------------------------------------------------------ cast
YOU, OLD, BOSS = "eng", "eng_old", "boss"
E1, E2, E3 = "exec1", "exec2", "exec3"
JOY, ANC, VIN, FUJI = "joy", "anchor", "vince", "fuji"
TA, TB, K1, K2 = "techa", "techb", "kid1", "kid2"
SPEAKERS = {"Y": {YOU, OLD}, "B": {BOSS, E1, E2, E3}, "J": {JOY, ANC}}

Y = 1000
TT = 210  # worktable top above its floor point


def A(who, pose="stand", expr="neutral", x=960, y=Y, **kw):
    return {"who": who, "pose": pose, "expr": expr, "x": x, "y": y, **kw}


def close(x, y=610, z0=1.55, z1=1.65):
    """Camera that holds a head at (x, y) and moves in on it."""
    return [z0, z1, x, y]


def S(start, set_, **kw):
    """start: a line index, or (line, word) to cut on a word."""
    if isinstance(start, tuple):
        t0 = at(start[0], start[1], -0.12)
    elif isinstance(start, float):
        t0 = start
    else:
        t0 = START[start] - 0.18
    return {"t0": t0, "set": set_ if ":" in set_ or set_ == "studio" else "img:" + set_, "chibi": True, **kw}


def worktable(x, s=1.0, front=False, **kw):
    return {"t": "worktable", "x": x, "y": Y + 20, "s": s, "front": front, **kw}


def cam_on_table(x, s=0.8, **kw):
    return {"t": "proto_cam", "x": x, "y": Y + 20 - TT * 1.15, "s": s, "front": True, **kw}


COUCH = dict(x=960, y=655, s=0.7)
TVC = {"t": "tv_pixels", "x": 1005, "y": 800, "s": 1.3, "from": 0.0, "to": 0.001, "static": True}  # the TV, centred for close-ups
TVCAM = [1.6, 1.75, 960, 520]
NEWS_HEAD = "KODAK FILES FOR BANKRUPTCY"

# --------------------------------------------------------------------------------------------- shots
SHOTS = [
    # ===================================================== COLD OPEN: 2012
    S(0.0, "living", tr="fade", where="January 2012", cam=[1.18, 1.3, 960, 560],
      actors=[A(OLD, "sit", "sleep", **COUCH)], fx=[{"t": "zzz", "x": 1010, "y": 330}]),
    S(1, "living", cam=[1.0, 1.06, 700, 520],
      props=[{"t": "news_bg", "x": 960, "y": 540, "box": "KODAK", "stamp": "CHAPTER 11"},
             {"t": "news_fg", "x": 960, "y": 540, "front": True, "head": NEWS_HEAD,
              "ticker": "Eastman Kodak, founded 1881, files for Chapter 11 bankruptcy protection   •   Rochester, New York   •"}],
      actors=[A(ANC, "stand", "neutral", 640, 960, s=1.35)], sfx=["ding@0.02"]),
    S(2, "living", cam=close(960, 470, 1.7, 1.8), actors=[A(OLD, "sit_look", "shocked", **COUCH)], sfx=["pop@0.05"]),
    S(3, "living", cam=[1.35, 1.45, 960, 470], actors=[A(OLD, "sit_look", "sad", **COUCH)],
      fx=[{"t": "thought", "x": 1180, "y": 260, "from": 0.2}]),
    S(4, "living", cam=close(960, 470, 1.75, 1.95), actors=[A(OLD, "sit", "deadpan", **COUCH)]),
    S(5, "lab", tod="sepia", cam=[1.1, 1.22, 960, 760],
      props=[worktable(960, 1.15), cam_on_table(960, 0.8)],
      fx=[{"t": "sparkle", "x": 960, "y": 640, "from": 0.05}]),
    S((5, "they"), "lab", tod="sepia", cam=[1.15, 1.2, 960, 700],
      props=[{"t": "drawer", "x": 960, "y": 1020, "s": 0.92, "open": [0.0, 0.01], "shut": 0.55, "items": [{"k": "cam"}]}],
      sfx=["drawer@0.5"]),
    S(6, "living", cam=[1.3, 2.1, 960, 470], actors=[A(OLD, "sit", "worried", **COUCH)], sfx=["whoosh@0.75"]),

    # ===================================================== 1974: THE ASSIGNMENT
    S(7, "street", tr="wipe", where="Rochester, New York, 1974", cam=[1.0, 1.08, 960, 620],
      actors=[A(YOU, "walk", "grin", 380, walk=[300, 960], pose2="wave", at=0.7)]),
    S(8, "factory", cam=[1.0, 1.1, 960, 560], actors=[A(YOU, "stand", "shocked", 560, s=0.8)],
      fx=[{"t": "sparkle", "x": 1300, "y": 420, "from": 0.2}]),
    S((8, "Cameras,"), "shop", cam=[1.05, 1.15, 960, 560], actors=[A(YOU, "point", "joy", 420, s=0.85)],
      ov={"t": "checklist", "items": ["Cameras", "Film", "Chemicals", "Paper"], "pos": "right", "w": 760,
          "ats": [W(8, "Cameras,"), W(8, "film,"), W(8, "chemicals,"), W(8, "paper.")]},
      fx=[{"t": "coins", "x": 1400, "y": 300, "from": W(8, "paid.", -0.3)}]),
    S(9, "lab", cam=[1.0, 1.05, 960, 620], where="Kodak Research Labs",
      props=[worktable(560, 1.1)],
      actors=[A(YOU, "stand", "neutral", 560, face=1), A(BOSS, "walk", "happy", 1500, walk=[1700, 1250], face=-1)],
      fx=[{"t": "clock_float", "x": 1500, "y": 260, "from": W(9, "whole")}]),
    S(10, "lab", cam=close(1250, 620, 1.35, 1.45), props=[worktable(560, 1.1)],
      actors=[A(YOU, "stand", "neutral", 700, face=1), A(BOSS, "point", "happy", 1250, face=-1)], spk={"B": 1}),
    S(11, "lab", cam=close(700, 600, 1.7, 1.8), props=[worktable(560, 1.1)],
      actors=[A(YOU, "shrug", "deadpan", 700, face=1), A(BOSS, "stand", "happy", 1250, face=-1)]),
    S(13, "lab", cam=[1.25, 1.32, 1000, 620], props=[worktable(560, 1.1)],
      actors=[A(YOU, "stand", "worried", 700, face=1), A(BOSS, "hold", "grin", 1250, face=-1)], spk={"B": 1},
      fx=[{"t": "bulb", "x": 1250, "y": 330, "from": 0.15}]),
    S(14, "lab", cam=close(700, 600, 1.6, 1.85), props=[worktable(560, 1.1)],
      actors=[A(YOU, "scared", "shocked", 700, face=1), A(BOSS, "stand", "happy", 1250, face=-1)],
      fx=[{"t": "question", "x": 700, "y": 290, "from": W(14, "Here?")}], shake=[0.55, 0.62]),
    S(15, "lab", cam=close(1250, 620, 1.45, 1.5), props=[worktable(560, 1.1)],
      actors=[A(YOU, "stand", "worried", 700, face=1), A(BOSS, "wave", "grin", 1250, face=-1)], spk={"B": 1}),
    S(16, "lab", cam=[1.05, 1.08, 960, 620], props=[worktable(560, 1.1)],
      actors=[A(YOU, "shrug", "deadpan", 700, face=1), A(BOSS, "walk", "happy", 1250, walk=[1250, 2250], face=1)],
      fx=[{"t": "crickets", "x": 1350, "y": 860, "from": W(16, "That's", 0.1)}]),

    # ===================================================== BUILDING IT
    S(17, "lab", cam=[1.25, 1.35, 900, 600], actors=[A(YOU, "think", "smug", 900)],
      fx=[{"t": "bulb", "x": 980, "y": 280, "from": W(17, "raid", -0.3)}]),
    S((17, "raid", -0.3), "office", cam=[1.0, 1.1, 960, 600], actors=[A(YOU, "walk", "grin", 300, walk=[200, 1500])], sfx=["whoosh@0.05"]),
    S(18, "lab", cam=[1.05, 1.1, 960, 600], props=[worktable(500, 1.1)],
      actors=[A(YOU, "hold", "happy", 520, face=1)],
      ov={"t": "checklist", "pos": "right", "w": 900,
          "items": ["Movie-camera lens", "Cassette recorder", "Circuit boards", "Lots of batteries"],
          "ats": [W(18, "lens"), W(18, "cassette"), W(18, "stack"), W(18, "batteries")]}),
    S(19, "lab", cam=[1.2, 1.3, 960, 720], where="One year later",
      props=[worktable(960, 1.15), cam_on_table(960, 0.8)],
      actors=[A(YOU, "cheer", "joy", 1420, face=-1)],
      fx=[{"t": "sparkle", "x": 960, "y": 650, "from": 0.05}],
      ov={"t": "stat", "big": "8 lb", "label": "and it looks like a toaster", "pos": "left", "delay": W(19, "weighs")}),
    S((19, "takes"), "lab", cam=close(960, 700, 1.5, 1.7), props=[worktable(960, 1.15), cam_on_table(960, 0.8)],
      fx=[{"t": "no_camera", "x": 1350, "y": 420, "from": W(19, "without")}], sfx=["ding@0.6"]),

    # ===================================================== DECEMBER 1975: JOY
    S(20, "lab", tr="wipe", where="December 1975", cam=[1.15, 1.25, 900, 620],
      actors=[A(YOU, "think", "worried", 900)], fx=[{"t": "question", "x": 900, "y": 280, "from": 0.2}]),
    S((20, "walk", -0.3), "lab", cam=[1.0, 1.06, 960, 620],
      actors=[A(YOU, "walk", "happy", 300, walk=[250, 800], face=1), A(JOY, "read", "bored", 1350, face=-1)]),
    S(21, "lab", cam=[1.25, 1.3, 1080, 620],
      actors=[A(YOU, "wave", "grin", 800, face=1), A(JOY, "stand", "deadpan", 1350, face=-1)]),
    S(22, "lab", cam=close(1350, 620, 1.5, 1.6), actors=[A(YOU, "stand", "grin", 800, face=1), A(JOY, "shrug", "deadpan", 1350, face=-1)]),
    S((22, "Click."), "lab", cam=[1.2, 1.25, 960, 620],
      props=[worktable(1350, 0.9)],
      actors=[A(YOU, "hold", "grin", 620, face=1), A(JOY, "sit", "deadpan", 1350, y=870, face=-1)],
      fx=[{"t": "flash", "from": W(22, "Click.", 0.05)}], sfx=[("shutter", W(22, "Click."))]),
    S(23, "lab", cam=[1.35, 1.45, 960, 760], props=[worktable(960, 1.15), cam_on_table(960, 0.8, save=W(23, "Twenty-three"), secs=23)],
      actors=[A(YOU, "stand", "bored", 560, face=1), A(JOY, "stand", "bored", 1380, face=-1)],
      fx=[{"t": "clock_float", "x": 960, "y": 380, "from": W(23, "Twenty-three")}]),
    S(24, "lab", cam=[1.0, 1.1, 1500, 620], actors=[A(YOU, "walk", "happy", 500, walk=[300, 900], face=1)],
      props=[{"t": "tv_pixels", "x": 1450, "y": Y + 20, "s": 1.3, "from": W(24, "slowly"), "to": W(24, "appears.", 0.6), "static": True}]),
    S(25, "lab", cam=TVCAM, props=[TVC], sfx=[("static", W(25, "static."))]),
    S(26, "lab", cam=[1.15, 1.25, 1200, 600],
      props=[{"t": "tv_pixels", "x": 1450, "y": Y + 20, "s": 1.3, "from": 0.0, "to": 0.001, "static": True}],
      actors=[A(JOY, "think", "deadpan", 980, face=1), A(YOU, "stand", "grin", 500, face=1)]),
    S(27, "lab", cam=close(980, 610, 1.8, 1.9),
      props=[{"t": "tv_pixels", "x": 1450, "y": Y + 20, "s": 1.3, "from": 0.0, "to": 0.001, "static": True}],
      actors=[A(JOY, "stand", "deadpan", 980, face=-1)]),
    S(28, "lab", cam=[1.05, 1.05, 960, 620],
      actors=[A(JOY, "walk", "deadpan", 980, walk=[980, -300], face=-1), A(YOU, "stand", "neutral", 1300, face=-1)],
      sfx=["whoosh@0.1"]),
    S(29, "lab", cam=close(1300, 600, 1.55, 1.75), actors=[A(YOU, "cheer", "grin", 1300, face=-1)],
      fx=[{"t": "sparkle", "x": 1300, "y": 420, "from": 0.1}]),
    S((29, "world's", -0.3), "lab", cam=[1.25, 1.3, 1450, 620],
      props=[{"t": "tv_pixels", "x": 1450, "y": Y + 20, "s": 1.3, "from": 0.0, "to": 0.001, "static": True}],
      ov={"t": "title", "title": "FIRST", "sub": "digital photo ever", "pos": "left", "small": True}),
    S(30, "lab", cam=[1.2, 1.3, 900, 620], props=[worktable(900, 1.0)],
      actors=[A(YOU, "think", "worried", 900)], fx=[{"t": "spark", "x": 900, "y": 760, "from": W(30, "wires")}]),
    S((30, "fix", -0.3), "lab", cam=[1.25, 1.35, 1450, 600],
      props=[{"t": "tv_pixels", "x": 1450, "y": Y + 20, "s": 1.3, "from": 0.0, "to": W(30, "there", 0.3)}],
      actors=[A(YOU, "cheer", "joy", 820, face=1)], sfx=["ding@0.55"]),
    S(31, "lab", cam=[1.0, 1.1, 960, 620], actors=[A(YOU, "walk", "smug", 400, walk=[300, 1100])],
      props=[], fx=[{"t": "sparkle", "x": 1100, "y": 400, "from": W(31, "How")}]),

    # ===================================================== 1976: THE MEETING
    S(32, "conf", tr="wipe", where="Kodak, 1976", cam=[1.0, 1.06, 960, 600],
      actors=[A(E1, "stand", "deadpan", 520), A(E2, "stand", "bored", 840), A(E3, "stand", "smug", 1160), A(BOSS, "stand", "neutral", 1480)]),
    S((32, "very"), "conf", cam=[1.35, 1.45, 840, 600],
      actors=[A(E1, "stand", "deadpan", 520), A(E2, "think", "bored", 840), A(E3, "stand", "smug", 1160), A(BOSS, "stand", "neutral", 1480)]),
    S(33, "conf", cam=[1.15, 1.2, 760, 620],
      actors=[A(YOU, "hold", "grin", 420, face=1), A(E1, "stand", "deadpan", 1000, face=-1), A(E2, "stand", "bored", 1300, face=-1), A(E3, "stand", "smug", 1600, face=-1)],
      fx=[{"t": "flash", "from": W(33, "Click.", 0.05)}], sfx=[("shutter", W(33, "Click."))]),
    S(34, "conf", cam=[1.0, 1.08, 1500, 560],
      props=[{"t": "tv_pixels", "x": 1540, "y": Y + 20, "s": 1.2, "from": W(34, "their"), "to": W(34, "TV.", 0.2)}],
      actors=[A(E1, "stand", "shocked", 560, face=1), A(E2, "stand", "shocked", 860, face=1), A(E3, "stand", "neutral", 1160, face=1)]),
    S(35, "conf", cam=close(420, 600, 1.55, 1.7), actors=[A(YOU, "cheer", "grin", 420, face=1)],
      fx=[{"t": "question", "x": 560, "y": 280, "from": W(35, "How")}]),
    S(36, "conf", cam=close(1300, 600, 1.4, 1.55), actors=[A(E2, "stand", "bored", 900, face=-1), A(E1, "think", "deadpan", 1300, face=-1)]),
    S(37, "conf", cam=close(1300, 600, 1.6, 1.7), actors=[A(E1, "shrug", "deadpan", 1300, face=-1)], spk={"B": 0}),
    S(38, "conf", cam=close(900, 600, 1.45, 1.6), actors=[A(E2, "reach", "bored", 900, face=-1), A(E1, "stand", "deadpan", 1300, face=-1)]),
    S(39, "conf", cam=close(900, 600, 1.6, 1.7), actors=[A(E2, "shrug", "worried", 900, face=-1)], spk={"B": 0}),
    S(40, "conf", cam=[1.3, 1.75, 1100, 600], actors=[A(E3, "stand", "smug", 1100, face=-1)], sfx=["thud@0.2"]),
    S(41, "conf", cam=close(1100, 600, 1.75, 1.8), actors=[A(E3, "point", "smug", 1100, face=-1)], spk={"B": 0}),
    S(42, "conf", cam=close(700, 600, 1.6, 1.7), actors=[A(YOU, "shrug", "grin", 700, face=1)]),
    S(43, "conf", cam=[1.0, 1.05, 960, 600],
      actors=[A(E1, "stretch", "happy", 520), A(E2, "stretch", "joy", 840), A(E3, "stand", "grin", 1160), A(BOSS, "cheer", "happy", 1480)]),
    S(44, "conf", cam=[1.1, 1.15, 960, 600],
      actors=[A(E1, "stand", "smug", 400), A(E2, "stand", "smug", 1520)],
      ov={"t": "title", "title": "“That's cute”", "sub": "but don't tell anyone", "pos": "center", "small": True, "delay": W(44, "That's", -0.25)}),

    # ===================================================== THE NAPKIN
    S(45, "exec", cam=[1.05, 1.12, 960, 620],
      actors=[A(E3, "walk", "smug", 1300, walk=[1500, 1150], face=-1), A(YOU, "stand", "worried", 640, face=1)]),
    S(46, "exec", cam=[1.0, 1.06, 960, 520], props=[{"t": "napkin", "x": 960, "y": 500, "s": 1.18, "end": "KODAK", "sign": "- how we get paid",
              "ats": [W(46, "film."), W(46, "chemicals."), W(46, "prints."), W(46, "prints.", 0.6)]}]),
    S((46, "chemicals.", -0.3), "exec", cam=close(1150, 600, 1.45, 1.55),
      actors=[A(E3, "hold", "grin", 1150, face=-1), A(YOU, "stand", "neutral", 640, face=1)], spk={"B": 0}),
    S((46, "prints.", -0.35), "exec", cam=[1.06, 1.1, 960, 520], props=[{"t": "napkin", "x": 960, "y": 500, "s": 1.18, "end": "KODAK", "sign": "- how we get paid",
              "ats": [W(46, "film."), W(46, "chemicals."), W(46, "prints."), W(46, "prints.", 0.6)]}]),
    S(47, "exec", cam=close(1150, 600, 1.45, 1.55),
      actors=[A(E3, "cheer", "grin", 1150, face=-1), A(YOU, "stand", "worried", 640, face=1)], spk={"B": 0},
      fx=[{"t": "coins", "x": 1150, "y": 300, "from": W(47, "paid.", -0.2)}], sfx=["ding@0.8"]),
    S(48, "factory", cam=[1.0, 1.08, 960, 560], actors=[A(E3, "cheer", "grin", 960, s=0.9)],
      fx=[{"t": "coins", "x": 960, "y": 300, "from": 0.1}]),
    S((48, "nineteen", -0.25), "factory", cam=[1.05, 1.1, 960, 560],
      ov={"t": "duo", "head": "Kodak in America, 1976", "a": {"big": "90%", "label": "of film sold"},
          "b": {"big": "~80%", "label": "profit margins"}, "pos": "center", "src": SRC_MARKET}),
    S(49, "exec", cam=close(1150, 600, 1.5, 1.6),
      actors=[A(E3, "point", "smug", 1150, face=-1), A(YOU, "stand", "worried", 640, face=1)], spk={"B": 0}),
    S(50, "exec", cam=close(640, 600, 1.7, 1.8), actors=[A(YOU, "slump", "sad", 640, face=1)]),
    S(51, "exec", cam=[1.25, 1.3, 900, 620],
      actors=[A(E3, "wave", "grin", 1150, face=-1), A(YOU, "slump", "deadpan", 640, face=1)], spk={"B": 0}),
    S(52, "lab", cam=[1.0, 1.06, 960, 700],
      props=[{"t": "drawer", "x": 960, "y": 1020, "s": 0.92, "open": [0.0, 0.12],
              "items": [{"k": "cam", "at": 0.2}], "shut": W(52, "hurt", -0.1)}],
      sfx=["drawer@0.05"]),
    S(53, "conf", cam=[1.1, 1.18, 960, 600],
      actors=[A(E1, "stand", "smug", 600), A(YOU, "stand", "smug", 960), A(E2, "stand", "smug", 1320)]),

    # ===================================================== 1981: THE WARNING
    S(54, "lab", cam=[1.0, 1.04, 960, 700],
      props=[{"t": "drawer", "x": 960, "y": 1020, "s": 0.92, "open": [2.0, 2.1], "items": []}],
      fx=[{"t": "zzz", "x": 1180, "y": 420}]),
    S((54, "Then,"), "shop", tr="wipe", where="1981", cam=[1.05, 1.15, 960, 560],
      props=[{"t": "digicam", "x": 960, "y": 560, "s": 1.1, "label": "SONY"}],
      ov={"t": "title", "title": "Mavica", "sub": "photos on a floppy disk", "pos": "right", "small": True, "delay": W(54, "floppy", -0.6)},
      sfx=["whoosh@0.02"]),
    S(55, "shop", cam=[1.1, 1.2, 960, 620],
      actors=[A(TA, "scared", "worried", 700), A(TB, "stand", "shocked", 1220)], shake=[0.1, 0.3]),
    S((55, "So"), "exec", cam=[1.1, 1.2, 960, 620], where="Vince Barabba, market research",
      actors=[A(VIN, "read", "neutral", 960)]),
    S((55, "Should"), "exec", cam=close(960, 600, 1.55, 1.7), actors=[A(VIN, "think", "worried", 960)],
      fx=[{"t": "question", "x": 1100, "y": 280, "from": 0.05}]),
    S(56, "exec", cam=[1.0, 1.04, 960, 540],
      props=[{"t": "memo", "x": 960, "y": 560, "s": 1.05, "head": "DIGITAL vs FILM", "sub": "Kodak market intelligence, 1981", "lines": []}]),
    S(57, "exec", cam=[1.04, 1.1, 960, 540],
      props=[{"t": "memo", "x": 960, "y": 560, "s": 1.05, "head": "DIGITAL vs FILM", "sub": "Kodak market intelligence, 1981",
              "lines": ["BAD NEWS|Digital could replace film", "GOOD NEWS|About 10 years to get ready"],
              "ats": [W(57, "bad"), W(57, "good")]}]),
    S(58, "conf", cam=[1.0, 1.06, 700, 600],
      actors=[A(E1, "read", "neutral", 520), A(E2, "stand", "bored", 860)],
      ov={"t": "stat", "big": "10", "label": "years' warning, in writing", "src": SRC_MUI, "pos": "right", "delay": 0.05}),
    S(59, "factory", cam=[1.0, 1.08, 960, 600],
      actors=[A(E1, "stand", "happy", 700, s=0.9), A(E2, "stand", "joy", 1200, s=0.9)],
      fx=[{"t": "coins", "x": 960, "y": 300, "from": W(59, "film")}]),
    S(60, "exec", cam=close(960, 600, 1.4, 1.5), actors=[A(E2, "cheer", "joy", 960)], spk={"B": 0},
      fx=[{"t": "confetti", "from": 0.05}],
      ov={"t": "stat", "big": "$10B", "label": "Kodak sales, 1981", "src": SRC_WHARTON, "pos": "right", "delay": 0.1}),
    S(61, "lab", cam=[1.0, 1.06, 960, 700],
      props=[{"t": "drawer", "x": 960, "y": 1020, "s": 0.92, "open": [0.0, 0.15],
              "items": [{"k": "cam"}, {"k": "memo", "at": 0.3}], "shut": W(61, "toaster.", 0.1)}],
      sfx=["drawer@0.02"]),
    S(62, "lab", tod="dusk", cam=[1.15, 1.22, 960, 620], props=[worktable(960, 1.1)],
      actors=[A(YOU, "think", "neutral", 760, face=1)],
      fx=[{"t": "clock_float", "x": 1250, "y": 300, "from": W(62, "Year")}]),

    # ===================================================== THE LOSING YEARS
    S(63, "shop", tr="wipe", where="1990s", cam=[1.05, 1.12, 960, 560],
      props=[{"t": "digicam", "x": 960, "y": 560, "s": 1.15, "label": "KODAK", "tag": "$20,000", "at": W(63, "twenty")}]),
    S(64, "shop", cam=close(800, 600, 1.7, 1.85), actors=[A(YOU, "scared", "shocked", 800)], sfx=["pop@0.05"]),
    S(65, "street", cam=[1.0, 1.15, 960, 600],
      actors=[A(TA, "walk", "happy", 300, walk=[100, 1400]), A(TB, "walk", "grin", 0, walk=[-300, 1100])], sfx=["whoosh@0.3"]),
    S(66, "office", where="2001", cam=[1.0, 1.08, 1200, 560],
      props=[{"t": "photo_app", "x": 1250, "y": 520, "s": 0.95, "label": "OFOTO"}],
      actors=[A(E3, "point", "grin", 520, face=1)]),
    S(67, "office", cam=[1.05, 1.1, 960, 620], actors=[A(TA, "phone", "happy", 620), A(TB, "phone", "joy", 1300)],
      fx=[{"t": "hearts", "x": 960, "y": 360, "from": 0.2}]),
    S((67, "grows", -0.3), "office", cam=[1.05, 1.12, 1200, 560],
      props=[{"t": "photo_app", "x": 1250, "y": 520, "s": 0.95, "label": "KODAK GALLERY", "badge": "75 MILLION USERS"}],
      ov={"t": "title", "title": "2001", "sub": "Instagram: 2010", "pos": "left", "small": True, "delay": W(67, "Years", -0.2)}),
    S(68, "exec", cam=[1.2, 1.4, 960, 600], actors=[A(E3, "stand", "smug", 960)]),
    S(69, "exec", cam=close(960, 600, 1.55, 1.6), actors=[A(E3, "point", "grin", 960)], spk={"B": 0}, sfx=["ding@0.7"]),
    S(70, "shop", where="2005", cam=[1.05, 1.12, 960, 560],
      props=[{"t": "digicam", "x": 960, "y": 560, "s": 1.15, "label": "KODAK"}],
      fx=[{"t": "confetti", "from": W(70, "Number")}],
      ov={"t": "title", "title": "#1", "sub": "US digital cameras", "pos": "left", "small": True, "delay": W(70, "Number", -0.3)}),
    S(71, "exec", cam=[1.1, 1.15, 960, 600], actors=[A(E1, "cheer", "joy", 700), A(E2, "cheer", "joy", 1220)]),
    S((71, "Harvard", -0.3), "shop", cam=[1.05, 1.12, 700, 560],
      props=[{"t": "digicam", "x": 620, "y": 560, "s": 1.1, "label": "KODAK", "tag": "-$60", "at": W(71, "losing")}],
      ov={"t": "stat", "big": "-$60", "label": "on every digital camera sold", "src": "Source: Harvard case study, via PetaPixel 2018", "pos": "right", "delay": W(71, "sixty", -0.3)}),
    S(72, "exec", cam=close(960, 600, 1.6, 1.7), actors=[A(E2, "scared", "shocked", 960)], spk={"B": 0}, shake=[0.2, 0.35]),
    S(73, "exec", cam=[1.0, 1.06, 960, 520],
      props=[{"t": "napkin", "x": 960, "y": 500, "s": 1.18, "end": "KODAK", "labels": ["DIGITAL", "FILM", "CHEMICALS", "PRINTS"],
              "ats": [0.0, 0.0, 0.0, 0.0], "broken": W(73, "nowhere", -0.3)}],
      sfx=["buzzer@0.8"]),
    S(74, "factory", cam=[1.0, 1.06, 960, 560], actors=[A(E1, "stand", "worried", 700, s=0.9)],
      ov={"t": "stat", "big": "72%", "count": True, "label": "of Kodak's revenue came from film", "sub": "in 2000", "src": SRC_PETA, "pos": "right", "delay": W(74, "In", -0.2)}),
    S((74, "Ten"), "factory", cam=[1.06, 1.12, 960, 560],
      ov={"t": "duo", "head": "World demand for camera film", "a": {"big": "100%", "label": "in 2000"}, "b": {"big": "<10%", "label": "in 2010"}, "pos": "center", "src": SRC_PETA}),
    S(75, "street", cam=[1.0, 1.1, 960, 600],
      actors=[A(TA, "phone", "happy", 380), A(TB, "phone", "grin", 760), A(K1, "phone", "joy", 1140, s=0.8), A(FUJI, "phone", "happy", 1520)],
      fx=[{"t": "sparkle", "x": 960, "y": 300, "from": W(75, "everyone")}]),
    S(76, "living", tod="day", where="2000s", cam=[1.25, 1.4, 960, 470],
      actors=[A(OLD, "sit", "smug", **COUCH)], fx=[{"t": "sparkle", "x": 960, "y": 280, "from": W(76, "You.")}]),
    S((76, "Your"), "living", tod="day", cam=[1.05, 1.1, 960, 560],
      actors=[A(OLD, "sit", "grin", **COUCH), A(K1, "cheer", "joy", 520, s=0.7), A(K2, "wave", "joy", 1400, s=0.7)],
      fx=[{"t": "hearts", "x": 960, "y": 300, "from": 0.05, "until": W(76, "For")},
          {"t": "clock_float", "x": 1300, "y": 300, "from": W(76, "For")}]),

    # ===================================================== BACK TO 2012
    S(77, "living", tr="fade", where="January 2012", cam=[1.2, 1.35, 960, 520], actors=[A(OLD, "sit", "sad", **COUCH)]),
    S(78, "living", cam=[1.0, 1.06, 700, 520],
      props=[{"t": "news_bg", "x": 960, "y": 540, "box": "KODAK", "stamp": "1,100 PATENTS"},
             {"t": "news_fg", "x": 960, "y": 540, "front": True, "head": "KODAK FAILED TO SELL ITS PATENTS IN TIME",
              "ticker": "About 1,100 digital imaging patents   •   " + SRC_DC[8:] + "   •"}],
      actors=[A(ANC, "stand", "neutral", 640, 960, s=1.35)]),
    S(79, "shop", cam=[1.05, 1.15, 960, 560],
      props=[{"t": "digicam", "x": 960, "y": 560, "s": 1.15, "label": "KODAK"}],
      fx=[{"t": "fail", "x": 960, "y": 560, "from": W(79, "stops")}], sfx=["buzzer@0.35"]),
    S(80, "office", cam=[1.0, 1.06, 1400, 560],
      props=[{"t": "photo_app", "x": 1480, "y": 520, "s": 0.95, "label": "KODAK GALLERY", "badge": "75 MILLION USERS"}],
      ov={"t": "stat", "big": "$23.8M", "label": "what Kodak sold it for", "src": SRC_AP, "pos": "left", "delay": W(80, "Kodak", -0.2)}),
    S(81, "startup", cam=[1.0, 1.08, 960, 600],
      actors=[A(TA, "cheer", "joy", 420), A(TB, "cheer", "grin", 780), A(K1, "wave", "joy", 1140), A(FUJI, "stand", "happy", 1500)],
      fx=[{"t": "confetti", "from": W(81, "billion")}],
      ov={"t": "stat", "big": "$1B", "label": "Instagram, 13 employees", "src": SRC_FB, "pos": "center", "delay": W(81, "one", -0.2)}),
    S(82, "living", cam=close(960, 470, 1.8, 1.95), actors=[A(OLD, "sit_look", "shocked", **COUCH)], sfx=["pop@0.05"]),
    S(83, "lab", tod="sepia", cam=[1.0, 1.06, 960, 700],
      props=[{"t": "drawer", "x": 960, "y": 1020, "s": 0.92, "open": [0.0, 0.2], "items": [{"k": "cam"}, {"k": "memo"}], "label": "EXPIRED"}],
      ov={"t": "title", "title": "1995", "sub": "patent ran out", "pos": "right", "small": True, "delay": W(83, "ran", -0.2)}),

    # ===================================================== FUJIFILM
    S(84, "factory", tr="wipe", where="Meanwhile, in Tokyo", cam=[1.0, 1.08, 960, 600],
      actors=[A(FUJI, "stand", "worried", 960)], shake=[0.6, 0.85],
      fx=[{"t": "fail", "x": 1300, "y": 420, "from": W(84, "collapsed")}]),
    S(85, "exec", cam=[1.15, 1.25, 960, 600], actors=[A(FUJI, "think", "neutral", 960)],
      fx=[{"t": "bulb", "x": 1060, "y": 270, "from": W(85, "good", -0.3)}]),
    S(86, "lab", cam=[1.05, 1.1, 960, 600], actors=[A(FUJI, "cheer", "joy", 560, face=1)],
      ov={"t": "checklist", "items": ["Chemistry", "Medical imaging", "Materials", "Face cream"], "pos": "right", "w": 820,
          "ats": [W(86, "chemistry."), W(86, "medical"), W(86, "materials,"), W(86, "face")]}),
    S((86, "Over"), "exec", cam=[1.05, 1.1, 960, 560],
      ov={"t": "duo", "head": "Revenue, 2000 to 2010", "a": {"big": "+57%", "label": "Fujifilm"}, "b": {"big": "-48%", "label": "Kodak"}, "pos": "center", "src": SRC_PETA}),

    # ===================================================== THE ANSWER
    S(87, "conf", cam=[1.0, 1.05, 960, 600],
      ov={"t": "rules", "items": ["Not stupidity", "Not money", "Not ideas"], "pos": "center",
          "ats": [W(87, "stupidity"), W(87, "money"), W(87, "ideas")]}),
    S((87, "invented", -0.45), "lab", tod="sepia", cam=[1.25, 1.4, 960, 720], props=[worktable(960, 1.15), cam_on_table(960, 0.8)],
      fx=[{"t": "sparkle", "x": 960, "y": 640, "from": 0.05}]),
    S(88, "lab", tod="sepia", cam=[1.0, 1.06, 960, 700],
      props=[{"t": "drawer", "x": 960, "y": 1020, "s": 0.92, "open": [0.0, 0.01], "items": [{"k": "cam"}, {"k": "memo"}], "shut": W(88, "Film", -0.1)}],
      sfx=["drawer@0.5"]),
    S((88, "Film"), "factory", cam=[1.0, 1.1, 960, 560],
      ov={"t": "title", "title": "THE TRAP", "sub": "protecting what pays", "pos": "center", "small": True}),

    # ===================================================== ENDING
    S(89, "living", cam=[1.2, 1.35, 960, 520], actors=[A(OLD, "sit", "sad", **COUCH)],
      fx=[{"t": "thought", "x": 1180, "y": 240, "from": W(89, "Joy's")}]),
    S(90, "lab", tod="sepia", cam=close(980, 610, 1.8, 1.9), actors=[A(JOY, "stand", "deadpan", 980, face=-1)]),
    S(91, "lab", tod="sepia", cam=TVCAM, props=[TVC]),
    S((91, "could", -0.35), "living", cam=[1.35, 1.5, 960, 470], actors=[A(OLD, "sit", "deadpan", **COUCH)]),
    S(92, "lab", tr="fade", cam=[1.1, 1.2, 700, 650], props=[worktable(720, 1.1), cam_on_table(720, 0.75)],
      actors=[A(YOU, "stand", "happy", 330, face=1)],
      ov={"t": "title", "title": "Steve Sasson", "sub": "built it at 24", "pos": "right", "small": True, "delay": W(92, "Steve", -0.3)}),
    S((92, "put", -0.5), "lab", cam=[1.0, 1.05, 960, 700],
      props=[{"t": "drawer", "x": 960, "y": 1020, "s": 0.92, "open": [0.0, 0.01], "items": [{"k": "cam"}], "shut": 0.6}],
      sfx=["drawer@0.6"]),
    S(93, "living", cam=[1.0, 1.08, 960, 700],
      props=[{"t": "drawer", "x": 960, "y": 1020, "s": 0.92, "open": [0.1, 0.4], "items": [{"k": "bulb"}], "label": "YOU"}],
      fx=[{"t": "sparkle", "x": 960, "y": 520, "from": 0.4}]),
    S((93, "Tell"), "living", cam=[1.05, 1.1, 960, 560], actors=[A(OLD, "wave", "grin", 960)],
      fx=[{"t": "speech", "x": 1300, "y": 330, "from": 0.1, "text": "Comment below!"}]),
    S(END_AT - 0.1, "living", tr="fade", cam=[1.0, 1.04, 960, 560], actors=[A(OLD, "wave", "happy", 960)],
      ov={"t": "end", "title": "The If Lab", "next": "What if you'd bought Bitcoin in 2010?", "pos": "center"}),
]


# ---------------------------------------------------------------------------------------- resolve
def _resolve(v, a, b):
    if isinstance(v, W):
        return round(min(1.0, (v.t - a) / (b - a)), 4)  # below 0: it happened before the cut
    if isinstance(v, dict):
        return {k: _resolve(x, a, b) for k, x in v.items()}
    if isinstance(v, list):
        return [_resolve(x, a, b) for x in v]
    return v


def build():
    shots = sorted(SHOTS, key=lambda s: s["t0"])
    shots[0]["t0"] = 0.0
    out, scenes = [], []
    for k, sh in enumerate(shots):
        a = sh["t0"]
        b = shots[k + 1]["t0"] if k + 1 < len(shots) else TOTAL
        assert b - a > 0.45, f"shot {k} too short: {b - a:.2f}s ({sh['set']})"
        sh = {key: val for key, val in sh.items() if key not in ("t0",)}
        spk = sh.pop("spk", {})
        actors = sh.get("actors", [])
        # mouths: every non-narrator line that overlaps this shot
        speak = []
        for i, ln in enumerate(LINES):
            if ln["who"] == "N":
                continue
            s, e = max(START[i], a), min(line_end(i), b)
            if e - s < 0.1:
                continue
            idx = spk.get(ln["who"])
            if idx is None:
                idx = next((j for j, ac in enumerate(actors) if ac["who"] in SPEAKERS[ln["who"]]), None)
            if idx is None:
                continue
            speak.append({"a": idx, "s": round(s - a, 3), "e": round(e - a, 3)})
        if speak:
            sh["speak"] = speak
        sh["sfx"] = [x if isinstance(x, str) else f"{x[0]}@{max(0.0, (x[1].t - a) / (b - a)):.3f}" for x in sh.get("sfx", [])]
        sh = _resolve(sh, a, b)
        sh["id"] = f"s{k:03d}"
        sh["n"] = ""
        out.append(sh)
        scenes.append({"id": sh["id"], "start_ms": round(a * 1000), "end_ms": round(b * 1000)})
    timing = {"total_sec": TOTAL, "scenes": scenes}
    plan = [{"i": i, "who": ln["who"], "src": ln["src"], "src_start": ln["src_start"], "dur": ln["dur"], "at": START[i]} for i, ln in enumerate(LINES)]
    return out, timing, plan


if __name__ == "__main__":
    shots, timing, plan = build()
    props = {"shots": shots, "timing": timing, "words": caption_words()}
    (WORK / "props.json").write_text(json.dumps(props))
    (WORK / "audio_plan.json").write_text(json.dumps({"total_sec": TOTAL, "lines": plan}, indent=1))
    lens = [(sc["end_ms"] - sc["start_ms"]) / 1000 for sc in timing["scenes"]]
    print(f"{len(shots)} shots, {TOTAL:.1f}s ({TOTAL / 60:.2f} min); shot length min {min(lens):.2f}s, "
          f"mean {sum(lens) / len(lens):.2f}s, max {max(lens):.2f}s")
    for sc, ln in zip(timing["scenes"], lens, strict=True):
        if ln > 7.5:
            print("  long:", sc["id"], round(ln, 2))
