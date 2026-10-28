import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('n8n_live_workflow.json', encoding='utf-8') as f:
    wf = json.load(f)

nodes_to_inspect = [
    'jira-gate2-card-node',
    'tg-gate2-request-node',
    'wait-gate2-code-approval',
    'f9c6c4de-640b-4909-a3a1-38e929a76d80', # gate1 card
    'wait-gate1-design-approval',
    'gh-dispatch-workflow'
]

for n in wf['nodes']:
    if n.get('id') in nodes_to_inspect or any(k in n.get('name', '').lower() for k in ['gate 2', 'отчет 7', 'запуск автотестов']):
        print(f"\n====================\nNODE: {n.get('id')} | {n.get('name')} | {n.get('type')}")
        print("PARAMETERS:")
        print(json.dumps(n.get('parameters', {}), indent=2, ensure_ascii=False))
