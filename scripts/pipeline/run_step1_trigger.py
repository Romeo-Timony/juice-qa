import os, requests, time, json
from dotenv import load_dotenv

load_dotenv('qa-automation/.env')
base_url = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
email = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678').rstrip('/')
auth = (email, token)

issue_key = 'JS-16'

print(f"--- [ШАГ 1] Перевод {issue_key} в статус «В работе» (Transition 21 -> 10046) ---")
r_trans = requests.post(f"{base_url}/rest/api/2/issue/{issue_key}/transitions", auth=auth, json={"transition": {"id": "21"}})
print(f"Jira transition response: {r_trans.status_code}")

r_issue = requests.get(f"{base_url}/rest/api/2/issue/{issue_key}?fields=status,summary", auth=auth)
if r_issue.ok:
    data = r_issue.json()
    status_name = data.get('fields', {}).get('status', {}).get('name')
    status_id = data.get('fields', {}).get('status', {}).get('id')
    print(f"Текущий статус {issue_key}: {status_name} (ID: {status_id})")

print(f"\n--- [ШАГ 2] Отправка события в n8n DoR Gate Webhook ({n8n_url}/webhook/jira-dor-gate) ---")
payload = {"issueKey": issue_key, "actor": "Roman Timoshenko"}
try:
    r_n8n = requests.post(f"{n8n_url}/webhook/jira-dor-gate", json=payload, timeout=10)
    print(f"n8n Webhook response: {r_n8n.status_code} {r_n8n.text}")
except Exception as e:
    print(f"n8n Webhook error: {e}")

