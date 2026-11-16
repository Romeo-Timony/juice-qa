"""SDD + TDD Contract Verification Suite for QAOps Platform (Contour 1 & Contour 2).

Validates that the n8n Master Workflow (`n8n/current_main_workflow.json`),
the Autonomous Python Daemon (`scripts/qa_agent_daemon.py`), and operational
tools strictly conform to `docs/SDD_MASTER_PRODUCT_SPECIFICATION.md`.
"""

import json
import re
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKFLOW_PATH = BASE_DIR / "n8n" / "current_main_workflow.json"
SPEC_PATH = BASE_DIR / "docs" / "SDD_MASTER_PRODUCT_SPECIFICATION.md"
RESET_SCRIPT_PATH = BASE_DIR / "scripts" / "tools" / "reset_epic_tasks.py"


@pytest.fixture(scope="module")
def workflow() -> dict:
    assert WORKFLOW_PATH.exists(), f"Missing workflow file: {WORKFLOW_PATH}"
    return json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def nodes_by_name(workflow: dict) -> dict[str, dict]:
    return {n["name"]: n for n in workflow.get("nodes", [])}


def test_sdd_master_specification_exists_and_covers_both_contours():
    """Verifies that the SDD Master Blueprint exists and documents all 11 blocks & Contour 2."""
    assert SPEC_PATH.exists(), "SDD_MASTER_PRODUCT_SPECIFICATION.md must exist"
    content = SPEC_PATH.read_text(encoding="utf-8")
    for block_num in range(1, 12):
        assert f"БЛОК {block_num}:" in content, f"Missing specification for БЛОК {block_num}"
    assert "PipelineTracker" in content
    assert "Seam 1" in content and "Seam 6" in content


def test_sdd_workflow_topology_and_blocks(workflow: dict):
    """REQ-N8N-00: Workflow must contain 11 sticky blocks and 66 functional nodes."""
    nodes = workflow.get("nodes", [])
    stickies = [n for n in nodes if "stickyNote" in n.get("type", "")]
    functional = [n for n in nodes if "stickyNote" not in n.get("type", "")]
    assert len(stickies) == 11, f"Expected 11 sticky block containers, got {len(stickies)}"
    assert len(functional) == 66, f"Expected 66 functional nodes, got {len(functional)}"


def test_req_n8n_47_no_hardcoded_issue_keys_in_http_urls(workflow: dict):
    """REQ-N8N-47: No HTTP Request node may hardcode a specific Jira issue key (e.g. /issue/JS-40) in its URL."""
    offenders = []
    for n in workflow.get("nodes", []):
        if n.get("type") == "n8n-nodes-base.httpRequest":
            url = str(n.get("parameters", {}).get("url", ""))
            if re.search(r"/issue/JS-\d+\b", url):
                offenders.append(f"{n['name']}: {url}")
    assert not offenders, f"Found hardcoded Jira issue keys in HTTP Request URLs: {offenders}"


def test_req_n8n_45_drift_detector_no_unconditional_alert_edge(workflow: dict):
    """REQ-N8N-45: Drift Detector must not unconditionally fire Telegram/Jira drift alerts when isDrift=false."""
    conns = workflow.get("connections", {})
    drift_conns = conns.get("Анализ рассинхрона Qase (Drift Detector)", {}).get("main", [[]])[0]
    targets = [d.get("node") for d in drift_conns]
    assert "Контроль 1: Подтверждение тест-кейсов" in targets
    assert "Telegram: Алерт о рассинхронизации Qase (Drift)" not in targets, (
        "Drift Detector must not unconditionally route to 'Telegram: Алерт о рассинхронизации Qase (Drift)' when isDrift is false"
    )


def test_req_n8n_37_testcases_node_no_dead_duplicate_e2e_branch_and_syncs_qase_ids(nodes_by_name: dict):
    """REQ-N8N-37: 'Создание тест-кейсов без повторов' must have no duplicate dead 'else if (kind === e2e)' branch
    and must resolve real Qase IDs via bulk creation before formatting Отчет 3 and Отчет 4."""
    node = nodes_by_name["Создание тест-кейсов без повторов"]
    code = node["parameters"]["jsCode"]

    # Check that generateRtmComment does not have back-to-back duplicate else if (kind === 'e2e')
    rtm_idx = code.find("function generateRtmComment")
    assert rtm_idx != -1
    rtm_code = code[rtm_idx:]
    nfr_idx = rtm_code.find("Покрытие нефункциональных требований")
    assert nfr_idx != -1
    nfr_section = rtm_code[nfr_idx:]
    e2e_branches_in_nfr = re.findall(r"else\s+if\s*\(\s*kind\s*===\s*'e2e'\s*\)", nfr_section)
    assert len(e2e_branches_in_nfr) == 1, (
        f"Expected exactly 1 'else if (kind === e2e)' branch in NFR section of generateRtmComment, found {len(e2e_branches_in_nfr)}"
    )

    # Check that bulk Qase creation happens before casesReport / rtmCommentBody formatting
    bulk_idx = code.find("case/' + qaseCode + '/bulk'")
    report_idx = code.find("const casesReport = lines.join")
    assert bulk_idx != -1 and bulk_idx < report_idx, (
        "New Qase cases must be created via bulk API before formatting casesReport and rtmCommentBody so real Qase IDs are linked"
    )


def test_req_n8n_52_55_gate2_and_stage7_no_duplicate_blind_post(nodes_by_name: dict):
    """REQ-N8N-52 & REQ-N8N-55: Gate 2 and Stage 7 Jira nodes in n8n must not blindly POST duplicate comments
    overwriting Contour 2's rich Evidence Pack and Promotion report."""
    gate2_node = nodes_by_name["Jira: Карточка проверки кода (Gate 2)"]
    stage7_node = nodes_by_name["Jira: Отчет 7 — Внедрение автотестов в проект"]

    gate2_method = gate2_node["parameters"].get("method", "GET")
    stage7_method = stage7_node["parameters"].get("method", "GET")

    assert gate2_method == "GET", (
        f"'Jira: Карточка проверки кода (Gate 2)' must use GET to verify Contour 2's Evidence Pack (got {gate2_method})"
    )
    assert stage7_method == "GET", (
        f"'Jira: Отчет 7 — Внедрение автотестов в проект' must use GET to verify Contour 2's Stage 7 report (got {stage7_method})"
    )


def test_req_n8n_53_telegram_gate2_dynamic_file_suffix(nodes_by_name: dict):
    """REQ-N8N-53: Telegram Gate 2 notification must dynamically resolve _api.py vs _ui.py instead of hardcoding _api.py."""
    tg_node = nodes_by_name["Telegram: Запрос согласования кода (Gate 2)"]
    text = tg_node["parameters"].get("text", "")
    assert "_api.py (13 тестов)" not in text, (
        "Telegram Gate 2 notification must not hardcode '_api.py (13 тестов)' for all tasks"
    )


def test_req_contour2_daemon_cold_start_completed_issue_guard():
    """REQ-DAEMON-01: PipelineTracker.step() must immediately set STATE_COMPLETED when status_id == '10048' on cold start."""
    from scripts.qa_agent_daemon import STATE_COMPLETED, STATE_IDLE, PipelineTracker

    tracker = PipelineTracker("JS-41")
    assert tracker.state == STATE_IDLE

    completed_issue = {
        "key": "JS-41",
        "fields": {
            "status": {"id": "10048", "name": "Автотесты пройдены"},
            "summary": "[UI] Разработка клиентской формы регистрации [DOR_OVERRIDE_APPROVED]",
            "labels": [],
            "comment": {
                "comments": [
                    {"id": "11705", "body": "h3. 🛡️ [Этап 5 из 8] Контроль 1"},
                    {"id": "11706", "body": "ОК"},
                ]
            },
        },
    }
    tracker.step(completed_issue)
    assert tracker.state == STATE_COMPLETED, (
        f"Expected STATE_COMPLETED ({STATE_COMPLETED}) for already-completed 10048 issue on cold start, got {tracker.state}"
    )


def test_req_contour2_reset_tool_dynamic_n8n_tables():
    """REQ-TOOL-01: reset_epic_tasks.py must dynamically query /api/v1/data-tables instead of stale hardcoded IDs."""
    content = RESET_SCRIPT_PATH.read_text(encoding="utf-8")
    assert "fanXRyDssOhkqnjc" not in content, "Stale table ID fanXRyDssOhkqnjc found in reset_epic_tasks.py"
    assert "/api/v1/data-tables" in content


def test_req_n8n_60_62_allure_report_preserves_issue_key_and_summary(nodes_by_name: dict[str, dict]):
    """REQ-N8N-60 & REQ-N8N-62: Allure parser and Telegram Allure card must preserve issueKey across HTTP Request boundary."""
    parser_node = nodes_by_name["Парсинг отчета Allure"]
    tg_node = nodes_by_name["Telegram: Отчет Allure из CI/CD"]

    values = {v["name"]: v["value"] for v in parser_node["parameters"]["values"]["string"]}
    assert "$('Фильтр: Задача взята в работу')" in values["issueKey"], (
        "Парсинг отчета Allure must fall back to root filter issueKey when resumed without body"
    )
    tg_text = tg_node["parameters"]["text"]
    assert "JS-41" not in tg_text, "Telegram Allure node must not hardcode fallback 'JS-41'"
    assert "$('Парсинг отчета Allure')" in tg_text


