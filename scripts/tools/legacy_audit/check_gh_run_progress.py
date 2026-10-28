import requests
import os
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('.env')

GH_TOKEN = os.getenv('GITHUB_TOKEN')
headers = {'Accept': 'application/vnd.github.v3+json'}
if GH_TOKEN:
    headers['Authorization'] = f'token {GH_TOKEN}'

r = requests.get('https://api.github.com/repos/Romeo-Timony/juice-qa/actions/runs?per_page=3', headers=headers)
if r.ok:
    for run in r.json().get('workflow_runs', []):
        rid = run.get('id')
        branch = run.get('head_branch')
        status = run.get('status')
        conclusion = run.get('conclusion')
        print(f"Run #{rid} ({branch}): status={status}, conclusion={conclusion}")
        
        # Check job details
        jr = requests.get(f'https://api.github.com/repos/Romeo-Timony/juice-qa/actions/runs/{rid}/jobs', headers=headers)
        if jr.ok:
            for j in jr.json().get('jobs', []):
                for s in j.get('steps', []):
                    if s.get('status') == 'in_progress':
                        print(f"   ⏳ Step in progress: {s.get('name')}")
                    elif s.get('status') == 'completed':
                        print(f"   ✅ Completed step: {s.get('name')} ({s.get('conclusion')})")
        break
