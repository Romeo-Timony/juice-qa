"""
Seam 4b: resilience for external calls (Jira, Qase, Gemini, n8n).

- Exponential backoff with full jitter on 408/425/429/5xx and network errors, honouring Retry-After.
- Per-service circuit breaker persisted in SQLite (survives daemon restarts).
- Mutating calls that still fail are parked in `qaops_outbox` (no data loss) and can be replayed:
  `python -m qaops.resilience --replay`.
"""

import argparse
import json
import random
import sys
import time
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import requests

from qaops import idempotency, store
from qaops.config import settings
from qaops.observability import span

RETRY_STATUSES = {408, 425, 429, 500, 502, 503, 504}
MUTATING = {"POST", "PUT", "PATCH", "DELETE"}
MAX_REPLAY_ATTEMPTS = 10


class TransientFailure(RuntimeError):
    def __init__(self, message: str, response: Optional[requests.Response] = None, outbox_id: Optional[int] = None):
        super().__init__(message)
        self.response = response
        self.outbox_id = outbox_id


class CircuitOpen(TransientFailure):
    pass


def service_of(url: str) -> str:
    host = urlparse(url).hostname or "generic"
    if "atlassian" in host:
        return "jira"
    if "qase" in host:
        return "qase"
    if "googleapis" in host:
        return "gemini"
    if "langfuse" in host:
        return "langfuse"
    return host


def backoff_delay(attempt: int, base: float, cap: float, retry_after: Optional[float] = None, rng: Callable[[float, float], float] = random.uniform) -> float:
    """Full-jitter backoff (AWS architecture blog): sleep = U(0, min(cap, base * 2^attempt))."""
    delay = rng(0, min(cap, base * (2 ** attempt)))
    if retry_after is not None:
        delay = max(delay, min(retry_after, cap))
    return delay


def _retry_after(resp: Optional[requests.Response]) -> Optional[float]:
    if resp is None:
        return None
    value = resp.headers.get("Retry-After")
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


class CircuitBreaker:
    def __init__(self, service: str, threshold: int = settings.breaker_threshold, cooldown: float = settings.breaker_cooldown):
        self.service = service
        self.threshold = threshold
        self.cooldown = cooldown

    def _row(self, conn):
        row = conn.execute("SELECT failures, opened_at FROM qaops_breaker WHERE service = ?", (self.service,)).fetchone()
        return (row["failures"], row["opened_at"]) if row else (0, 0.0)

    def state(self) -> str:
        with store.connect() as conn:
            failures, opened_at = self._row(conn)
        if failures < self.threshold:
            return "CLOSED"
        return "OPEN" if time.time() - opened_at < self.cooldown else "HALF_OPEN"

    def allow(self) -> bool:
        return self.state() != "OPEN"

    def success(self) -> None:
        with store.connect() as conn:
            conn.execute("INSERT INTO qaops_breaker (service, failures, opened_at) VALUES (?, 0, 0) ON CONFLICT(service) DO UPDATE SET failures = 0, opened_at = 0", (self.service,))

    def failure(self) -> None:
        with store.connect() as conn:
            failures, _ = self._row(conn)
            failures += 1
            opened_at = time.time() if failures >= self.threshold else 0
            conn.execute(
                "INSERT INTO qaops_breaker (service, failures, opened_at) VALUES (?, ?, ?) ON CONFLICT(service) DO UPDATE SET failures = excluded.failures, opened_at = excluded.opened_at",
                (self.service, failures, opened_at),
            )


def _record_call(service: str, method: str, attempts: int, had_transient: bool, succeeded: bool) -> None:
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO qaops_calls (service, method, attempts, had_transient_failure, succeeded, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (service, method, attempts, int(had_transient), int(succeeded), store.now_iso()),
        )


def _enqueue(service: str, method: str, url: str, payload: Any, idem_key: Optional[str], error: str) -> int:
    now = store.now_iso()
    with store.connect() as conn:
        cur = conn.execute(
            "INSERT INTO qaops_outbox (idem_key, service, method, url, payload_json, status, last_error, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?, ?)",
            (idem_key, service, method, url, json.dumps(payload, ensure_ascii=False, default=str), error[:1000], now, now),
        )
        return cur.lastrowid


def resilient_request(
    method: str,
    url: str,
    *,
    service: Optional[str] = None,
    idem_key: Optional[str] = None,
    park_on_failure: bool = True,
    attempts: Optional[int] = None,
    sleep: Callable[[float], None] = time.sleep,
    session: Any = requests,
    **kwargs,
) -> requests.Response:
    """
    Drop-in for `requests.request`. Returns the final response for non-retryable statuses
    (caller still checks `.ok`); raises TransientFailure when retries are exhausted.
    """
    method = method.upper()
    service = service or service_of(url)
    attempts = attempts or settings.retry_attempts
    breaker = CircuitBreaker(service)
    kwargs.setdefault("timeout", 30)
    park = park_on_failure and method in MUTATING

    with span(f"http.{service}.{method.lower()}", input={"url": url, "json": kwargs.get("json")}, metadata={"service": service, "idem_key": idem_key}) as s:
        if not breaker.allow():
            outbox_id = _enqueue(service, method, url, kwargs.get("json"), idem_key, "circuit open") if park else None
            s.warn(f"circuit open for {service}; parked in outbox #{outbox_id}" if outbox_id else f"circuit open for {service}")
            _record_call(service, method, 0, True, False)
            raise CircuitOpen(f"Circuit breaker OPEN for {service}", outbox_id=outbox_id)

        last_resp: Optional[requests.Response] = None
        last_err = ""
        had_transient = False
        for attempt in range(attempts):
            s.iterations = attempt + 1
            try:
                resp = session.request(method, url, **kwargs)
            except (requests.ConnectionError, requests.Timeout) as exc:
                had_transient, last_resp, last_err = True, None, f"{type(exc).__name__}: {exc}"
            else:
                if resp.status_code not in RETRY_STATUSES:
                    breaker.success()
                    _record_call(service, method, attempt + 1, had_transient, True)
                    s.set_output({"status": resp.status_code, "attempts": attempt + 1})
                    return resp
                had_transient, last_resp, last_err = True, resp, f"HTTP {resp.status_code}"
            if attempt < attempts - 1:
                sleep(backoff_delay(attempt, settings.retry_base_delay, settings.retry_max_delay, _retry_after(last_resp)))

        breaker.failure()
        _record_call(service, method, attempts, had_transient, False)
        outbox_id = _enqueue(service, method, url, kwargs.get("json"), idem_key, last_err) if park else None
        s.error(f"{last_err} after {attempts} attempts" + (f"; parked in outbox #{outbox_id}" if outbox_id else ""))
        raise TransientFailure(f"{service} {method} failed after {attempts} attempts: {last_err}", last_resp, outbox_id)


def _auth_for(service: str) -> Dict[str, Any]:
    if service == "jira":
        return {"auth": settings.jira_auth}
    if service == "qase":
        import os
        return {"headers": {"Token": os.getenv("QASE_API_TOKEN", ""), "Content-Type": "application/json"}}
    return {}


def replay_outbox(limit: int = 50) -> Dict[str, int]:
    """Replays parked mutations. Successful replays count as recovered calls."""
    summary = {"replayed": 0, "failed": 0, "dead": 0}
    pending = store.rows("SELECT * FROM qaops_outbox WHERE status = 'PENDING' ORDER BY id LIMIT ?", (limit,))
    for row in pending:
        payload = json.loads(row["payload_json"] or "null")
        kwargs = _auth_for(row["service"])
        if payload is not None:
            kwargs["json"] = payload
        now = store.now_iso()
        try:
            resp = resilient_request(row["method"], row["url"], service=row["service"], park_on_failure=False, attempts=2, **kwargs)
            ok = resp.ok
            err = "" if ok else f"HTTP {resp.status_code}: {resp.text[:300]}"
        except TransientFailure as exc:
            ok, err = False, str(exc)
        with store.connect() as conn:
            if ok:
                conn.execute("UPDATE qaops_outbox SET status = 'REPLAYED', attempts = attempts + 1, updated_at = ? WHERE id = ?", (now, row["id"]))
                conn.execute(
                    "INSERT INTO qaops_calls (service, method, attempts, had_transient_failure, succeeded, created_at) VALUES (?, ?, ?, 1, 1, ?)",
                    (row["service"], row["method"], row["attempts"] + 1, now),
                )
                summary["replayed"] += 1
            else:
                status = "DEAD" if row["attempts"] + 1 >= MAX_REPLAY_ATTEMPTS else "PENDING"
                conn.execute("UPDATE qaops_outbox SET status = ?, attempts = attempts + 1, last_error = ?, updated_at = ? WHERE id = ?", (status, err[:1000], now, row["id"]))
                summary["dead" if status == "DEAD" else "failed"] += 1
        if ok and row["idem_key"]:
            idempotency.complete(row["idem_key"], {"replayed_from_outbox": row["id"]})
    return summary


def recovery_stats() -> Dict[str, Any]:
    row = store.rows(
        """SELECT COUNT(*) AS total,
                  COALESCE(SUM(had_transient_failure), 0) AS transient,
                  COALESCE(SUM(CASE WHEN had_transient_failure = 1 AND succeeded = 1 THEN 1 ELSE 0 END), 0) AS recovered
           FROM qaops_calls"""
    )[0]
    pending = store.rows("SELECT COUNT(*) AS n FROM qaops_outbox WHERE status = 'PENDING'")[0]["n"]
    transient = row["transient"]
    rate = (row["recovered"] / transient) if transient else 1.0
    return {"calls": row["total"], "transient": transient, "recovered": row["recovered"], "recovery_rate": round(rate, 4), "outbox_pending": pending}


def main():
    parser = argparse.ArgumentParser(description="QAOps resilience utilities")
    parser.add_argument("--replay", action="store_true", help="Replay parked mutations from the outbox")
    parser.add_argument("--stats", action="store_true", help="Show recovery statistics")
    args = parser.parse_args()
    if args.replay:
        print(json.dumps(replay_outbox(), indent=2))
    elif args.stats:
        print(json.dumps(recovery_stats(), indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
