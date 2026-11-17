"""Four vertical Shorts cut from the POV Kodak episode, each opening on a new spoken hook.

usage: python3 episodes/kodak-pov/shorts.py      (after shots.py) -> work/shorts/s<k>/props.json, audio_plan.json

A Short is: a hook shot (a new line in the narrator's voice, from the "hooks" take) followed by one or
two runs of whole shots from the long video, so every shot keeps its own timing and animation. The
last line of each sets up the first, so the Short loops.
"""

import json
from pathlib import Path

from shots import END_AT, LINES, START, TVC, TVCAM, A, caption_words

HERE = Path(__file__).parent
WORK = HERE / "work"
LONG = json.loads((WORK / "props.json").read_text())
HOOKS = json.loads((HERE / "data" / "voice_hooks.json").read_text())  # vidIQ result: lines [{startSeconds, durationSeconds}]
LEAD = 0.25
GAP = 0.35

SHORTS = [
    {
        "hook": 0,
        "shot": dict(set="img:lab", chibi=True, cam=TVCAM, props=[dict(TVC)], sfx=["static@0.05"]),
        "runs": [(20, 29)],
        "title": ["THE FIRST DIGITAL", "PHOTO HAD NO FACE"],
        "highlight": ["FACE"],
    },
    {
        "hook": 1,
        "shot": dict(set="img:conf", chibi=True, cam=[1.05, 1.12, 960, 600],
                     actors=[A("eng", "hold", "grin", 420, face=1), A("exec1", "stand", "deadpan", 1000, face=-1),
                             A("exec2", "stand", "bored", 1300, face=-1), A("exec3", "stand", "smug", 1600, face=-1)],
                     sfx=["thud@0.7"]),
        "runs": [(33, 44)],
        "title": ["KODAK SAW THE", "FUTURE IN 1976"],
        "highlight": ["1976"],
    },
    {
        "hook": 2,
        "shot": dict(set="img:exec", chibi=True, cam=[1.0, 1.06, 960, 520],
                     props=[{"t": "napkin", "x": 960, "y": 500, "s": 1.18, "end": "KODAK", "sign": "- how we get paid", "ats": [0, 0, 0, 0]}],
                     sfx=["pop@0.05"]),
        "runs": [(45, 52)],
        "title": ["WHY KODAK HID", "ITS OWN INVENTION"],
        "highlight": ["HID"],
    },
    {
        "hook": 3,
        "shot": dict(set="img:office", chibi=True, cam=[1.0, 1.08, 1200, 560],
                     props=[{"t": "photo_app", "x": 1250, "y": 520, "s": 0.95, "label": "KODAK GALLERY", "badge": "75 MILLION USERS"}],
                     actors=[A("techa", "phone", "happy", 520)], sfx=["ding@0.1"]),
        "runs": [(66, 69), (80, 82)],
        "title": ["KODAK HAD", "INSTAGRAM FIRST"],
        "highlight": ["FIRST"],
    },
]


def _run_span(first, last):
    """Whole shots: from the cut before line `first` to the cut after line `last`."""
    scenes = LONG["timing"]["scenes"]
    a = START[first] - 0.18
    nxt = START[last + 1] - 0.18 if last + 1 < len(LINES) else END_AT
    idx = [k for k, sc in enumerate(scenes) if sc["start_ms"] / 1000 >= a - 0.01 and sc["start_ms"] / 1000 < nxt - 0.01]
    s0 = scenes[idx[0]]["start_ms"] / 1000
    s1 = scenes[idx[-1]]["end_ms"] / 1000
    return idx, s0, s1


def build(k, spec):
    hook = HOOKS["lines"][spec["hook"]]
    hdur = hook["durationSeconds"]
    shots, scenes, plan, caps = [], [], [], []
    t = 0.0
    h_end = LEAD + hdur + GAP
    shots.append({**spec["shot"], "id": "h", "n": ""})
    scenes.append({"id": "h", "start_ms": 0, "end_ms": round(h_end * 1000)})
    plan.append({"src": "hooks", "src_start": hook["startSeconds"], "dur": hdur, "at": LEAD})
    # hook captions, spread by word length
    words = HOOK_TEXT[spec["hook"]].split()
    tot = sum(len(w) + 2 for w in words)
    acc = LEAD
    for w in words:
        d = hdur * 0.94 * (len(w) + 2) / tot
        caps.append({"text": w, "start_ms": round(acc * 1000), "end_ms": round((acc + d * 0.85) * 1000)})
        acc += d
    t = h_end
    all_words = caption_words()
    for first, last in spec["runs"]:
        idx, s0, s1 = _run_span(first, last)
        off = t - s0
        for j in idx:
            sh = dict(LONG["shots"][j])
            sh.pop("where", None)  # no room for the place tag in the vertical frame
            sc = LONG["timing"]["scenes"][j]
            shots.append(sh)
            scenes.append({"id": sh["id"], "start_ms": round(sc["start_ms"] + off * 1000), "end_ms": round(sc["end_ms"] + off * 1000)})
        for i in range(first, last + 1):
            ln = LINES[i]
            plan.append({"src": ln["src"], "src_start": ln["src_start"], "dur": ln["dur"], "at": round(START[i] + off, 3)})
        for w in all_words:
            if s0 <= w["s"] < s1:
                caps.append({"text": w["w"], "start_ms": round((w["s"] + off) * 1000), "end_ms": round((w["e"] + off) * 1000)})
        t = s1 + off
    total = round(t + 0.2, 3)
    scenes[-1]["end_ms"] = round(total * 1000)
    words_ = [{"word": c["text"], "start_ms": c["start_ms"], "end_ms": c["end_ms"]} for c in caps]
    props = {"shots": shots, "timing": {"total_sec": total, "scenes": scenes}, "words": words_, "caps": caps,
             "title": spec["title"], "highlight": spec["highlight"], "brand": "THE IF LAB"}
    out = WORK / "shorts" / f"s{k + 1}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "props.json").write_text(json.dumps(props))
    (out / "audio_plan.json").write_text(json.dumps({"total_sec": total, "lines": plan}, indent=1))
    return total


HOOK_TEXT = [
    "The first digital photo in history had no face. And the woman in it said two words.",
    "You just showed Kodak the first digital camera. Their first question was a disaster.",
    "You invented the digital camera. A Kodak executive explained on a napkin why it had to disappear.",
    "Kodak had Instagram before Instagram existed. 75 million users. Wait till you hear what it sold for.",
]

if __name__ == "__main__":
    for k, spec in enumerate(SHORTS):
        print(f"short {k + 1}: {build(k, spec):.1f}s")
