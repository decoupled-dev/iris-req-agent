"""Claude API adapter — swap point, not yet selected by the program.

Auth: ANTHROPIC_API_KEY.
Mapping from app.runtime.types: system -> top-level system; Message(tool_calls) -> tool_use blocks; Message(role=tool) -> user message with tool_result blocks; thinking -> thinking blocks (pass back unchanged); stop_reason maps 1:1.
Contract: return a ModelTurn whose tool_calls name tools from the request; the loop
in app/runtime/loop.py does the rest. See docs/11-agent-runtime.md#swapping-in-a-real-provider.
"""

from __future__ import annotations

from ..types import ModelRequest, ModelTurn


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, **options):
        self.options = options

    def generate(self, request: ModelRequest) -> ModelTurn:
        raise NotImplementedError("Claude API provider is not implemented yet; set runtime.provider: simulated")
