import os, sys, requests, json
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')

n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678').rstrip('/')
n8n_key = os.getenv('N8N_API_KEY')
wf_id = os.getenv('N8N_WORKFLOW_ID', 'Dv1WydaTMC1lxR0E')

r = requests.get(f"{n8n_url}/api/v1/workflows/{wf_id}", headers={'X-N8N-API-KEY': n8n_key})
if r.ok:
    wf = r.json()
    connections = wf.get('connections', {})
    nodes = {n['name']: n for n in wf.get('nodes', [])}
    
    print("=== Connections from Gate 1 ===")
    for src, dst in connections.items():
        if 'Контроль 1' in src or 'Gate 1' in src or 'Карточка подтверждения' in src or 'Ожидание' in src or 'Wait' in src:
            print(f"{src} -> {dst}")
            
    print("\n=== Wait nodes in workflow ===")
    for name, node in nodes.items():
        if 'wait' in node.get('type', '').lower() or 'wait' in name.lower() or 'ожидание' in name.lower():
            print(f"Node: {name} ({node.get('type')})")
            print("  Params:", node.get('parameters'))
