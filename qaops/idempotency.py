"""
Seam 4a: idempotency keys in SQLite.

A mutating side effect (Qase write, Jira transition, git push) is executed at most once
per key. Repeated webhooks / daemon restarts hit the stored result instead of the API.
"""

import hashlib
import json
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from qaops import store

IN_FLIGHT_TTL = timedelta(minutes=10)


class DuplicateInFlight(RuntimeError):
    """Another worker currently holds this key; the caller must not repeat the side effect."""


def make_key(scope: str, *parts: Any) -> str:
    digest = hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:32]
    return f"{scope}:{digest}"


class Guard:
    def __init__(self, key: str, duplicate: bool, result: Optional[Dict[str, Any]] = None):
        self.key = key
        self.duplicate = duplicate
        self.result = result or {}
        self._completed = duplicate

    def complete(self, result: Optional[Dict[str, Any]] = None, db_path: Optional[Path] = None) -> None:
        complete(self.key, result, db_path)
        self.result = result or {}
        self._completed = True


def begin(key: str, scope: str, db_path: Optional[Path] = None) -> Guard:
    now = store.now_iso()
    with store.connect(db_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute("SELECT * FROM qaops_idempotency WHERE idem_key = ?", (key,)).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO qaops_idempotency (idem_key, scope, status, created_at, updated_at) VALUES (?, ?, 'IN_FLIGHT', ?, ?)",
                    (key, scope, now, now),
                )
                conn.execute("COMMIT")
                return Guard(key, duplicate=False)

            if row["status"] == "DONE":
                conn.execute("UPDATE qaops_idempotency SET blocked_duplicates = blocked_duplicates + 1, updated_at = ? WHERE idem_key = ?", (now, key))
                conn.execute("COMMIT")
                return Guard(key, duplicate=True, result=json.loads(row["result_json"] or "{}"))

            stale = datetime.fromisoformat(row["updated_at"]) < datetime.now(timezone.utc) - IN_FLIGHT_TTL
            if row["status"] == "IN_FLIGHT" and not stale:
                conn.execute("UPDATE qaops_idempotency SET blocked_duplicates = blocked_duplicates + 1 WHERE idem_key = ?", (key,))
                conn.execute("COMMIT")
                raise DuplicateInFlight(key)

            conn.execute(
                "UPDATE qaops_idempotency SET status = 'IN_FLIGHT', attempts = attempts + 1, updated_at = ? WHERE idem_key = ?",
                (now, key),
            )
            conn.execute("COMMIT")
            return Guard(key, duplicate=False)
        except DuplicateInFlight:
            raise
        except Exception:
            conn.execute("ROLLBACK")
            raise


def complete(key: str, result: Optional[Dict[str, Any]] = None, db_path: Optional[Path] = None) -> None:
    with store.connect(db_path) as conn:
        conn.execute(
            "UPDATE qaops_idempotency SET status = 'DONE', completions = completions + 1, result_json = ?, updated_at = ? WHERE idem_key = ?",
            (json.dumps(result or {}, ensure_ascii=False, default=str), store.now_iso(), key),
        )


def fail(key: str, error: str, db_path: Optional[Path] = None) -> None:
    with store.connect(db_path) as conn:
        conn.execute(
            "UPDATE qaops_idempotency SET status = 'FAILED', result_json = ?, updated_at = ? WHERE idem_key = ?",
            (json.dumps({"error": error[:1000]}, ensure_ascii=False), store.now_iso(), key),
        )


@contextmanager
def idempotent(scope: str, *parts: Any, db_path: Optional[Path] = None) -> Iterator[Guard]:
    """
    with idempotent("jira.transition", issue_key, "31") as g:
        if not g.duplicate:
            do_side_effect()
            g.complete({"ok": True})
    """
    key = make_key(scope, *parts)
    guard = begin(key, scope, db_path)
    try:
        yield guard
        if not guard._completed:
            guard.complete({}, db_path)
    except Exception as exc:
        if not guard.duplicate:
            fail(key, f"{type(exc).__name__}: {exc}", db_path)
        raise


def stats(db_path: Optional[Path] = None) -> Dict[str, int]:
    with store.connect(db_path) as conn:
        row = conn.execute(
            """SELECT COUNT(*) AS keys,
                      COALESCE(SUM(blocked_duplicates), 0) AS blocked,
                      COALESCE(SUM(CASE WHEN completions > 1 THEN completions - 1 ELSE 0 END), 0) AS leaks
               FROM qaops_idempotency"""
        ).fetchone()
    return {"keys": row["keys"], "blocked_duplicates": row["blocked"], "leaks": row["leaks"]}
