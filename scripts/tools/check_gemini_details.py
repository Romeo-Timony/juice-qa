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

for n in wf['nodes']:
    if 'Gemini' in n['name'] or 'Judge' in n['name']:
        print(f"Name: {n['name']}")
        print(f"Type: {n['type']}")
        print(f"Position: {n.get('position')}")
        print(f"Parameters: {json.dumps(n.get('parameters'), ensure_ascii=False, indent=2)}")
        print("-" * 50)
