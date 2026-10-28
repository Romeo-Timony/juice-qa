import os
import sys
import json
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')

n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678').rstrip('/')
n8n_key = os.getenv('N8N_API_KEY')
wf_id = os.getenv('N8N_WORKFLOW_ID', 'Dv1WydaTMC1lxR0E')

r = requests.get(f"{n8n_url}/api/v1/workflows/{wf_id}", headers={'X-N8N-API-KEY': n8n_key})
wf = r.json()

# 1. Update Node 15: "Подготовка задачи к проверке"
for n in wf['nodes']:
    if n.get('name') == 'Подготовка задачи к проверке':
        code = n['parameters']['jsCode']
        # Replace classify()
        old_classify = "function classify () {"
        new_classify = """function classify () {
  if (/^\s*\[\s*(api|back|backend)/i.test(summary)) return 'backend'
  if (/^\s*\[\s*(ui|front|frontend)/i.test(summary)) return 'frontend'
  if (/^\s*\[\s*(e2e|end-to-end|journey)/i.test(summary)) return 'e2e'"""
        if old_classify in code and 'api|back|backend' not in code:
            n['parameters']['jsCode'] = code.replace(old_classify, new_classify)
            print("Node 15 classify() updated!")

    elif n.get('name') == 'Создание тест-кейсов без повторов':
        code = n['parameters']['jsCode']
        # Update suite logic: rootTitle by layer, no task sub-suite!
        # Search for rootTitle
        old_part = "const rootTitle = isBackend ? 'Backend' : 'Frontend'"
        new_part = """let rootTitle = 'API'
if (/^\s*\[\s*(ui|front|frontend)/i.test(issueSummary) || kind === 'frontend') {
  rootTitle = 'UI'
} else if (/^\s*\[\s*(e2e|end-to-end|journey)/i.test(issueSummary) || kind === 'e2e') {
  rootTitle = 'E2E'
} else {
  rootTitle = 'API'
}"""
        if old_part in code:
            code = code.replace(old_part, new_part)
            # Make targetSuiteId be rootSuiteId directly
            code = code.replace("const targetSuiteId = childSuite ? childSuite.id : (rootSuiteId || null)", "const targetSuiteId = rootSuiteId || null")
            n['parameters']['jsCode'] = code
            print("Node 30 suite logic updated!")

# PUT updated workflow
update_payload = {
    "name": wf["name"],
    "nodes": wf["nodes"],
    "connections": wf["connections"],
    "settings": wf.get("settings", {})
}

put_r = requests.put(f"{n8n_url}/api/v1/workflows/{wf_id}", headers={'X-N8N-API-KEY': n8n_key}, json=update_payload)
print(f"Workflow update status: {put_r.status_code}")
if not put_r.ok:
    print(put_r.text)
else:
    print("Workflow successfully updated in n8n!")
