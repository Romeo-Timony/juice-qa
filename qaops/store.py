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

CREATE INDEX IF NOT EXISTS ix_qaops_metrics_issue ON qaops_metrics(issue_key, metric);
CREATE INDEX IF NOT EXISTS ix_qaops_spans_issue ON qaops_spans(issue_key);
"""

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


def rows(query: str, params: tuple = (), db_path: Optional[Path] = None) -> List[sqlite3.Row]:
    with connect(db_path) as conn:
        return conn.execute(query, params).fetchall()
