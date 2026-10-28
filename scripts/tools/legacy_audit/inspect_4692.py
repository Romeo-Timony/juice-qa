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

r = requests.get(f'{n8n_url}/api/v1/executions/4692?includeData=true', headers=headers)
data = r.json()
print('Status:', data.get('status'))
res_data = data.get('data', {}).get('resultData', {})
last_node = res_data.get('lastNodeExecuted')
print('Last node executed:', last_node)

run_data = res_data.get('runData', {})
print(f'Total nodes executed: {len(run_data)}')
for i, k in enumerate(run_data.keys()):
    print(f'{i+1:02d}. Ran: {k}')
