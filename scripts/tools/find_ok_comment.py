import os
import sys
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')

u = os.getenv('ATLASSIAN_BASE_URL').rstrip('/')
auth = (os.getenv('ATLASSIAN_USER_EMAIL'), os.getenv('ATLASSIAN_API_TOKEN'))

keys = ['JS-39', 'JS-40', 'JS-41', 'JS-42', 'JS-16', 'JS-20', 'JS-22', 'JS-17']

print("=== Поиск комментария 'Окей' по задачам Jira ===")
for k in keys:
    r = requests.get(f"{u}/rest/api/2/issue/{k}", auth=auth)
    if not r.ok:
        continue
    data = r.json()
    status = data['fields']['status']['name']
    comments = data['fields']['comment']['comments']
    print(f"\n[{k}] Статус: {status} | Комментариев: {len(comments)}")
    for c in comments:
        author = c.get('author', {}).get('displayName', 'Unknown')
        body = str(c.get('body', ''))
        print(f"  - ({author}): {body[:100]}...")
