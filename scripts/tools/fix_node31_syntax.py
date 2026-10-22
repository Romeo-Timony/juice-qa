import os
import sys
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')

n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678')
key = os.getenv('N8N_API_KEY')

r = requests.get(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E', headers={'X-N8N-API-KEY': key})
wf = r.json()

target_node = None
for n in wf['nodes']:
    if n['name'] == 'Создание тест-кейсов без повторов':
        target_node = n
        break

js = target_node['parameters']['jsCode']

# Replace broken lines
old_line_1 = "url: https://api.qase.io/v1/,"
new_line_1 = "url: 'https://api.qase.io/v1/' + endpoint,"

old_line_2 = "const r = await qasePost(suite/, { title: rootTitle })"
new_line_2 = "const r = await qasePost('suite/' + qaseCode, { title: rootTitle })"

if old_line_1 in js and old_line_2 in js:
    js = js.replace(old_line_1, new_line_1)
    js = js.replace(old_line_2, new_line_2)
    target_node['parameters']['jsCode'] = js

    payload = {
        'name': wf['name'],
        'nodes': wf['nodes'],
        'connections': wf['connections'],
        'settings': wf.get('settings', {})
    }
    put_r = requests.put(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E', headers={'X-N8N-API-KEY': key, 'Content-Type': 'application/json'}, json=payload)
    print(f"Successfully fixed syntax in node 31! Status: {put_r.status_code}")
else:
    print("Could not find exact broken lines. Showing lines 30-70:")
    lines = js.split('\n')
    for i, l in enumerate(lines[30:70]):
        print(f"{i+31}: {l}")
