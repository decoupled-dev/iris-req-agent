"""The agent loop: model turn -> tool calls -> tool results -> ... -> submit_result."""

from __future__ import annotations

import json
import threading
from typing import Callable

from pydantic import ValidationError

from ..models import AgentResult, RunContext, RunStatus
from .providers import ModelProvider
from .tools import TOOLS
from .types import Message, ModelRequest, ToolResult

Emit = Callable[[str, dict], None]


class Cancelled(Exception):
    pass


def _preview(content, limit: int = 600) -> str:
    text = json.dumps(content, default=str)
    return text if len(text) <= limit else text[:limit] + f"… ({len(text)} chars)"


def run_agent(spec, ctx: RunContext, provider: ModelProvider, model: str, emit: Emit,
              cancel: threading.Event, max_turns: int = 12) -> AgentResult:
    tools = [TOOLS[name].spec for name in spec.tools]
    messages = [Message(role="user", text=spec.task(ctx))]
    totals = {"input_tokens": 0, "output_tokens": 0, "latency_ms": 0}
    emit("start", {"provider": provider.name, "model": model, "tools": list(spec.tools)})

    for turn_no in range(1, max_turns + 1):
        if cancel.is_set():
            raise Cancelled()
        turn = provider.generate(ModelRequest(agent_id=spec.id, model=model, system=spec.system_prompt(),
                                              messages=messages, tools=tools))
        totals["input_tokens"] += turn.usage.input_tokens
        totals["output_tokens"] += turn.usage.output_tokens
        totals["latency_ms"] += turn.latency_ms
        emit("turn", {"n": turn_no, "stop_reason": turn.stop_reason, "latency_ms": turn.latency_ms,
                      **turn.usage.model_dump()})
        if turn.thinking:
            emit("thinking", {"text": turn.thinking})
        if turn.text:
            emit("message", {"text": turn.text})
        messages.append(Message(role="assistant", text=turn.text, thinking=turn.thinking, tool_calls=turn.tool_calls))
        if cancel.is_set():
            raise Cancelled()

        if not turn.tool_calls:
            messages.append(Message(role="user", text="Call submit_result to finish the run."))
            continue

        results = []
        for call in turn.tool_calls:
            emit("tool_call", {"id": call.id, "name": call.name, "input": call.input})
            if call.name == "submit_result":
                try:
                    result = AgentResult.model_validate({**call.input, "agent_id": spec.id,
                                                         "status": RunStatus.succeeded})
                except ValidationError as exc:
                    results.append(ToolResult(tool_call_id=call.id, name=call.name, content=str(exc), is_error=True))
                    emit("tool_result", {"id": call.id, "name": call.name, "is_error": True, "preview": str(exc)[:600]})
                    continue
                result.metrics.update({"provider": provider.name, "model": model, "turns": turn_no, **totals})
                emit("result", {"summary": result.summary, "findings": len(result.findings),
                                "proposals": len(result.proposals), **totals})
                return result
            if call.name not in spec.tools:
                content, is_error = f"Tool {call.name} is not available to {spec.id}", True
            else:
                try:
                    content, is_error = TOOLS[call.name].fn(ctx, **call.input), False
                except Exception as exc:  # Tool errors go back to the model, as with a real provider.
                    content, is_error = f"{type(exc).__name__}: {exc}", True
            results.append(ToolResult(tool_call_id=call.id, name=call.name, content=content, is_error=is_error))
            emit("tool_result", {"id": call.id, "name": call.name, "is_error": is_error, "preview": _preview(content)})
        messages.append(Message(role="tool", tool_results=results))

    raise RuntimeError(f"Agent did not call submit_result within {max_turns} turns")
