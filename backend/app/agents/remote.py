"""HTTP client for a remote worker. Contract: docs/07-remote-agents.md."""

from __future__ import annotations

import os
import threading
import time

import httpx

from ..models import AgentResult, RunContext, RunStatus

TERMINAL = {RunStatus.succeeded, RunStatus.failed, RunStatus.cancelled}


class RemoteAgent:
    def __init__(self, agent_id: str, endpoint: str, auth_env: str | None = None, poll_seconds: float = 2.0):
        self.agent_id, self.endpoint, self.poll_seconds = agent_id, endpoint.rstrip("/"), poll_seconds
        token = os.environ.get(auth_env, "") if auth_env else ""
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def run(self, ctx: RunContext, cancel: threading.Event) -> AgentResult:
        body = ctx.model_dump(mode="json", exclude={"open_proposals"})
        with httpx.Client(headers=self.headers, timeout=30) as client:
            client.post(f"{self.endpoint}/runs", json=body).raise_for_status()
            while True:
                if cancel.is_set():
                    try:
                        client.post(f"{self.endpoint}/runs/{ctx.run_id}/cancel")
                    except httpx.HTTPError:
                        pass  # The workbench marks the run cancelled locally either way.
                    return AgentResult(agent_id=self.agent_id, status=RunStatus.cancelled, summary="Cancelled.")
                data = client.get(f"{self.endpoint}/runs/{ctx.run_id}").raise_for_status().json()
                if data.get("status") in TERMINAL:
                    return AgentResult.model_validate({"agent_id": self.agent_id, "summary": "", **data})
                time.sleep(self.poll_seconds)
