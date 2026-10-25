"""Deterministic compliance rules behind the gate's `run_compliance_checks` tool. See docs/03-agents.md#9-compliance-gate."""

from __future__ import annotations

import re

from . import cognition, vehicle
from .models import ASIL_NOTE, CATEGORIES, INCLUDED_STATES, VERIFICATION_METHODS, RunContext, State

CL5_CAPS = {"COG-09", "COG-15", "COG-16", "COG-17"}
BEHAVIOURAL = {"SYS-FUNC", "SYS-HMI", "SYS-COG", "SYS-DIST"}
REQUIRED = ("title", "statement", "rationale", "source", "category", "priority")


def checks(ctx: RunContext) -> list[dict]:
    issues: list[dict] = []

    def issue(check: str, ref: str, title: str, detail: str, severity: str = "major"):
        issues.append({"check": check, "ref": ref, "title": title, "detail": detail, "severity": severity})

    included = [r for r in ctx.requirements if r.state in INCLUDED_STATES]
    for r in included:
        if missing := [f for f in REQUIRED if not getattr(r, f)]:
            issue("attributes", r.id, f"{r.id} missing attributes", f"Missing: {', '.join(missing)}.")
        if re.sub(r"-\d+$", "", r.id) != r.category or r.category not in CATEGORIES:
            issue("prefix", r.id, f"{r.id} prefix mismatch", f"Category {r.category} does not match the ID.")
        if r.category == "SYS-COG" and not r.cognitive_capability:
            issue("cognitive", r.id, f"{r.id} cites no capability", "SYS-COG items must cite at least one COG-xx.")
        if r.state == State.baselined:
            if r.verification_method not in VERIFICATION_METHODS or not r.acceptance_criteria:
                issue("verification", r.id, f"{r.id} lacks verification",
                      "Baselined items need a verification method and acceptance criteria.", "critical")
            if not r.source:
                issue("source", r.id, f"{r.id} has no source", "Baselined items need a source.", "critical")
            if CL5_CAPS & set(r.cognitive_capability) and "privacy" not in r.change_note.lower():
                issue("cl5-review", r.id, f"{r.id} baselined without privacy review",
                      "CL5 companion items need a privacy reviewer on the change note.", "critical")
        if r.scenario is not None:
            for v in vehicle.validate(r.scenario):
                issue(f"scenario:{v['check']}", r.id, f"{r.id} scenario: {v['check']}", v["detail"], v["severity"])
        elif r.category in BEHAVIOURAL and vehicle.REACTIVE_CAPS & set(r.cognitive_capability):
            issue("scenario-missing", r.id, f"{r.id} has no GIVEN/WHEN/THEN",
                  "Behavioural requirement reacting to vehicle state should carry a scenario.", "minor")
        if r.category == "SYS-SAFE" and r.state != State.baselined and r.asil_note != ASIL_NOTE:
            issue("asil", r.id, f"{r.id} ASIL note changed", f"Preliminary ASIL must stay marked '{ASIL_NOTE}'.")

    baselined = {r.id for r in included if r.state == State.baselined}
    for p in ctx.open_proposals:
        if p.id in baselined:
            issue("conflict", p.id, f"Open proposal changes {p.id}",
                  f"'{p.title}' proposes a new version of a baselined statement.")

    traced = {fid.strip() for r in ctx.requirements for fid in r.source.split(",")}
    traced |= {fid for p in ctx.open_proposals for fid in p.finding_ids()}
    for run in ctx.dependency_runs:
        for f in run.findings:
            if f.id not in traced:
                issue("trace", f.id, f"Untraced finding {f.id}", f"{run.agent_id}: {f.title}", "minor")

    if any("COG-12" in r.cognitive_capability for r in included) and not any(
            "COG-13" in r.cognitive_capability and r.category == "SYS-DIST" for r in included):
        issue("proactive", "COG-12", "Proactive behaviour without workload timing",
              "A COG-12 item exists but no SYS-DIST item cites COG-13.")

    used_triggers = {r.scenario.when.trigger for r in included if r.scenario}
    if any(r.scenario for r in included):
        for t in vehicle.triggers():
            if t not in used_triggers:
                issue("trigger-unused", t, f"Trigger {t} has no behaviour",
                      f"No included requirement reacts to {vehicle.triggers()[t]['label']}.", "minor")

    target = ctx.project.get("target_cognitive_level", "CL5")
    covered = {row["id"] for row in cognition.coverage(ctx.requirements) if row["covered"]}
    for cap in cognition.capabilities_up_to(target):
        if cap["id"] not in covered:
            issue("coverage", cap["id"], f"{cap['id']} {cap['title']} not covered",
                  f"No included, verifiable requirement cites {cap['id']} ({cap['level']}).")
    return issues
