import os
import sys
import json
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')

n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678').rstrip('/')
n8n_key = os.getenv('N8N_API_KEY')
wf_id = os.getenv('N8N_WORKFLOW_ID', 'Dv1WydaTMC1lxR0E')

r = requests.get(f"{n8n_url}/api/v1/workflows/{wf_id}", headers={'X-N8N-API-KEY': n8n_key})
nodes = r.json().get('nodes', [])
for idx in [11, 14, 15, 16, 28, 29]:
    n = nodes[idx]
    print(f"\n=== Node {idx}: {n.get('name')} ===")
    code = n.get('parameters', {}).get('jsCode')
    if code:
        print(code[:400])
    else:
        print(json.dumps(n.get('parameters'), indent=2, ensure_ascii=False)[:300])
