"""Provider registry. `runtime.provider` in config/agents.yaml selects one."""

from __future__ import annotations

from typing import Protocol

from ..types import ModelRequest, ModelTurn


class ModelProvider(Protocol):
    name: str

    def generate(self, request: ModelRequest) -> ModelTurn: ...


def get_provider(runtime_cfg: dict) -> ModelProvider:
    name = runtime_cfg.get("provider", "simulated")
    if name == "simulated":
        from .simulated import SimulatedProvider
        return SimulatedProvider(**runtime_cfg.get("simulated", {}))
    if name == "anthropic":
        from .anthropic import AnthropicProvider
        return AnthropicProvider(**runtime_cfg.get("anthropic", {}))
    if name == "vertex":
        from .vertex import VertexProvider
        return VertexProvider(**runtime_cfg.get("vertex", {}))
    if name == "gemini":
        from .gemini import GeminiProvider
        return GeminiProvider(**runtime_cfg.get("gemini", {}))
    if name == "openai_compat":
        from .openai_compat import OpenAICompatProvider
        return OpenAICompatProvider(**runtime_cfg.get("openai_compat", {}))
    raise ValueError(f"Unknown provider {name!r}")
