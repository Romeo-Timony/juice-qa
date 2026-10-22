import os
import sys
import time
import requests
import json
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('d:/Desktop/Juice_shop/qa-automation/.env')

jira_url = os.getenv('ATLASSIAN_BASE_URL').rstrip('/')
user = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
auth = (user, token)

n8n_url = os.getenv('N8N_URL').rstrip('/')
n8n_key = os.getenv('N8N_API_KEY')
n8n_headers = {'X-N8N-API-KEY': n8n_key}

issue_key = 'JS-40'

print(f"==================================================")
print(f"🚀 ЗАПУСК СКВОЗНОЙ ПРОВЕРКИ ПАЙПЛАЙНА ДЛЯ {issue_key}")
print(f"==================================================")

# Step 1: Transition JS-40 to 'В работе' (transition ID 21)
print(f"\n[1/6] Перевод задачи {issue_key} в 'В работе' (10046)...")
r_trans = requests.post(f"{jira_url}/rest/api/2/issue/{issue_key}/transitions", auth=auth, json={"transition": {"id": "21"}})
print(f" -> Ответ Jira: {r_trans.status_code}")

# Trigger webhook directly to guarantee immediate pickup
print(" -> Вызов webhook n8n для задачи...")
webhook_res = requests.post(f"{n8n_url}/webhook/jira-dor-gate", json={"issueKey": issue_key, "actor": "Roman Timoshenko"})
print(f" -> Ответ n8n webhook: {webhook_res.status_code}")

print("\n[2/6] Ожидание выполнения Этапов 1-5 и остановки на Gate 1 Wait...")
active_exec_id = None
for i in range(20):
    time.sleep(2)
    r_exec = requests.get(f"{n8n_url}/api/v1/executions?limit=3", headers=n8n_headers)
    execs = r_exec.json().get('data', [])
    for e in execs:
        # Check if running or waiting
        if e['status'] in ['waiting', 'running']:
            active_exec_id = e['id']
            break
    if active_exec_id:
        print(f" -> Найден активный execution #{active_exec_id}")
        break

if not active_exec_id:
    # Check if latest execution succeeded or errored
    latest = execs[0] if execs else None
    print(f" -> Нет waiting/running, последний execution: {latest}")
    if latest:
        active_exec_id = latest['id']

# Monitor execution state
for i in range(30):
    r_detail = requests.get(f"{n8n_url}/api/v1/executions/{active_exec_id}?includeData=true", headers=n8n_headers)
    d = r_detail.json().get('data', {})
    status = d.get('status')
    finished = d.get('finished')
    run_data = d.get('resultData', {}).get('runData', {})
    print(f"[{i+1}] Execution #{active_exec_id}: status={status}, nodes_run={len(run_data)}")
    
    if status == 'error':
        print(f"❌ ОШИБКА в execution #{active_exec_id}!")
        last_node = d.get('resultData', {}).get('lastNodeExecuted')
        print(f"Последний узел с ошибкой: {last_node}")
        error_info = d.get('resultData', {}).get('error', {})
        print(f"Error message: {error_info.get('message')}")
        break
        
    if status == 'waiting':
        print(f"✅ Воркфлоу успешно ВСТАЛ НА ПАУЗУ (HITL Gate)!")
        break
        
    if finished:
        print(f"Воркфлоу завершился со статусом: {status}")
        break
    time.sleep(3)
