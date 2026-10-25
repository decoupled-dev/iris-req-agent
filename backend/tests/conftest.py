import os

import pytest

os.environ.setdefault("SEW1_SIM_LATENCY_MS", "0")

from app import db  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    db.use(tmp_path / "test.db")
    yield
