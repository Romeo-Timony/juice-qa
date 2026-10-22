import os
import sys
import requests
import sqlite3
import subprocess
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

JIRA_URL = os.getenv("ATLASSIAN_BASE_URL", "https://romeo-timony.atlassian.net").rstrip("/")
EMAIL = os.getenv("ATLASSIAN_USER_EMAIL")
TOKEN = os.getenv("ATLASSIAN_API_TOKEN")
auth = (EMAIL, TOKEN)
ISSUE_KEY = "JS-16"

print("=" * 80)
print(f"🧹 ПОЛНАЯ ПОДГОТОВКА И ОЧИСТКА ЗАДАЧИ {ISSUE_KEY}")
print("=" * 80)

# 1. Удаление всех комментариев в Jira
res = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment", auth=auth)
comments = res.json().get("comments", [])
print(f" • Удаление {len(comments)} комментариев в Jira...")
for c in comments:
    cid = c["id"]
    requests.delete(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/comment/{cid}", auth=auth)
print(" • Все комментарии в Jira удалены")

# 2. Очистка меток
requests.put(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=auth, json={"fields": {"labels": []}})
print(" • Метки задачи очищены")

# 2.1. Удаление ссылок на Qase TMS из Remote Links (сохраняя Confluence и Figma)
r_links = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/remotelink", auth=auth)
if r_links.ok and isinstance(r_links.json(), list):
    for rl in r_links.json():
        rl_id = rl.get("id")
        title = rl.get("object", {}).get("title", "")
        url = rl.get("object", {}).get("url", "")
        app_name = rl.get("application", {}).get("name", "")
        global_id = rl.get("globalId", "")
        if any("qase" in str(x).lower() for x in [title, url, app_name, global_id]):
            del_res = requests.delete(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/remotelink/{rl_id}", auth=auth)
            print(f" • Удалена ссылка на Qase TMS (ID {rl_id}): {del_res.status_code}")

# 3. Перевод в «К выполнению» (10045)
r_trans = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth).json().get("transitions", [])
target_t = next((t for t in r_trans if t["to"]["id"] == "10045" or t["id"] == "11"), None)
if target_t:
    requests.post(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}/transitions", auth=auth, json={"transition": {"id": target_t["id"]}})
    print(f" • Статус задачи успешно переведен в «К выполнению» (ID {target_t['id']})")

# 4. Очистка Qase
qase_headers = {"Token": os.getenv("QASE_API_TOKEN"), "Content-Type": "application/json"}
s_res = requests.get("https://api.qase.io/v1/suite/JS?limit=100", headers=qase_headers).json().get("result", {}).get("entities", [])
for s in s_res:
    if ISSUE_KEY in s.get("title", ""):
        requests.delete(f"https://api.qase.io/v1/suite/JS/{s['id']}", headers=qase_headers)
        print(f" • Удален Qase suite: {s.get('title')}")

# 5. Очистка SQLite
db_path = BASE_DIR / "data" / "qa_pipeline.db"
if db_path.exists():
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM test_cases WHERE issue_key = ?", (ISSUE_KEY,))
    conn.execute("DELETE FROM pipeline_stages WHERE issue_key = ?", (ISSUE_KEY,))
    conn.execute("DELETE FROM pipeline_tasks WHERE issue_key = ?", (ISSUE_KEY,))
    conn.commit()
    conn.close()
    print(" • Записи задачи в SQLite очищены")

# 6. Очистка Staging review папки
review_dir = BASE_DIR / "tests" / "review"
if review_dir.exists():
    for f in review_dir.rglob("*.py"):
        f.unlink()
    print(" • Папка tests/review очищена")

# 7. Очистка изолированного worktree
wt_dir = BASE_DIR / ".worktrees" / f"qa-{ISSUE_KEY.lower()}"
if wt_dir.exists():
    subprocess.run(["git", "worktree", "remove", "--force", str(wt_dir)], cwd=BASE_DIR, capture_output=True)
    print(" • Изолированный Git Worktree очищен")

# 8. Проверка итогового статуса
info = requests.get(f"{JIRA_URL}/rest/api/2/issue/{ISSUE_KEY}", auth=auth).json()
final_status = info["fields"]["status"]["name"]
final_comments = len(info["fields"]["comment"]["comments"])
final_labels = info["fields"]["labels"]

print("\n" + "=" * 80)
print(f"✅ Задача {ISSUE_KEY} полностью готова к тестированию!")
print(f"   Статус в Jira: {final_status}")
print(f"   Комментариев: {final_comments}")
print(f"   Метки: {final_labels}")
print("=" * 80)
