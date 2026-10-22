import os
import requests
import dotenv

dotenv.load_dotenv('.env')
email = os.getenv('ATLASSIAN_USER_EMAIL')
token = os.getenv('ATLASSIAN_API_TOKEN')
base_url = os.getenv('CONFLUENCE_BASE_URL', 'https://romeo-timony.atlassian.net/wiki').rstrip('/')
auth = (email, token)

r = requests.get(f'{base_url}/rest/api/content?spaceKey=JS&limit=25', auth=auth)
if r.ok:
    results = r.json().get('results', [])
    print(f'Total pages in Confluence space JS: {len(results)}')
    for p in results:
        print(f"[{p.get('id')}] {p.get('title')}")
else:
    print('Error:', r.status_code, r.text)
