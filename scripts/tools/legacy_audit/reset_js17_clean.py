import os
import sys
import requests
import json
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

JIRA_URL = os.getenv("ATLASSIAN_BASE_URL", "https://romeo-timony.atlassian.net").rstrip("/")
EMAIL = os.getenv("ATLASSIAN_USER_EMAIL")
TOKEN = os.getenv("ATLASSIAN_API_TOKEN")
QASE_TOKEN = os.getenv("QASE_API_TOKEN")
QASE_PROJECT = os.getenv("QASE_PROJECT_CODE", "JS")

ISSUE_KEY = "JS-17"

print("=" * 80)
print(f"🧹 ПОЛНЫЙ СБРОС И ОБНУЛЕНИЕ ЗАДАЧИ {ISSUE_KEY} ДО ЭТАЛОННОГО СОСТОЯНИЯ")
print("=" * 80)

# 1. Удаление всех комментариев в Jira
auth = (EMAIL, TOKEN)
res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth)
comments = res.json().get("comments", [])
print(f"1. Удаление {len(comments)} комментариев в Jira...")
for c in comments:
    cid = c["id"]
    r = requests.delete(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment/{cid}", auth=auth)
    print(f"   • Удален комментарий {cid}: {r.status_code}")

# 2. Очистка меток (labels)
print(f"2. Очистка меток задачи {ISSUE_KEY}...")
r_labels = requests.put(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=auth, json={"fields": {"labels": []}})
print(f"   • Метки очищены: {r_labels.status_code}")

# 3. Сброс статуса на «К выполнению» (ID 10045, Transition 11)
print(f"3. Перевод статуса {ISSUE_KEY} в «К выполнению»...")
# Сначала проверяем доступные переходы
r_trans = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth).json().get("transitions", [])
target_t = next((t for t in r_trans if t["to"]["id"] == "10045" or t["id"] == "11"), None)
if target_t:
    r_post = requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth, json={"transition": {"id": target_t["id"]}})
    print(f"   • Переход {target_t['name']} (ID {target_t['id']}): {r_post.status_code}")
else:
    print("   ℹ️ Переход в 10045 не найден или задача уже в статусе 'К выполнению'")

issue_now = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=auth).json()
print(f"   • Текущий статус в Jira: {issue_now['fields']['status']['name']} (ID {issue_now['fields']['status']['id']})")

# 4. Очистка в Qase TMS
print(f"4. Очистка сьютов и кейсов {ISSUE_KEY} в Qase TMS...")
qase_headers = {"Token": QASE_TOKEN, "Content-Type": "application/json"}
s_res = requests.get(f"https://api.qase.io/v1/suite/{QASE_PROJECT}?limit=100", headers=qase_headers).json().get("result", {}).get("entities", [])
for s in s_res:
    if ISSUE_KEY in s.get("title", ""):
        sid = s["id"]
        # Delete suite
        r_del = requests.delete(f"https://api.qase.io/v1/suite/{QASE_PROJECT}/{sid}", headers=qase_headers)
        print(f"   • Удален сьют Qase #{sid} «{s['title']}»: {r_del.status_code}")

# 5. Очистка SQLite
db_path = BASE_DIR / "data" / "qa_pipeline.db"
if db_path.exists():
    print("5. Очистка локальной базы SQLite...")
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM test_cases WHERE issue_key = ?", (ISSUE_KEY,))
    conn.execute("DELETE FROM pipeline_stages WHERE issue_key = ?", (ISSUE_KEY,))
    conn.execute("DELETE FROM pipeline_tasks WHERE issue_key = ?", (ISSUE_KEY,))
    conn.commit()
    conn.close()
    print("   • SQLite очищена для", ISSUE_KEY)

# 6. Очистка Staging папок
print("6. Очистка Staging директорий...")
review_dir = BASE_DIR / "tests" / "review"
if review_dir.exists():
    for f in review_dir.rglob("*.py"):
        f.unlink()
    state_file = review_dir / ".review_state.json"
    if state_file.exists():
        state_file.unlink()
    report_file = review_dir / "REVIEW_REPORT.md"
    if report_file.exists():
        report_file.unlink()
print("   • Staging директория tests/review/ очищена.")

# 7. Синхронизация n8n Data Tables
print("7. Обновление n8n Data Tables...")
try:
    sys.path.insert(0, str(BASE_DIR))
    from scripts.n8n_tables import sync_all_to_n8n
    sync_all_to_n8n()
    print("   • n8n Data Tables синхронизированы.")
except Exception as e:
    print(f"   ⚠️ Ошибка синхронизации n8n Data Tables: {e}")

print("=" * 80)
print(f"✅ ЗАДАЧА {ISSUE_KEY} ПОЛНОСТЬЮ ОБНУЛЕНА И ГОТОВА К ЭТАЛОННОМУ ЗАПУСКУ!")
print("=" * 80)
