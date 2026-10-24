import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('n8n_live_workflow.json', encoding='utf-8') as f:
    wf = json.load(f)

for n in wf['nodes']:
    if n.get('id') == '8672714e-feb5-4242-b9c5-efb63bbbfe20' or 'тест-кейсов без повторов' in n.get('name', '').lower():
        print("NODE:", n.get('id'), n.get('name'))
        print(n.get('parameters', {}).get('jsCode'))
