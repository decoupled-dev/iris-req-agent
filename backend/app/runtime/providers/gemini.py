"""Google Gemini adapter — swap point, not yet selected by the program.

Auth: GEMINI_API_KEY or Vertex credentials.
Mapping from app.runtime.types: system -> system_instruction; ToolSpec -> function_declarations; ToolCall <-> functionCall / functionResponse parts.
Contract: return a ModelTurn whose tool_calls name tools from the request; the loop
in app/runtime/loop.py does the rest. See docs/11-agent-runtime.md#swapping-in-a-real-provider.
"""

from __future__ import annotations

from ..types import ModelRequest, ModelTurn


class GeminiProvider:
    name = "gemini"

    def __init__(self, **options):
        self.options = options

    def generate(self, request: ModelRequest) -> ModelTurn:
        raise NotImplementedError("Google Gemini provider is not implemented yet; set runtime.provider: simulated")
