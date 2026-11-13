"""Graph state. Kept small and JSON-friendly: big artifacts live on disk in runs/<run_id>/."""

from __future__ import annotations

from typing import TypedDict


class RunState(TypedDict, total=False):
    run_id: str
    video_id: str
    topic_title: str
    angle: str
    story_shape: str
    attempts: int  # script attempts so far
    fixes: list[str]  # problems to fix on the next script attempt
    route: str  # pass | retry | human
    scripts_provided: bool  # `pipeline build`: hand-written scripts, skip the agents
