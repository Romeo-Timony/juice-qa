"""
Tests for QAOps Seam 5: HITL Integration & Evidence Pack.
Verifies aggregation of LLM-as-a-Judge verdicts, static code gate status,
Allure test failure summaries, and Langfuse trace links.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from qaops.evidence import allure_summary, build_evidence_block
from qaops.code_gate import CodeGateResult, FileAudit


def test_allure_summary_parsing():
    with tempfile.TemporaryDirectory() as tmpdir:
        res_dir = Path(tmpdir)
        # Create a mock passed test result
        pass_file = res_dir / "1-result.json"
        pass_file.write_text(json.dumps({
            "fullName": "tests.test_api.test_login",
            "historyId": "h1",
            "status": "passed",
            "stop": 100
        }), encoding="utf-8")

        # Create a mock failed test result with an attachment
        att_file = res_dir / "fail_screen.png"
        att_file.write_bytes(b"mock_png_data")

        fail_file = res_dir / "2-result.json"
        fail_file.write_text(json.dumps({
            "name": "test_payment_failure",
            "fullName": "tests.test_api.test_payment",
            "historyId": "h2",
            "status": "failed",
            "statusDetails": {"message": "AssertionError: 400 != 200"},
            "attachments": [{"source": "fail_screen.png", "type": "image/png"}],
            "stop": 200
        }), encoding="utf-8")

        summary = allure_summary(results_dir=res_dir)
        assert summary["total"] == 2
        assert summary["counts"].get("passed") == 1
        assert summary["counts"].get("failed") == 1
        assert len(summary["failures"]) == 1
        assert summary["failures"][0]["name"] == "test_payment_failure"
        assert len(summary["failures"][0]["attachments"]) == 1


def test_build_evidence_block_structure():
    code_result = CodeGateResult(
        files=[FileAudit(path="test_mock.py", syntax_ok=True, tests=3)],
        syntax_ok=True,
        lint_ok=True,
        collect_ok=True,
        collected=3,
        runtime="local",
        collect_output="3 tests collected",
        passed=True
    )
    ai_verdict = {
        "verdict": "APPROVED",
        "score": 92,
        "summary": "Clean code structure, all boundary cases covered."
    }
    trace_url = "https://cloud.langfuse.com/project/p1/traces/tr-123"

    block = build_evidence_block(
        issue_key="JS-TEST-5",
        code_gate=code_result,
        ai_verdict=ai_verdict,
        trace_url=trace_url,
        test_files=[],
        upload_artifacts=False
    )

    assert "QAOps Evidence Pack" in block
    assert "LLM-as-a-Judge" in block
    assert "APPROVED (92/100)" in block
    assert "Статическая сборка" in block
    assert "pytest --collect-only (local): (/)" in block
    assert "Allure" in block
    assert trace_url in block
    assert "решение:" in block or "Индекс Качества Релиза" in block
