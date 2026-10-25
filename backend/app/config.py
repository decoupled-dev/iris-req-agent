"""Loads config/agents.yaml. See docs/02-architecture.md#configuration."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(os.environ.get("SEW1_CONFIG", REPO_ROOT / "config" / "agents.yaml"))
DB_PATH = Path(os.environ.get("SEW1_DB", REPO_ROOT / "backend" / "sew1.db"))


@lru_cache
def load() -> dict[str, Any]:
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def project() -> dict[str, Any]:
    return load()["project"]


def runtime() -> dict[str, Any]:
    return load().get("runtime") or {"provider": "simulated", "model": "sim-companion-1"}


def agent_config(agent_id: str) -> dict[str, Any]:
    return load().get("agents", {}).get(agent_id) or {"mode": "local"}
