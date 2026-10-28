import os
import requests
import json
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')
n8n_url = os.getenv('N8N_URL')
api_key = os.getenv('N8N_API_KEY')
headers = {'X-N8N-API-KEY': api_key}

r = requests.get(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E', headers=headers)
wf = r.json()

nodes = wf['nodes']

for n in nodes:
    if n['name'] == 'Стикер: GitHub Actions Результаты':
        n['position'] = [5050, 50]
        n['parameters']['height'] = 340
        n['parameters']['width'] = 1050
    elif n['name'] == 'Стикер: Qase Drift Monitor':
        n['position'] = [250, -350]
        n['parameters']['height'] = 280
        n['parameters']['width'] = 1050

wf_update = {
    'name': wf['name'],
    'nodes': nodes,
    'connections': wf['connections'],
    'settings': wf.get('settings', {})
}

up_r = requests.put(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E', json=wf_update, headers=headers)
print('Stickies update status:', up_r.status_code)

with open('qa-automation/n8n_current_workflow.json', 'w', encoding='utf-8') as f:
    json.dump(wf_update, f, indent=2, ensure_ascii=False)
print('Backup saved to qa-automation/n8n_current_workflow.json')
