"""
Tests for QAOps Seam 6: Observability-First & Release Quality Index.
Verifies PII/secret redaction, trace & span lifecycle, latency p95 calculation,
and Release Quality Index (Go/No-Go decision) calculation.
"""

import time
import pytest

from qaops.observability import redact, trace, span
from qaops.metrics import _p95, release_quality, span_stats
from qaops.config import settings
from qaops import store


def test_redact_pii_and_secrets():
    # Email redaction
    assert redact("Contact us at test.user@example.com for support") == "Contact us at <EMAIL> for support"

    # Bearer token redaction
    assert redact("Authorization: Bearer secret_token_value_123456789") == "Authorization: Bearer <TOKEN>"

    # JWT redaction
    sample_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgN_p_mock_signature_12345678"
    assert "<JWT>" in redact(f"Token is {sample_jwt}")

    # Phone number redaction
    assert redact("Call +7 999 123-45-67 now") == "Call <PHONE> now"

    # Dictionary secret field redaction
    payload = {
        "username": "admin",
        "password": "SuperSecretPassword123!",
        "api_key": "some_secret_key",
        "nested": {"client_secret": "xyz789"}
    }
    redacted_dict = redact(payload)
    assert redacted_dict["username"] == "admin"
    assert redacted_dict["password"] == "<SECRET>"
    assert redacted_dict["api_key"] == "<SECRET>"
    assert redacted_dict["nested"]["client_secret"] == "<SECRET>"


def test_trace_and_span_lifecycle():
    issue = f"JS-OBS-{int(time.time()*1000)}"

    with trace("test_pipeline", issue_key=issue) as t:
        assert t.id is not None
        assert t.url.startswith("http") or t.url.startswith("local://")

        with span("step_1", input={"param": "value"}) as s1:
            time.sleep(0.01)
            s1.set_output({"status": "ok"})
            s1.usage(model="gemini-2.5-flash", input_tokens=150, output_tokens=50)

        with span("step_2", input={"sensitive": "secret_data@domain.com"}) as s2:
            s2.set_output("done")

    # Verify spans persisted in database
    rows = store.rows("SELECT * FROM qaops_spans WHERE trace_id = ?", (t.id,))
    assert len(rows) >= 2
    step_1_row = next(r for r in rows if r["name"] == "step_1")
    assert step_1_row["input_tokens"] == 150
    assert step_1_row["output_tokens"] == 50
    assert step_1_row["latency_ms"] > 0

    # Verify redaction: sensitive email in input was replaced with <EMAIL> in the trace log
    log_text = settings.trace_log.read_text(encoding="utf-8")
    assert "<EMAIL>" in log_text
    assert "secret_data@domain.com" not in log_text


def test_p95_percentile_calculation():
    assert _p95([]) is None
    assert _p95([10.0]) == 10.0
    # 20 items: 95th percentile is the 19th item (0.95 * 20 = 19)
    items = [float(i) for i in range(1, 21)]
    assert _p95(items) == 19.0


def test_release_quality_calculation_and_hard_gates():
    issue = f"JS-REL-{int(time.time()*1000)}"

    # When no metrics exist, hard gates are missing -> NO-GO
    initial_rq = release_quality(issue)
    assert initial_rq["decision"] == "NO-GO"

    # Record passing metrics for all hard gates:
    # 1. Schema Compliance Rate = 100%
    store.record_metric(issue, "schema_compliance_rate.jira_issue", 1.0, True, 1.0)
    # 2. Test Design Integrity >= 90%
    store.record_metric(issue, "test_design_integrity", 0.95, True, 0.90)
    # 3. Syntax Collect Validity = 100%
    store.record_metric(issue, "syntax_collect_validity", 1.0, True, 1.0)

    # Note: Idempotency Leaks and Recovery Rate come from store / resilience state.
    rq = release_quality(issue)
    assert isinstance(rq["release_quality_index"], float)
    assert len(rq["hard_gates"]) == 5
    assert len(rq["advisory"]) == 2
