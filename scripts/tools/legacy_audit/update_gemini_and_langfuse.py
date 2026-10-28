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

# 1. Update Gemini Model to gemini-1.5-flash in both judge model nodes
for n in nodes:
    if 'Gemini Model' in n['name']:
        n['parameters']['modelName'] = 'models/gemini-1.5-flash'
        print(f"Updated {n['name']} modelName to models/gemini-1.5-flash")

# 2. Add Langfuse node
langfuse_public = os.getenv('LANGFUSE_PUBLIC_KEY', 'pk-lf-c3705de5-0196-465a-841a-e6f11de57c58')
langfuse_secret = os.getenv('LANGFUSE_SECRET_KEY', 'sk-lf-4ce48db5-2ce6-4058-b0ff-1e190c35f601')
langfuse_host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')

langfuse_node = next((n for n in nodes if n['name'] == 'Langfuse: Observability & Tracing'), None)
if not langfuse_node:
    langfuse_node = {
        "parameters": {
            "publicKey": langfuse_public,
            "secretKey": langfuse_secret,
            "baseUrl": langfuse_host
        },
        "id": "langfuse-tracer-node",
        "name": "Langfuse: Observability & Tracing",
        "type": "@n8n/n8n-nodes-langchain.langfuse",
        "typeVersion": 1,
        "position": [1344, 620],
        "notes": "🔭 Langfuse Cloud Observability: сбор трейсов, расчет стоимости токенов, задержек и вердиктов LLM-as-a-Judge в проект cmv9jxup10181ad0eby8arexx."
    }
    nodes.append(langfuse_node)
    print("Added Langfuse node!")
else:
    langfuse_node['parameters'] = {
        "publicKey": langfuse_public,
        "secretKey": langfuse_secret,
        "baseUrl": langfuse_host
    }
    print("Updated Langfuse node parameters!")

# Connect Langfuse via ai_tracer to DoR Judge & Design Gate Judge
connections['Langfuse: Observability & Tracing'] = {
    'ai_tracer': [
        [
            {'node': 'LLM Judge: Оценка готовности (DoR Gate)', 'type': 'ai_tracer', 'index': 0},
            {'node': 'LLM Judge: Аудит тест-дизайна (Design Gate)', 'type': 'ai_tracer', 'index': 0}
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
    print('Successfully updated Gemini model to gemini-1.5-flash and connected Langfuse tracer!')
else:
    print('Error updating workflow:', up_r.text[:500])
