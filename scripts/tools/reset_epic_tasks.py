"""Utility to completely reset and anonymize Epic tasks JS-40, JS-41, JS-42:
- Jira Cloud: Status 10045 (К выполнению), 0 comments, labels=[]
- Qase TMS: Deletes any lingering test cases for JS-40, JS-41, JS-42
- Local Codebase: Deletes generated test files (tests/backend/test_js40*, tests/frontend/test_js41*, tests/frontend/test_js42*, tests/review/*)
- Databases: Clears event store, state projections, and n8n Data Tables
"""

import os
import sys
import glob
import shutil
import sqlite3
import requests
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

JIRA_URL = (os.getenv("ATLASSIAN_BASE_URL") or "https://romeo-timony.atlassian.net").rstrip('/')
JIRA_EMAIL = os.getenv("ATLASSIAN_USER_EMAIL")
JIRA_TOKEN = os.getenv("ATLASSIAN_API_TOKEN")
auth = (JIRA_EMAIL, JIRA_TOKEN)

N8N_URL = (os.getenv("N8N_URL") or "http://201.34.147.33:5678").rstrip('/')
N8N_API_KEY = os.getenv("N8N_API_KEY")
n8n_headers = {"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"}

QASE_TOKEN = os.getenv("QASE_API_TOKEN")
QASE_PROJECT = os.getenv("QASE_PROJECT_CODE", "JS")
qase_headers = {"Token": QASE_TOKEN, "Accept": "application/json", "Content-Type": "application/json"}

TASKS = ["JS-40", "JS-41", "JS-42"]

print("=" * 80)
print("🧹 ПОЛНЫЙ СБРОС И СИНХРОНИЗАЦИЯ ЗАДАЧ: JS-40, JS-41, JS-42")
print("=" * 80)

# 1. Сброс Jira Cloud
for key in TASKS:
    print(f"\n[JIRA] Обработка задачи {key}...")
    r = requests.get(f"{JIRA_URL}/rest/api/2/issue/{key}", auth=auth, timeout=10)
    if r.status_code != 200:
        print(f"  ❌ Ошибка загрузки {key}: HTTP {r.status_code}")
        continue
    
    data = r.json()
    fields = data.get("fields", {})
    status_id = fields.get("status", {}).get("id")
    comments = fields.get("comment", {}).get("comments", [])
    
    # 1.1 Перевод в 'К выполнению' (10045)
    if status_id != "10045":
        r_tr = requests.post(f"{JIRA_URL}/rest/api/2/issue/{key}/transitions", auth=auth, json={"transition": {"id": "11"}}, timeout=10)
        if r_tr.status_code in (200, 204):
            print("  ✅ Статус возвращен в «К выполнению» (ID: 10045)")
        else:
            print(f"  ⚠️ Ошибка смены статуса: HTTP {r_tr.status_code}")
    else:
        print("  ℹ️ Статус уже «К выполнению» (ID: 10045)")

    # 1.2 Очистка всех комментариев
    if comments:
        deleted_count = 0
        for c in comments:
            cid = c["id"]
            r_del = requests.delete(f"{JIRA_URL}/rest/api/2/issue/{key}/comment/{cid}", auth=auth, timeout=10)
            if r_del.status_code in (200, 204):
                deleted_count += 1
        print(f"  ✅ Удалено {deleted_count}/{len(comments)} комментариев")
    else:
        print("  ℹ️ Комментариев нет (Чисто)")

    # 1.3 Сброс меток
    r_put = requests.put(f"{JIRA_URL}/rest/api/2/issue/{key}", auth=auth, json={"fields": {"labels": []}}, timeout=10)
    if r_put.status_code in (200, 204):
        print("  ✅ Метки сброшены в []")
    else:
        print(f"  ⚠️ Ошибка сброса меток: HTTP {r_put.status_code}")

# 2. Очистка Qase TMS
print("\n[QASE TMS] Проверка и очистка тест-кейсов в Qase TMS...")
if QASE_TOKEN:
    res = requests.get(f"https://api.qase.io/v1/case/{QASE_PROJECT}?limit=100", headers=qase_headers, timeout=10)
    if res.status_code == 200:
        cases = res.json().get("result", {}).get("entities", [])
        del_cases = 0
        for c in cases:
            title = str(c.get("title", "")).lower()
            desc = str(c.get("description", "")).lower()
            if any(t.lower() in title or t.lower() in desc for t in TASKS) or "дубликат" in title or "регистрация" in title or "авторизация" in title:
                cid = c["id"]
                r_dc = requests.delete(f"https://api.qase.io/v1/case/{QASE_PROJECT}/{cid}", headers=qase_headers, timeout=10)
                if r_dc.status_code in (200, 204):
                    del_cases += 1
                    print(f"  🗑️ Удален тест-кейс из Qase: [JS-{cid}] {c.get('title')[:60]}")
        print(f"  ✅ Qase TMS: Удалено {del_cases} кейсов (Осталось: {len(cases) - del_cases})")
    else:
        print(f"  ⚠️ Ошибка Qase API: HTTP {res.status_code}")

# 3. Очистка локальных сгенерированных автотестов в коде
print("\n[КОДОВАЯ БАЗА] Удаление локальных файлов автотестов для JS-40, JS-41, JS-42...")
test_patterns = [
    "tests/backend/test_js40*.py",
    "tests/frontend/test_js41*.py",
    "tests/frontend/test_js42*.py",
    "tests/review/backend/*.py",
    "tests/review/frontend/*.py",
    "tests/review/REVIEW_REPORT.md"
]

deleted_files = 0
for pat in test_patterns:
    for fp in glob.glob(str(BASE_DIR / pat)):
        p = Path(fp)
        if p.is_file():
            p.unlink()
            deleted_files += 1
            print(f"  🗑️ Удален файл автотестов: {p.relative_to(BASE_DIR)}")

# Очистка pycache
for root, dirs, files in os.walk(BASE_DIR / "tests"):
    for d in dirs:
        if d == "__pycache__":
            shutil.rmtree(os.path.join(root, d), ignore_errors=True)
print(f"  ✅ Удалено сгенерированных файлов автотестов: {deleted_files}")

# 4. Очистка базы данных событий (Event Store & State)
print("\n[БАЗА ДАННЫХ] Очистка истории событий и состояний задач...")
db_path = BASE_DIR / "data" / "qa_pipeline.db"
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    placeholders = ",".join("?" for _ in TASKS)
    
    cur.execute(f"DELETE FROM qa_pipeline_events WHERE issue_key IN ({placeholders})", TASKS)
    ev_del = cur.rowcount
    cur.execute(f"DELETE FROM qa_pipeline_state WHERE issue_key IN ({placeholders})", TASKS)
    st_del = cur.rowcount
    cur.execute(f"DELETE FROM qa_scheduled_events WHERE issue_key IN ({placeholders})", TASKS)
    sc_del = cur.rowcount
    cur.execute(f"DELETE FROM qaops_idempotency WHERE scope IN ({placeholders})", TASKS)
    id_del = cur.rowcount
    conn.commit()
    conn.close()
    print(f"  ✅ База данных очищена: events={ev_del}, state={st_del}, scheduled={sc_del}, idempotency={id_del}")

# 5. Очистка n8n Data Tables
print("\n[N8N DATA TABLES] Очистка строк в витрине n8n...")
TABLES = [
    ("fanXRyDssOhkqnjc", "QA Pipeline Tasks"),
    ("LV1Se308Nm5Nfy7S", "QA Pipeline Stages"),
    ("zWJuBLsR2JvJz0Oo", "QA Test Cases"),
    ("eCPXK5QUBpIxYyEc", "QA Pipeline Errors")
]

for tid, tname in TABLES:
    r_rows = requests.get(f"{N8N_URL}/api/v1/data-tables/{tid}/rows", headers=n8n_headers, timeout=10)
    if r_rows.status_code == 200:
        rows = r_rows.json().get("data", [])
        del_count = 0
        for row in rows:
            if row.get("issue_key") in TASKS:
                row_id = row.get("id")
                r_del = requests.delete(f"{N8N_URL}/api/v1/data-tables/{tid}/rows/{row_id}", headers=n8n_headers, timeout=10)
                if r_del.status_code in (200, 204):
                    del_count += 1
        print(f"  ✅ {tname}: Удалено {del_count} строк")
    else:
        print(f"  ⚠️ Ошибка доступа к {tname}: HTTP {r_rows.status_code}")

print("\n" + "=" * 80)
print("🎉 ВСЕ 3 ЗАДАЧИ (JS-40, JS-41, JS-42) И ИХ АВТОТЕСТЫ ПОЛНОСТЬЮ ОБНУЛЕНЫ И СИНХРОНИЗИРОВАНЫ!")
print("=" * 80)
