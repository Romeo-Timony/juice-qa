import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678')
n8n_key = os.getenv('N8N_API_KEY')
headers = {'X-N8N-API-KEY': n8n_key}

with open('n8n_live_workflow.json', encoding='utf-8') as f:
    wf = json.load(f)

for n in wf['nodes']:
    if n.get('name') == 'Telegram: Отчет Allure из CI/CD':
        old_text = n['parameters']['text']
        bad_token = "{{ $json.issueKey || $('Фильтр: Задача взята в работу').item.json.issueKey || 'JS-39' }}"
        good_token = "{{ $json.issueKey || 'JS-41' }}"
        new_text = old_text.replace(bad_token, good_token)
        n['parameters']['text'] = new_text
        print('Updated Telegram node text!')

with open('n8n_live_workflow.json', 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

payload = {
    'name': wf['name'],
    'nodes': wf['nodes'],
    'connections': wf['connections'],
    'settings': wf.get('settings', {}),
    'staticData': wf.get('staticData')
}
res = requests.put(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E', headers=headers, json=payload)
print('PUT status:', res.status_code)
act_res = requests.post(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E/activate', headers=headers)
print('Activate status:', act_res.status_code)
