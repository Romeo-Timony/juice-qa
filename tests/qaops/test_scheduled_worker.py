"""Unit tests for the Scheduled Events Worker."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from qaops import store
from scripts.scheduled_events_worker import process_due_events


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "test_worker.db"


def test_process_due_events_success(temp_db: Path) -> None:
    now = datetime.now(UTC)
    due_time = (now - timedelta(minutes=1)).isoformat()

    s_id = store.schedule_event(
        action="HEARTBEAT",
        target_time_iso=due_time,
        issue_key="JS-40",
        payload={"ping": "pong"},
        db_path=temp_db,
    )

    processed = process_due_events(batch_size=5, db_path=temp_db)
    assert processed == 1

    # Check status changed to COMPLETED
    remaining = store.fetch_due_scheduled_events(limit=5, db_path=temp_db)
    assert len(remaining) == 0

    # Check event was logged to stream
    events = store.get_events(issue_key="JS-40", event_type="SCHEDULED_EVENT_COMPLETED", db_path=temp_db)
    assert len(events) == 1
    assert events[0]["correlation_id"] == s_id
