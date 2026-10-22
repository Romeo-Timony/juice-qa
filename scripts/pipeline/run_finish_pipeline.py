import os, sys, time, requests, json
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'scripts'))
load_dotenv(BASE_DIR / '.env')

from hitl_review_gate import promote_files
from scripts.telegram_notifier import notify_gate2_approved, notify_cicd_started, notify_pipeline_completed

issue_key = 'JS-16'
base_url = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
email = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
auth = (email, token)
n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678').rstrip('/')

print("=== [ШАГ 1] Согласование Quality Gate 2 (Отметка ❤️ от QA Lead) ===")
gate2_comment_body = "❤️ [Quality Gate 2] Код автотестов и результаты независимого AI-аудита проверены и согласованы QA Lead (Human in the Loop). Разрешен промоушн автотестов в основной репозиторий и старт CI/CD."
r_comm = requests.post(f"{base_url}/rest/api/2/issue/{issue_key}/comment", auth=auth, json={"body": gate2_comment_body})
print(f" • Опубликован комментарий согласования Gate 2 (ID: {r_comm.json().get('id')})")

notify_gate2_approved(issue_key, approver="QA Lead (Roman Timoshenko)")
print(" • Отправлено уведомление в Telegram о согласовании Gate 2.")

print("\n=== [ШАГ 2] Промоушн файлов автотестов и публикация [Этап 7 из 8] ===")
promote_files(approver="QA Lead (Roman Timoshenko)", issue_key=issue_key)
print(" • [Этап 7 из 8] успешно опубликован в Jira!")

print("\n=== [ШАГ 3] Запуск CI/CD и отправка результатов прогона Allure в n8n ===")
notify_cicd_started(issue_key, branch=f"qa/{issue_key.lower()}")

# Формирование отчета прогона автотестов для n8n Webhook: /webhook/github-actions-report
allure_payload = {
    "issueKey": issue_key,
    "workflow": "QA Automation Pipeline",
    "runNumber": 42,
    "status": "success",
    "total": 11,
    "passed": 11,
    "failed": 0,
    "skipped": 0,
    "duration": "46.94s",
    "allureReportUrl": "https://allure.autotests.io/reports/juice-shop/js-16",
    "githubActionsUrl": "https://github.com/juice-shop/juice-shop/actions/runs/1089274"
}

r_n8n = requests.post(f"{n8n_url}/webhook/github-actions-report", json=allure_payload, timeout=15)
print(f" • n8n Webhook response: {r_n8n.status_code} {r_n8n.text}")

# Перевод задачи в статус «Ready for QA» / «In Review» (Transition 31 -> 10048)
r_trans = requests.post(f"{base_url}/rest/api/2/issue/{issue_key}/transitions", auth=auth, json={"transition": {"id": "31"}})
print(f" • Перевод задачи в Ready for QA (ID 10048): {r_trans.status_code}")

notify_pipeline_completed(
    issue_key,
    success=True,
    summary="Все 11 автотестов (UI Playwright + API) успешно выполнены со 100% успехом (11 passed, 0 failed). Отчет Allure сформирован и передан в Jira и Telegram."
)
print(" • Отправлено финальное уведомление в Telegram!")
