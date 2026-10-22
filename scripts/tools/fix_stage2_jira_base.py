import os
import requests
from dotenv import load_dotenv

load_dotenv('d:/Desktop/Juice_shop/qa-automation/.env')

n8n_url = os.getenv('N8N_URL')
api_key = os.getenv('N8N_API_KEY')
wf_id = os.getenv('N8N_WORKFLOW_ID')
headers = {'X-N8N-API-KEY': api_key}

r = requests.get(f'{n8n_url}/api/v1/workflows/{wf_id}', headers=headers)
wf = r.json()

target_node = next((n for n in wf['nodes'] if n['name'] == 'Создание карты проверок'), None)
if not target_node:
    print('Node not found!')
    exit(1)

code = target_node['parameters']['jsCode']
old_str = "const commentUrl = `${ctx.config.jiraBase}/rest/api/2/issue/${issueKey}/comment`;"

new_str = """const jiraBase = 'https://romeo-timony.atlassian.net';
const existingComments = ($('Jira: Загрузить данные задачи').first().json.fields?.comment?.comments) || [];
const stage2 = existingComments.find(c => c.body && c.body.includes('[Этап 2 из'));
const commentMethod = stage2 ? 'PUT' : 'POST';
const commentUrl = stage2
  ? `${jiraBase}/rest/api/2/issue/${issueKey}/comment/${stage2.id}`
  : `${jiraBase}/rest/api/2/issue/${issueKey}/comment`;"""

if old_str in code:
    code = code.replace(old_str, new_str)
    code = code.replace("commentMethod: 'POST',", "commentMethod,")
    target_node['parameters']['jsCode'] = code
    print("Replaced old_str with new_str successfully!")
else:
    print("old_str not found! Let's check code contents.")
    print(code[-300:])
    exit(1)

payload = {
    'name': wf['name'],
    'nodes': wf['nodes'],
    'connections': wf['connections'],
    'settings': wf.get('settings', {}),
    'staticData': wf.get('staticData', None)
}

res = requests.put(f'{n8n_url}/api/v1/workflows/{wf_id}', json=payload, headers=headers)
print("PUT status:", res.status_code)
if res.status_code == 200:
    print("Workflow updated successfully in n8n!")
else:
    print("Error updating workflow:", res.text)
