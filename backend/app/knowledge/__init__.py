"""Versioned knowledge packs. Reviewed source: docs/08-knowledge-baseline.md and docs/09-cognitive-companion.md."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

PACK_DIR = Path(__file__).parent / "packs"


@lru_cache
def load_pack(name: str) -> dict:
    with (PACK_DIR / f"{name}.yaml").open() as f:
        return yaml.safe_load(f)
