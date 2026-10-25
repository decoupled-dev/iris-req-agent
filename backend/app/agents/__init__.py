"""Agent definitions: prompt, tools, dependencies. Behaviour comes from the model provider.

See docs/03-agents.md for responsibilities and docs/11-agent-runtime.md for the runtime.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from ..models import RunContext

PROMPTS = Path(__file__).parent / "prompts"


@dataclass(frozen=True)
class AgentSpec:
    id: str
    name: str
    stage: str
    description: str
    tools: tuple[str, ...]
    depends_on: tuple[str, ...] = ()
    # Research proposals are candidates for synthesis; only publishing agents reach the inbox.
    publishes: bool = False

    @cache
    def system_prompt(self) -> str:
        return (PROMPTS / "_common.md").read_text() + "\n\n" + (PROMPTS / f"{self.id}.md").read_text()

    def task(self, ctx: RunContext) -> str:
        project = json.dumps(ctx.project)
        deps = ", ".join(r.agent_id for r in ctx.dependency_runs) or "none"
        return (f"Run {ctx.run_id} for project {project}.\n"
                f"Register: {len(ctx.requirements)} items. Inbox: {len(ctx.open_proposals)} open proposals. "
                f"Upstream runs available: {deps}.\n"
                f"Do your job as described in the system prompt and finish with submit_result.")


RESEARCH = ("google_assistant_reference", "oem_feature_research", "customer_expectations", "companion_cognition",
            "vehicle_context")
ASSURANCE = ("gdpr_privacy", "driver_distraction", "safety_cybersecurity")
_PACK_TOOLS = ("search_knowledge", "list_requirements", "submit_result")
_ASSURANCE_TOOLS = ("get_dependency_output", "search_knowledge", "list_requirements", "list_open_proposals",
                    "submit_result")

AGENTS: dict[str, AgentSpec] = {a.id: a for a in (
    AgentSpec("google_assistant_reference", "Google assistant reference", "research",
              "Driving-mode capabilities used as reference requirements", _PACK_TOOLS),
    AgentSpec("oem_feature_research", "OEM feature research", "research",
              "Production assistants: match, limit, or exclude", _PACK_TOOLS),
    AgentSpec("customer_expectations", "Customer expectations", "research",
              "Complaint and expectation themes into needs", _PACK_TOOLS),
    AgentSpec("companion_cognition", "Companion cognition", "research",
              "Cognitive capabilities up to the target level",
              ("get_capability_catalog", "get_cognitive_coverage", "list_requirements", "submit_result")),
    AgentSpec("vehicle_context", "Vehicle context", "research",
              "Signals and triggers into GIVEN/WHEN/THEN behaviour",
              ("get_vehicle_signals", "search_knowledge", "check_scenarios", "list_requirements", "submit_result")),
    AgentSpec("requirements_synthesis", "Requirements synthesis", "synthesis",
              "Merge research into one coherent shall-set",
              ("get_dependency_output", "list_requirements", "list_open_proposals", "submit_result"),
              depends_on=RESEARCH, publishes=True),
    AgentSpec("gdpr_privacy", "GDPR and privacy", "assurance",
              "Cabin audio, memory, consent, AI Act transparency", _ASSURANCE_TOOLS,
              depends_on=("requirements_synthesis",), publishes=True),
    AgentSpec("driver_distraction", "Driver distraction", "assurance",
              "Eyes-off-road, dialogue pacing, workload timing", _ASSURANCE_TOOLS,
              depends_on=("requirements_synthesis",), publishes=True),
    AgentSpec("safety_cybersecurity", "Safety and cybersecurity", "assurance",
              "Preliminary ASIL, action tiers, threat themes", _ASSURANCE_TOOLS,
              depends_on=("requirements_synthesis",), publishes=True),
    AgentSpec("compliance_gate", "Compliance gate", "gate",
              "Attributes, trace, coverage, cognitive level",
              ("run_compliance_checks", "get_cognitive_coverage", "submit_result"), depends_on=ASSURANCE),
)}

STAGES = ["research", "synthesis", "assurance", "gate"]


def stage_agents(stage: str) -> list[AgentSpec]:
    return [a for a in AGENTS.values() if a.stage == stage]
