"""Amazon Bedrock AgentCore harness client.

The harness runs the model. Inline tools execute in the workbench, and their
results go back on the same session until the model calls submit_result.
See docs/07-remote-agents.md.
"""

from __future__ import annotations

import json
import re
import threading
from typing import Any, Callable

from pydantic import ValidationError

from ..models import AgentResult, RunContext, RunStatus
from ..runtime.loop import Cancelled
from ..runtime.tools import TOOLS

Emit = Callable[[str, dict], None]
_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


def session_id(run_id: str) -> str:
    """AgentCore requires 33–100 characters matching [A-Za-z0-9][A-Za-z0-9-_]*."""
    raw = f"sew1-{run_id}-session"
    if len(raw) < 33:
        raw = f"{raw}-{'0' * (33 - len(raw))}"
    return raw[:100]


def _region(arn: str) -> str:
    parts = arn.split(":")
    if len(parts) < 4 or not parts[3]:
        raise ValueError(f"Harness ARN has no region: {arn}")
    return parts[3]


def _client(region: str):
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("boto3 is required for mode bedrock. Install it with: pip install 'boto3>=1.38'") from exc
    return boto3.client("bedrock-agentcore", region_name=region)


def _inline_tools(names: tuple[str, ...]) -> list[dict]:
    return [{
        "type": "inline_function",
        "name": name,
        "config": {"inlineFunction": {
            "description": TOOLS[name].spec.description,
            "inputSchema": TOOLS[name].spec.input_schema,
        }},
    } for name in names]


def _preview(content, limit: int = 600) -> str:
    text = json.dumps(content, default=str)
    return text if len(text) <= limit else text[:limit] + f"… ({len(text)} chars)"


def _parse_input(raw: str) -> dict:
    raw = (raw or "").strip()
    if not raw:
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Tool input must be a JSON object")
    return value


def _consume(stream) -> dict:
    """Fold one InvokeHarness stream into text, tool calls, stop reason, and usage."""
    blocks: dict[int, dict] = {}
    text: list[str] = []
    reasoning: list[str] = []
    stop = "end_turn"
    usage = {"input_tokens": 0, "output_tokens": 0}
    latency_ms = 0
    for event in stream:
        for key in ("runtimeClientError", "validationException", "internalServerException"):
            if key in event:
                message = (event[key] or {}).get("message") or key
                raise RuntimeError(message)
        if start := event.get("contentBlockStart"):
            tool = (start.get("start") or {}).get("toolUse") or {}
            if tool:
                blocks[start.get("contentBlockIndex", 0)] = {
                    "id": tool.get("toolUseId", ""), "name": tool.get("name", ""), "input": ""}
        if delta := event.get("contentBlockDelta"):
            idx = delta.get("contentBlockIndex", 0)
            body = delta.get("delta") or {}
            if "text" in body:
                text.append(body["text"])
            if piece := (body.get("reasoningContent") or {}).get("text"):
                reasoning.append(piece)
            if "toolUse" in body:
                blocks.setdefault(idx, {"id": "", "name": "", "input": ""})
                blocks[idx]["input"] += body["toolUse"].get("input") or ""
        if stop_event := event.get("messageStop"):
            stop = stop_event.get("stopReason") or stop
        if meta := event.get("metadata"):
            used = meta.get("usage") or {}
            usage["input_tokens"] += int(used.get("inputTokens") or 0)
            usage["output_tokens"] += int(used.get("outputTokens") or 0)
            latency_ms += int((meta.get("metrics") or {}).get("latencyMs") or 0)
    calls = []
    for block in blocks.values():
        if not block["name"]:
            continue
        try:
            parsed = _parse_input(block["input"])
        except json.JSONDecodeError as exc:
            raise ValueError(f"Tool {block['name']} input is not valid JSON: {exc}") from exc
        calls.append({**block, "input": parsed})
    return {"text": "".join(text), "reasoning": "".join(reasoning), "calls": calls,
            "stop": stop, "usage": usage, "latency_ms": latency_ms}


def _result_from_text(agent_id: str, text: str) -> AgentResult | None:
    match = _JSON_FENCE.search(text)
    blob = match.group(1) if match else None
    if blob is None:
        start, end = text.find("{"), text.rfind("}")
        blob = text[start:end + 1] if start >= 0 and end > start else None
    if not blob:
        return None
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "findings" not in data or "proposals" not in data:
        return None
    return AgentResult.model_validate({**data, "agent_id": agent_id, "status": RunStatus.succeeded,
                                       "summary": data.get("summary", "")})


class BedrockHarnessAgent:
    def __init__(self, spec, cfg: dict, client=None):
        self.spec = spec
        self.harness_arn = cfg["harness_arn"]
        self.region = cfg.get("region") or _region(self.harness_arn)
        self.qualifier = cfg.get("qualifier") or "DEFAULT"
        self._client = client

    def _service(self):
        return self._client or _client(self.region)

    def run(self, ctx: RunContext, cancel: threading.Event, emit: Emit, max_turns: int = 12) -> AgentResult:
        client = self._service()
        sid = session_id(ctx.run_id)
        tools = _inline_tools(self.spec.tools)
        messages: list[dict] = [{"role": "user", "content": [{"text": self.spec.task(ctx)}]}]
        totals = {"input_tokens": 0, "output_tokens": 0, "latency_ms": 0}
        model = self.harness_arn.rsplit("/", 1)[-1]
        emit("start", {"provider": "bedrock-agentcore", "model": model, "region": self.region,
                       "harness_arn": self.harness_arn, "tools": list(self.spec.tools)})

        for turn_no in range(1, max_turns + 1):
            if cancel.is_set():
                raise Cancelled()
            response = client.invoke_harness(
                harnessArn=self.harness_arn, qualifier=self.qualifier, runtimeSessionId=sid,
                runtimeUserId="sew1-workbench", messages=messages,
                systemPrompt=[{"text": self.spec.system_prompt()}], tools=tools,
                allowedTools=list(self.spec.tools),
            )
            folded = _consume(response["stream"])
            totals["input_tokens"] += folded["usage"]["input_tokens"]
            totals["output_tokens"] += folded["usage"]["output_tokens"]
            totals["latency_ms"] += folded["latency_ms"]
            emit("turn", {"n": turn_no, "stop_reason": folded["stop"], "latency_ms": folded["latency_ms"],
                          **folded["usage"]})
            if folded["reasoning"]:
                emit("thinking", {"text": folded["reasoning"]})
            if folded["text"]:
                emit("message", {"text": folded["text"]})
            if cancel.is_set():
                raise Cancelled()

            if folded["stop"] not in {"tool_use", "end_turn"}:
                raise RuntimeError(f"Harness stopped: {folded['stop']}")

            if not folded["calls"]:
                if parsed := _result_from_text(self.spec.id, folded["text"]):
                    return self._finish(parsed, model, turn_no, totals, emit)
                preview = folded["text"].strip()[:600] or "(empty response)"
                messages.append({"role": "user", "content": [{"text":
                    "Call submit_result exactly once with summary, findings, proposals, and metrics. "
                    f"The previous reply was not a tool call: {preview}"}]})
                continue

            assistant: list[dict] = []
            if folded["text"]:
                assistant.append({"text": folded["text"]})
            results: list[dict] = []
            for call in folded["calls"]:
                assistant.append({"toolUse": {"name": call["name"], "toolUseId": call["id"],
                                              "input": call["input"], "type": "tool_use"}})
                emit("tool_call", {"id": call["id"], "name": call["name"], "input": call["input"]})
                if call["name"] == "submit_result":
                    try:
                        result = AgentResult.model_validate({**call["input"], "agent_id": self.spec.id,
                                                             "status": RunStatus.succeeded})
                    except ValidationError as exc:
                        results.append(_tool_result(call["id"], str(exc), error=True))
                        emit("tool_result", {"id": call["id"], "name": call["name"], "is_error": True,
                                             "preview": str(exc)[:600]})
                        continue
                    return self._finish(result, model, turn_no, totals, emit)
                results.append(self._call_tool(ctx, call, emit))

            messages.append({"role": "assistant", "content": assistant})
            messages.append({"role": "user", "content": results})

        raise RuntimeError(f"Agent did not call submit_result within {max_turns} turns")

    def _call_tool(self, ctx: RunContext, call: dict, emit: Emit) -> dict:
        if call["name"] not in self.spec.tools:
            content, is_error = f"Tool {call['name']} is not available to {self.spec.id}", True
        else:
            try:
                content, is_error = TOOLS[call["name"]].fn(ctx, **call["input"]), False
            except Exception as exc:
                content, is_error = f"{type(exc).__name__}: {exc}", True
        emit("tool_result", {"id": call["id"], "name": call["name"], "is_error": is_error,
                             "preview": _preview(content)})
        return _tool_result(call["id"], content, error=is_error)

    def _finish(self, result: AgentResult, model: str, turns: int, totals: dict, emit: Emit) -> AgentResult:
        result.metrics.update({"provider": "bedrock-agentcore", "model": model, "turns": turns, **totals})
        emit("result", {"summary": result.summary, "findings": len(result.findings),
                        "proposals": len(result.proposals), **totals})
        return result


def _tool_result(tool_use_id: str, content: Any, error: bool) -> dict:
    block = {"text": content} if isinstance(content, str) else {"json": content}
    return {"toolResult": {"toolUseId": tool_use_id, "status": "error" if error else "success",
                           "type": "tool_use", "content": [block]}}
