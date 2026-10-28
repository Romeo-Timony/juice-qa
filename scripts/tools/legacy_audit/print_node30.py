import os
import sys
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')

n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678').rstrip('/')
n8n_key = os.getenv('N8N_API_KEY')
wf_id = os.getenv('N8N_WORKFLOW_ID', 'Dv1WydaTMC1lxR0E')

r = requests.get(f"{n8n_url}/api/v1/workflows/{wf_id}", headers={'X-N8N-API-KEY': n8n_key})
node30 = r.json().get('nodes', [])[30]
print(node30.get('parameters', {}).get('jsCode'))
