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

res = requests.get(f"{n8n_url}/api/v1/executions?limit=30", headers=headers)
for ex in res.json().get('data', []):
    eid = ex.get('id')
    detail_res = requests.get(f"{n8n_url}/api/v1/executions/{eid}?includeData=true", headers=headers)
    if not detail_res.ok:
        continue
    detail = detail_res.json()
    run_data = (detail.get('data') or {}).get('resultData', {}).get('runData', {})
    if 'GitHub: Запуск автотестов в CI/CD' in run_data:
        gh_data = run_data['GitHub: Запуск автотестов в CI/CD']
        print(f"Exec {eid} ran GitHub node: status={detail.get('status')}")
        print("Data:", json.dumps(gh_data, indent=2, ensure_ascii=False))
        break
