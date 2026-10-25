"""Neutral request and turn shapes. Every provider adapter maps to and from these."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolSpec(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class ToolCall(BaseModel):
    id: str
    name: str
    input: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool_call_id: str
    name: str
    content: Any
    is_error: bool = False


class Message(BaseModel):
    role: Literal["user", "assistant", "tool"]
    text: str = ""
    thinking: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class ModelRequest(BaseModel):
    agent_id: str
    model: str
    system: str
    messages: list[Message]
    tools: list[ToolSpec]
    max_tokens: int = 8000


class ModelTurn(BaseModel):
    thinking: str = ""
    text: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    stop_reason: Literal["tool_use", "end_turn", "max_tokens"] = "end_turn"
    usage: Usage = Field(default_factory=Usage)
    latency_ms: int = 0
