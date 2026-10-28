"""Scheduled Events Worker for QAOps.

Pulls due tasks from `qa_scheduled_events` (retries, outbox replays, regression jobs),
executes them idempotently, and records state updates & telemetry events.
"""

import argparse
import logging
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# Ensure qa-automation directory is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core_utils.crash_monitor import install_global_crash_hook
from qaops import resilience, store

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [ScheduledWorker] %(message)s")
logger = logging.getLogger("scheduled_worker")


def execute_action(action: str, issue_key: str, payload: dict[str, Any]) -> None:
    """Executes a scheduled action based on its type."""
    logger.info("Executing action: %s for issue: %s", action, issue_key)
    if action == "REPLAY_OUTBOX":
        resilience.flush_outbox()
    elif action == "HEARTBEAT":
        logger.info("Heartbeat tick for scheduled worker. Payload: %s", payload)
    else:
        logger.info("Action %s handled (simulated or routed). Payload: %s", action, payload)


def process_due_events(batch_size: int = 10, db_path: Path | None = None) -> int:
    """Processes a single batch of due events."""
    events = store.fetch_due_scheduled_events(limit=batch_size, db_path=db_path)
    if not events:
        return 0

    logger.info("Found %d due scheduled event(s)", len(events))
    processed_count = 0

    for ev in events:
        s_id = ev["schedule_id"]
        action = ev["action"]
        issue = ev.get("issue_key") or "SYSTEM"
        retries = ev["retry_count"]
        max_retries = ev["max_retries"]
        payload = ev.get("payload") or {}

        try:
            execute_action(action, issue, payload)
            store.mark_scheduled_event(s_id, status="COMPLETED", db_path=db_path)
            store.record_event(
                correlation_id=s_id,
                issue_key=issue,
                event_type="SCHEDULED_EVENT_COMPLETED",
                producer="scheduled_worker",
                payload={"action": action, "retries": retries},
                db_path=db_path,
            )
            processed_count += 1
            logger.info("Successfully executed event %s (%s)", s_id, action)
        except Exception as e:
            logger.exception("Error executing event %s", s_id)
            if retries + 1 >= max_retries:
                store.mark_scheduled_event(s_id, status="FAILED", error=str(e), db_path=db_path)
                store.record_event(
                    correlation_id=s_id,
                    issue_key=issue,
                    event_type="SCHEDULED_EVENT_DEAD_LETTER",
                    producer="scheduled_worker",
                    payload={"action": action, "error": str(e), "retries": retries + 1},
                    db_path=db_path,
                )
            else:
                # Exponential backoff retry
                delay_sec = 2 ** (retries + 1) * 30
                next_target = (datetime.now(UTC) + timedelta(seconds=delay_sec)).isoformat()
                with store.connect(db_path) as conn:
                    conn.execute(
                        """
                        UPDATE qa_scheduled_events
                        SET retry_count = retry_count + 1, target_time = ?, last_error = ?, updated_at = ?
                        WHERE schedule_id = ?
                        """,
                        (next_target, str(e)[:1000], store.now_iso(), s_id),
                    )
                logger.info("Event %s rescheduled to %s (attempt %d/%d)", s_id, next_target, retries + 1, max_retries)

    return processed_count


def run_loop(interval_sec: int = 15, run_once: bool = False, db_path: Path | None = None) -> None:
    install_global_crash_hook()
    logger.info("Starting QA Scheduled Events Worker (interval=%ds, once=%s)", interval_sec, run_once)

    while True:
        try:
            process_due_events(db_path=db_path)
        except Exception:
            logger.exception("Unexpected error in worker loop")

        if run_once:
            break
        time.sleep(interval_sec)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QAOps Scheduled Events Worker")
    parser.add_argument("--once", action="store_true", help="Run a single pass and exit")
    parser.add_argument("--interval", type=int, default=15, help="Polling interval in seconds")
    args = parser.parse_args()

    run_loop(interval_sec=args.interval, run_once=args.once)
