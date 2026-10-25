"""Handoff data gathered from the register at download time. See docs/06-export.md."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .. import cognition, config, orchestrator, register
from ..models import ASIL_NOTE, Requirement, State


@dataclass
class Handoff:
    project: dict
    exported_at: datetime
    requirements: list[Requirement]
    state_counts: dict[str, int]
    target_level: str
    specified_level: str
    coverage: list[dict]
    traceability: list[dict]
    open_items: list[dict]
    run_log: list[dict] = field(default_factory=list)

    def stamp(self) -> str:
        return self.exported_at.strftime("%Y%m%d")


def gather() -> Handoff:
    reqs = register.included()
    project = config.project()
    target = project.get("target_cognitive_level", "CL5")

    findings = {}
    for run in orchestrator.runs():
        for f in (run["result"] or {}).get("findings", []):
            findings[f["id"]] = (run["agent_id"], f)
    trace = []
    for r in reqs:
        for fid in filter(None, (s.strip() for s in r.source.split(","))):
            agent, f = findings.get(fid, ("", {}))
            trace.append({"requirement_id": r.id, "requirement_title": r.title, "finding_id": fid,
                          "agent": agent, "finding_title": f.get("title", ""), "source": f.get("source", "")})

    coverage = cognition.coverage(reqs)
    open_items = []
    gate = orchestrator.latest_result("compliance_gate")
    for f in gate.findings if gate else []:
        open_items.append({"kind": "Gate finding", "id": f.id, "state": "Open", "summary": f.title,
                           "owner": "Systems engineering"})
    for r in reqs:
        if r.state in (State.draft, State.in_review):
            open_items.append({"kind": "Requirement", "id": r.id, "state": r.state, "summary": r.title,
                               "owner": "Reviewer for " + r.category})
        if r.category == "SYS-SAFE" and r.asil_note == ASIL_NOTE:
            open_items.append({"kind": "ASIL confirmation", "id": r.id, "state": r.state,
                               "summary": f"Preliminary ASIL {r.preliminary_asil}", "owner": "Safety manager"})
    for row in coverage:
        if not row["covered"] and cognition.LEVELS.index(row["level"]) <= cognition.LEVELS.index(target):
            open_items.append({"kind": "Cognitive coverage", "id": row["id"], "state": "Uncovered",
                               "summary": row["title"], "owner": "Systems engineering"})

    return Handoff(
        project=project, exported_at=datetime.now(timezone.utc), requirements=reqs,
        state_counts=dict(Counter(str(r.state) for r in reqs)), target_level=target,
        specified_level=cognition.specified_level(reqs), coverage=coverage, traceability=trace,
        open_items=open_items,
        run_log=[{**{k: r[k] for k in ("run_id", "agent_id", "mode", "status", "started", "finished", "summary")},
                  **{k: ((r["result"] or {}).get("metrics") or {}).get(k, "")
                     for k in ("provider", "model", "turns", "input_tokens", "output_tokens")}}
                 for r in orchestrator.runs()],
    )
