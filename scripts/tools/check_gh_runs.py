import os
import requests
import json
import sys

token = os.getenv('GITHUB_TOKEN', '')
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github.v3+json'
}

r = requests.get('https://api.github.com/repos/Romeo-Timony/juice-qa/actions/runs?per_page=5', headers=headers)
print('Runs status:', r.status_code)
if r.status_code == 200:
    runs = r.json().get('workflow_runs', [])
    for run in runs:
        print(f"Run #{run['id']}: name={run['name']}, event={run['event']}, status={run['status']}, conclusion={run['conclusion']}, branch={run['head_branch']}")
