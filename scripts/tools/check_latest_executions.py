import os
import sys
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')
dotenv.load_dotenv('qa-automation/.env')

n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678').rstrip('/')
n8n_key = os.getenv('N8N_API_KEY')
headers = {'X-N8N-API-KEY': n8n_key}

r = requests.get(f"{n8n_url}/api/v1/executions?limit=10", headers=headers)
if r.ok:
    execs = r.json().get('data', [])
    print(f"Latest {len(execs)} executions in n8n:")
    for ex in execs:
        print(f"ID: {ex.get('id')} | WorkflowId: {ex.get('workflowId')} | Mode: {ex.get('mode')} | Status: {ex.get('status')} | Started: {ex.get('startedAt')} | Stopped: {ex.get('stoppedAt')}")
else:
    print("Error fetching executions:", r.status_code, r.text)
