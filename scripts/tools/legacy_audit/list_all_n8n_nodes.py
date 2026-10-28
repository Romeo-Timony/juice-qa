import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('n8n_live_workflow.json', encoding='utf-8') as f:
    wf = json.load(f)

print(f"Total nodes: {len(wf['nodes'])}")
for idx, n in enumerate(wf['nodes']):
    print(f"[{idx+1}] {n.get('id')} | {n.get('name')} ({n.get('type')})")
