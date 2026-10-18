"""
Tests for QAOps Seam 4: Idempotency & External Resilience.
Verifies SQLite idempotency keys, duplicate blocking, CircuitBreaker state machine,
full-jitter backoff, and outbox failure recovery.
"""

import time
import pytest
from qaops import idempotency, store
from qaops.resilience import (
    CircuitBreaker,
    CircuitOpen,
    backoff_delay,
    service_of,
    recovery_stats,
    MUTATING,
)


def test_make_key_deterministic():
    k1 = idempotency.make_key("jira.transition", "JS-10", 31)
    k2 = idempotency.make_key("jira.transition", "JS-10", 31)
    k3 = idempotency.make_key("jira.transition", "JS-10", 21)
    assert k1 == k2
    assert k1 != k3
    assert k1.startswith("jira.transition:")


def test_idempotent_execution_and_duplicate_caching():
    test_key_suffix = f"test_{time.time()}"
    scope = "unit_test"

    # 1. First run executes and completes
    executed = False
    with idempotency.idempotent(scope, test_key_suffix) as g:
        assert g.duplicate is False
        executed = True
        g.complete({"status": "created", "id": 42})

    assert executed is True

    # 2. Second run with same parameters is blocked as duplicate and retrieves stored result
    with idempotency.idempotent(scope, test_key_suffix) as g2:
        assert g2.duplicate is True
        assert g2.result.get("status") == "created"
        assert g2.result.get("id") == 42


def test_idempotency_duplicate_in_flight_rejected():
    key_suffix = f"inflight_{time.time()}"
    scope = "concurrency_test"

    # Enter first context without completing immediately
    with idempotency.idempotent(scope, key_suffix) as g1:
        assert g1.duplicate is False

        # Attempt to run second operation with same key while first is IN_FLIGHT
        with pytest.raises(idempotency.DuplicateInFlight):
            with idempotency.idempotent(scope, key_suffix) as g2:
                pass


def test_service_of_url_mapping():
    assert service_of("https://mycompany.atlassian.net/rest/api/2/issue") == "jira"
    assert service_of("https://api.qase.io/v1/case/JS") == "qase"
    assert service_of("https://generativelanguage.googleapis.com/v1beta/models") == "gemini"
    assert service_of("https://cloud.langfuse.com/api/public/ingestion") == "langfuse"
    assert service_of("https://custom-host.com/endpoint") == "custom-host.com"


def test_backoff_delay_calculation():
    # Deterministic mock RNG returning high end
    rng_max = lambda low, high: high
    delay = backoff_delay(attempt=2, base=0.5, cap=5.0, retry_after=None, rng=rng_max)
    # base * 2^2 = 0.5 * 4 = 2.0
    assert delay == 2.0

    # With cap
    delay_capped = backoff_delay(attempt=10, base=1.0, cap=10.0, retry_after=None, rng=rng_max)
    assert delay_capped == 10.0

    # Respects retry_after
    delay_retry_after = backoff_delay(attempt=0, base=0.1, cap=15.0, retry_after=12.0, rng=rng_max)
    assert delay_retry_after == 12.0


def test_circuit_breaker_state_transitions():
    svc = f"test_svc_{int(time.time()*1000)}"
    breaker = CircuitBreaker(service=svc, threshold=2, cooldown=1.0)

    # Initial state is CLOSED
    assert breaker.state() == "CLOSED"
    assert breaker.allow() is True

    # 1 failure -> still CLOSED (< threshold)
    breaker.failure()
    assert breaker.state() == "CLOSED"
    assert breaker.allow() is True

    # 2 failures -> reaches threshold -> OPEN
    breaker.failure()
    assert breaker.state() == "OPEN"
    assert breaker.allow() is False

    # Success resets to CLOSED
    breaker.success()
    assert breaker.state() == "CLOSED"
    assert breaker.allow() is True


def test_recovery_stats_calculation():
    stats = recovery_stats()
    assert "calls" in stats
    assert "recovered" in stats
    assert "recovery_rate" in stats
    assert 0.0 <= stats["recovery_rate"] <= 1.0
