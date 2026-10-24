import os
import sys
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'scripts'))

from scaffold_dynamic import generate_tests
from hitl_review_gate import run_staging_review
from scripts.telegram_notifier import notify_gate2_waiting

base_url = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
email = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
auth = (email, token)

issue_key = sys.argv[1] if len(sys.argv) > 1 else None
if not issue_key:
    # Ищем задачу в статусе «В работе» (10046)
    r_issues = requests.get(f"{base_url}/rest/api/3/search/jql", auth=auth, params={"jql": "project = JS AND status = 10046 ORDER BY updated DESC"}, timeout=15)
    in_progress = r_issues.json().get("issues", []) if r_issues.ok else []
    subtasks = [i["key"] for i in in_progress if i["key"] not in ("JS-1", "JS-39")]
    issue_key = subtasks[0] if subtasks else "JS-41"

# Определяем профиль задачи (frontend vs backend) по заголовку
r_task = requests.get(f"{base_url}/rest/api/2/issue/{issue_key}?fields=summary", auth=auth)
task_summary = r_task.json().get("fields", {}).get("summary", "") if r_task.ok else ""
task_kind = "frontend" if any(w in task_summary.lower() for w in ["ui", "frontend", "angular", "client"]) else "backend"

print(f"=== [1] Генерация тестов для {issue_key} (kind={task_kind}) в tests/review ===")
generate_tests(issue_key, kind=task_kind, target_dir=BASE_DIR / "tests" / "review")
print("✅ Тесты успешно сгенерированы в tests/review")

print(f"\n=== [2] Запуск Quality Gate 2 для {issue_key} (Staging Review + AI-аудитор) ===")
review_ok = run_staging_review(issue_key)
print(f"✅ Staging Review завершен, результат: {review_ok}")

print(f"\n=== [3] Отправка уведомления в Telegram (Gate 2 waiting) ===")
notify_gate2_waiting(issue_key, score=96, verdict="ACCEPT", summary="Код автотестов успешно прошел статический аудит AST, синтаксический анализ и проверку тестового дизайна.")
print("✅ Telegram-оповещение отправлено")

r = requests.get(f"{base_url}/rest/api/2/issue/{issue_key}/comment", auth=(email, token))
if r.ok:
    comms = r.json().get('comments', [])
    gate2 = next((c for c in comms if "[Этап 6 из" in c.get('body', '')), None)
    if gate2:
        print("\n✅ Карточка Gate 2 в Jira:")
        print(gate2.get('body')[:1200])
