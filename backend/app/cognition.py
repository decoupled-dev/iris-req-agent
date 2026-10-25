"""Cognitive capability catalog and coverage rule. See docs/09-cognitive-companion.md."""

from __future__ import annotations

from functools import lru_cache

from .knowledge import load_pack
from .models import Requirement, INCLUDED_STATES

LEVELS = ["CL0", "CL1", "CL2", "CL3", "CL4", "CL5"]


@lru_cache
def catalog() -> list[dict]:
    return load_pack("companion_cognition")["capabilities"]


def capabilities_up_to(level: str) -> list[dict]:
    limit = LEVELS.index(level)
    return [c for c in catalog() if LEVELS.index(c["level"]) <= limit]


def is_covering(req: Requirement) -> bool:
    return req.state in INCLUDED_STATES and bool(req.verification_method) and bool(req.acceptance_criteria)


def coverage(register: list[Requirement]) -> list[dict]:
    """One row per capability: covered flag and the requirement IDs that cover it."""
    rows = []
    for cap in catalog():
        ids = [r.id for r in register if cap["id"] in r.cognitive_capability and is_covering(r)]
        rows.append({"id": cap["id"], "faculty": cap["faculty"], "title": cap["title"],
                     "level": cap["level"], "covered": bool(ids), "requirement_ids": ids})
    return rows


def specified_level(register: list[Requirement]) -> str:
    """Highest CLn for which every capability at CL1..CLn is covered."""
    covered = {row["id"] for row in coverage(register) if row["covered"]}
    reached = "CL0"
    for level in LEVELS[1:]:
        caps = [c["id"] for c in catalog() if c["level"] == level]
        if not all(c in covered for c in caps):
            break
        reached = level
    return reached
