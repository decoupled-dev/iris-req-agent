"""Shared result and register shapes. See docs/03-agents.md and docs/04-requirements.md."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RunStatus(StrEnum):
    idle = "idle"
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class State(StrEnum):
    proposed = "Proposed"
    draft = "Draft"
    in_review = "In Review"
    baselined = "Baselined"
    rejected = "Rejected"
    superseded = "Superseded"


# States that count as part of the handoff and for cognitive coverage.
INCLUDED_STATES = (State.draft, State.in_review, State.baselined)

CATEGORIES = ("STK", "SYS-FUNC", "SYS-PERF", "SYS-HMI", "SYS-COG", "SYS-SAFE", "SYS-SEC", "SYS-PRIV", "SYS-DIST")
VERIFICATION_METHODS = ("Test", "Analysis", "Inspection", "Demonstration")
ASIL_NOTE = "to be confirmed by the safety manager"


class Condition(BaseModel):
    """GIVEN clause: a catalog signal compared with a value or, as "@alias", another signal."""

    signal: str
    op: str  # == != < > <= >= in known
    value: Any = None
    note: str = ""


class When(BaseModel):
    trigger: str
    intent: str = ""
    example: str = ""


class Response(BaseModel):
    """THEN clause. `target` is a signal alias or family; `zone` is a zone, "speaker", or "all"."""

    type: str  # ACT CONFIRM_THEN_ACT ASK SUGGEST INFORM DEFER REFUSE
    target: str = ""
    zone: str = ""
    value: Any = None
    say: str = ""
    note: str = ""


class Scenario(BaseModel):
    """Behavioural specification: GIVEN conditions, WHEN one trigger, THEN the companion's responses.

    See docs/12-vehicle-context.md.
    """

    given: list[Condition] = Field(default_factory=list)
    when: When
    then: list[Response]


class Finding(BaseModel):
    id: str
    title: str
    statement: str
    source: str
    confidence: str = "high"


class Proposal(BaseModel):
    # Empty id means "new requirement"; an existing register id means "new version of it".
    id: str = ""
    title: str
    statement: str
    rationale: str
    # Comma-separated finding IDs. Must not be empty for agent proposals.
    source: str
    category: str
    priority: str = "Must"
    preliminary_asil: str = ""
    asil_note: str = ""
    cognitive_capability: list[str] = Field(default_factory=list)
    standard_references: list[str] = Field(default_factory=list)
    verification_method: str = "Test"
    acceptance_criteria: str = ""
    scenario: Scenario | None = None
    change_note: str = "Initial proposal"

    def finding_ids(self) -> list[str]:
        return [s.strip() for s in self.source.split(",") if s.strip()]


class AgentResult(BaseModel):
    agent_id: str
    status: RunStatus
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    proposals: list[Proposal] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class Requirement(BaseModel):
    id: str
    version: int = 1
    state: State = State.draft
    title: str
    statement: str
    rationale: str = ""
    source: str = "engineer"
    category: str
    priority: str = "Must"
    preliminary_asil: str = ""
    asil_note: str = ""
    cognitive_capability: list[str] = Field(default_factory=list)
    standard_references: list[str] = Field(default_factory=list)
    verification_method: str = ""
    acceptance_criteria: str = ""
    scenario: Scenario | None = None
    change_note: str = "Initial version"
    updated_at: str = ""
    updated_by: str = ""


class RunContext(BaseModel):
    """Input an agent receives; mirrors the remote POST body in docs/07-remote-agents.md."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    run_id: str
    agent_id: str
    project: dict[str, Any]
    # "register" on the wire; renamed here because BaseModel already has a `register` attribute.
    requirements: list[Requirement] = Field(alias="register")
    dependency_runs: list[AgentResult]
    open_proposals: list[Proposal] = Field(default_factory=list)
