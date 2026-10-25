"""Stage DAG, background runs, cancel. See docs/05-pipeline.md."""

from __future__ import annotations

import json
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor, wait
from datetime import datetime, timezone

from . import config, db, register
from .agents import AGENTS, STAGES, stage_agents
from .agents.bedrock import BedrockHarnessAgent
from .agents.remote import RemoteAgent
from .models import AgentResult, Proposal, RunContext, RunStatus
from .runtime import events
from .runtime.loop import Cancelled, run_agent
from .runtime.providers import get_provider


class DependencyError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _update_run(run_id: str, **fields) -> None:
    cols = ", ".join(f"{k} = ?" for k in fields)
    with db.connect() as conn:
        conn.execute(f"UPDATE runs SET {cols} WHERE run_id = ?", (*fields.values(), run_id))


def runs(agent_id: str | None = None) -> list[dict]:
    q, args = "SELECT run_id, agent_id, mode, status, started, finished, summary, result FROM runs", ()
    if agent_id:
        q, args = q + " WHERE agent_id = ?", (agent_id,)
    with db.connect() as conn:
        rows = conn.execute(q + " ORDER BY rowid", args).fetchall()
    return [dict(r) | {"result": json.loads(r["result"]) if r["result"] else None} for r in rows]


def latest_run(agent_id: str, status: RunStatus | None = None) -> dict | None:
    matching = [r for r in runs(agent_id) if status is None or r["status"] == status]
    return matching[-1] if matching else None


def latest_result(agent_id: str) -> AgentResult | None:
    run = latest_run(agent_id, RunStatus.succeeded)
    return AgentResult.model_validate(run["result"]) if run else None


class Orchestrator:
    def __init__(self, workers: int = 8):
        self.pool = ThreadPoolExecutor(max_workers=workers)
        self.cycle_running = threading.Event()
        self.cancels: dict[str, threading.Event] = {}
        self.futures: dict[str, Future] = {}

    def missing_dependencies(self, agent_id: str) -> list[str]:
        return [d for d in AGENTS[agent_id].depends_on if latest_result(d) is None]

    def start(self, agent_id: str) -> str:
        if agent_id not in AGENTS:
            raise KeyError(agent_id)
        if missing := self.missing_dependencies(agent_id):
            raise DependencyError(f"{', '.join(missing)} must succeed before {agent_id}")
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        mode = config.agent_config(agent_id).get("mode", "local")
        with db.connect() as conn:
            conn.execute("INSERT INTO runs (run_id, agent_id, mode, status) VALUES (?, ?, ?, ?)",
                         (run_id, agent_id, mode, RunStatus.queued))
        self.cancels[run_id] = threading.Event()
        self.futures[run_id] = self.pool.submit(self._execute, run_id, agent_id)
        return run_id

    def cancel(self, run_id: str) -> None:
        if event := self.cancels.get(run_id):
            event.set()
        _update_run(run_id, status=RunStatus.cancelled, finished=_now(), summary="Cancelled by engineer.")
        events.emit(run_id, "cancelled", {})

    def _context(self, run_id: str, agent_id: str) -> RunContext:
        deps = [r for d in AGENTS[agent_id].depends_on if (r := latest_result(d))]
        return RunContext(
            run_id=run_id, agent_id=agent_id, project=config.project(),
            requirements=register.current(), dependency_runs=deps,
            open_proposals=[Proposal.model_validate(p["proposal"]) for p in register.proposals("open")],
        )

    def _execute(self, run_id: str, agent_id: str) -> RunStatus:
        cancel = self.cancels[run_id]
        if cancel.is_set():
            return RunStatus.cancelled
        _update_run(run_id, status=RunStatus.running, started=_now())
        agent, cfg, rt = AGENTS[agent_id], config.agent_config(agent_id), config.runtime()
        emit = lambda type_, data: events.emit(run_id, type_, data)  # noqa: E731
        try:
            ctx = self._context(run_id, agent_id)
            if cfg.get("mode") == "remote":
                emit("start", {"provider": "remote", "endpoint": cfg["endpoint"]})
                result = RemoteAgent(agent_id, cfg["endpoint"], cfg.get("auth_env")).run(ctx, cancel)
            elif cfg.get("mode") == "bedrock":
                result = BedrockHarnessAgent(agent, cfg).run(ctx, cancel, emit, rt.get("max_turns", 12))
            else:
                result = run_agent(agent, ctx, get_provider(rt), cfg.get("model", rt.get("model", "")), emit,
                                   cancel, rt.get("max_turns", 12))
            if unsourced := [p.title for p in result.proposals if not p.finding_ids()]:
                raise ValueError(f"Proposals without finding ID refused: {', '.join(unsourced)}")
        except Cancelled:
            return RunStatus.cancelled
        except Exception as exc:  # A failed run is recorded, never raised into the API.
            result = AgentResult(agent_id=agent_id, status=RunStatus.failed, summary=f"{type(exc).__name__}: {exc}")
            emit("error", {"message": result.summary})
        if cancel.is_set():
            return RunStatus.cancelled
        if result.status == RunStatus.succeeded and agent.publishes:
            register.store_proposals(run_id, agent_id, result.proposals)
        _update_run(run_id, status=result.status, finished=_now(), summary=result.summary,
                    result=result.model_dump_json())
        return result.status

    def run_cycle(self) -> list[str]:
        """Full cycle, blocking: each stage starts only when every agent of the previous one succeeded."""
        started: list[str] = []
        self.cycle_running.set()
        try:
            for stage in STAGES:
                ids = [self.start(a.id) for a in stage_agents(stage)]
                started += ids
                wait([self.futures[i] for i in ids])
                if any(self.futures[i].result() != RunStatus.succeeded for i in ids):
                    break
        finally:
            self.cycle_running.clear()
        return started

    def start_cycle(self) -> bool:
        if self.cycle_running.is_set():
            return False
        self.cycle_running.set()
        threading.Thread(target=self.run_cycle, daemon=True).start()
        return True


orchestrator = Orchestrator()
