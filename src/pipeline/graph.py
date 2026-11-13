"""The LangGraph state machine.

    topic -> script -> critic -(pass)-> tts -> assets -> render -> package -> export -> END
                         ^  (retry, at most twice) |
                         +-----------------------+   critic -(human)-> END  (needs_review)

`pipeline build` (hand-written scripts) enters at tts and skips the agents.
Publishing plugs in after `export`: notify -> approve (interrupt) -> publish. Not built yet.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph

from .context import RunContext
from .nodes.assets import assets_node
from .nodes.critic import critic_node, route_after_critic
from .nodes.export import export_node
from .nodes.package import package_node
from .nodes.render import render_node
from .nodes.script import script_node
from .nodes.topic import topic_node
from .nodes.tts import tts_node
from .state import RunState

NodeFn = Callable[[RunContext, RunState], dict[str, Any]]


def _bind(ctx: RunContext, fn: NodeFn) -> Callable[[RunState], dict[str, Any]]:
    def node(state: RunState) -> dict[str, Any]:
        return fn(ctx, state)

    node.__name__ = fn.__name__
    return node


def route_entry(state: RunState) -> str:
    return "tts" if state.get("scripts_provided") else "topic"


def build_graph(ctx: RunContext, checkpointer: Any) -> Any:
    g: StateGraph = StateGraph(RunState)
    for name, fn in [
        ("topic", topic_node),
        ("script", script_node),
        ("critic", critic_node),
        ("tts", tts_node),
        ("assets", assets_node),
        ("render", render_node),
        ("package", package_node),
        ("export", export_node),
    ]:
        g.add_node(name, _bind(ctx, fn))  # type: ignore[call-overload]
    g.add_conditional_edges(START, route_entry, {"topic": "topic", "tts": "tts"})
    g.add_edge("topic", "script")
    g.add_edge("script", "critic")
    g.add_conditional_edges("critic", route_after_critic, {"pass": "tts", "retry": "script", "human": END})
    g.add_edge("tts", "assets")
    g.add_edge("assets", "render")
    g.add_edge("render", "package")
    g.add_edge("package", "export")
    g.add_edge("export", END)
    return g.compile(checkpointer=checkpointer)
