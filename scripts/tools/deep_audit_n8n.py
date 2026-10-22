import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

with open('n8n_current_workflow.json', 'r', encoding='utf-8') as f:
    wf = json.load(f)

nodes = wf['nodes']
connections = wf['connections']

print(f"Total Nodes: {len(nodes)}")
print("="*80)

code_nodes = [n for n in nodes if n['type'] == 'n8n-nodes-base.code']
print(f"Total Code (JavaScript) Nodes: {len(code_nodes)}")

for n in code_nodes:
    name = n['name']
    js = n.get('parameters', {}).get('jsCode', '')
    lines = js.split('\n')
    print(f"\n[JS Node] '{name}' | Total lines: {len(lines)}")
    preview = "\n  ".join(lines[:8])
    print(f"  {preview}")

print("\n" + "="*80)
print("HTTP REQUEST NODES:")
http_nodes = [n for n in nodes if n['type'] == 'n8n-nodes-base.httpRequest']
for n in http_nodes:
    url = n.get('parameters', {}).get('url', '')
    method = n.get('parameters', {}).get('requestMethod') or n.get('parameters', {}).get('method', 'GET')
    auth = n.get('parameters', {}).get('authentication', 'none')
    print(f"  - [{method}] '{n['name']}' -> URL: {url[:70]}... | Auth: {auth}")

print("\n" + "="*80)
print("IF / CONDITION NODES:")
if_nodes = [n for n in nodes if n['type'] == 'n8n-nodes-base.if']
for n in if_nodes:
    print(f"  - '{n['name']}'")
