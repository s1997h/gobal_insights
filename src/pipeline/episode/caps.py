"""Caption tokens for Shorts: spelled-out numbers become numerals (eighty-six percent -> 86%)."""

from __future__ import annotations

import re
from typing import Any

_UNITS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
)}  # fmt: skip
_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
_UNIT_WORDS = {"percent", "second", "seconds", "minute", "minutes", "hour", "hours", "day", "days", "week", "weeks",
               "month", "months", "year", "years", "times", "people", "million", "billion"}  # fmt: skip


def _core(w: str) -> str:
    return re.sub(r"[^a-z\-]", "", w.lower())


def _val(c: str) -> int | None:
    if c in _UNITS:
        return _UNITS[c]
    if c in _TENS:
        return _TENS[c]
    if "-" in c:
        a, b = c.split("-", 1)
        if a in _TENS and b in _UNITS and _UNITS[b] < 10:
            return _TENS[a] + _UNITS[b]
    return None


def _is_num(c: str) -> bool:
    return _val(c) is not None or c in ("hundred", "thousand", "half")


def _ends(w: str) -> bool:
    return bool(re.search(r"[.,;:!?]$", w))


def _parse(cs: list[str]) -> tuple[str, bool]:
    if len(cs) == 2:
        a, b = _val(cs[0]), _val(cs[1])
        if a in (19, 20) and b is not None:
            return str(a * 100 + b), True  # a year: twenty sixteen -> 2016
    total = cur = 0
    half = False
    for c in cs:
        if c in ("and", "a"):
            continue
        if c == "half":
            half = True
        elif c == "hundred":
            cur = max(cur, 1) * 100
        elif c == "thousand":
            total += max(cur, 1) * 1000
            cur = 0
        else:
            cur += _val(c) or 0
    n = total + cur
    return (f"{n}.5" if half else str(n)), False


def caption_tokens(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """[{word,start_ms,end_ms}] -> [{text,start_ms,end_ms,num?}] with number phrases merged into numerals."""
    out: list[dict[str, Any]] = []
    i = 0
    n = len(words)

    def plain(k: int) -> None:
        tok: dict[str, Any] = {
            "text": words[k]["word"],
            "start_ms": words[k]["start_ms"],
            "end_ms": words[k]["end_ms"],
        }
        if re.search(r"\d", words[k]["word"]):
            tok["num"] = True  # the script already used numerals
        out.append(tok)

    while i < n:
        c = _core(words[i]["word"])
        starts = (_is_num(c) and c != "half") or (
            c == "a" and i + 1 < n and _core(words[i + 1]["word"]) == "hundred"
        )
        if not starts:
            plain(i)
            i += 1
            continue
        j = i
        run = [c]
        while not _ends(words[j]["word"]) and j + 1 < n:
            n1 = _core(words[j + 1]["word"])
            n2 = _core(words[j + 2]["word"]) if j + 2 < n else ""
            if (
                _is_num(n1)
                or (n1 == "and" and (_is_num(n2) or n2 == "a"))
                or (n1 == "a" and n2 in ("half", "hundred"))
            ):
                j += 1
                run.append(n1)
            else:
                break
        text, year = _parse(run)
        nxt = _core(words[j + 1]["word"]) if j + 1 < n else ""
        prev = _core(words[i - 1]["word"]) if i > 0 else ""
        numeric = year or "." in text or int(text) >= 10 or nxt in _UNIT_WORDS or prev == "day"
        if not numeric:
            for k in range(i, j + 1):
                plain(k)
            i = j + 1
            continue
        if not year and "." not in text:
            text = f"{int(text):,}"
        m = re.search(r"[.,;:!?]*$", words[j]["word"])
        tail = m.group(0) if m else ""
        end = words[j]["end_ms"]
        if nxt == "percent" and not _ends(words[j]["word"]):
            j += 1
            text += "%"
            m = re.search(r"[.,;:!?]*$", words[j]["word"])
            tail = m.group(0) if m else ""
            end = words[j]["end_ms"]
        out.append({"text": text + tail, "start_ms": words[i]["start_ms"], "end_ms": end, "num": True})
        i = j + 1
    return out


def srt(words: list[dict[str, Any]]) -> str:
    """Captions for the long video: cues of up to about 40 characters, broken after punctuation where possible."""

    def ts(sec: float) -> str:
        ms = int(round(sec * 1000))
        h, ms = divmod(ms, 3600000)
        m, ms = divmod(ms, 60000)
        s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    cues: list[list[dict[str, Any]]] = []
    cur: list[dict[str, Any]] = []
    for w in words:
        cur.append(w)
        text = " ".join(x["word"] for x in cur)
        last = w["word"][-1:]
        if last in ".?!" or len(text) >= 38 or (last in ",;:" and len(text) >= 22):
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)
    lines: list[str] = []
    for i, c in enumerate(cues, 1):
        a = c[0]["start_ms"] / 1000
        b = max(c[-1]["end_ms"] / 1000, a + 0.8)
        if i < len(cues):
            b = min(b + 0.15, cues[i][0]["start_ms"] / 1000)
        lines += [str(i), f"{ts(a)} --> {ts(max(b, a + 0.2))}", " ".join(x["word"] for x in c), ""]
    return "\n".join(lines)
