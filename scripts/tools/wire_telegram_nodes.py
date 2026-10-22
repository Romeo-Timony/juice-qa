import os
import sys
import json
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')

n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678')
key = os.getenv('N8N_API_KEY')
wf_id = 'Dv1WydaTMC1lxR0E'

r = requests.get(f'{n8n_url}/api/v1/workflows/{wf_id}', headers={'X-N8N-API-KEY': key})
wf = r.json()

nodes = wf['nodes']
connections = wf['connections']

# Find Telegram success node
tg_success = next((n for n in nodes if n['name'] == 'Telegram: Оповещение об успешном DoR'), None)
tg_failed = next((n for n in nodes if n['name'] == 'Telegram: Алерт об отклонении DoR'), None)

print("Found TG Success Node:", bool(tg_success))
print("Found TG Failed Node:", bool(tg_failed))

# Wire Gate 1 -> TG Success
gate1_name = "Jira: Карточка подтверждения тестов (Gate 1)"
connections[gate1_name] = {
    "main": [
        [
            {
                "node": "Telegram: Оповещение об успешном DoR",
                "type": "main",
                "index": 0
            }
        ]
    ]
}

# Wire DoR Rejection -> TG Failed
dor_reject_label = "Jira: Поставить метку Требует доработки"
connections[dor_reject_label] = {
    "main": [
        [
            {
                "node": "Telegram: Алерт об отклонении DoR",
                "type": "main",
                "index": 0
            }
        ]
    ]
}

payload = {
    "name": wf['name'],
    "nodes": nodes,
    "connections": connections,
    "settings": wf.get('settings', {})
}

put_r = requests.put(f'{n8n_url}/api/v1/workflows/{wf_id}', headers={'X-N8N-API-KEY': key, 'Content-Type': 'application/json'}, json=payload)
print(f"Workflow connections updated: {put_r.status_code}")
