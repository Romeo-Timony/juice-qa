import os
import requests
import json
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

n8n_url = os.getenv("N8N_URL", "http://201.34.147.33:5678")
n8n_key = os.getenv("N8N_API_KEY")

headers = {"X-N8N-API-KEY": n8n_key}

res = requests.get(f"{n8n_url}/api/v1/executions?limit=5", headers=headers)
print(f"Status: {res.status_code}")
if res.ok:
    data = res.json().get('data', [])
    for ex in data:
        eid = ex.get('id')
        status = ex.get('status')
        mode = ex.get('mode')
        started = ex.get('startedAt')
        wfid = ex.get('workflowId')
        print(f"Exec ID: {eid} | Status: {status} | Mode: {mode} | Started: {started} | WF: {wfid}")
        # fetch execution detail
        detail_res = requests.get(f"{n8n_url}/api/v1/executions/{eid}?includeData=true", headers=headers)
        if detail_res.ok:
            detail = detail_res.json()
            resume_token = (detail.get('data') or {}).get('resumeToken')
            wait_node = (detail.get('data') or {}).get('waitTill')
            print(f"   resumeToken: {resume_token}")
            # check last executed node or resultData
            last_node = (detail.get('data') or {}).get('resultData', {}).get('lastNodeExecuted')
            print(f"   lastNodeExecuted: {last_node}")
