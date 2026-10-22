import os, requests
from dotenv import load_dotenv

load_dotenv('qa-automation/.env')
base_url = os.getenv('ATLASSIAN_BASE_URL')
email = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
auth = (email, token)

r = requests.get(f'{base_url}/rest/api/3/issue/JS-16/transitions', auth=auth)
for t in r.json().get('transitions', []):
    print(t['id'], repr(t['name']), repr(t.get('to', {}).get('name')), t.get('to', {}).get('id'))
