"""Engagement gate: the retention checks a careful editor would run, as numbers.

None of this predicts views. It catches the known ways a script leaks viewers: a slow or vague
opening, no open question, long stretches that stop talking to the viewer, chapters that begin
without a reason to stay, and an ending with no ask.
"""

from __future__ import annotations

import re
from typing import Any

from .schemas import EpisodeScript

WPS = 2.6  # narration words per second, for estimating time from text
_YOU = re.compile(r"\byou(r|rs|'re|'ve|'d|'ll)?\b", re.I)
_STAKES = re.compile(
    r"\b(fail|failed|lose|lost|stop|stopped|broke|crash|collapse|never|nobody|only|last|survive|worth|free|empty|gone|ban|shut)\w*",
    re.I,
)
_REHOOK = re.compile(
    r"\?|\b(but|twist|turns|until|except|remember|worse|strange|real one|here's|suddenly|only|then)\b", re.I
)


def hook_score(text: str) -> dict[str, int]:
    """0-100 on five properties of an opening line, and their average."""
    words = text.split()
    n = len(words)
    numbers = len(
        re.findall(
            r"\d|\b(one|two|three|four|five|six|seven|eight|nine|ten|twenty|thirty|hundred|thousand|million|billion)\b",
            text,
            re.I,
        )
    )
    specificity = min(
        100,
        35
        + 25 * numbers
        + (15 if re.search(r"\b(AM|PM|o'clock|tomorrow|tonight|today|morning|night)\b", text, re.I) else 0),
    )
    address = min(100, 40 * len(_YOU.findall(text)) + 20)
    stakes = min(100, 30 + 30 * len(_STAKES.findall(text)))
    curiosity = min(
        100,
        30
        + (40 if "?" in text else 0)
        + (30 if re.search(r"\b(what if|why|how|until|but)\b", text, re.I) else 0),
    )
    brevity = 100 if 9 <= n <= 24 else max(10, 100 - 9 * (9 - n if n < 9 else n - 24))
    total = round((specificity + address + stakes + curiosity + brevity) / 5)
    return {
        "specificity": specificity,
        "address": address,
        "stakes": stakes,
        "curiosity": curiosity,
        "brevity": brevity,
        "total": total,
    }


def audit(script: EpisodeScript) -> dict[str, Any]:
    """Metrics plus `fixes`: plain-language rewrites to ask the writer for. No fixes means the gate is passed."""
    beats = script.beats
    counts = [len(b.say.split()) for b in beats]
    total = sum(counts)
    text = " ".join(b.say for b in beats)

    first15: list[str] = []
    acc = 0
    for b, c in zip(beats, counts, strict=True):
        if acc / WPS < 15:
            first15.append(b.say)
        acc += c
    hook = hook_score(beats[0].say)

    run = worst = 0
    worst_at = 0
    for i, (b, c) in enumerate(zip(beats, counts, strict=True)):
        if _YOU.search(b.say):
            run = 0
        else:
            run += c
            if run > worst:
                worst, worst_at = run, i + 1
    chapter_beats = [b for b in beats if b.chapter]
    rehooked = sum(1 for b in chapter_beats if b.clock or _REHOOK.search(b.say))
    payoff_sec = sum(counts[: script.payoff_beat - 1]) / WPS
    cards = sum(1 for b in beats if b.view not in ("scene", "object"))
    same_view = longest = 1
    for a, b in zip(beats, beats[1:], strict=False):
        same_view = same_view + 1 if a.view == b.view and a.view in ("stat", "title", "list") else 1
        longest = max(longest, same_view)

    m: dict[str, Any] = {
        "words": total,
        "beats": len(beats),
        "est_minutes": round(total / WPS / 60, 1),
        "hook": hook,
        "questions": text.count("?"),
        "questions_in_first_15s": sum(x.count("?") for x in first15),
        "you_per_100_words": round(len(_YOU.findall(text)) / max(1, total) * 100, 1),
        "longest_stretch_without_you_sec": round(worst / WPS),
        "chapters": len(chapter_beats),
        "chapters_with_rehook": rehooked,
        "payoff_at_fraction": round(payoff_sec / max(1.0, total / WPS), 2),
        "avg_sec_per_beat": round(total / WPS / len(beats), 1),
        "share_of_card_beats": round(cards / len(beats), 2),
    }
    fixes: list[str] = []
    if hook["total"] < 50:
        weakest = min((k for k in hook if k != "total"), key=lambda k: hook[k])
        fixes.append(
            f"The first line scores {hook['total']}/100 (weakest: {weakest}). Rewrite it in 9-24 words: address 'you', name a concrete moment or number, and leave a question open."
        )
    if m["questions_in_first_15s"] == 0:
        fixes.append("Ask the viewer a question inside the first 15 seconds.")
    if m["you_per_100_words"] < 2.5:
        fixes.append("Talk to the viewer more: use 'you' or 'your' at least 3 times per 100 words.")
    if m["longest_stretch_without_you_sec"] > 45:
        fixes.append(
            f"About {m['longest_stretch_without_you_sec']} seconds pass without 'you' (ending near beat {worst_at}). Put the viewer back in the story there."
        )
    if m["chapters"] < 4 and total > 600:
        fixes.append("Give the video at least 5 chapters (set `chapter` on the first beat of each).")
    elif chapter_beats and rehooked / len(chapter_beats) < 0.6:
        fixes.append("Open more chapters with a reason to stay: a question, a time on the clock, or a 'but'.")
    if not 0.45 <= m["payoff_at_fraction"] <= 0.9 and total > 600:
        fixes.append(
            "Answer the opening promise between the halfway point and the last tenth of the video, and say that you are answering it."
        )
    if m["avg_sec_per_beat"] > 8.5:
        fixes.append(
            "Shots are too long on average. Split long beats so something changes on screen every 5-8 seconds."
        )
    if longest >= 4:
        fixes.append("Four card-style beats run back to back. Put a scene or an object between them.")
    if m["share_of_card_beats"] > 0.6:
        fixes.append("More than 60% of beats are text cards. Show more scenes with people.")
    last = " ".join(b.say for b in beats[-2:])
    if "?" not in last and not re.search(r"\b(tell|comment|count|try)\b", last, re.I):
        fixes.append("End on one ask: a question the viewer can answer in the comments.")
    m["fixes"] = fixes
    return m
