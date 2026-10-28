"""Unit tests for QAOps Event Sourcing & Scheduled Events store."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from qaops import store


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    db_file = tmp_path / "test_events.db"
    return db_file


def test_record_and_get_events(temp_db: Path) -> None:
    event_id1 = store.record_event(
        correlation_id="corr-123",
        issue_key="JS-40",
        event_type="DOR_EVALUATED",
        producer="qa_agent",
        payload={"score": 85.0, "status": "PASSED"},
        db_path=temp_db,
    )
    assert event_id1 is not None

    event_id2 = store.record_event(
        correlation_id="corr-124",
        issue_key="JS-40",
        event_type="TESTS_GENERATED",
        producer="qa_agent",
        payload={"test_count": 3},
        db_path=temp_db,
    )
    assert event_id2 is not None

    # Retrieve all events for JS-40
    events = store.get_events(issue_key="JS-40", db_path=temp_db)
    assert len(events) == 2
    # Check ordering (newest first)
    assert events[0]["event_type"] == "TESTS_GENERATED"
    assert events[1]["event_type"] == "DOR_EVALUATED"
    assert events[1]["payload"]["score"] == 85.0

    # Retrieve by event_type
    filtered = store.get_events(event_type="DOR_EVALUATED", db_path=temp_db)
    assert len(filtered) == 1
    assert filtered[0]["event_id"] == event_id1


def test_update_and_get_pipeline_state(temp_db: Path) -> None:
    # 1. Initial State creation
    store.update_pipeline_state(
        issue_key="JS-40",
        stage_idx=1,
        stage_name="DoR Gate",
        hitl_gate1="PENDING",
        rqi=75.0,
        metadata={"dor_passed": True},
        db_path=temp_db,
    )

    state = store.get_pipeline_state("JS-40", db_path=temp_db)
    assert state is not None
    assert state["issue_key"] == "JS-40"
    assert state["current_stage"] == 1
    assert state["stage_name"] == "DoR Gate"
    assert state["rqi_score"] == 75.0
    assert state["hitl_gate1_status"] == "PENDING"
    assert state["metadata"]["dor_passed"] is True

    # 2. Advance to Stage 2 (Gate 1 Approved)
    store.update_pipeline_state(
        issue_key="JS-40",
        stage_idx=2,
        stage_name="Code Generation",
        hitl_gate1="APPROVED",
        metadata={"tests_count": 3},
        db_path=temp_db,
    )

    updated = store.get_pipeline_state("JS-40", db_path=temp_db)
    assert updated is not None
    assert updated["current_stage"] == 2
    assert updated["stage_name"] == "Code Generation"
    assert updated["hitl_gate1_status"] == "APPROVED"
    assert updated["rqi_score"] == 75.0  # Kept previous value
    # Check merged metadata
    assert updated["metadata"]["dor_passed"] is True
    assert updated["metadata"]["tests_count"] == 3


def test_schedule_events_workflow(temp_db: Path) -> None:
    now = datetime.now(UTC)
    past_time = (now - timedelta(minutes=5)).isoformat()
    future_time = (now + timedelta(hours=1)).isoformat()

    # Schedule a past (due) event
    due_id = store.schedule_event(
        action="RUN_REGRESSION",
        target_time_iso=past_time,
        issue_key="JS-40",
        payload={"suite": "api_auth"},
        db_path=temp_db,
    )

    # Schedule a future (not due) event
    future_id = store.schedule_event(
        action="NIGHTLY_CLEANUP",
        target_time_iso=future_time,
        issue_key=None,
        payload={},
        db_path=temp_db,
    )
    assert future_id is not None

    # Fetch due
    due_events = store.fetch_due_scheduled_events(limit=10, db_path=temp_db)
    assert len(due_events) == 1
    assert due_events[0]["schedule_id"] == due_id
    assert due_events[0]["action"] == "RUN_REGRESSION"
    assert due_events[0]["payload"]["suite"] == "api_auth"

    # Mark as completed
    store.mark_scheduled_event(due_id, status="COMPLETED", db_path=temp_db)

    # Fetch due again -> should be empty
    remaining_due = store.fetch_due_scheduled_events(limit=10, db_path=temp_db)
    assert len(remaining_due) == 0
