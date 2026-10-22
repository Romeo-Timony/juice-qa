import json, sys

with open('d:/Desktop/Juice_shop/qa-automation/n8n_current_workflow_dump.json', encoding='utf-8') as f:
    wf = json.load(f)

out_file = open('d:/Desktop/Juice_shop/qa-automation/scripts/inspect_wf_report.txt', 'w', encoding='utf-8')
def p(*args, **kwargs):
    print(*args, **kwargs, file=out_file)

p('=== TELEGRAM NODES ===')
for n in wf['nodes']:
    if 'telegram' in n['type'].lower() or 'Telegram' in n['name']:
        p('Node:', n['name'])
        params = n.get('parameters', {})
        text = params.get('text', '')
        p('  Text:\n', text)
        add = params.get('additionalFields', {})
        p('  Parse mode:', add.get('parse_mode') if add else None)
        p('  Reply markup:', params.get('replyMarkup'))
        p('='*40)

p('\n=== ALL JIRA NODES ===')
for n in wf['nodes']:
    if 'Jira' in n['name'] or 'jira' in n['type'].lower():
        p('Node:', n['name'])
        params = n.get('parameters', {})
        body = params.get('body') or params.get('jsonBody') or params.get('bodyParametersUi')
        p('  Body snippet:', str(body)[:200])

p('\n=== GATES AND WAIT NODES ===')
for n in wf['nodes']:
    if 'gate' in n['name'].lower() or 'wait' in n['type'].lower():
        p('Node:', n['name'], 'type:', n['type'])
        p('  Params:', str(n.get('parameters', {}))[:200])

p('\n=== CONNECTIONS AROUND GATE 2 ===')
conns = wf.get('connections', {})
for src, targets in conns.items():
    if 'Gate 2' in src or 'Внедрение' in src or 'Scaffold' in src or 'pytest' in src:
        p(f'{src} -> {targets}')

out_file.close()
