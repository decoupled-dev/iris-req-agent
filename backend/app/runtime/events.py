"""Run trace events, stored per run for the control room. Types: docs/11-agent-runtime.md#events."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from .. import db


def emit(run_id: str, type_: str, data: dict | None = None) -> None:
    with db.connect() as conn:
        seq = conn.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM run_events WHERE run_id = ?", (run_id,)).fetchone()[0]
        conn.execute("INSERT INTO run_events (run_id, seq, ts, type, data) VALUES (?, ?, ?, ?, ?)",
                     (run_id, seq, datetime.now(timezone.utc).isoformat(timespec="milliseconds"), type_,
                      json.dumps(data or {}, default=str)))


def list_events(run_id: str, after: int = 0) -> list[dict]:
    with db.connect() as conn:
        rows = conn.execute("SELECT seq, ts, type, data FROM run_events WHERE run_id = ? AND seq > ? ORDER BY seq",
                            (run_id, after)).fetchall()
    return [{"seq": r["seq"], "ts": r["ts"], "type": r["type"], "data": json.loads(r["data"])} for r in rows]
