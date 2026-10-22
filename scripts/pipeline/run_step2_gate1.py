import os, sys, requests, time
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from scripts.telegram_notifier import notify_gate1_approved

base_url = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
email = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678').rstrip('/')
auth = (email, token)
issue_key = 'JS-16'

print(f"\n[ЭТАП 2] Отправка согласования Quality Gate 1 с отметкой ❤️...")
gate1_approval_body = "❤️ [Quality Gate 1] Спецификация BDD тест-кейсов и матрица трассируемости RTM проверены и согласованы QA Lead (Human in the Loop). Разрешен переход к созданию кейсов в Qase TMS и генерации кода автотестов."
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
    gate2_card = next((c for c in comms2 if "[Этап 6 из 8]" in c["body"]), None)
    if gate2_card:
        break

if gate2_card:
    print("✅ Карточка Gate 2 успешно создана в Jira!")
    print(gate2_card["body"][:1000])
else:
    print("Внимание: карточка Gate 2 пока не появилась. Проверим комментарии.")

