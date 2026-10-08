"""
n8n Data Tables Synchronization Manager
Integrates SQLite QA Pipeline State with native n8n Data Tables.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "qa_pipeline.db"
load_dotenv(BASE_DIR / ".env")

N8N_URL = (os.getenv("N8N_URL") or os.getenv("N8N_SERVER_URL") or "http://201.34.147.33:5678").rstrip("/")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")


def get_headers() -> Dict[str, str]:
    return {
        "X-N8N-API-KEY": N8N_API_KEY,
        "Content-Type": "application/json"
    }


def list_n8n_tables() -> List[Dict[str, Any]]:
    res = requests.get(f"{N8N_URL}/api/v1/data-tables", headers=get_headers(), timeout=15)
    if not res.ok:
        raise RuntimeError(f"Failed to fetch n8n data tables ({res.status_code}): {res.text}")
    return res.json().get("data", [])


def delete_n8n_table(table_id: str):
    res = requests.delete(f"{N8N_URL}/api/v1/data-tables/{table_id}", headers=get_headers(), timeout=15)
    return res.ok


def create_n8n_table(name: str, columns: List[Dict[str, str]]) -> str:
    payload = {
        "name": name,
        "columns": columns
    }
    res = requests.post(f"{N8N_URL}/api/v1/data-tables", headers=get_headers(), json=payload, timeout=15)
    if not res.ok:
        raise RuntimeError(f"Failed to create n8n data table '{name}' ({res.status_code}): {res.text}")
    return res.json().get("id")


def insert_rows(table_id: str, rows: List[Dict[str, Any]]):
    if not rows:
        return
    payload = {"data": rows}
    res = requests.post(f"{N8N_URL}/api/v1/data-tables/{table_id}/rows", headers=get_headers(), json=payload, timeout=20)
    if not res.ok:
        raise RuntimeError(f"Failed to insert rows into table {table_id} ({res.status_code}): {res.text}")


def recreate_table_with_data(name: str, columns: List[Dict[str, str]], rows: List[Dict[str, Any]]) -> str:
    tables = list_n8n_tables()
    for t in tables:
        if t.get("name") == name:
            delete_n8n_table(t["id"])
    
    table_id = create_n8n_table(name, columns)
    if rows:
        insert_rows(table_id, rows)
    return table_id


def sync_all_to_n8n():
    if not N8N_API_KEY:
        print("⚠️ Ошибка: N8N_API_KEY не задан в .env")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    print("=" * 60)
    print("🔄 СИНХРОНИЗАЦИЯ QA PIPELINE В N8N DATA TABLES")
    print(f"🌐 Сервер n8n: {N8N_URL}")
    print("=" * 60)

    # 1. QA Pipeline Tasks Table
    tasks = conn.execute("SELECT * FROM pipeline_tasks").fetchall()
    tasks_rows = []
    for t in tasks:
        issue_key = t["issue_key"]
        cases_count = conn.execute("SELECT COUNT(*) FROM test_cases WHERE issue_key = ?", (issue_key,)).fetchone()[0]
        files_count = conn.execute("SELECT COUNT(*) FROM autotest_files WHERE issue_key = ?", (issue_key,)).fetchone()[0]
        latest_audit = conn.execute("SELECT * FROM audit_reports WHERE issue_key = ? ORDER BY id DESC LIMIT 1", (issue_key,)).fetchone()

        audit_score = latest_audit["score"] if latest_audit else 0
        audit_verdict = latest_audit["verdict"] if latest_audit else "PENDING"

        tasks_rows.append({
            "issue_key": str(t["issue_key"]),
            "summary": str(t["summary"] or "")[:100],
            "current_stage": int(t["current_stage"] or 0),
            "status": str(t["status"] or "INITIAL"),
            "dor_score": int(t["dor_score"] or 0),
            "dor_verdict": str(t["dor_verdict"] or "PENDING"),
            "test_cases_count": int(cases_count),
            "autotests_count": int(files_count),
            "audit_score": int(audit_score),
            "audit_verdict": str(audit_verdict),
            "updated_at": str(t["updated_at"] or "")
        })

    tasks_columns = [
        {"name": "issue_key", "type": "string"},
        {"name": "summary", "type": "string"},
        {"name": "current_stage", "type": "number"},
        {"name": "status", "type": "string"},
        {"name": "dor_score", "type": "number"},
        {"name": "dor_verdict", "type": "string"},
        {"name": "test_cases_count", "type": "number"},
        {"name": "autotests_count", "type": "number"},
        {"name": "audit_score", "type": "number"},
        {"name": "audit_verdict", "type": "string"},
        {"name": "updated_at", "type": "string"}
    ]
    t1_id = recreate_table_with_data("QA Pipeline Tasks", tasks_columns, tasks_rows)
    print(f"✅ Таблица 1: 'QA Pipeline Tasks' (ID: {t1_id}) — {len(tasks_rows)} строк")

    # 2. QA Pipeline Stages Table
    stages = conn.execute("SELECT * FROM pipeline_stages ORDER BY stage_number ASC").fetchall()
    stages_rows = []
    for s in stages:
        stages_rows.append({
            "issue_key": str(s["issue_key"]),
            "stage_number": int(s["stage_number"]),
            "stage_name": str(s["stage_name"]),
            "status": str(s["status"]),
            "score": int(s["score"] or 0),
            "verdict": str(s["verdict"] or ""),
            "completed_at": str(s["completed_at"] or "")
        })

    stages_columns = [
        {"name": "issue_key", "type": "string"},
        {"name": "stage_number", "type": "number"},
        {"name": "stage_name", "type": "string"},
        {"name": "status", "type": "string"},
        {"name": "score", "type": "number"},
        {"name": "verdict", "type": "string"},
        {"name": "completed_at", "type": "string"}
    ]
    t2_id = recreate_table_with_data("QA Pipeline Stages", stages_columns, stages_rows)
    print(f"✅ Таблица 2: 'QA Pipeline Stages' (ID: {t2_id}) — {len(stages_rows)} строк")

    # 3. QA Test Cases Table
    cases = conn.execute("SELECT * FROM test_cases ORDER BY id ASC").fetchall()
    cases_rows = []
    for c in cases:
        steps_list = json.loads(c["steps_json"] or "[]")
        cases_rows.append({
            "issue_key": str(c["issue_key"]),
            "qase_id": str(c["qase_id"] or ""),
            "title": str(c["title"] or "")[:120],
            "layer": str(c["layer"] or "api"),
            "severity": str(c["severity"] or "normal"),
            "steps_count": int(len(steps_list))
        })

    cases_columns = [
        {"name": "issue_key", "type": "string"},
        {"name": "qase_id", "type": "string"},
        {"name": "title", "type": "string"},
        {"name": "layer", "type": "string"},
        {"name": "severity", "type": "string"},
        {"name": "steps_count", "type": "number"}
    ]
    t3_id = recreate_table_with_data("QA Test Cases", cases_columns, cases_rows)
    print(f"✅ Таблица 3: 'QA Test Cases' (ID: {t3_id}) — {len(cases_rows)} строк")

    conn.close()
    print("=" * 60)
    print(f"🎉 Все таблицы n8n Data Tables успешно обновлены!")
    print(f"👉 Откройте в браузере раздел Data Tables: {N8N_URL}/tables")
    print("=" * 60)


def print_tables_status():
    tables = list_n8n_tables()
    print("=" * 60)
    print("📊 ТЕКУЩИЕ N8N DATA TABLES:")
    print("=" * 60)
    for t in tables:
        tid = t["id"]
        tname = t["name"]
        res = requests.get(f"{N8N_URL}/api/v1/data-tables/{tid}/rows", headers=get_headers(), timeout=10)
        rows_count = len(res.json().get("data", [])) if res.ok else 0
        cols_count = len(t.get("columns", []))
        print(f"  • Таблица: '{tname}' (ID: {tid})")
        print(f"    Колонок: {cols_count} | Записей: {rows_count}")
    print("=" * 60)


if __name__ == "__main__":
    if "--status" in sys.argv or "--list" in sys.argv:
        print_tables_status()
    else:
        sync_all_to_n8n()
