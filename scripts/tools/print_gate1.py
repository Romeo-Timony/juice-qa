import os, sys, requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')
base_url = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
email = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
auth = (email, token)
issue_key = 'JS-16'

r = requests.get(f"{base_url}/rest/api/2/issue/{issue_key}/comment", auth=auth)
if r.ok:
    comments = r.json().get('comments', [])
    for c in comments:
        body = c.get('body', '')
        if '[Этап 5 из' in body:
            print("=== Карточка Gate 1 ===")
            print(body)
            break
