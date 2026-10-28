import os
import requests
import json
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')
jira_base = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
auth = (os.getenv('ATLASSIAN_USER_EMAIL'), os.getenv('ATLASSIAN_API_TOKEN'))

r = requests.get(f'{jira_base}/rest/api/2/issue/JS-39', auth=auth)
print('Status code:', r.status_code)
if r.status_code == 200:
    issue = r.json()
    print('Key:', issue['key'])
    print('Summary:', issue['fields']['summary'])
    print('Status:', issue['fields']['status']['name'], f"id={issue['fields']['status']['id']}")
    print('Labels:', issue['fields']['labels'])
    print('Comments count:', issue['fields']['comment']['total'])
    for c in issue['fields']['comment']['comments']:
        print(f" - [{c['id']}] {c['author']['displayName']}: {c['body'][:80].replace(chr(10), ' ')}")
