import os
import sys
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

JIRA_URL = os.getenv("ATLASSIAN_BASE_URL", "https://romeo-timony.atlassian.net").rstrip("/")
EMAIL = os.getenv("ATLASSIAN_USER_EMAIL")
TOKEN = os.getenv("ATLASSIAN_API_TOKEN")
auth = (EMAIL, TOKEN)
ISSUE_KEY = "JS-17"

print("=" * 80)
print(f"🚀 ЧИСТЫЙ ЭТАЛОННЫЙ СБРОС И ЗАПУСК ЗАДАЧИ {ISSUE_KEY}")
print("=" * 80)

# 1. Удаление всех существующих комментариев
res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth)
comments = res.json().get("comments", [])
print(f"1. Удаление {len(comments)} комментариев в Jira...")
for c in comments:
    cid = c["id"]
    requests.delete(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment/{cid}", auth=auth)
print("   • Все комментарии удалены.")

# 2. Очистка меток
print(f"2. Очистка меток задачи {ISSUE_KEY}...")
requests.put(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=auth, json={"fields": {"labels": []}})

# 3. Сброс в «К выполнению» (ID 10045, Transition 11)
print(f"3. Перевод {ISSUE_KEY} в «К выполнению»...")
r_trans = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth).json().get("transitions", [])
target_t = next((t for t in r_trans if t["to"]["id"] == "10045" or t["id"] == "11"), None)
if target_t:
    requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth, json={"transition": {"id": target_t["id"]}})
    print("   • Статус: К выполнению")

# 4. Очистка Qase
qase_headers = {"Token": os.getenv("QASE_API_TOKEN"), "Content-Type": "application/json"}
s_res = requests.get(f"https://api.qase.io/v1/suite/JS?limit=100", headers=qase_headers).json().get("result", {}).get("entities", [])
for s in s_res:
    if ISSUE_KEY in s.get("title", ""):
        sid = s["id"]
        requests.delete(f"https://api.qase.io/v1/suite/JS/{sid}", headers=qase_headers)
        print(f"   • Удален сьют Qase #{sid}")

# 5. Очистка SQLite и Staging
import sqlite3
db_path = BASE_DIR / "data" / "qa_pipeline.db"
if db_path.exists():
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM test_cases WHERE issue_key = ?", (ISSUE_KEY,))
    conn.execute("DELETE FROM pipeline_stages WHERE issue_key = ?", (ISSUE_KEY,))
    conn.execute("DELETE FROM pipeline_tasks WHERE issue_key = ?", (ISSUE_KEY,))
    conn.commit()
    conn.close()

review_dir = BASE_DIR / "tests" / "review"
if review_dir.exists():
    for f in review_dir.rglob("*.py"):
        f.unlink()

# 6. Ожидание 5 сек, чтобы внешние вебхуки завершились
print("6. Ожидание 5 секунд для стабилизации состояния Jira...")
time.sleep(5)

# 7. Перевод в «В работе» (ID 10046, Transition 21)
print(f"7. Перевод задачи {ISSUE_KEY} в статус «В работе» (запуск пайплайна)...")
requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth, json={"transition": {"id": "21"}})
print("   • Статус успешно переведен в «В работе».")

print("\n⏳ Ожидание автоматического прогона этапов 1–5 (30 секунд)...")
time.sleep(30)

# 8. Проверка комментариев
r_comm = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth).json()
final_comments = r_comm.get("comments", [])
print(f"\n📊 ИТОГО КОММЕНТАРИЕВ В JIRA: {len(final_comments)}")
for i, c in enumerate(final_comments):
    cid = c.get("id")
    first_line = c["body"].strip().split("\n")[0]
    print(f"   [{i+1}] ID: {cid} | {first_line}")

print("=" * 80)
