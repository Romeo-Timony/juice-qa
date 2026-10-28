import json
import sys

with open('n8n_live_workflow.json', encoding='utf-8') as f:
    wf = json.load(f)

print("=== NODES IN WORKFLOW ===")
for n in wf['nodes']:
    nid = n.get('id')
    name = n.get('name')
    ntype = n.get('type')
    if any(w in (nid + ' ' + name).lower() for w in ['gate', 'wait', 'код', 'карточка', 'этап', 'github', 'allure']):
        print(f"[{nid}] ({ntype}) -> {name}")

print("\n=== CONNECTIONS ===")
for src, targets in wf['connections'].items():
    for output_type, conn_list in targets.items():
        for conn_group in conn_list:
            for c in conn_group:
                print(f"  {src} ---> {c.get('node')}")
