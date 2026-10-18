"""
Seam 5: evidence pack for the Senior AQA Human-in-the-Loop review (Gate 2, before merge).

Aggregates into one Jira block: LLM-as-a-Judge verdicts, static gate results, Allure
summary (failure screenshots/screencasts attached to the issue), Langfuse trace link
and the Release Quality Index.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from qaops import idempotency, metrics
from qaops.code_gate import CodeGateResult
from qaops.config import BASE_DIR, settings
from qaops.observability import span
from qaops.resilience import TransientFailure, resilient_request

ALLURE_RESULTS = BASE_DIR / "allure-results"
MAX_ATTACHMENTS = 5


def allure_summary(test_files: Optional[List[Path]] = None, results_dir: Path = ALLURE_RESULTS) -> Dict[str, Any]:
    """Latest result per test (by historyId) from allure-results, optionally limited to given test modules."""
    modules = {Path(f).stem for f in (test_files or [])}
    latest: Dict[str, Dict[str, Any]] = {}
    for path in results_dir.glob("*-result.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        full = data.get("fullName", "")
        if modules and not any(m in full for m in modules):
            continue
        hid = data.get("historyId") or full
        if hid not in latest or data.get("stop", 0) > latest[hid].get("stop", 0):
            latest[hid] = data

    counts: Dict[str, int] = {}
    failures = []
    for data in latest.values():
        status = data.get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1
        if status in ("failed", "broken"):
            atts = [a for a in _walk_attachments(data) if a.get("type") in ("image/png", "video/webm")]
            failures.append({
                "name": data.get("name"),
                "message": (data.get("statusDetails") or {}).get("message", "")[:300],
                "attachments": [str(results_dir / a["source"]) for a in atts if (results_dir / a.get("source", "")).exists()],
            })
    return {"total": len(latest), "counts": counts, "failures": failures}


def _walk_attachments(node: Dict[str, Any]):
    yield from node.get("attachments", [])
    for st in node.get("steps", []):
        yield from _walk_attachments(st)


def attach_to_jira(issue_key: str, files: List[str]) -> List[str]:
    """Uploads failure artefacts once per (issue, file content) — idempotent across re-runs."""
    uploaded = []
    for f in files[:MAX_ATTACHMENTS]:
        path = Path(f)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        try:
            with idempotency.idempotent("jira.attachment", issue_key, digest) as g:
                if g.duplicate:
                    uploaded.append(g.result.get("filename", path.name))
                    continue
                with path.open("rb") as fh:
                    resp = resilient_request(
                        "POST", f"{settings.jira_url}/rest/api/2/issue/{issue_key}/attachments",
                        auth=settings.jira_auth, headers={"X-Atlassian-Token": "no-check"},
                        files={"file": (path.name, fh)}, park_on_failure=False, timeout=60,
                    )
                if not resp.ok:
                    raise RuntimeError(f"HTTP {resp.status_code}")
                g.complete({"filename": path.name})
                uploaded.append(path.name)
        except (TransientFailure, RuntimeError, idempotency.DuplicateInFlight):
            continue
    return uploaded


def build_evidence_block(
    issue_key: str,
    code_gate: CodeGateResult,
    ai_verdict: Dict[str, Any],
    trace_url: str,
    test_files: List[Path],
    upload_artifacts: bool = True,
) -> str:
    with span("seam5.evidence_pack", input={"issue_key": issue_key}) as s:
        allure = allure_summary(test_files)
        uploaded = []
        if upload_artifacts and allure["failures"]:
            uploaded = attach_to_jira(issue_key, [a for f in allure["failures"] for a in f["attachments"]])
        quality = metrics.release_quality(issue_key)
        coverage = quality["advisory"][0]

        report_url = os.getenv("QAOPS_ALLURE_REPORT_URL") or (BASE_DIR / "allure-report" / "index.html").as_posix()
        counts = ", ".join(f"{k}: {v}" for k, v in sorted(allure["counts"].items())) or "нет результатов прогона (тесты ещё не запускались)"

        lines = [
            "h3. 🧾 QAOps Evidence Pack для Senior AQA (Human-in-the-Loop)",
            "",
            "h4. ⚖️ LLM-as-a-Judge",
            f"• *Покрытие AC тест-кейсами (G-Eval Coverage):* {coverage['value'] if coverage['value'] is not None else '—'} "
            f"{'(/)' if coverage['passed'] else '(x)' if coverage['passed'] is False else '(?)'}",
            f"• *Код-ревью автотестов:* {ai_verdict.get('verdict', '—')} ({ai_verdict.get('score', '—')}/100) — {str(ai_verdict.get('summary', ''))[:300]}",
            "",
            "h4. 🧱 Статическая сборка (Seam 3)",
            f"• AST: {'(/)' if code_gate.syntax_ok else '(x)'} | Ruff: {'(/)' if code_gate.lint_ok else '(x)'} | "
            f"pytest --collect-only ({code_gate.runtime}): {'(/) ' + str(code_gate.collected) + ' тестов' if code_gate.collect_ok else '(x)'}",
        ]
        warnings = [w for f in code_gate.files for w in f.lint_warnings][:5]
        if warnings:
            lines.append("• Рекомендации линтера: " + "; ".join(warnings))
        lines += [
            "",
            "h4. 📊 Allure",
            f"• Результаты: {counts}",
            f"• Отчёт: {report_url}",
        ]
        for f in allure["failures"][:5]:
            lines.append(f"• (x) {f['name']}: {f['message'][:150]}")
        if uploaded:
            lines.append("• Вложения (скриншоты/скринкасты падений): " + ", ".join(f"[^{n}]" for n in uploaded))
        lines += ["", *metrics.format_jira(quality), "", f"🔭 *Сквозной трейс Langfuse:* {trace_url}"]
        s.set_output({"allure": allure["counts"], "uploaded": uploaded, "decision": quality["decision"]})
        return "\n".join(lines)
