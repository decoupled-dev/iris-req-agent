"""Workbench API. Surfaces: docs/02-architecture.md#workbench-ui."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from . import cognition, config, db, orchestrator as orch, register
from .agents import AGENTS
from .export import excel, gather, word
from .models import State
from .orchestrator import DependencyError, orchestrator
from .runtime import events


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init()
    yield


app = FastAPI(title="SEW1 workbench", lifespan=lifespan)


@app.get("/api/project")
def project():
    gate = orch.latest_result("compliance_gate")
    reqs = register.included()
    return {**config.project(),
            "specified_cognitive_level": cognition.specified_level(reqs),
            "gate_level": gate.metrics.get("specified_cognitive_level") if gate else None}


@app.get("/api/agents")
def agents():
    return [{"id": a.id, "name": a.name, "stage": a.stage, "description": a.description,
             "depends_on": a.depends_on, "tools": a.tools, "publishes": a.publishes,
             "mode": config.agent_config(a.id).get("mode", "local"),
             "latest_run": orch.latest_run(a.id)} for a in AGENTS.values()]


@app.get("/api/agents/{agent_id}/prompt")
def agent_prompt(agent_id: str):
    from .runtime.tools import TOOLS
    if agent_id not in AGENTS:
        raise HTTPException(404, f"Unknown agent {agent_id}")
    a = AGENTS[agent_id]
    return {"system": a.system_prompt(), "tools": [TOOLS[t].spec for t in a.tools]}


@app.post("/api/agents/{agent_id}/runs", status_code=202)
def start_agent(agent_id: str):
    try:
        return {"run_id": orchestrator.start(agent_id)}
    except KeyError:
        raise HTTPException(404, f"Unknown agent {agent_id}")
    except DependencyError as exc:
        raise HTTPException(409, str(exc))


@app.post("/api/pipeline/runs", status_code=202)
def start_pipeline():
    if not orchestrator.start_cycle():
        raise HTTPException(409, "A full cycle is already running")
    return {"status": "started"}


@app.get("/api/runtime")
def runtime():
    rt = config.runtime()
    return {"provider": rt.get("provider"), "model": rt.get("model"), "max_turns": rt.get("max_turns", 12),
            "options": rt.get(rt.get("provider"), {})}


@app.get("/api/overview")
def overview():
    current = register.current()
    included = [r for r in current if r.state in (State.draft, State.in_review, State.baselined)]
    gate = orch.latest_result("compliance_gate")
    by_state, by_cat = {}, {}
    for r in current:
        by_state[r.state] = by_state.get(r.state, 0) + 1
    for r in included:
        by_cat[r.category] = by_cat.get(r.category, 0) + 1
    all_runs = orch.runs()
    return {
        "requirements": len(included), "by_state": by_state, "by_category": by_cat,
        "inbox": len(register.proposals("open")),
        "target_cognitive_level": config.project().get("target_cognitive_level"),
        "specified_cognitive_level": cognition.specified_level(included),
        "gate": {"findings": len(gate.findings), **gate.metrics} if gate else None,
        "cycle_running": orchestrator.cycle_running.is_set(),
        "runs": len(all_runs),
        "tokens": sum(((r["result"] or {}).get("metrics", {}).get("input_tokens", 0)
                       + (r["result"] or {}).get("metrics", {}).get("output_tokens", 0)) for r in all_runs),
    }


@app.get("/api/findings")
def findings():
    out = {}
    for a in AGENTS:
        if run := orch.latest_run(a, "succeeded"):
            for f in (run["result"] or {}).get("findings", []):
                out[f["id"]] = {**f, "agent_id": a, "run_id": run["run_id"]}
    return out


@app.get("/api/runs")
def runs(agent_id: str | None = None):
    return orch.runs(agent_id)


@app.get("/api/runs/{run_id}")
def run_detail(run_id: str):
    match = [r for r in orch.runs() if r["run_id"] == run_id]
    if not match:
        raise HTTPException(404, f"Unknown run {run_id}")
    return match[0]


@app.get("/api/runs/{run_id}/events")
def run_events(run_id: str, after: int = 0):
    return events.list_events(run_id, after)


@app.post("/api/runs/{run_id}/cancel")
def cancel(run_id: str):
    orchestrator.cancel(run_id)
    return {"run_id": run_id, "status": "cancelled"}


@app.get("/api/requirements")
def requirements():
    return register.current()


@app.get("/api/requirements/{req_id}/history")
def requirement_history(req_id: str):
    return register.history(req_id)


class NewRequirement(BaseModel):
    category: str
    title: str
    statement: str
    rationale: str = ""
    priority: str = "Must"
    cognitive_capability: list[str] = []
    verification_method: str = ""
    acceptance_criteria: str = ""


@app.post("/api/requirements", status_code=201)
def add_requirement(body: NewRequirement):
    try:
        return register.add(body.model_dump())
    except register.RegisterError as exc:
        raise HTTPException(400, str(exc))


class EditRequirement(BaseModel):
    fields: dict
    change_note: str


@app.patch("/api/requirements/{req_id}")
def edit_requirement(req_id: str, body: EditRequirement):
    try:
        return register.edit(req_id, body.fields, body.change_note)
    except register.RegisterError as exc:
        raise HTTPException(400, str(exc))


@app.get("/api/proposals")
def proposals(status: str | None = "open"):
    return register.proposals(status)


class Accept(BaseModel):
    state: State = State.draft
    role: str = "systems_engineer"
    edits: dict | None = None


@app.post("/api/proposals/{pk}/accept")
def accept(pk: int, body: Accept):
    try:
        return register.accept(pk, body.state, body.role, body.edits)
    except register.RegisterError as exc:
        raise HTTPException(400, str(exc))


class Bulk(BaseModel):
    pks: list[int]
    action: str  # accept | reject
    state: State = State.draft
    role: str = "systems_engineer"


@app.post("/api/proposals/bulk")
def bulk(body: Bulk):
    done, errors = 0, []
    for pk in body.pks:
        try:
            if body.action == "accept":
                register.accept(pk, body.state, body.role)
            else:
                register.reject(pk)
            done += 1
        except register.RegisterError as exc:
            errors.append(str(exc))
    return {"done": done, "errors": errors}


@app.post("/api/proposals/{pk}/reject")
def reject(pk: int):
    try:
        register.reject(pk)
    except register.RegisterError as exc:
        raise HTTPException(400, str(exc))
    return {"pk": pk, "status": "rejected"}


@app.get("/api/cognition")
def cognitive_coverage():
    reqs = register.included()
    return {"target": config.project().get("target_cognitive_level"),
            "specified": cognition.specified_level(reqs), "capabilities": cognition.coverage(reqs)}


XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@app.get("/api/export/excel")
def export_excel():
    h = gather()
    return Response(excel.build(h), media_type=XLSX,
                    headers={"Content-Disposition": f'attachment; filename="{excel.filename(h)}"'})


@app.get("/api/export/word")
def export_word():
    h = gather()
    return Response(word.build(h), media_type=DOCX,
                    headers={"Content-Disposition": f'attachment; filename="{word.filename(h)}"'})
