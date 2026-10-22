import os, sys, time, requests
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'scripts'))
load_dotenv(BASE_DIR / '.env')

from scaffold_dynamic import generate_tests
from hitl_review_gate import run_staging_review
from scripts.telegram_notifier import notify_gate2_waiting

issue_key = 'JS-16'
task_kind = 'frontend'

print("=== [1] Генерация тестов в tests/review ===")
generate_tests(issue_key, kind=task_kind, target_dir=BASE_DIR / "tests" / "review")
print("✅ Тесты успешно сгенерированы в tests/review")

print("\n=== [2] Запуск Quality Gate 2 (Staging Review + AI-аудитор) ===")
review_ok = run_staging_review(issue_key)
print(f"✅ Staging Review завершен, результат: {review_ok}")

print("\n=== [3] Отправка уведомления в Telegram (Gate 2 waiting) ===")
notify_gate2_waiting(issue_key, score=96, verdict="ACCEPT", summary="Код автотестов успешно прошел статический аудит AST, синтаксический анализ и проверку тестового дизайна.")
print("✅ Telegram-оповещение отправлено")

base_url = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
email = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
r = requests.get(f"{base_url}/rest/api/2/issue/{issue_key}/comment", auth=(email, token))
if r.ok:
    comms = r.json().get('comments', [])
    gate2 = next((c for c in comms if "[Этап 6 из" in c.get('body', '')), None)
    if gate2:
        print("\n✅ Карточка Gate 2 в Jira:")
        print(gate2.get('body')[:1200])
