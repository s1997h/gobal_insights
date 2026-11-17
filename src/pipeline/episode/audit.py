"""Engagement gate: the retention checks a careful editor would run, as numbers.

None of this predicts views. It catches the known ways a script leaks viewers: a slow or vague
opening, no open question, a list of facts where a story should be, the same empty room shot after
shot, narration written for the eye instead of the ear, chapters that begin without a reason to
stay, and an ending with no ask.
"""

from __future__ import annotations

import re
from typing import Any

from .schemas import EpisodeScript

WPS = 2.6  # narration words per second, for estimating time from text
_YOU = re.compile(r"\byou(r|rs|'re|'ve|'d|'ll)?\b", re.I)
_STAKES = re.compile(
    r"\b(fail|failed|lose|lost|stop|stopped|broke|crash|collapse|never|nobody|only|last|survive|worth|free|empty|gone|ban|shut|"
    r"hid|hide|hidden|buried|kill|dead|died|bankrupt|fired|cost|secret|refus|destroy|vanish|wiped|wrong|mistake|"
    r"quiet|silen|told|tell|warn|ignor|everything|nothing|billion|million)\w*",
    re.I,
)
_REHOOK = re.compile(
    r"\?|\b(but|twist|turns|until|except|remember|worse|strange|real one|here's|suddenly|only|then)\b", re.I
)


# a story moves on "but" and "so"; a list of facts moves on "and"
_TURN = re.compile(
    r"\b(but|so|until|except|instead|then|suddenly|because|which meant|that's when|only|yet|still|meanwhile)\b",
    re.I,
)
_STIFF = re.compile(
    r"\b(do not|does not|did not|is not|are not|was not|were not|cannot|will not|would not|could not|should not|"
    r"it is|that is|there is|you are|they are|we are|you will|you have|they have|let us|what is|here is)\b",
    re.I,
)
_PROPER = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]{2,}\b")
_NUMBER = re.compile(
    r"\d|\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|sixty|seventy|"
    r"eighty|ninety|hundred|thousand|million|billion|trillion|nineteen|half|percent)\b",
    re.I,
)
_IDLE = {"stand", "think", "shrug"}
# openings the viewer has heard a thousand times, and lines that announce a topic instead of telling it
_STOCK = re.compile(
    r"^\W*(have you ever|ever wonder|did you know|imagine|picture this|today,? (we|i)|in this video|welcome|hey|hi\b|"
    r"let's|let us|what is|what are|here's the story|this is the story|the story of|so,? )"
    r"|\b(in this video|we('ll| will) (look|explore|talk|find)|let's (look|talk|explore|find)|find out (why|how|what))\b",
    re.I,
)
# something left unexplained: a contrast, a secret, an order to keep quiet
_GAP = re.compile(
    r"\b(what if|why|how|until|but|yet|then|instead|still|nobody|no one|secret|told (him|her|them) to|"
    r"tells? (him|her|them) to|was told|keep (it )?quiet|and it|not the only|never|no film|nothing)\b",
    re.I,
)
_OPENERS = {
    "The", "A", "An", "In", "It", "Its", "It's", "This", "That", "Then", "But", "And", "So", "You", "Your", "He",
    "She", "They", "We", "I", "His", "Her", "Their", "On", "At", "By", "For", "If", "What", "Why", "How", "When",
    "One", "Every", "No", "Now", "Today", "Tonight", "Nobody", "Here", "There", "Have", "Did", "Do", "Imagine",
    "Let", "Let's", "Welcome", "Hey", "Hi", "Ever", "Picture", "Some", "Most", "All", "Was", "Is", "Are",
}  # fmt: skip


def _names(text: str) -> list[str]:
    """Capitalised words that are not ordinary sentence openers: people, companies, places, products."""
    return [w for w in re.findall(r"\b[A-Z][A-Za-z]+\b", text) if w not in _OPENERS]


def hook_score(text: str) -> dict[str, int]:
    """0-100 on five properties of an opening line, and their average.

    A heuristic, not a predictor: it separates a line that names a moment, a person and a cost from one
    that announces a topic. Lines that open on a stock phrase ("Have you ever", "In this video") are capped
    at 35 whatever else they do, because the viewer has heard that opening a thousand times.
    """
    words = text.split()
    n = len(words)
    numbers = min(2, len(_NUMBER.findall(text)))
    names = min(2, len(_names(text)))
    specificity = min(
        100,
        30
        + 20 * numbers
        + 20 * names
        + (10 if re.search(r"\b(AM|PM|o'clock|tomorrow|tonight|today|morning|night)\b", text, re.I) else 0),
    )
    # the line is about someone: the viewer, or a named person or company
    address = min(100, 20 + 40 * len(_YOU.findall(text)) + 30 * names)
    stakes = min(100, 30 + 30 * len(_STAKES.findall(text)))
    curiosity = min(
        100,
        30 + (35 if "?" in text else 0) + (35 if _GAP.search(text) else 0),
    )
    brevity = 100 if 8 <= n <= 24 else max(10, 100 - 9 * (8 - n if n < 8 else n - 24))
    total = round((specificity + address + stakes + curiosity + brevity) / 5)
    if _STOCK.search(text):
        total = min(total, 35)
    return {
        "specificity": specificity,
        "address": address,
        "stakes": stakes,
        "curiosity": curiosity,
        "brevity": brevity,
        "total": total,
    }


# Words that make a viewer stop and translate. Each with what to say instead.
JARGON = {
    "deficit": "spending more than it had", "denomination": "bigger notes", "nominal": "on paper",
    "nominally": "on paper", "real terms": "what the money buys", "expectations": "what people think will happen",
    "hard currency": "dollars", "formal economy": "shops and offices", "monetary": "money", "fiscal": "budget",
    "liquidity": "cash on hand", "issuance": "printing", "transactions": "payments", "institutions": "banks",
    "insolvent": "out of money", "insolvency": "running out of money", "liabilities": "what it owed",
    "leverage": "borrowed money", "valuation": "price tag", "stakeholders": "people involved", "synergy": "teamwork",
    "macroeconomic": "the whole economy", "gdp": "everything the country makes", "yields": "interest",
    "market share": "share of buyers", "paradigm": "way of doing things", "infrastructure": "roads and power",
}  # fmt: skip
_ABSTRACT = re.compile(r"\b[a-z]{4,}(?:tion|sion|ment|ity|ance|ence|ism)s?\b", re.I)


def plain_english(script: EpisodeScript) -> dict[str, Any]:
    """How easy the narration is to follow by ear: sentence length, abstract words, jargon."""
    text = " ".join(b.say for b in script.beats)
    words = re.findall(r"[A-Za-z0-9']+", text)
    sentences = [x for x in re.split(r"[.!?]+", text) if x.split()]
    abstract = _ABSTRACT.findall(text)
    low = " " + re.sub(r"[^a-z ]", " ", text.lower()) + " "
    jargon = [w for w in JARGON if f" {w} " in low]
    long_ones = sorted((x.strip() for x in sentences), key=lambda x: -len(x.split()))[:3]
    return {
        "avg_words_per_sentence": round(len(words) / max(1, len(sentences)), 1),
        "abstract_per_100_words": round(100 * len(abstract) / max(1, len(words)), 1),
        "abstract_words": sorted(set(w.lower() for w in abstract))[:12],
        "jargon": jargon,
        "longest_sentences": long_ones,
    }


def plain_fixes(m: dict[str, Any]) -> list[str]:
    fixes: list[str] = []
    if m["jargon"]:
        swaps = "; ".join(f"'{w}' (say '{JARGON[w]}')" for w in m["jargon"][:5])
        fixes.append(
            f"These words make a viewer stop and translate: {swaps}. Say it the way you'd tell a friend, "
            "or show it happening in a scene."
        )
    if m["abstract_per_100_words"] > 3.0:
        fixes.append(
            f"Too many abstract words ({', '.join(m['abstract_words'][:8])}). Swap each for something you can "
            "see: not 'prices rise with expectations' but 'the baker writes a new price on the bread every "
            "morning'. A 12-year-old should follow every sentence."
        )
    if m["avg_words_per_sentence"] > 9:
        fixes.append(
            f"Sentences average {m['avg_words_per_sentence']} words; aim for about 8 (the Kodak video averaged 6). "
            f"Split these: {' | '.join(m['longest_sentences'])}"
        )
    return fixes


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

    opening = beats[: min(3, len(beats))]
    open_text = " ".join(first15)
    scenes = [b for b in beats if b.view == "scene"]
    sets: list[str] = [b.set or "street" for b in scenes]
    top_set = max(set(sets), key=sets.count) if sets else ""
    same_set = longest_set = 1 if scenes else 0
    for s1, s2 in zip(sets, sets[1:], strict=False):
        same_set = same_set + 1 if s1 == s2 else 1
        longest_set = max(longest_set, same_set)
    idle = sum(
        1
        for b in scenes
        if len(b.people) <= 1 and b.scene_prop == "none" and all(x.pose in _IDLE for x in b.people)
    )
    sentences = [x for x in re.split(r"(?<=[.!?])\s+", text) if x.strip()]
    minutes = max(0.2, total / WPS / 60)
    best_alt = max((hook_score(h)["total"] for h in script.hooks), default=0)

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
        "best_candidate_hook": best_alt,
        "story_turns_per_minute": round(len(_TURN.findall(text)) / minutes, 1),
        "avg_words_per_sentence": round(total / max(1, len(sentences)), 1),
        "stiff_phrases": len(_STIFF.findall(text)),
        "different_places": len(set(sets)),
        "most_used_place": top_set,
        "share_in_most_used_place": round(sets.count(top_set) / len(sets), 2) if sets else 0,
        "longest_run_in_one_place": longest_set,
        "share_of_idle_scenes": round(idle / len(scenes), 2) if scenes else 0,
        "scenes_with_place_tag": sum(1 for b in scenes if b.where),
    }
    fixes: list[str] = []
    if hook["total"] < 58:
        weakest = min((k for k in hook if k != "total"), key=lambda k: hook[k])
        fixes.append(
            f"The first line scores {hook['total']}/100 (weakest: {weakest}). Rewrite it in 8-22 words: a named person or company (or 'you') in one concrete moment, with a year, an amount or an object, and something left unexplained."
        )
    elif best_alt >= hook["total"] + 12:
        fixes.append(
            f"One of your own candidate first lines scores {best_alt}/100 against {hook['total']} for the one you used. Open with the stronger one."
        )
    if sum(1 for b in opening if b.view in ("scene", "object")) < min(2, len(opening)) or any(
        b.view in ("title", "list", "checklist") or b.object == "mystery" for b in opening[:2]
    ):
        fixes.append(
            "The first three beats must be the cold open: people in a place, mid-action. Move the cards and the mystery notebook later."
        )
    if not _NUMBER.search(open_text) and not _PROPER.search(open_text):
        fixes.append(
            "Nothing in the first 15 seconds is specific. Name a person, a company, a year or an amount in the first two beats."
        )
    if m["story_turns_per_minute"] < 2.5 and total > 120:
        fixes.append(
            "This reads as a list of facts. Join the beats as cause and effect: each one should follow from the last with a 'but' or a 'so', not an 'and then'."
        )
    plain = plain_english(script)
    m["plain_english"] = plain
    fixes += plain_fixes(plain)
    if m["stiff_phrases"] > max(2, total // 150):
        fixes.append(
            f'{m["stiff_phrases"]} phrases are written for the page ("do not", "it is", "you are"). Use the contractions people say out loud: don\'t, it\'s, you\'re.'
        )
    if total > 600 and scenes:
        if m["different_places"] < 4:
            fixes.append(
                f"The whole story happens in {m['different_places']} place(s). Move it through at least four (where the product was made, where it sold, where the decision was taken, where the viewer meets it)."
            )
        elif m["share_in_most_used_place"] > 0.4:
            fixes.append(
                f"{round(m['share_in_most_used_place'] * 100)}% of scenes are in the {top_set}. Spread them across the other places."
            )
        if m["scenes_with_place_tag"] < 3:
            fixes.append(
                "Set `where` (place and year) on the first scene and whenever the story jumps in time or place."
            )
    if longest_set > 4:
        fixes.append(
            f"{longest_set} scenes in a row use the same place. Cut away to another place, an object or a number."
        )
    if m["share_of_idle_scenes"] > 0.35 and len(scenes) >= 4:
        fixes.append(
            "Too many scenes are one person standing still. Give them something to do (walk, hold, read, point, phone), a prop, or a second person to react."
        )
    if m["questions_in_first_15s"] == 0:
        fixes.append("Ask the viewer a question inside the first 15 seconds.")
    # a what-if puts the viewer in every beat; a company story still turns to them at each twist
    viewer_story = script.hero.strip().lower() in ("", "you", "the viewer")
    if m["you_per_100_words"] < (2.5 if viewer_story else 1.2):
        fixes.append(
            "Talk to the viewer more: 'you' or 'your' at least "
            + (
                "3 times per 100 words."
                if viewer_story
                else "once every 80 words, at the turns ('you'd have done the same')."
            )
        )
    if m["longest_stretch_without_you_sec"] > (45 if viewer_story else 75):
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
