"""Tools agents may call. Same catalog for simulated and real providers. See docs/11-agent-runtime.md#tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .. import cognition, compliance
from ..knowledge import load_pack
from ..models import Finding, Proposal, RunContext
from .types import ToolSpec


@dataclass(frozen=True)
class Tool:
    spec: ToolSpec
    fn: Callable[..., Any] | None  # None for the terminal submit_result


def _req_view(r) -> dict:
    return {"id": r.id, "version": r.version, "state": r.state, "category": r.category, "title": r.title,
            "statement": r.statement, "cognitive_capability": r.cognitive_capability}


def search_knowledge(ctx: RunContext, pack: str, query: str = "") -> dict:
    data = load_pack(pack)
    entries = data.get("entries", [])
    if query:
        q = query.lower()
        entries = [e for e in entries if q in f"{e.get('title', '')} {e.get('finding', '')}".lower()]
    meta = {k: v for k, v in data.items() if k not in ("entries", "capabilities")}
    return {**meta, "entries": entries}


def get_capability_catalog(ctx: RunContext) -> dict:
    target = ctx.project.get("target_cognitive_level", "CL5")
    pack = load_pack("companion_cognition")
    return {"target_level": target, "source": pack["source"], "version": pack["version"],
            "principles": pack["principles"], "capabilities": cognition.capabilities_up_to(target)}


def get_cognitive_coverage(ctx: RunContext) -> dict:
    return {"target_level": ctx.project.get("target_cognitive_level", "CL5"),
            "specified_level": cognition.specified_level(ctx.requirements),
            "capabilities": cognition.coverage(ctx.requirements)}


def list_requirements(ctx: RunContext, category: str = "", state: str = "") -> dict:
    reqs = [r for r in ctx.requirements
            if (not category or r.category == category) and (not state or r.state == state)]
    return {"count": len(reqs), "requirements": [_req_view(r) for r in reqs]}


def list_open_proposals(ctx: RunContext) -> dict:
    return {"count": len(ctx.open_proposals),
            "proposals": [{"id": p.id, "title": p.title, "category": p.category} for p in ctx.open_proposals]}


def get_dependency_output(ctx: RunContext, agent_id: str) -> dict:
    run = next((r for r in ctx.dependency_runs if r.agent_id == agent_id), None)
    if run is None:
        raise ValueError(f"No succeeded run of {agent_id} is available to this agent")
    return run.model_dump(mode="json", include={"agent_id", "summary", "findings", "proposals"})


def run_compliance_checks(ctx: RunContext) -> dict:
    issues = compliance.checks(ctx)
    return {"issue_count": len(issues), "issues": issues}


_OBJ = {"type": "object", "properties": {}, "additionalProperties": False}

TOOLS: dict[str, Tool] = {t.spec.name: t for t in (
    Tool(ToolSpec(name="search_knowledge",
                  description="Read a versioned knowledge pack. Optional query filters entries by title or finding text.",
                  input_schema={"type": "object", "required": ["pack"], "properties": {
                      "pack": {"type": "string", "enum": ["google_assistant_reference", "production_assistants",
                                                          "customer_themes", "privacy", "distraction", "safety_security"]},
                      "query": {"type": "string"}}}), search_knowledge),
    Tool(ToolSpec(name="get_capability_catalog",
                  description="Cognitive capabilities up to the program's target level, with guidance and companion principles.",
                  input_schema=_OBJ), get_capability_catalog),
    Tool(ToolSpec(name="get_cognitive_coverage",
                  description="Which capabilities the register already covers, and the specified cognitive level.",
                  input_schema=_OBJ), get_cognitive_coverage),
    Tool(ToolSpec(name="list_requirements",
                  description="Current register items (latest version). Filter by category or state.",
                  input_schema={"type": "object", "properties": {
                      "category": {"type": "string"}, "state": {"type": "string"}}}), list_requirements),
    Tool(ToolSpec(name="list_open_proposals",
                  description="Proposals waiting in the review inbox, to avoid proposing them again.",
                  input_schema=_OBJ), list_open_proposals),
    Tool(ToolSpec(name="get_dependency_output",
                  description="Findings and proposals from the latest succeeded run of an upstream agent.",
                  input_schema={"type": "object", "required": ["agent_id"],
                                "properties": {"agent_id": {"type": "string"}}}), get_dependency_output),
    Tool(ToolSpec(name="run_compliance_checks",
                  description="Run the deterministic register checks (attributes, prefixes, verification, ASIL, trace, coverage).",
                  input_schema=_OBJ), run_compliance_checks),
    Tool(ToolSpec(name="submit_result",
                  description="Finish the run. Call exactly once with the summary, findings, and proposals.",
                  input_schema={"type": "object", "required": ["summary", "findings", "proposals"], "properties": {
                      "summary": {"type": "string", "description": "One paragraph for the control room."},
                      "findings": {"type": "array", "items": Finding.model_json_schema()},
                      "proposals": {"type": "array", "items": Proposal.model_json_schema()},
                      "metrics": {"type": "object"}}}), None),
)}
