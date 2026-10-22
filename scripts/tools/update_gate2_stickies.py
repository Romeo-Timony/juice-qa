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

# Add or update Sticky for Gate 2 & Stage 7
gate2_sticky = next((n for n in nodes if n['name'] == 'Стикер: Gate 2 и Внедрение'), None)
if not gate2_sticky:
    gate2_sticky = {
        "parameters": {
            "content": "## 🛡️ 7. Контроль 2 (Gate 2 Review) & Внедрение [Этапы 6 и 7]\n\n**Что здесь происходит:**\nПубликация карточки проверки качества кода автотестов (Gate 2) в Jira, оповещение QA Lead в Telegram, подтверждение и выпуск Отчета №7 о внедрении автотестов в боевой репозиторий.",
            "height": 340,
            "width": 950,
            "color": 2
        },
        "id": "sticky-gate2-and-stage7",
        "name": "Стикер: Gate 2 и Внедрение",
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [4350, 50]
    }
    nodes.append(gate2_sticky)

# Update Stage 8 Sticky position
for n in nodes:
    if n['name'] == 'Стикер: GitHub Actions Результаты':
        n['position'] = [5650, 50]
        n['parameters']['width'] = 950
        n['parameters']['height'] = 340
    elif n['name'] == 'Стикер: GitHub Actions Trigger':
        n['position'] = [5250, 50]
        n['parameters']['width'] = 380
        n['parameters']['height'] = 340

wf_update = {
    'name': wf['name'],
    'nodes': nodes,
    'connections': wf['connections'],
    'settings': wf.get('settings', {})
}

up_r = requests.put(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E', json=wf_update, headers=headers)
print('Sticky update status:', up_r.status_code)

with open('qa-automation/n8n_current_workflow.json', 'w', encoding='utf-8') as f:
    json.dump(wf_update, f, indent=2, ensure_ascii=False)
print('Backup saved.')
