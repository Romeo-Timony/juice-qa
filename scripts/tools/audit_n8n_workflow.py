import os
import sys
import json
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')

n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678')
key = os.getenv('N8N_API_KEY')

r = requests.get(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E', headers={'X-N8N-API-KEY': key})
wf = r.json()

print(f"=== Workflow: {wf.get('name')} ===")
print(f"Total Nodes: {len(wf.get('nodes', []))}")

nodes = wf.get('nodes', [])
for i, n in enumerate(nodes):
    ntype = n.get('type')
    name = n.get('name')
    notes = n.get('notes', '')
    notesInEditor = n.get('notesInEditor', False)
    pos = n.get('position', [0, 0])
    print(f"{i+1:02d}. [{ntype}] \"{name}\" (pos: {pos}) | notesInEditor={notesInEditor} | notes: '{notes[:50]}'")

# Save full workflow to a local json for easy inspection
with open('n8n_current_workflow.json', 'w', encoding='utf-8') as f:
    json.dump(wf, f, ensure_ascii=False, indent=2)

print("\nSaved full workflow to qa-automation/n8n_current_workflow.json")
