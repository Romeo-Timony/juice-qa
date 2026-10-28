import os, sys, requests, json
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')

n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678').rstrip('/')
n8n_key = os.getenv('N8N_API_KEY')

r = requests.get(f"{n8n_url}/api/v1/executions/4658?includeData=true", headers={'X-N8N-API-KEY': n8n_key})
if r.ok:
    data = r.json().get('data', {})
    print("Execution 4658 status:", data.get('status'))
    result_data = data.get('resultData', {}).get('runData', {})
    print("Executed nodes:", list(result_data.keys()))
    for node_name, runs in result_data.items():
        for run in runs:
            err = run.get('error')
            if err:
                print(f"ERROR in node '{node_name}':", err)
