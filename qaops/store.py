"""SQLite state for QAOps seams. Lives next to the existing pipeline tables in qa_pipeline.db."""

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from qaops.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS qaops_idempotency (
    idem_key TEXT PRIMARY KEY,
    scope TEXT NOT NULL,
    status TEXT NOT NULL,              -- IN_FLIGHT | DONE | FAILED
    result_json TEXT DEFAULT '{}',
    attempts INTEGER DEFAULT 1,
    completions INTEGER DEFAULT 0,
    blocked_duplicates INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS qaops_outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idem_key TEXT,
    service TEXT NOT NULL DEFAULT 'generic',
    method TEXT NOT NULL,
    url TEXT NOT NULL,
    payload_json TEXT DEFAULT 'null',
    status TEXT NOT NULL DEFAULT 'PENDING',   -- PENDING | REPLAYED | DEAD
    last_error TEXT,
    attempts INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS qaops_breaker (
    service TEXT PRIMARY KEY,
    failures INTEGER DEFAULT 0,
    opened_at REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS qaops_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service TEXT NOT NULL,
    method TEXT NOT NULL,
    attempts INTEGER NOT NULL,
    had_transient_failure INTEGER NOT NULL,
    succeeded INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS qaops_spans (
    id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    parent_id TEXT,
    issue_key TEXT,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,                -- span | generation
    level TEXT DEFAULT 'DEFAULT',
    latency_ms REAL,
    iterations INTEGER DEFAULT 1,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    model TEXT,
    metadata_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS qaops_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_key TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    passed INTEGER NOT NULL,
    details_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS qa_pipeline_events (
    event_id TEXT PRIMARY KEY,
    correlation_id TEXT NOT NULL,
    issue_key TEXT NOT NULL,
    event_type TEXT NOT NULL,
    producer TEXT NOT NULL,
    payload_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS qa_pipeline_state (
    issue_key TEXT PRIMARY KEY,
    current_stage INTEGER NOT NULL DEFAULT 1,
    stage_name TEXT NOT NULL DEFAULT 'DoR Gate',
    hitl_gate1_status TEXT NOT NULL DEFAULT 'PENDING',
    hitl_gate2_status TEXT NOT NULL DEFAULT 'PENDING',
    rqi_score REAL DEFAULT 0.0,
    last_execution_id TEXT,
    metadata_json TEXT DEFAULT '{}',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS qa_scheduled_events (
    schedule_id TEXT PRIMARY KEY,
    issue_key TEXT,
    action TEXT NOT NULL,
    target_time TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'SCHEDULED',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    payload_json TEXT DEFAULT '{}',
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS qa_pipeline_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_key TEXT,
    workflow_name TEXT NOT NULL,
    execution_id TEXT,
    failed_node TEXT,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    payload_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_qaops_metrics_issue ON qaops_metrics(issue_key, metric);
CREATE INDEX IF NOT EXISTS ix_qaops_spans_issue ON qaops_spans(issue_key);
CREATE INDEX IF NOT EXISTS ix_qa_events_issue ON qa_pipeline_events(issue_key, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_qa_events_cid ON qa_pipeline_events(correlation_id);
CREATE INDEX IF NOT EXISTS ix_qa_scheduled_pending ON qa_scheduled_events(status, target_time);
CREATE INDEX IF NOT EXISTS ix_qa_errors_issue ON qa_pipeline_errors(issue_key, created_at DESC);
"""

import uuid

_lock = threading.Lock()
_initialized: set = set()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect(db_path: Optional[Path] = None) -> Iterator[sqlite3.Connection]:
    path = Path(db_path or settings.db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        with _lock:
            if str(path) not in _initialized:
                conn.executescript(_SCHEMA)
                _initialized.add(str(path))
        yield conn
    finally:
        conn.close()


def record_event(
    correlation_id: str,
    issue_key: str,
    event_type: str,
    producer: str,
    payload: Optional[Dict[str, Any]] = None,
    db_path: Optional[Path] = None,
) -> str:
    """Records an immutable event in the Event Store stream."""
    event_id = uuid.uuid4().hex
    now = now_iso()
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO qa_pipeline_events (event_id, correlation_id, issue_key, event_type, producer, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (event_id, correlation_id, issue_key, event_type, producer, json.dumps(payload or {}, ensure_ascii=False, default=str), now),
        )
    return event_id


def get_events(
    issue_key: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 50,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Retrieves events matching the given criteria."""
    query = "SELECT * FROM qa_pipeline_events WHERE 1=1"
    params: List[Any] = []
    if issue_key:
        query += " AND issue_key = ?"
        params.append(issue_key)
    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with connect(db_path) as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
    return [
        {
            "event_id": r["event_id"],
            "correlation_id": r["correlation_id"],
            "issue_key": r["issue_key"],
            "event_type": r["event_type"],
            "producer": r["producer"],
            "payload": json.loads(r["payload_json"] or "{}"),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def update_pipeline_state(
    issue_key: str,
    stage_idx: int,
    stage_name: str,
    hitl_gate1: Optional[str] = None,
    hitl_gate2: Optional[str] = None,
    rqi: Optional[float] = None,
    execution_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[Path] = None,
) -> None:
    """Updates or inserts the materialized pipeline state for a task."""
    now = now_iso()
    with connect(db_path) as conn:
        existing = conn.execute("SELECT * FROM qa_pipeline_state WHERE issue_key = ?", (issue_key,)).fetchone()
        if existing:
            g1 = hitl_gate1 if hitl_gate1 is not None else existing["hitl_gate1_status"]
            g2 = hitl_gate2 if hitl_gate2 is not None else existing["hitl_gate2_status"]
            r_val = rqi if rqi is not None else existing["rqi_score"]
            exec_id = execution_id if execution_id is not None else existing["last_execution_id"]
            meta = {**json.loads(existing["metadata_json"] or "{}"), **(metadata or {})}
            conn.execute(
                """
                UPDATE qa_pipeline_state
                SET current_stage = ?, stage_name = ?, hitl_gate1_status = ?, hitl_gate2_status = ?,
                    rqi_score = ?, last_execution_id = ?, metadata_json = ?, updated_at = ?
                WHERE issue_key = ?
                """,
                (stage_idx, stage_name, g1, g2, r_val, exec_id, json.dumps(meta, ensure_ascii=False, default=str), now, issue_key),
            )
        else:
            conn.execute(
                """
                INSERT INTO qa_pipeline_state (issue_key, current_stage, stage_name, hitl_gate1_status, hitl_gate2_status, rqi_score, last_execution_id, metadata_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (issue_key, stage_idx, stage_name, hitl_gate1 or "PENDING", hitl_gate2 or "PENDING", rqi or 0.0, execution_id, json.dumps(metadata or {}, ensure_ascii=False, default=str), now),
            )


def get_pipeline_state(issue_key: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Retrieves current pipeline state projection for an issue."""
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM qa_pipeline_state WHERE issue_key = ?", (issue_key,)).fetchone()
    if not row:
        return None
    return {
        "issue_key": row["issue_key"],
        "current_stage": row["current_stage"],
        "stage_name": row["stage_name"],
        "hitl_gate1_status": row["hitl_gate1_status"],
        "hitl_gate2_status": row["hitl_gate2_status"],
        "rqi_score": row["rqi_score"],
        "last_execution_id": row["last_execution_id"],
        "metadata": json.loads(row["metadata_json"] or "{}"),
        "updated_at": row["updated_at"],
    }


def schedule_event(
    action: str,
    target_time_iso: str,
    issue_key: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
    db_path: Optional[Path] = None,
) -> str:
    """Enqueues an action to be executed in the future or on retry."""
    schedule_id = uuid.uuid4().hex
    now = now_iso()
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO qa_scheduled_events (schedule_id, issue_key, action, target_time, status, retry_count, max_retries, payload_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'SCHEDULED', 0, ?, ?, ?, ?)
            """,
            (schedule_id, issue_key, action, target_time_iso, max_retries, json.dumps(payload or {}, ensure_ascii=False, default=str), now, now),
        )
    return schedule_id


def fetch_due_scheduled_events(limit: int = 10, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Fetches scheduled events that are ready to run."""
    now = now_iso()
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM qa_scheduled_events
            WHERE status = 'SCHEDULED' AND target_time <= ?
            ORDER BY target_time ASC
            LIMIT ?
            """,
            (now, limit),
        ).fetchall()
    return [
        {
            "schedule_id": r["schedule_id"],
            "issue_key": r["issue_key"],
            "action": r["action"],
            "target_time": r["target_time"],
            "status": r["status"],
            "retry_count": r["retry_count"],
            "max_retries": r["max_retries"],
            "payload": json.loads(r["payload_json"] or "{}"),
        }
        for r in rows
    ]


def mark_scheduled_event(
    schedule_id: str,
    status: str,
    error: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> None:
    """Updates the status of a scheduled event."""
    now = now_iso()
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE qa_scheduled_events
            SET status = ?, last_error = ?, updated_at = ?
            WHERE schedule_id = ?
            """,
            (status, error[:1000] if error else None, now, schedule_id),
        )


def record_metric(issue_key: str, metric: str, value: float, passed: bool, details: Optional[Dict[str, Any]] = None, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO qaops_metrics (issue_key, metric, value, passed, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (issue_key, metric, float(value), int(bool(passed)), json.dumps(details or {}, ensure_ascii=False, default=str), now_iso()),
        )


def latest_metrics(issue_key: str, db_path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT m.* FROM qaops_metrics m
            JOIN (SELECT metric, MAX(id) AS max_id FROM qaops_metrics WHERE issue_key = ? GROUP BY metric) last
              ON m.id = last.max_id
            """,
            (issue_key,),
        ).fetchall()
    return {r["metric"]: {"value": r["value"], "passed": bool(r["passed"]), "details": json.loads(r["details_json"] or "{}"), "at": r["created_at"]} for r in rows}


def record_pipeline_error(
    issue_key: Optional[str],
    workflow_name: str,
    execution_id: Optional[str],
    failed_node: Optional[str],
    error_message: str,
    stack_trace: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    db_path: Optional[Path] = None,
) -> int:
    """Persists a workflow or pipeline error into qa_pipeline_errors."""
    now = now_iso()
    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO qa_pipeline_errors (
                issue_key, workflow_name, execution_id, failed_node, error_message, stack_trace, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                issue_key,
                workflow_name,
                execution_id,
                failed_node,
                error_message,
                stack_trace,
                json.dumps(payload or {}, ensure_ascii=False, default=str),
                now,
            ),
        )
        return cursor.lastrowid


def rows(query: str, params: tuple = (), db_path: Optional[Path] = None) -> List[sqlite3.Row]:
    with connect(db_path) as conn:
        return conn.execute(query, params).fetchall()

