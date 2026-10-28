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

def find_execution_for_issue(issue_key: str):
    res = requests.get(f"{n8n_url}/api/v1/executions?limit=20", headers=headers)
    if not res.ok:
        print("Failed to fetch executions:", res.text)
        return None
    for ex in res.json().get('data', []):
        eid = ex.get('id')
        detail_res = requests.get(f"{n8n_url}/api/v1/executions/{eid}?includeData=true", headers=headers)
        if not detail_res.ok:
            continue
        detail = detail_res.json()
        run_data = (detail.get('data') or {}).get('resultData', {}).get('runData', {})
        # Check 'Фильтр: Задача взята в работу'
        filter_node = run_data.get('Фильтр: Задача взята в работу')
        if filter_node:
            main_out = filter_node[0].get('data', {}).get('main', [[]])
            if main_out and main_out[0]:
                first_item = main_out[0][0].get('json', {})
                key = first_item.get('issueKey')
                if key == issue_key:
                    print(f"Found execution {eid} for {issue_key}: status={detail.get('status')}, waitTill={detail.get('waitTill')}")
                    resume_token = (detail.get('data') or {}).get('resumeToken')
                    print(f"   resumeToken: {resume_token}")
                    return eid, detail.get('status'), resume_token
    return None

find_execution_for_issue("JS-41")
