"""OpenAI-compatible endpoint (OpenAI, Azure, vLLM, Ollama) adapter — swap point, not yet selected by the program.

Auth: base_url and api_key_env.
Mapping from app.runtime.types: system -> first system message; ToolSpec -> tools[type=function]; ToolCall <-> tool_calls / role=tool messages.
Contract: return a ModelTurn whose tool_calls name tools from the request; the loop
in app/runtime/loop.py does the rest. See docs/11-agent-runtime.md#swapping-in-a-real-provider.
"""

from __future__ import annotations

from ..types import ModelRequest, ModelTurn


class OpenAICompatProvider:
    name = "openai_compat"

    def __init__(self, **options):
        self.options = options

    def generate(self, request: ModelRequest) -> ModelTurn:
        raise NotImplementedError("OpenAI-compatible endpoint (OpenAI, Azure, vLLM, Ollama) provider is not implemented yet; set runtime.provider: simulated")
