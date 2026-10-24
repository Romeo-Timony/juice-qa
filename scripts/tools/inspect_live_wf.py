import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('d:/Desktop/Juice_shop/qa-automation/n8n_live_workflow.json', encoding='utf-8') as f:
    wf = json.load(f)

nodes = wf.get('nodes', [])
conns = wf.get('connections', {})

print("=== WORKFLOW NODES ===")
for i, n in enumerate(nodes):
    params = n.get("parameters", {})
    sub = ""
    if "path" in params:
        sub = f"path='{params['path']}'"
    elif "url" in params:
        sub = f"url='{params['url']}'"
    print(f"{i+1:02d}. [{n.get('type')}] \"{n.get('name')}\" {sub}")

print("\n=== WEBHOOKS & TRIGGERS ===")
for n in nodes:
    t = n.get('type', '').lower()
    if 'trigger' in t or 'webhook' in t:
        print(f"Trigger: {n.get('name')} ({n.get('type')}) -> parameters: {n.get('parameters')}")

print("\n=== FLOW CONNECTIONS ===")
for src, targets in conns.items():
    for out_type, out_list in targets.items():
        for branch in out_list:
            for dest in branch:
                node_dest = dest.get('node')
                if any(k in src or k in node_dest for k in ['Gate', 'Контроль', 'Wait', 'Ожидание', 'GitHub', 'Allure', 'Внедрение']):
                    print(f"  {src}  ===>  {node_dest}")
