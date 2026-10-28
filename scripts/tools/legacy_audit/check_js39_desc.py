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
issue = r.json()
print('Summary:', issue['fields']['summary'])
print('Description:\n', issue['fields']['description'][:800])
