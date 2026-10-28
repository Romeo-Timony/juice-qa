import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('n8n_live_workflow.json', encoding='utf-8') as f:
    wf = json.load(f)

for n in wf['nodes']:
    if n.get('id') == '8672714e-feb5-4242-b9c5-efb63bbbfe20':
        code = n.get('parameters', {}).get('jsCode', '')
        lines = code.splitlines()
        case_titles = []
        for l in lines:
            if 'title:' in l and ('[Frontend]' in l or '[API]' in l):
                case_titles.append(l.strip())
        print(f"Total case titles in node: {len(case_titles)}")
        for ct in case_titles:
            print("  ", ct)
