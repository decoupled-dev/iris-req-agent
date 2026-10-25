"""Simulation policies: one scripted 'model' per agent.

A policy sees only the ModelRequest (system prompt, transcript, tools) and returns the next ModelTurn.
It reads data exclusively from tool results already in the transcript, never from the database,
so a real provider can replace it without changing anything around it.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable

from ..types import Message, ModelRequest, ModelTurn, ToolCall

Policy = Callable[[ModelRequest], ModelTurn]
POLICIES: dict[str, Policy] = {}


def policy(*agent_ids: str):
    def register(fn: Policy) -> Policy:
        for a in agent_ids:
            POLICIES[a] = fn
        return fn
    return register


def results(req: ModelRequest, name: str) -> list[Any]:
    """Contents of every successful tool result with this name, in transcript order."""
    calls = {c.id: c for m in req.messages if m.role == "assistant" for c in m.tool_calls}
    out = []
    for m in req.messages:
        for r in m.tool_results:
            if r.name == name and not r.is_error:
                out.append((calls.get(r.tool_call_id), r.content))
    return out


def result(req: ModelRequest, name: str, **match) -> Any | None:
    for call, content in reversed(results(req, name)):
        if all(call and call.input.get(k) == v for k, v in match.items()):
            return content
    return None


def call(req: ModelRequest, name: str, **args) -> ToolCall:
    # Unique per turn and per call, stable for the same transcript, like provider-issued IDs.
    turn_no = sum(1 for m in req.messages if m.role == "assistant") + 1
    digest = hashlib.sha1(f"{req.agent_id}:{turn_no}:{name}:{json.dumps(args, sort_keys=True)}".encode()).hexdigest()
    return ToolCall(id=f"toolu_{digest[:20]}", name=name, input=args)


def turn(thinking: str, calls: list[ToolCall], text: str = "") -> ModelTurn:
    return ModelTurn(thinking=thinking, text=text, tool_calls=calls)


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def finding_id(key: str) -> str:
    return f"find_{key.lower().replace('-', '_')}"


def task_text(req: ModelRequest) -> str:
    first: Message = req.messages[0]
    return first.text


from . import assurance, gate, research, synthesis  # noqa: E402,F401  (registers policies)
