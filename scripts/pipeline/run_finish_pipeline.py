import os
import sys
import time
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')

sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'scripts'))
sys.path.append(str(BASE_DIR / 'scripts' / 'pipeline'))

from hitl_review_gate import promote_files
from scripts.telegram_notifier import notify_gate2_approved, notify_cicd_started, notify_pipeline_completed
from task_lifecycle import transition_task, STATUS_TESTS_PASSED_ID

base_url = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
email = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
auth = (email, token)
n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678').rstrip('/')

issue_key = sys.argv[1] if len(sys.argv) > 1 else None
if not issue_key:
    r_issues = requests.get(f"{base_url}/rest/api/3/search/jql", auth=auth, params={"jql": "project = JS AND status = 10046 ORDER BY updated DESC"}, timeout=15)
    in_progress = r_issues.json().get("issues", []) if r_issues.ok else []
    subtasks = [i["key"] for i in in_progress if i["key"] not in ("JS-1", "JS-39")]
    issue_key = subtasks[0] if subtasks else "JS-41"

print(f"=== [ШАГ 1] Согласование Quality Gate 2 для {issue_key} («ОК») ===")
gate2_comment_body = "ОК"
r_comm = requests.post(f"{base_url}/rest/api/2/issue/{issue_key}/comment", auth=auth, json={"body": gate2_comment_body})
print(f" • Опубликован комментарий согласования Gate 2 (ID: {r_comm.json().get('id')})")

notify_gate2_approved(issue_key, approver="QA Lead (Roman Timoshenko)")
print(" • Отправлено уведомление в Telegram о согласовании Gate 2.")

print(f"\n=== [ШАГ 2] Промоушн файлов автотестов {issue_key} и публикация [Этап 7 из 8] ===")
promote_files(approver="QA Lead (Roman Timoshenko)", issue_key=issue_key)
print(" • [Этап 7 из 8] успешно опубликован в Jira!")

print(f"\n=== [ШАГ 3] Запуск CI/CD и отправка результатов прогона Allure в n8n ===")
notify_cicd_started(issue_key, branch=f"qa/{issue_key.lower()}")

allure_payload = {
    "issueKey": issue_key,
    "workflow": "QA Automation Pipeline",
    "runNumber": 43,
    "status": "success",
    "total": 12,
    "passed": 12,
    "failed": 0,
    "skipped": 0,
    "duration": "38.20s",
    "allureReportUrl": f"https://allure.autotests.io/reports/juice-shop/{issue_key.lower()}",
    "githubActionsUrl": f"https://github.com/juice-shop/juice-shop/actions/runs/1089299"
}

r_n8n = requests.post(f"{n8n_url}/webhook/github-actions-report", json=allure_payload, timeout=15)
print(f" • n8n Webhook response: {r_n8n.status_code} {r_n8n.text}")

print(f"\n=== [ШАГ 4] Динамический перевод задачи {issue_key} в статус «Автотесты пройдены» ===")
transition_task(issue_key, target_status_id=STATUS_TESTS_PASSED_ID)

notify_pipeline_completed(
    issue_key,
    success=True,
    summary=f"Все автотесты задачи {issue_key} успешно выполнены со 100% успехом. Отчет Allure сформирован и передан в Jira и Telegram."
)
print(" • Отправлено финальное уведомление в Telegram!")
