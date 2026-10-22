import os
import requests
import json
import time
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')

jira_base = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
auth = (os.getenv('ATLASSIAN_USER_EMAIL'), os.getenv('ATLASSIAN_API_TOKEN'))
n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678')
api_key = os.getenv('N8N_API_KEY')
n8n_headers = {'X-N8N-API-KEY': api_key}

issue_key = 'JS-39'

print(f"🚀 1. Transitioning {issue_key} to «В работе» (10046)...")
r_trans = requests.post(
    f'{jira_base}/rest/api/2/issue/{issue_key}/transitions',
    auth=auth,
    json={'transition': {'id': '21'}}
)
print(f"Transition status: {r_trans.status_code}")

print("\n⏳ 2. Monitoring n8n workflow execution...")
start_time = time.time()
target_exec = None

for attempt in range(20):
    time.sleep(2)
    try:
        r = requests.get(f'{n8n_url}/api/v1/executions?limit=5', headers=n8n_headers, timeout=5)
        if r.status_code == 200:
            execs = r.json().get('data', [])
            for e in execs:
                # Check recent execution
                if e.get('workflowId') == 'Dv1WydaTMC1lxR0E':
                    exec_id = e.get('id')
                    status = e.get('status')
                    started = e.get('startedAt')
                    print(f" - Found Execution #{exec_id}: status={status}, started={started}")
                    target_exec = exec_id
                    if status in ['success', 'error', 'waiting']:
                        break
            if target_exec:
                break
    except Exception as err:
        print("Polling error:", err)

print(f"\nTarget Execution: #{target_exec}")
