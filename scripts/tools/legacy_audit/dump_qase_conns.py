import os, json, requests
from dotenv import load_dotenv

load_dotenv('d:/Desktop/Juice_shop/qa-automation/.env')
n8n_url = os.getenv('N8N_URL')
api_key = os.getenv('N8N_API_KEY')
wf_id = os.getenv('N8N_WORKFLOW_ID')
headers = {'X-N8N-API-KEY': api_key}

r = requests.get(f'{n8n_url}/api/v1/workflows/{wf_id}', headers=headers)
wf = r.json()

conns = wf.get('connections', {})
with open('d:/Desktop/Juice_shop/qa-automation/scripts/qase_conns.txt', 'w', encoding='utf-8') as f:
    for src, targets in conns.items():
        if any(k in src.lower() for k in ['qase', 'drift', 'дрифт', 'ссылку', 'контроль 1', 'gate 1']):
            f.write(f"{src} -> {json.dumps(targets, ensure_ascii=False)}\n")
print("Saved qase_conns.txt")
