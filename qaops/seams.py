"""High-level seam entry points used by the daemon / HITL gate without changing their control flow."""

from typing import Any, Dict, List

from qaops import jira, store
from qaops.config import settings
from qaops.contracts import validate
from qaops.design_gate import format_jira_alert, run_design_gate
from qaops.observability import current_trace, span
from qaops.resilience import TransientFailure, resilient_request


def _trace_url() -> str:
    tr = current_trace()
    return tr.url if tr else "—"


def check_issue_contract(issue_key: str) -> bool:
    """Seam 1 (Python side): the Jira issue must satisfy JiraIssueContract before any generation starts."""
    with span("seam1.issue_contract", input={"issue_key": issue_key}) as s:
        try:
            resp = resilient_request("GET", f"{settings.jira_url}/rest/api/2/issue/{issue_key}",
                                     params={"fields": "summary,description,issuetype,labels"}, auth=settings.jira_auth, timeout=20)
        except TransientFailure as exc:
            s.error(str(exc))
            return False
        result = validate("jira_issue", resp.json() if resp.ok else {"key": issue_key})
        store.record_metric(issue_key, "schema_compliance_rate.jira_issue", 1.0 if result.valid else 0.0, result.valid, {"violations": result.violations})
        s.set_output(result.model_dump())
        if not result.valid:
            body = "\n".join([
                "h3. ⛔ QAOps Seam 1: Нарушен контракт входных данных задачи — пайплайн на паузе (qa-paused)",
                "{noformat}", *result.violations[:20], "{noformat}",
                f"🔭 Трейс: {_trace_url()}",
            ])
            jira.pause(issue_key, body, scope_key="seam1:" + "|".join(result.violations))
        return result.valid


def run_design_seam(issue_key: str, cases: List[Dict[str, Any]]) -> bool:
    """Seam 2: semantic gate over Qase cases. Pauses the issue when integrity is below target."""
    if not cases:
        jira.pause(issue_key, "h3. ⛔ QAOps Seam 2: в Qase не найдено тест-кейсов задачи — пайплайн на паузе (qa-paused)", scope_key="seam2:empty")
        return False
    result = run_design_gate(issue_key, cases, use_llm=False)
    if not result.gate_passed:
        jira.pause(issue_key, format_jira_alert(result, _trace_url()), scope_key=f"seam2:{result.integrity}:{result.dropped_case_ids}")
    return result.gate_passed
