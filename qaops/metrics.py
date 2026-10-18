"""
Release Quality Index & Go/No-Go, computed from QAOps metrics, call stats and spans.

Hard gates (all must pass for GO): Schema Compliance = 100%, Test Design Integrity >= 90%,
Syntax Collect Validity = 100%, Idempotency Leaks = 0, Recovery Rate >= 85%.
"""

import argparse
import json
import math
import sys
from typing import Any, Dict, List, Optional

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from qaops import idempotency, store
from qaops.config import settings
from qaops.resilience import recovery_stats


def _p95(values: List[float]) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)], 1)


def span_stats(issue_key: str) -> Dict[str, Any]:
    rows = store.rows("SELECT name, latency_ms, iterations, input_tokens, output_tokens, level FROM qaops_spans WHERE issue_key = ?", (issue_key,))
    by_name: Dict[str, List[float]] = {}
    for r in rows:
        by_name.setdefault(r["name"], []).append(r["latency_ms"] or 0.0)
    return {
        "spans": len(rows),
        "errors": sum(1 for r in rows if r["level"] == "ERROR"),
        "p95_latency_ms": _p95([r["latency_ms"] or 0.0 for r in rows]),
        "p95_by_step": {k: _p95(v) for k, v in sorted(by_name.items())},
        "max_iterations": max((r["iterations"] or 1 for r in rows), default=0),
        "tokens": {"input": sum(r["input_tokens"] or 0 for r in rows), "output": sum(r["output_tokens"] or 0 for r in rows)},
    }


def release_quality(issue_key: str) -> Dict[str, Any]:
    m = store.latest_metrics(issue_key)
    schema = [v["value"] for k, v in m.items() if k.startswith("schema_compliance_rate")]
    idem = idempotency.stats()
    rec = recovery_stats()

    def gate(name: str, value: Optional[float], target: str, ok: Optional[bool]) -> Dict[str, Any]:
        return {"metric": name, "value": value, "target": target, "passed": ok}

    gates = [
        gate("Schema Compliance Rate", min(schema) if schema else None, "= 100%", (min(schema) == 1.0) if schema else None),
        gate("Test Design Integrity", m.get("test_design_integrity", {}).get("value"), f">= {settings.design_integrity_min:.0%}",
             m.get("test_design_integrity", {}).get("passed")),
        gate("Syntax Collect Validity", m.get("syntax_collect_validity", {}).get("value"), "= 100%", m.get("syntax_collect_validity", {}).get("passed")),
        gate("Idempotency Leaks", idem["leaks"], "= 0", idem["leaks"] == 0),
        gate("Recovery Rate", rec["recovery_rate"], f">= {settings.recovery_rate_min:.0%}", rec["recovery_rate"] >= settings.recovery_rate_min),
    ]
    advisory = [
        gate("LLM-as-a-Judge Coverage", m.get("llm_judge_coverage", {}).get("value"), ">= 80%", m.get("llm_judge_coverage", {}).get("passed")),
        gate("AI Code Audit Score", (m.get("ai_code_audit", {}).get("value")), ">= 70/100", m.get("ai_code_audit", {}).get("passed")),
    ]

    measured = [g for g in gates if g["passed"] is not None]
    missing = [g["metric"] for g in gates if g["passed"] is None]
    failed = [g["metric"] for g in measured if not g["passed"]]

    scores = []
    for g in gates + advisory:
        v = g["value"]
        if v is None:
            continue
        if g["metric"] == "Idempotency Leaks":
            scores.append(1.0 if v == 0 else 0.0)
        elif g["metric"] == "AI Code Audit Score":
            scores.append(min(1.0, v / 100))
        else:
            scores.append(max(0.0, min(1.0, float(v))))
    index = round(100 * sum(scores) / len(scores), 1) if scores else 0.0
    decision = "GO" if not failed and not missing else "NO-GO"

    report = {
        "issue_key": issue_key,
        "decision": decision,
        "release_quality_index": index,
        "hard_gates": gates,
        "advisory": advisory,
        "failed": failed,
        "missing": missing,
        "idempotency": idem,
        "resilience": rec,
        "telemetry": span_stats(issue_key),
    }
    store.record_metric(issue_key, "release_quality_index", index, decision == "GO", {"failed": failed, "missing": missing})
    return report


def format_jira(report: Dict[str, Any]) -> List[str]:
    icon = {True: "(/)", False: "(x)", None: "(?)"}
    lines = [
        f"h4. 📈 Индекс Качества Релиза: *{report['release_quality_index']}* / 100 — решение: *{report['decision']}*",
        "||Метрика||Значение||Цель||Статус||",
    ]
    for g in report["hard_gates"] + report["advisory"]:
        v = g["value"]
        shown = "—" if v is None else (f"{v:.0%}" if isinstance(v, float) and v <= 1 and "Score" not in g["metric"] else str(v))
        lines.append(f"|{g['metric']}|{shown}|{g['target']}|{icon[g['passed']]}|")
    t = report["telemetry"]
    lines.append(f"_Телеметрия: spans {t['spans']}, ошибок {t['errors']}, p95 {t['p95_latency_ms']} ms, "
                 f"токены in/out {t['tokens']['input']}/{t['tokens']['output']}, макс. итераций {t['max_iterations']}._")
    return lines


def main():
    parser = argparse.ArgumentParser(description="Release Quality Index / Go-No-Go")
    parser.add_argument("--issue", required=True)
    args = parser.parse_args()
    report = release_quality(args.issue)
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    raise SystemExit(0 if report["decision"] == "GO" else 1)


if __name__ == "__main__":
    main()
