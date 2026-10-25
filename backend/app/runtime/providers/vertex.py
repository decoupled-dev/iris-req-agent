"""Claude on Vertex AI adapter — swap point, not yet selected by the program.

Auth: gcloud application-default credentials, project_id, region.
Mapping from app.runtime.types: Same mapping as the Claude API adapter; only client construction and auth differ.
Contract: return a ModelTurn whose tool_calls name tools from the request; the loop
in app/runtime/loop.py does the rest. See docs/11-agent-runtime.md#swapping-in-a-real-provider.
"""

from __future__ import annotations

from ..types import ModelRequest, ModelTurn


class VertexProvider:
    name = "vertex"

    def __init__(self, **options):
        self.options = options

    def generate(self, request: ModelRequest) -> ModelTurn:
        raise NotImplementedError("Claude on Vertex AI provider is not implemented yet; set runtime.provider: simulated")
