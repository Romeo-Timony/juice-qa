import os
import sys
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')
u = os.getenv('ATLASSIAN_BASE_URL').rstrip('/')
a = (os.getenv('ATLASSIAN_USER_EMAIL'), os.getenv('ATLASSIAN_API_TOKEN'))

r = requests.get(f"{u}/rest/api/3/issue/createmeta?projectKeys=JS", auth=a)
if r.ok:
    projects = r.json().get('projects', [])
    for p in projects:
        print(f"Project: {p.get('key')} - {p.get('name')}")
        for it in p.get('issuetypes', []):
            print(f"  Type ID: {it.get('id')} | Name: {it.get('name')} | Subtask: {it.get('subtask')}")
else:
    print('Error:', r.status_code, r.text)
