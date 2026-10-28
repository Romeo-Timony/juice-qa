import os, requests
from dotenv import load_dotenv

load_dotenv('qa-automation/.env')
n8n_url = os.getenv('N8N_URL')
api_key = os.getenv('N8N_API_KEY')
wf_id = os.getenv('N8N_WORKFLOW_ID', 'Dv1WydaTMC1lxR0E')

headers = {"X-N8N-API-KEY": api_key}
r = requests.get(f"{n8n_url}/api/v1/workflows/{wf_id}", headers=headers)
if r.status_code == 200:
    wf = r.json()
    print("Workflow Name:", wf.get('name'))
    nodes = wf.get('nodes', [])
    print(f"Total nodes: {len(nodes)}")
    for node in nodes:
        node_type = node.get('type')
        if 'webhook' in node_type.lower() or 'trigger' in node_type.lower():
            print(f"Trigger Node: {node.get('name')} ({node_type})")
            print("  Params:", node.get('parameters'))
            print("  WebhookId:", node.get('webhookId'))
else:
    print("Error:", r.status_code, r.text)
