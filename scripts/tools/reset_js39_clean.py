import os
import requests
import json
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')
jira_base = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
auth = (os.getenv('ATLASSIAN_USER_EMAIL'), os.getenv('ATLASSIAN_API_TOKEN'))

issue_key = 'JS-39'

# 1. Fetch issue
r = requests.get(f'{jira_base}/rest/api/2/issue/{issue_key}', auth=auth)
issue = r.json()
print(f"Current status of {issue_key}: {issue['fields']['status']['name']} (ID: {issue['fields']['status']['id']})")

# 2. Delete all comments
comments = issue['fields']['comment']['comments']
print(f"Deleting {len(comments)} comments from {issue_key}...")
for c in comments:
    cid = c['id']
    del_r = requests.delete(f'{jira_base}/rest/api/2/issue/{issue_key}/comment/{cid}', auth=auth)
    print(f" - Deleted comment {cid}: status {del_r.status_code}")

# 3. Clean labels
put_r = requests.put(
    f'{jira_base}/rest/api/2/issue/{issue_key}',
    auth=auth,
    json={'fields': {'labels': []}}
)
print("Cleared labels, status:", put_r.status_code)

# 4. Check available transitions
trans_r = requests.get(f'{jira_base}/rest/api/2/issue/{issue_key}/transitions', auth=auth)
transitions = trans_r.json().get('transitions', [])
print("Available transitions:")
for t in transitions:
    print(f" - ID: {t['id']}, Name: {t['name']} -> Target: {t['to']['name']} ({t['to']['id']})")

# Transition to 'К выполнению' (To Do)
to_do_transition = next((t for t in transitions if t['to']['id'] == '10045' or 'выполн' in t['to']['name'].lower() or 'to do' in t['to']['name'].lower()), None)
if to_do_transition:
    trans_post = requests.post(
        f'{jira_base}/rest/api/2/issue/{issue_key}/transitions',
        auth=auth,
        json={'transition': {'id': to_do_transition['id']}}
    )
    print(f"Transitioned to {to_do_transition['to']['name']}: status {trans_post.status_code}")
else:
    print("Could not find transition to 'К выполнению'")

# 5. Check Qase TMS cases for JS-39
qase_token = os.getenv('QASE_API_TOKEN')
if qase_token:
    qase_headers = {'Token': qase_token, 'Content-Type': 'application/json'}
    q_r = requests.get('https://api.qase.io/v1/case/JS?limit=100', headers=qase_headers)
    if q_r.status_code == 200:
        cases = q_r.json().get('result', {}).get('entities', [])
        js39_cases = [c for c in cases if 'JS-39' in str(c.get('description', '')) or 'JS-39' in c.get('title', '')]
        print(f"Found {len(js39_cases)} cases in Qase TMS for JS-39")
        for c in js39_cases:
            cid = c['id']
            del_c = requests.delete(f'https://api.qase.io/v1/case/JS/{cid}', headers=qase_headers)
            print(f" - Deleted Qase case #{cid}: status {del_c.status_code}")

print(f"\n✅ {issue_key} successfully reset to clean slate!")
