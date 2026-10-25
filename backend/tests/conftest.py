import os

import pytest

os.environ.setdefault("SEW1_SIM_LATENCY_MS", "0")
# The checked-in companion agent calls Bedrock. Tests stay on the local simulator.
os.environ.setdefault("SEW1_FORCE_LOCAL", "1")

from app import db  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    db.use(tmp_path / "test.db")
    yield
