import os, json, requests
from dotenv import load_dotenv

load_dotenv('d:/Desktop/Juice_shop/qa-automation/.env')
n8n_url = os.getenv('N8N_URL')
api_key = os.getenv('N8N_API_KEY')
wf_id = os.getenv('N8N_WORKFLOW_ID')
headers = {'X-N8N-API-KEY': api_key}

r = requests.get(f'{n8n_url}/api/v1/workflows/{wf_id}', headers=headers)
wf = r.json()

nodes = {n['name']: n for n in wf['nodes']}
conns = wf.get('connections', {})

print("Current nodes in workflow:")
for name in nodes.keys():
    if any(k in name for k in ['Gate 2', 'Qase', 'дрифт', 'Drift', 'Внедрение', 'Контроль 1']):
        print(" -", name)

# Let's see how Gate 2 is connected
for src, targets in conns.items():
    if any(k in src for k in ['Gate 2', 'Внедрение']):
        print(f"Conn: {src} -> {targets}")
