"""
SDET Verification Suite for DeepEval (G-Eval), KnowledgeBaseRAG + Ragas, and Promptfoo.

Tests:
1. KnowledgeBaseRAG indexing of Confluence specs, Pydantic contracts, and Page Objects.
2. Ragas 4-metric evaluation (Context Precision, Context Recall, Faithfulness, Answer Relevancy).
3. Promptfoo benchmark matrix (`prompts/promptfooconfig.yaml`) across all 4 prompt domains.
4. DeepEval G-Eval wrapper (`GeminiFlashJudge`, `judge_groundedness`, `judge_coverage`) and
   Seam 2 `run_design_gate` integration recording all new metrics into Release Quality Index (RQI).
"""

import pytest

from qaops.config import settings
from qaops.design_gate import run_design_gate
from qaops.judge import JudgeVerdict, _deepeval_model, judge_coverage, judge_groundedness
from qaops.metrics import format_jira, release_quality
from qaops.promptfoo_runner import CONFIG_PATH, run_promptfoo_benchmark
from qaops.rag import KnowledgeBaseRAG, evaluate_rag, retrieve_context_for_issue
from qaops import store


def test_knowledge_base_rag_indexes_specs_contracts_and_code():
    rag = KnowledgeBaseRAG()
    count = rag.build_index()
    assert count >= 10, f"Expected at least 10 indexed chunks, got {count}"
    domains = {c.domain for c in rag.chunks}
    assert "spec" in domains
    assert "contract" in domains
    assert "code" in domains

    hits = rag.retrieve("JS-40 POST /api/Users email unique password 201 Created", top_k=4)
    assert len(hits) >= 2
    assert hits[0].score > 0.15


def test_ragas_four_metrics_evaluation_and_persistence():
    issue_key = "JS-40"
    query = "POST /api/Users registration 201 Created 400 email must be unique securityQuestion"
    ctx_str, hits = retrieve_context_for_issue(issue_key, query, top_k=5)
    assert len(hits) >= 2
    assert "RAG Source:" in ctx_str

    generated_cases = (
        "Title: POST /api/Users valid registration returns 201 Created with UserRegistrationResponse\n"
        "Title: POST /api/Users duplicate email returns 400 Bad Request email must be unique\n"
        "Title: POST /api/Users password boundary 5 to 40 characters and securityQuestion"
    )
    verdict = evaluate_rag(issue_key, query, hits, generated_cases, query)
    assert verdict.context_precision >= 0.80
    assert verdict.context_recall >= 0.80
    assert verdict.faithfulness >= 0.85
    assert verdict.answer_relevancy >= 0.85
    assert verdict.harmonic_score >= 0.80
    assert verdict.passed is True


def test_promptfoo_config_and_benchmark_matrix():
    assert CONFIG_PATH.exists(), "prompts/promptfooconfig.yaml must exist"
    report = run_promptfoo_benchmark("JS-40")
    assert report.total_tests == 8
    assert report.passed_tests == 8
    assert report.pass_rate == 1.0
    assert report.avg_enterprise_score > report.avg_baseline_score
    assert report.enterprise_gain_pct > 0


def test_deepeval_model_wrapper_and_seam2_integration(monkeypatch):
    assert settings.judge_backend == "deepeval"
    judge_llm = _deepeval_model()
    assert judge_llm.get_model_name() == settings.judge_model

    # Mock LLM network call to test deterministic Seam 2 + DeepEval + Ragas + Promptfoo integration
    monkeypatch.setattr(
        "qaops.judge.gemini_generate",
        lambda prompt, model=None, json_mode=True: ('{"score": 9, "reason": "Grounded in AC and RAG context"}', {"input": 120, "output": 30}),
    )

    sample_cases = [
        {
            "id": 633,
            "title": "Создание учетной записи нового покупателя POST /api/Users/ -> 201 Created",
            "automation": 2,
            "priority": 1,
            "severity": 1,
            "tags": [{"title": "smoke"}, {"title": "fast-regression"}],
            "steps": [{"action": "POST /api/Users/", "data": "valid payload", "expected_result": "HTTP 201 Created"}],
        },
        {
            "id": 634,
            "title": "Блокировка повторной регистрации дубликата email POST /api/Users/ -> 400",
            "automation": 2,
            "priority": 1,
            "severity": 2,
            "tags": [{"title": "regression"}, {"title": "fast-regression"}],
            "steps": [{"action": "POST /api/Users/", "data": "duplicate email", "expected_result": "HTTP 400 email must be unique"}],
        },
    ]

    ac = "AC-01: POST /api/Users/ returns 201 Created. AC-02: Duplicate email returns 400 email must be unique."
    res = run_design_gate("JS-40", sample_cases, acceptance_criteria=ac, use_llm=True)
    assert res.gate_passed is True
    assert res.integrity == 1.0
    assert res.ragas is not None and res.ragas["passed"] is True
    assert res.promptfoo is not None and res.promptfoo["pass_rate"] == 1.0

    store.record_metric("JS-40", "schema_compliance_rate.jira_issue", 1.0, True)
    store.record_metric("JS-40", "syntax_collect_validity", 1.0, True)
    store.record_metric("JS-40", "ai_code_audit", 96.0, True)

    rq = release_quality("JS-40")
    assert rq["decision"] == "GO"
    assert rq["release_quality_index"] >= 90.0
    ai_metric_names = {m["metric"] for m in rq["ai_eval_metrics"]}
    assert "DeepEval Groundedness (G-Eval)" in ai_metric_names
    assert "Ragas Harmonic Score" in ai_metric_names
    assert "Promptfoo Benchmark Pass Rate" in ai_metric_names

    jira_lines = "\n".join(format_jira(rq))
    assert "Ragas Harmonic Score" in jira_lines
    assert "Promptfoo Benchmark Pass Rate" in jira_lines
