import os
import requests
import json
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

n8n_url = os.getenv("N8N_URL", "http://201.34.147.33:5678")
n8n_key = os.getenv("N8N_API_KEY")

headers = {"X-N8N-API-KEY": n8n_key}

res = requests.get(f"{n8n_url}/api/v1/executions/4715?includeData=true", headers=headers)
data = res.json()
print("Top keys:", list(data.keys()))
print("Data keys:", list((data.get('data') or {}).keys()))
print("resumeToken:", (data.get('data') or {}).get('resumeToken'))
wait_node_data = (data.get('data') or {}).get('resultData', {}).get('runData', {}).get('Ожидание согласования тест-дизайна (Gate 1 Wait)')
print("Wait node runData:", json.dumps(wait_node_data, indent=2, ensure_ascii=False) if wait_node_data else "None")
