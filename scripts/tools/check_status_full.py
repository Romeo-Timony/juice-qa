import os, sys, requests, json
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')

base_url = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
email = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
auth = (email, token)
issue_key = 'JS-16'

# 1. Jira Comments
r = requests.get(f"{base_url}/rest/api/2/issue/{issue_key}/comment", auth=auth)
if r.ok:
    comms = r.json().get('comments', [])
    print(f"Jira комментарии ({len(comms)} шт.):")
    for i, c in enumerate(comms):
        first_line = c.get('body', '').strip().splitlines()[0] if c.get('body') else ''
        print(f"  [{i+1}] ID: {c['id']} | {first_line[:80]}")

# 2. Qase Suites
qase_token = os.getenv('QASE_API_TOKEN')
qase_url = os.getenv('QASE_API_URL', 'https://api.qase.io/v1')
headers = {'Token': qase_token}
r_qase = requests.get(f"{qase_url}/suite/JS", headers=headers)
if r_qase.ok:
    suites = r_qase.json().get('result', {}).get('entities', [])
    print(f"\nQase Suites ({len(suites)} шт.):")
    for s in suites:
        print(f"  - Suite ID: {s.get('id')}, Title: {s.get('title')}, Cases count: {s.get('cases_count')}")

# 3. Check n8n executions
n8n_url = os.getenv('N8N_URL', 'http://201.34.147.33:5678').rstrip('/')
n8n_key = os.getenv('N8N_API_KEY')
r_n8n = requests.get(f"{n8n_url}/api/v1/executions?limit=5", headers={'X-N8N-API-KEY': n8n_key})
if r_n8n.ok:
    execs = r_n8n.json().get('data', [])
    print(f"\nПоследние n8n executions ({len(execs)} шт.):")
    for ex in execs:
        print(f"  - ID: {ex.get('id')}, Mode: {ex.get('mode')}, Status: {ex.get('status')}, Finished: {ex.get('finished')}")
