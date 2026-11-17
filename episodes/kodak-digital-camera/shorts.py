"""Four vertical Shorts cut from the Kodak episode, each with a new spoken first line and its own on-screen title.

usage: python3 episodes/kodak-digital-camera/shorts.py work/shots.json work/shorts/
Writes work/shorts/s<k>/shots.json for each Short (voice them with tools/episode/voice_vo.py).
Each stands alone, opens on its surprise, and ends on a line that sends the viewer back to the start.
"""

import copy
import json
import sys
from pathlib import Path

Y = 1000


def p(who, pose="stand", expr="neutral", x=960, **kw):
    return {"who": who, "pose": pose, "expr": expr, "x": x, "y": kw.pop("y", Y), **kw}


SHORTS = [
    {
        "hook": dict(
            id="h1",
            n="In nineteen seventy-five, an engineer built this in Kodak's lab. Kodak decided nobody should see it.",
            set="lab", setopt={"sign": "KODAK"}, tod="sepia", cam=[1.0, 1.08, 1100, 560],
            actors=[p("leo", "point", "happy", 560)],
            props=[{"t": "proto_cam", "x": 1220, "y": 705, "s": 0.95}],
            fx=[{"t": "sparkle", "x": 1220, "y": 360, "from": 0.1}, {"t": "fail", "x": 1220, "y": 300, "from": 0.62, "text": "SECRET", "tilt": -6}],
            sfx=["ding@0.1", "thud@0.63"],
        ),
        "beats": ["s02", "s03", "s04", "s05", "s06"],
        "title": ["KODAK BUILT IT", "THEN HID IT"],
        "highlight": ["HID"],
        "youtube_title": "Kodak Built the First Digital Camera, Then Hid It #shorts",
        "caption": "1975: a 24-year-old Kodak engineer builds the first digital camera. 8 pounds, 23 seconds per photo. "
        "His bosses' reaction, as he remembers it: \"that's cute, but don't tell anyone.\" 37 years later, Kodak was bankrupt. "
        "Would you have shipped it? 👇",
        "hashtags": ["#kodak", "#businessstory", "#digitalcamera", "#history", "#startup"],
    },
    {
        "hook": dict(
            id="h2",
            n="Seventy-five million people shared photos on a website Kodak owned. You've probably never heard of it.",
            set="studio", cam=[1.0, 1.06],
            actors=[p("you", "scared", "shocked", 560)],
            props=[{"t": "photo_app", "x": 1250, "y": 490, "s": 0.95, "label": "KODAK GALLERY", "badge": "75 MILLION USERS"}],
            sfx=["pop@0.1", "ding@0.5"],
        ),
        "beats": ["s33", "s34", "s35", "s36"],
        "title": ["KODAK HAD", "INSTAGRAM FIRST"],
        "highlight": ["FIRST"],
        "youtube_title": "Kodak Had Its Own Instagram. It Sold It for $23.8M #shorts",
        "caption": "Kodak bought a photo-sharing site in 2001 and grew it to 75 million users. In 2012 Instagram sold for "
        "$1 billion with 13 employees. The same spring, bankrupt Kodak sold its site for $23.8 million. "
        "Same idea, very different ending. Which one would you have bought? 👇",
        "hashtags": ["#kodak", "#instagram", "#business", "#startup", "#tech"],
    },
    {
        "hook": dict(
            id="h3",
            n="In nineteen eighty-one, Kodak got a warning about digital cameras. In writing. With a deadline.",
            set="studio", cam=[1.0, 1.08],
            props=[{"t": "memo", "x": 960, "y": 560, "s": 1.05, "head": "DIGITAL vs FILM", "sub": "Kodak market intelligence, 1981",
                    "lines": ["BAD NEWS|digital can replace film"], "stamp": "WARNING", "at": 0.6}],
            sfx=["flip@0.05", "thud@0.62"],
        ),
        "beats": ["s17", "s18", "s19", "s20", "s21", "s23"],
        "title": ["THEY KNEW", "10 YEARS EARLY"],
        "highlight": ["KNEW"],
        "youtube_title": "Kodak Was Warned 10 Years Early. Here's What It Did #shorts",
        "caption": "1981: Kodak's own market research said digital could replace film, and that Kodak had roughly ten years "
        "to get ready. The film business was too good to disturb. What would you have done with those ten years? 👇",
        "hashtags": ["#kodak", "#business", "#strategy", "#history", "#entrepreneur"],
    },
    {
        "hook": dict(
            id="h4",
            n="Two film giants faced the same disaster. One went bankrupt. The other started selling face cream.",
            set="studio", cam=[1.0, 1.06],
            actors=[p("sam", "slump", "sad", 520)],
            props=[{"t": "cream", "x": 1330, "y": 600, "s": 0.85, "label": "ASTALIFT"}],
            fx=[{"t": "fail", "x": 520, "y": 380, "from": 0.3, "text": "BANKRUPT", "tilt": -6}],
            sfx=["thud@0.31", "ding@0.7"],
        ),
        "beats": ["s37", "s38", "s39", "s40", "s41"],
        "title": ["SAME DISASTER", "OPPOSITE ENDINGS"],
        "highlight": ["OPPOSITE"],
        "youtube_title": "Why Fujifilm Survived and Kodak Didn't #shorts",
        "caption": "Film demand collapsed for both of them. Kodak protected its product. Fujifilm asked what it was good at, "
        "and took its chemistry into skincare, medical imaging and materials. Over 2000-2010 its revenue grew 57%; "
        "Kodak's fell 48%. What's your company's hidden skill? 👇",
        "hashtags": ["#kodak", "#fujifilm", "#business", "#strategy", "#reinvention"],
    },
]

if __name__ == "__main__":
    long = {s["id"]: s for s in json.loads(Path(sys.argv[1]).read_text())["shots"]}
    out = Path(sys.argv[2])
    for k, sh in enumerate(SHORTS, 1):
        picked = [sh["hook"]]
        for sid in sh["beats"]:
            c = copy.deepcopy(long[sid])
            c["tr"] = "punch"
            c.pop("where", None)  # the vertical frame has no room for the place tag
            picked.append(c)
        d = out / f"s{k}"
        d.mkdir(parents=True, exist_ok=True)
        meta = {key: v for key, v in sh.items() if key not in ("hook", "beats")}
        json.dump({"title": sh["youtube_title"], "shots": picked, "chapters": [], **meta}, open(d / "shots.json", "w"), indent=1)
        print(k, len(picked), "shots", sum(len(s["n"].split()) for s in picked), "words")
