import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('n8n_live_workflow.json', encoding='utf-8') as f:
    wf = json.load(f)

for n in wf['nodes']:
    if n.get('id') == 'gh-dispatch-workflow':
        print("GH DISPATCH NODE:")
        print(json.dumps(n, indent=2, ensure_ascii=False))
