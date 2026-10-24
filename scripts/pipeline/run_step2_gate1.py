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
sys.path.append(str(BASE_DIR / "scripts"))
from scripts.telegram_notifier import notify_gate1_approved

base_url = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
email = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678').rstrip('/')
auth = (email, token)

issue_key = sys.argv[1] if len(sys.argv) > 1 else None
if not issue_key:
    # Ищем задачу в статусе «В работе» (10046)
    r_issues = requests.get(f"{base_url}/rest/api/3/search/jql", auth=auth, params={"jql": "project = JS AND status = 10046 ORDER BY updated DESC"}, timeout=15)
    in_progress = r_issues.json().get("issues", []) if r_issues.ok else []
    subtasks = [i["key"] for i in in_progress if i["key"] not in ("JS-1", "JS-39")]
    issue_key = subtasks[0] if subtasks else (in_progress[0]["key"] if in_progress else "JS-41")
    print(f"🎯 Динамически определена активная задача: {issue_key}")

print(f"\n[ЭТАП 2] Отправка согласования Quality Gate 1 для {issue_key} («ОК»)...")
gate1_approval_body = "ОК"
r_app1 = requests.post(f"{base_url}/rest/api/2/issue/{issue_key}/comment", auth=auth, json={"body": gate1_approval_body})
print(f" • Опубликован комментарий согласования Gate 1 (ID: {r_app1.json().get('id')})")

notify_gate1_approved(issue_key, approver="QA Lead (Roman Timoshenko)")
print(" • Отправлено уведомление в Telegram о согласовании Gate 1.")

print(" • Запуск пайплайна n8n для обработки Gate 1 и создания кейсов в Qase...")
r_n8n = requests.post(f"{n8n_url}/webhook/jira-dor-gate", json={"issueKey": issue_key, "actor": "Roman Timoshenko"})
print(f" • n8n ответ: {r_n8n.status_code} {r_n8n.text}")

print(" • Ожидание создания кейсов в Qase TMS и карточки Gate 2 в Jira...")
gate2_card = None
for attempt in range(30):
    time.sleep(3)
    r_comm2 = requests.get(f"{base_url}/rest/api/2/issue/{issue_key}/comment", auth=auth).json()
    comms2 = r_comm2.get("comments", [])
    gate2_card = next((c for c in comms2 if "[Этап 6 из 8]" in c.get("body", "")), None)
    if gate2_card:
        break

if gate2_card:
    print("✅ Карточка Gate 2 успешно создана в Jira!")
    print(gate2_card["body"][:1000])
else:
    print("Внимание: карточка Gate 2 пока не появилась. Проверим комментарии.")
