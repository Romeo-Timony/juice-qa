"""
Tests for QAOps Seam 1: Input Control & Contract Validation (DoR Gate).
Verifies Pydantic v2 schema compliance, INVEST criteria validation,
Schema Compliance Rate = 100%, and PAUSED state handling upon failure.
"""

import pytest
from pydantic import ValidationError
from qaops.contracts import (
    JiraIssueContract,
    DorVerdictContract,
    validate,
    INVEST_MAP
)
from qaops.seams import check_issue_contract


def test_valid_jira_issue_contract():
    payload = {
        "key": "JS-25",
        "fields": {
            "summary": "Разработка REST API профиля пользователя",
            "description": "h2. Acceptance Criteria\n1. User can view profile",
            "issuetype": {"name": "Story"},
            "labels": ["backend"]
        }
    }
    result = validate("jira_issue", payload)
    assert result.valid is True
    assert len(result.violations) == 0


def test_invalid_jira_issue_contract_rejects_missing_key():
    payload = {
        "key": "INVALIDKEY",
        "fields": {
            "summary": "Short",
            "issuetype": {"name": "Bug"}
        }
    }
    result = validate("jira_issue", payload)
    assert result.valid is False
    assert any("key" in v for v in result.violations)


def test_dor_verdict_contract_valid_with_invest_coverage():
    results = [
        {"id": "C01", "title": "Summary", "mandatory": True, "status": "pass", "comment": "OK"},
        {"id": "C02", "title": "Value", "mandatory": True, "status": "pass", "comment": "OK"},
        {"id": "C03", "title": "Independent", "mandatory": True, "status": "pass", "comment": "OK"},
        {"id": "C04", "title": "Testable AC", "mandatory": True, "status": "pass", "comment": "OK"},
        {"id": "C05", "title": "Estimable", "mandatory": True, "status": "pass", "comment": "OK"},
        {"id": "C06", "title": "Errors", "mandatory": True, "status": "pass", "comment": "OK"},
        {"id": "C07", "title": "Negotiable", "mandatory": True, "status": "pass", "comment": "OK"},
    ]
    payload = {
        "issueKey": "JS-25",
        "passed": True,
        "score": 95,
        "results": results,
        "commentBody": "h2. [Этап 1 из 8] QA-валидация требований (DoR Gate): (/) ТРЕБОВАНИЯ ПРИНЯТЫ\nДетали...",
        "commentMethod": "POST",
        "commentUrl": "https://romeo-timony.atlassian.net/rest/api/2/issue/JS-25/comment"
    }
    result = validate("dor_verdict", payload)
    assert result.valid is True


def test_dor_verdict_contract_rejects_missing_invest_criteria():
    # Пропускаем C06 (Testable - негативные проверки) и C07 (Negotiable)
    results = [
        {"id": "C01", "title": "Summary", "mandatory": True, "status": "pass", "comment": "OK"},
        {"id": "C02", "title": "Value", "mandatory": True, "status": "pass", "comment": "OK"},
        {"id": "C03", "title": "Independent", "mandatory": True, "status": "pass", "comment": "OK"},
        {"id": "C04", "title": "Testable AC", "mandatory": True, "status": "pass", "comment": "OK"},
        {"id": "C05", "title": "Estimable", "mandatory": True, "status": "pass", "comment": "OK"},
        {"id": "X01", "title": "Extra 1", "mandatory": False, "status": "pass", "comment": "OK"},
        {"id": "X02", "title": "Extra 2", "mandatory": False, "status": "pass", "comment": "OK"},
    ]
    payload = {
        "issueKey": "JS-25",
        "passed": True,
        "score": 95,
        "results": results,
        "commentBody": "h2. [Этап 1 из 8] DoR Gate валидация требований: ТРЕБОВАНИЯ ПРИНЯТЫ подробный комментарий для Jira",
        "commentMethod": "POST",
        "commentUrl": "https://romeo-timony.atlassian.net/rest/api/2/issue/JS-25/comment"
    }
    result = validate("dor_verdict", payload)
    assert result.valid is False
    assert any("INVEST" in v for v in result.violations)


def test_paused_state_on_contract_violation(monkeypatch, tmp_path):
    # Тестируем функцию паузы при нарушении контракта
    paused_called = []
    
    def mock_pause(issue_key, body, scope_key, extra_label=None):
        paused_called.append({"issue": issue_key, "body": body, "scope": scope_key, "label": extra_label})

    monkeypatch.setattr("qaops.jira.pause", mock_pause)
    
    # Имитируем невалидный ответ от Jira
    class MockResp:
        ok = True
        def json(self):
            return {"key": "BAD-FORMAT", "fields": {}}

    monkeypatch.setattr("qaops.seams.resilient_request", lambda *args, **kwargs: MockResp())
    
    valid = check_issue_contract("BAD-FORMAT")
    assert valid is False
    assert len(paused_called) == 1
    assert "qa-paused" in paused_called[0]["body"]
