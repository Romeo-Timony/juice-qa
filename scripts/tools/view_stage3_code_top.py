import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('n8n_live_workflow.json', encoding='utf-8') as f:
    wf = json.load(f)

for n in wf['nodes']:
    if n.get('id') == '8672714e-feb5-4242-b9c5-efb63bbbfe20':
        code = n.get('parameters', {}).get('jsCode', '')
        print("TOTAL CODE LENGTH:", len(code))
        lines = code.splitlines()
        for idx, line in enumerate(lines[:120]):
            print(f"{idx+1}: {line}")
