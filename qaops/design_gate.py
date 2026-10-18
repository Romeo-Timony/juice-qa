"""
Seam 2: semantic control of test design (Qase cases before automation).

Deterministic layer (no LLM): automation flag, priority, Smoke/Regress suite tag.
Semantic layer (LLM-as-a-Judge, G-Eval): groundedness of each flagged case in the AC.
Test Design Integrity = cases passing both layers / all cases; gate threshold >= 90%.
"""

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from qaops import store
from qaops.config import settings
from qaops.contracts import SUITE_TAGS, QaseCaseContract
from qaops.observability import span
from qaops.resilience import resilient_request

AC_HEADER = re.compile(r"(?im)^\s*(?:h\d\.\s*)?\**\s*(критерии\s+приемки|критерии\s+приёмки|acceptance\s+criteria|ac\b)")


@dataclass
class CaseReview:
    id: int
    title: str
    automation: str
    deterministic_ok: bool
    grounded: Optional[bool] = None
    groundedness: Optional[float] = None
    reasons: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.deterministic_ok and self.grounded is not False


@dataclass
class DesignGateResult:
    issue_key: str
    total: int
    passed_count: int
    integrity: float
    schema_compliance: float
    gate_passed: bool
    automation_case_ids: List[int]
    dropped_case_ids: List[int]
    reviews: List[CaseReview]
    coverage: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["reviews"] = [{**asdict(r), "passed": r.passed} for r in self.reviews]
        return d


def fetch_acceptance_criteria(issue_key: str) -> str:
    resp = resilient_request(
        "GET", f"{settings.jira_url}/rest/api/2/issue/{issue_key}",
        params={"fields": "summary,description"}, auth=settings.jira_auth, timeout=20,
    )
    resp.raise_for_status()
    fields = resp.json().get("fields", {})
    return extract_ac(fields.get("summary", ""), fields.get("description") or "")


def extract_ac(summary: str, description: str) -> str:
    match = AC_HEADER.search(description)
    body = description[match.start():] if match else description
    return f"{summary}\n\n{body}"[:8000]


def _tag_titles(case: Dict[str, Any]) -> List[str]:
    return [str(t.get("title", t) if isinstance(t, dict) else t).lower() for t in case.get("tags", [])]


def automation_flag(case: Dict[str, Any]) -> Optional[str]:
    """Qase stores 0 for both 'manual' and 'unset', so a 0 counts only with an explicit 'manual' tag."""
    tags = _tag_titles(case)
    if case.get("automation") == 2:
        return "automated"
    if case.get("automation") == 1 or "to-be-automated" in tags:
        return "to-be-automated"
    if "manual" in tags:
        return "manual"
    return None


def deterministic_review(case: Dict[str, Any]) -> CaseReview:
    reasons = []
    flag = automation_flag(case)
    if flag is None:
        reasons.append("нет флага автоматизации (to-be-automated / manual)")
    if not case.get("priority"):
        reasons.append("не задан приоритет")
    if not set(_tag_titles(case)).intersection(SUITE_TAGS) and case.get("type") not in (3, 4):
        reasons.append("нет тега набора Smoke/Regress")
    if not case.get("steps"):
        reasons.append("нет шагов")
    return CaseReview(id=int(case.get("id", 0)), title=case.get("title", ""), automation=flag or "missing", deterministic_ok=not reasons, reasons=reasons)


def case_as_text(case: Dict[str, Any]) -> str:
    lines = [f"Title: {case.get('title', '')}", f"Preconditions: {case.get('preconditions') or '-'}"]
    for i, st in enumerate(case.get("steps") or [], 1):
        lines.append(f"{i}. {st.get('action', '')} | data: {st.get('data', '') or '-'} | expected: {st.get('expected_result', '')}")
    return "\n".join(lines)


def run_design_gate(issue_key: str, cases: List[Dict[str, Any]], acceptance_criteria: Optional[str] = None, use_llm: bool = True) -> DesignGateResult:
    with span("seam2.design_gate", input={"issue_key": issue_key, "cases": len(cases)}) as s:
        compliant = 0
        for c in cases:
            try:
                QaseCaseContract.model_validate(c)
                compliant += 1
            except Exception:
                pass

        reviews = [deterministic_review(c) for c in cases]
        by_id = {int(c.get("id", 0)): c for c in cases}

        if use_llm and cases:
            ac = acceptance_criteria if acceptance_criteria is not None else fetch_acceptance_criteria(issue_key)
            from qaops.judge import judge_coverage, judge_groundedness
            for r in reviews:
                if r.automation == "missing":
                    continue
                verdict = judge_groundedness(case_as_text(by_id[r.id]), ac)
                r.groundedness, r.grounded = verdict.score, verdict.passed
                if not verdict.passed:
                    r.reasons.append(f"Groundedness {verdict.score:.2f} < {settings.groundedness_min}: {verdict.reason[:200]}")
            coverage = judge_coverage("\n\n".join(case_as_text(c) for c in cases), ac).to_dict()
        else:
            coverage = None

        total = len(cases)
        passed_count = sum(1 for r in reviews if r.passed)
        integrity = passed_count / total if total else 0.0
        result = DesignGateResult(
            issue_key=issue_key,
            total=total,
            passed_count=passed_count,
            integrity=round(integrity, 4),
            schema_compliance=round(compliant / total, 4) if total else 0.0,
            gate_passed=total > 0 and integrity >= settings.design_integrity_min,
            automation_case_ids=[r.id for r in reviews if r.passed and r.automation == "to-be-automated"],
            dropped_case_ids=[r.id for r in reviews if r.automation == "missing"],
            reviews=reviews,
            coverage=coverage,
        )
        store.record_metric(issue_key, "test_design_integrity", result.integrity, result.gate_passed,
                            {"passed": passed_count, "total": total, "dropped": result.dropped_case_ids})
        store.record_metric(issue_key, "schema_compliance_rate.qase_cases", result.schema_compliance, result.schema_compliance == 1.0)
        if coverage:
            store.record_metric(issue_key, "llm_judge_coverage", coverage["score"], coverage["passed"], {"reason": coverage["reason"]})
        s.set_output({k: v for k, v in result.to_dict().items() if k != "reviews"})
        if not result.gate_passed:
            s.warn(f"Test Design Integrity {result.integrity:.0%} < {settings.design_integrity_min:.0%}")
        return result


def format_jira_alert(result: DesignGateResult, trace_url: str) -> str:
    lines = [
        "h3. ⛔ QAOps Seam 2: Тест-дизайн не прошёл семантический контроль — пайплайн на паузе (qa-paused)",
        f"*Test Design Integrity:* {result.integrity:.0%} (порог {settings.design_integrity_min:.0%}) | *Кейсов:* {result.passed_count}/{result.total}",
        f"*Schema Compliance (Qase):* {result.schema_compliance:.0%}",
        "",
        "||Qase ID||Кейс||Флаг||Groundedness||Причины||",
    ]
    for r in result.reviews:
        if r.passed:
            continue
        g = f"{r.groundedness:.2f}" if r.groundedness is not None else "—"
        reasons = "; ".join(r.reasons).replace("|", "/")[:300]
        lines.append(f"|{r.id}|{r.title.replace('|', '/')[:80]}|{r.automation}|{g}|{reasons}|")
    lines += ["", f"🔭 Трейс: {trace_url}", "_Исправьте кейсы в Qase и снимите метку qa-paused, затем повторите согласование._"]
    return "\n".join(lines)
