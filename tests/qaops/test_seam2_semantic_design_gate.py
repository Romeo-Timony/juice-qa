"""
Tests for QAOps Seam 2: Semantic Control of Test Design (Whimsical / Qase / BDD).
Verifies tag & priority validation, filtering out cases without automation flag,
Groundedness rubric evaluation, and Test Design Integrity >= 90% threshold.
"""

import pytest
from qaops.design_gate import (
    deterministic_review,
    run_design_gate,
    automation_flag
)
from qaops.judge import JudgeVerdict


def test_automation_flag_detection():
    # 1. to-be-automated через числовой флаг 1
    assert automation_flag({"automation": 1}) == "to-be-automated"
    # 2. to-be-automated через тег
    assert automation_flag({"automation": 0, "tags": [{"title": "to-be-automated"}]}) == "to-be-automated"
    # 3. manual через тег
    assert automation_flag({"automation": 0, "tags": [{"title": "manual"}]}) == "manual"
    # 4. missing - нет ни флага, ни тега
    assert automation_flag({"automation": 0, "tags": []}) is None


def test_deterministic_review_detects_missing_attributes():
    # Кейс без флага автоматизации, без приоритета и без тега набора
    case = {
        "id": 101,
        "title": "Unconfigured test case",
        "automation": 0,
        "priority": 0,
        "tags": [],
        "steps": []
    }
    review = deterministic_review(case)
    assert review.deterministic_ok is False
    assert any("нет флага автоматизации" in r for r in review.reasons)
    assert any("не задан приоритет" in r for r in review.reasons)
    assert any("нет тега набора" in r for r in review.reasons)
    assert any("нет шагов" in r for r in review.reasons)


def test_design_gate_filters_unflagged_cases_and_checks_integrity(monkeypatch):
    cases = [
        # Валидный автотест с обязательными тегами
        {
            "id": 1,
            "title": "[API] Регистрация пользователя с валидными данными",
            "automation": 1,
            "priority": 1,
            "severity": 1,
            "tags": [{"title": "smoke"}, {"title": "allure"}],
            "steps": [{"action": "POST /api/Users/", "expected_result": "HTTP 201 Created"}]
        },
        # Валидный ручной кейс
        {
            "id": 2,
            "title": "[Manual] Визуальная проверка анимации",
            "automation": 0,
            "priority": 2,
            "severity": 2,
            "tags": [{"title": "manual"}, {"title": "regression"}],
            "steps": [{"action": "Open page", "expected_result": "Animation played"}]
        },
        # Кейс без флага автоматизации (должен отсечься)
        {
            "id": 3,
            "title": "[Unknown] Кейс без флага",
            "automation": 0,
            "priority": 1,
            "tags": [{"title": "smoke"}],
            "steps": [{"action": "Click button", "expected_result": "Clicked"}]
        }
    ]

    # Мокаем судью Groundedness, чтобы проверить логику без внешнего API
    def mock_groundedness(case_text, ac):
        return JudgeVerdict("Groundedness", 0.95, True, "Fully grounded in AC", "mock")

    def mock_coverage(cases_text, ac):
        return JudgeVerdict("Coverage", 0.90, True, "All AC covered", "mock")

    monkeypatch.setattr("qaops.judge.judge_groundedness", mock_groundedness)
    monkeypatch.setattr("qaops.judge.judge_coverage", mock_coverage)

    result = run_design_gate("JS-25", cases, acceptance_criteria="AC 1: Регистрация пользователя", use_llm=True)
    
    # 2 из 3 кейсов валидны -> 66.7% < 90% (gate_passed = False)
    assert result.total == 3
    assert result.passed_count == 2
    assert result.integrity == pytest.approx(0.6667, 0.01)
    assert result.gate_passed is False
    assert 3 in result.dropped_case_ids
    assert 1 in result.automation_case_ids


def test_design_gate_passes_when_integrity_above_90_percent(monkeypatch):
    # 10 кейсов, все 10 валидны
    cases = []
    for i in range(10):
        cases.append({
            "id": i + 1,
            "title": f"[API] Тест-сценарий #{i + 1}",
            "automation": 1,
            "priority": 1,
            "severity": 1,
            "tags": [{"title": "smoke"}],
            "steps": [{"action": f"Step {i}", "expected_result": "OK"}]
        })

    monkeypatch.setattr("qaops.judge.judge_groundedness", lambda *a, **k: JudgeVerdict("Groundedness", 0.95, True, "OK", "mock"))
    monkeypatch.setattr("qaops.judge.judge_coverage", lambda *a, **k: JudgeVerdict("Coverage", 0.95, True, "OK", "mock"))

    result = run_design_gate("JS-26", cases, acceptance_criteria="AC", use_llm=True)
    assert result.integrity == 1.0
    assert result.gate_passed is True
    assert len(result.automation_case_ids) == 10
    assert len(result.dropped_case_ids) == 0
