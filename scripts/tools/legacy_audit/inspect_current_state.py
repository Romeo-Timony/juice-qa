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

print(f"Total nodes: {len(wf['nodes'])}")
for i, n in enumerate(wf['nodes']):
    name = n['name']
    ntype = n['type']
    params = n.get('parameters', {})
    if any(k in name for k in ['Gemini', 'Judge', 'Qase', 'Allure', 'Webhook', 'Wait', 'GitHub']):
        print(f"{i:02d}. [{name}] ({ntype}) params={params}")

print("\n--- CONNECTIONS ---")
for src, targets in wf.get('connections', {}).items():
    print(f"{src} -> {targets}")
