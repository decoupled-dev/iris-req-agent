"""Register rules: identifiers, versions, accept and reject. See docs/04-requirements.md."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from . import db
from .models import CATEGORIES, INCLUDED_STATES, Proposal, Requirement, State

# Roles allowed to move an item to Baselined (docs/05-pipeline.md#roles).
BASELINE_ROLES = {"baseline_owner", "safety_manager"}


class RegisterError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row(r) -> Requirement:
    return Requirement.model_validate(json.loads(r["data"]))


def current() -> list[Requirement]:
    """Latest version of every requirement that is not Superseded."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT r.data FROM requirements r "
            "JOIN (SELECT id, MAX(version) v FROM requirements GROUP BY id) m "
            "ON r.id = m.id AND r.version = m.v ORDER BY r.id"
        ).fetchall()
    return [_row(r) for r in rows]


def included() -> list[Requirement]:
    return [r for r in current() if r.state in INCLUDED_STATES]


def history(req_id: str) -> list[Requirement]:
    with db.connect() as conn:
        rows = conn.execute("SELECT data FROM requirements WHERE id = ? ORDER BY version", (req_id,)).fetchall()
    return [_row(r) for r in rows]


def get(req_id: str) -> Requirement | None:
    versions = history(req_id)
    return versions[-1] if versions else None


def next_id(category: str) -> str:
    if category not in CATEGORIES:
        raise RegisterError(f"Unknown category {category}")
    with db.connect() as conn:
        ids = [r["id"] for r in conn.execute("SELECT DISTINCT id FROM requirements WHERE category = ?", (category,))]
    numbers = [int(m.group(1)) for i in ids if (m := re.search(r"-(\d+)$", i))]
    return f"{category}-{max(numbers, default=0) + 1:03d}"


def _insert(req: Requirement) -> Requirement:
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO requirements (id, version, state, category, data) VALUES (?, ?, ?, ?, ?)",
            (req.id, req.version, req.state, req.category, req.model_dump_json()),
        )
    return req


def _set_state(req: Requirement, state: State) -> None:
    req.state = state
    with db.connect() as conn:
        conn.execute(
            "UPDATE requirements SET state = ?, data = ? WHERE id = ? AND version = ?",
            (state, req.model_dump_json(), req.id, req.version),
        )


def _check_state(state: State, role: str) -> None:
    if state not in INCLUDED_STATES:
        raise RegisterError(f"Cannot accept into {state}")
    if state == State.baselined and role not in BASELINE_ROLES:
        raise RegisterError(f"Role {role!r} may not baseline")


def add(fields: dict, author: str = "engineer") -> Requirement:
    """Engineer adds a requirement directly: next free ID, Draft, version 1."""
    req = Requirement.model_validate(
        {**fields, "id": next_id(fields["category"]), "version": 1, "state": State.draft,
         "updated_at": _now(), "updated_by": author}
    )
    return _insert(req)


def edit(req_id: str, fields: dict, change_note: str, author: str = "engineer") -> Requirement:
    """In-place edit of a Draft or In Review item as a new version."""
    prev = get(req_id)
    if prev is None:
        raise RegisterError(f"{req_id} not found")
    if prev.state not in (State.draft, State.in_review):
        raise RegisterError(f"{req_id} is {prev.state}; accept a new version instead")
    new = prev.model_copy(update={**fields, "version": prev.version + 1, "change_note": change_note,
                                  "updated_at": _now(), "updated_by": author})
    _set_state(prev, State.superseded)
    return _insert(new)


def store_proposals(run_id: str, agent_id: str, proposals: list[Proposal]) -> None:
    with db.connect() as conn:
        conn.executemany(
            "INSERT INTO proposals (run_id, agent_id, data, created_at) VALUES (?, ?, ?, ?)",
            [(run_id, agent_id, p.model_dump_json(), _now()) for p in proposals],
        )


def proposals(status: str | None = "open") -> list[dict]:
    q, args = "SELECT * FROM proposals", ()
    if status:
        q, args = q + " WHERE status = ?", (status,)
    with db.connect() as conn:
        rows = conn.execute(q + " ORDER BY pk", args).fetchall()
    return [{"pk": r["pk"], "run_id": r["run_id"], "agent_id": r["agent_id"], "status": r["status"],
             "resolved_id": r["resolved_id"], "proposal": json.loads(r["data"])} for r in rows]


def _proposal(pk: int) -> tuple[Proposal, str]:
    with db.connect() as conn:
        row = conn.execute("SELECT data, status, agent_id FROM proposals WHERE pk = ?", (pk,)).fetchone()
    if row is None:
        raise RegisterError(f"Proposal {pk} not found")
    if row["status"] != "open":
        raise RegisterError(f"Proposal {pk} is already {row['status']}")
    return Proposal.model_validate_json(row["data"]), row["agent_id"]


def accept(pk: int, state: State = State.draft, role: str = "systems_engineer",
           edits: dict | None = None, author: str = "engineer") -> Requirement:
    """Accept a proposal as a new requirement or as a new version of an existing one."""
    _check_state(state, role)
    prop, agent_id = _proposal(pk)
    if edits:
        prop = prop.model_copy(update=edits)
    fields = prop.model_dump(exclude={"id"})
    change_note = f"{prop.change_note} (accepted by {role}, from {agent_id})"
    prev = get(prop.id) if prop.id else None
    if prev is not None:
        req = prev.model_copy(update={**fields, "version": prev.version + 1, "state": state,
                                      "change_note": change_note, "updated_at": _now(), "updated_by": author})
        _set_state(prev, State.superseded)
    else:
        # A suggested ID that is not yet in the register is renumbered by the workbench.
        req = Requirement.model_validate({**fields, "id": next_id(prop.category), "version": 1, "state": state,
                                          "change_note": change_note, "updated_at": _now(), "updated_by": author})
    _insert(req)
    with db.connect() as conn:
        conn.execute("UPDATE proposals SET status = 'accepted', resolved_id = ? WHERE pk = ?", (req.id, pk))
    return req


def reject(pk: int) -> None:
    _proposal(pk)
    with db.connect() as conn:
        conn.execute("UPDATE proposals SET status = 'rejected' WHERE pk = ?", (pk,))
