import os
import requests
import json
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')
n8n_url = os.getenv('N8N_URL')
api_key = os.getenv('N8N_API_KEY')
headers = {'X-N8N-API-KEY': api_key}

r = requests.get(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E', headers=headers)
wf = r.json()

nodes = wf['nodes']
connections = wf['connections']

# Add Langfuse HTTP Request node
langfuse_http_node = next((n for n in nodes if n['name'] == 'Langfuse: Фиксация трейса и метрик'), None)
if not langfuse_http_node:
    langfuse_http_node = {
        "parameters": {
            "method": "POST",
            "url": "https://cloud.langfuse.com/api/public/ingestion",
            "authentication": "predefinedCredentialType",
            "nodeCredentialType": "httpBasicAuth",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({\n  batch: [{\n    id: 'trace-' + $('Фильтр: Задача взята в работу').item.json.issueKey + '-' + Date.now(),\n    type: 'trace-create',\n    timestamp: new Date().toISOString(),\n    body: {\n      name: 'QAOps DoR & Design Gate',\n      userId: $('Фильтр: Задача взята в работу').item.json.actor || 'qa-engineer',\n      metadata: {\n        issueKey: $('Фильтр: Задача взята в работу').item.json.issueKey,\n        model: 'gemini-1.5-flash',\n        workflow: 'Dv1WydaTMC1lxR0E',\n        harness: 'n8n'\n      },\n      tags: ['n8n', 'gemini-1.5-flash', 'qaops']\n    }\n  }]\n}) }}",
            "options": {}
        },
        "credentials": {
            "httpBasicAuth": {
                "id": "wwajdqJ0aPX5fVrv",
                "name": "Langfuse Cloud Basic Auth"
            }
        },
        "id": "langfuse-http-trace-node",
        "name": "Langfuse: Фиксация трейса и метрик",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [1808, 480],
        "notes": "🔭 Отправляет телеметрию и трейс судейства в Langfuse Cloud (проект cmv9jxup10181ad0eby8arexx) через официальный Ingestion API."
    }
    nodes.append(langfuse_http_node)
    print("Added Langfuse HTTP Request node!")

# Wire: Jira Report 1 -> Langfuse Trace
connections['Jira: Отчет 1 — Задача готова к работе (DoR Gate)'] = {
    'main': [
        [
            {'node': 'Подготовка данных для чек-листа', 'type': 'main', 'index': 0},
            {'node': 'Langfuse: Фиксация трейса и метрик', 'type': 'main', 'index': 0}
        ]
    ]
}

# Update workflow in n8n
wf_update = {
    'name': wf['name'],
    'nodes': nodes,
    'connections': connections,
    'settings': wf.get('settings', {})
}

up_r = requests.put(f'{n8n_url}/api/v1/workflows/Dv1WydaTMC1lxR0E', json=wf_update, headers=headers)
print('Workflow update status:', up_r.status_code)
if up_r.status_code == 200:
    print('Workflow successfully updated with Langfuse node and Gemini 1.5-flash!')
else:
    print('Error:', up_r.text[:500])
