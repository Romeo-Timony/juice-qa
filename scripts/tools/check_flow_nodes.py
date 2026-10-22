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

print(f"Total nodes in Dv1WydaTMC1lxR0E: {len(wf['nodes'])}")
for i, n in enumerate(wf['nodes']):
    name = n['name']
    ntype = n['type']
    pos = n.get('position', [0, 0])
    print(f"{i:02d}. [{name}] ({ntype}) at {pos}")
