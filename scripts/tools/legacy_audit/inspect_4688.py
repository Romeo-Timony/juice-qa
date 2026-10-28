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

r = requests.get(f'{n8n_url}/api/v1/executions/4688?includeData=true', headers=headers)
data = r.json()
print('Status:', data.get('status'))
res_data = data.get('data', {}).get('resultData', {})
error = res_data.get('error', {})
print('Last node executed:', res_data.get('lastNodeExecuted'))
print('Error message:', error.get('message'))
print('Error details:', json.dumps(error, indent=2, ensure_ascii=False))

run_data = res_data.get('runData', {})
for k in run_data:
    print('Ran node:', k)
