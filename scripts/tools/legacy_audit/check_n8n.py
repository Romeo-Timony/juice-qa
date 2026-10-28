import os, requests
from dotenv import load_dotenv

load_dotenv('.env')
load_dotenv('qa-automation/.env')
n8n_url = os.getenv('N8N_URL')
api_key = os.getenv('N8N_API_KEY')

print(f"Checking n8n at {n8n_url}...")
try:
    headers = {"X-N8N-API-KEY": api_key}
    r = requests.get(f"{n8n_url}/api/v1/workflows", headers=headers, timeout=5)
    print("n8n status code:", r.status_code)
    if r.status_code == 200:
        workflows = r.json().get('data', [])
        print(f"Total workflows in n8n: {len(workflows)}")
        for wf in workflows:
            print(f" - ID: {wf.get('id')}, Name: {wf.get('name')}, Active: {wf.get('active')}")
except Exception as e:
    print("Error connecting to n8n:", e)
