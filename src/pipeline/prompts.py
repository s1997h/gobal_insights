"""Prompts live in prompts/*.md under git. {placeholders} are filled per channel; unknown braces are left alone."""

from __future__ import annotations

import re
from pathlib import Path

from .schemas import TEMPLATE_SPECS, StyleBible


def render_prompt(root: Path, name: str, **values: object) -> str:
    text = (root / "prompts" / f"{name}.md").read_text(encoding="utf-8")

    def sub(m: re.Match[str]) -> str:
        key = m.group(1)
        return str(values[key]) if key in values else m.group(0)

    return re.sub(r"\{([a-z_]+)\}", sub, text)


def template_catalog() -> str:
    return "\n".join(
        f'  - "{name}": {desc} Props example: {ex}' for name, (desc, ex) in TEMPLATE_SPECS.items()
    )


def story_shapes_text(style: StyleBible) -> str:
    return "\n".join(f"- {s.id}: {s.name}. {s.description}" for s in style.story_shapes)


def banned_text(style: StyleBible) -> str:
    return ", ".join(f'"{p}"' for p in style.banned_phrases) or "(none)"
