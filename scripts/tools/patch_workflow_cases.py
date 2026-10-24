import json
import requests
import os
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('.env')

N8N_URL = os.getenv('N8N_URL', 'http://201.34.147.33:5678').rstrip('/')
N8N_KEY = os.getenv('N8N_API_KEY')
WORKFLOW_ID = 'Dv1WydaTMC1lxR0E'

with open('n8n_live_workflow.json', 'r', encoding='utf-8') as f:
    wf = json.load(f)

for node in wf.get('nodes', []):
    if node['name'] == 'Создание тест-кейсов без повторов':
        code = node['parameters']['jsCode']
        
        # 1. Fix cases selection
        old_part = "if (kind === 'backend') cases = defaultBackendCases"
        new_part = "if (kind === 'backend') cases = defaultBackendCases\nelse if (kind === 'e2e') cases = defaultE2ECases"
        if new_part not in code:
            code = code.replace(old_part, new_part, 1)
            print("✅ Updated cases selection to include e2e")

        # 2. Fix kindTitle in lines
        old_kt = "if (kind === 'backend') kindTitle = 'Backend'"
        new_kt = "if (kind === 'backend') kindTitle = 'Backend'\nelse if (kind === 'e2e') kindTitle = 'E2E Onboarding'"
        if new_kt not in code:
            code = code.replace(old_kt, new_kt, 1)
            print("✅ Updated kindTitle in Stage 3 header")

        # 3. Fix kindTitle in rtm
        old_kt2 = "if (isBackend) kindTitle = 'Backend'"
        new_kt2 = "if (isBackend) kindTitle = 'Backend'\n  else if (kind === 'e2e') kindTitle = 'E2E Onboarding'"
        if new_kt2 not in code:
            code = code.replace(old_kt2, new_kt2, 1)
            print("✅ Updated kindTitle in Stage 4 header")

        node['parameters']['jsCode'] = code

with open('n8n_live_workflow.json', 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

# Push to n8n
payload = {
    'name': wf.get('name', 'Juice Shop'),
    'nodes': wf.get('nodes', []),
    'connections': wf.get('connections', {}),
    'settings': wf.get('settings', {})
}
headers = {'X-N8N-API-KEY': N8N_KEY, 'Content-Type': 'application/json'}
r = requests.put(f'{N8N_URL}/api/v1/workflows/{WORKFLOW_ID}', headers=headers, json=payload, timeout=30)
print('PUT workflow:', r.status_code)
r_act = requests.post(f'{N8N_URL}/api/v1/workflows/{WORKFLOW_ID}/activate', headers=headers, timeout=15)
print('Activated workflow:', r_act.status_code)
