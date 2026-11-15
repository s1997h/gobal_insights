"""Captions (SRT), chapters and the upload text for the episode.

usage: python3 tools/episode/package.py shots.json audio/timing.json audio/words.json out/
The description text below is written for the phone episode; edit it per episode.
"""

import json
import sys
from pathlib import Path

shots = json.loads(Path(sys.argv[1]).read_text())["shots"]
timing = json.loads(Path(sys.argv[2]).read_text())
words = json.loads(Path(sys.argv[3]).read_text())
out = Path(sys.argv[4])
out.mkdir(parents=True, exist_ok=True)
start = {s["id"]: s["start_ms"] / 1000 for s in timing["scenes"]}


def ts(sec, srt=True):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return (
        f"{h:02d}:{m:02d}:{s:02d},{ms:03d}" if srt else (f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}")
    )


# ---- captions: cues of up to 42 characters, broken after punctuation where possible
cues, cur = [], []
for w in words:
    cur.append(w)
    text = " ".join(x["word"] for x in cur)
    end_punct = w["word"][-1] in ".?!"
    soft = w["word"][-1] in ",;:"
    if end_punct or len(text) >= 38 or (soft and len(text) >= 22):
        cues.append(cur)
        cur = []
if cur:
    cues.append(cur)
lines = []
for i, c in enumerate(cues, 1):
    a = c[0]["start_ms"] / 1000
    b = max(c[-1]["end_ms"] / 1000, a + 0.8)
    if i < len(cues):
        b = min(b + 0.15, cues[i][0]["start_ms"] / 1000)
    lines += [str(i), f"{ts(a)} --> {ts(b)}", " ".join(x["word"] for x in c), ""]
(out / "captions.srt").write_text("\n".join(lines))

# ---- chapters
CHAPTERS = json.loads(Path(sys.argv[1]).read_text()).get("chapters", [])
chap = "\n".join(f"{ts(start[i], srt=False)} {name}" for i, name in CHAPTERS)

title = "What If You Quit Your Phone for 30 Days?"
description = f"""You check your phone about 186 times a day. So what actually happens if you lock it in a drawer for 30 days? We follow your brain day by day, from the first reach for an empty nightstand to the boredom wall on day 4, the 2025 study that found two weeks without mobile internet gave people the attention of someone ten years younger, and what's waiting in the drawer on day 30.

Which day would you quit on? Day 1, day 4 or day 14? Tell us in the comments.

CHAPTERS
{chap}

SOURCES
- Castelo, Kushlev, Ward, Esterman & Reiner (2025). Blocking mobile internet on smartphones improves sustained attention, mental health, and subjective well-being. PNAS Nexus 4(2). https://doi.org/10.1093/pnasnexus/pgaf017
- Reviews.org, Cell Phone Usage Stats 2026 (survey of ~1,000 US adults, Q4 2025): 186 checks a day, 84.6% check within 10 minutes of waking, 67.9% use their phone on the toilet. https://www.reviews.org/mobile/cell-phone-addiction/
- Reviews.org, Screen Time and Internet Usage Statistics 2026: about 4 hours a day on smartphones. https://www.reviews.org/internet-service/internet-screen-time-statistics/
- Cheever, Rosen, Carrier & Chavez (2014). Out of sight is not out of mind: The impact of restricting wireless mobile device use on anxiety levels among low, moderate and high users. Computers in Human Behavior 37, 290-297.
- Drouin, Kaiser & Miller (2012). Phantom vibrations among undergraduates: Prevalence and associated psychological characteristics. Computers in Human Behavior 28(4), 1490-1496.
- Hjetland, Skogen, Hysing, Gradisar & Sivertsen (2025). How and when screens are used: comparing different screen activities and sleep in Norwegian university students. Frontiers in Psychiatry. https://doi.org/10.3389/fpsyt.2025.1548273
- Mark, G. Attention Span (2023), and Mark, Gonzalez & Harris, No Task Left Behind? (CHI 2005): time on one screen fell from about 2.5 minutes (2004) to 47 seconds; about 25 minutes to return to an interrupted task.

This video is for general information, not medical advice.
This video uses AI-generated narration and visuals.

#WhatIf #DigitalDetox #Psychology"""

tags = [
    "what if you quit your phone",
    "quit phone for 30 days",
    "30 days without phone",
    "digital detox",
    "phone addiction",
    "screen time",
    "what happens if you stop using your phone",
    "dopamine detox",
    "phantom vibration",
    "attention span",
    "what if",
    "what if animated",
    "smartphone addiction",
    "no phone challenge",
    "brain without phone",
]

(out / "upload.md").write_text(
    f"# Upload kit\n\n## Title\n{title}\n\n## Thumbnail text\nDAY 4...\n\n## Description\n\n{description}\n\n## Tags\n{', '.join(tags)}\n"
)
(out / "description.txt").write_text(description)
print(chap)
print(f"{len(cues)} caption cues; tags {len(', '.join(tags))} chars")
