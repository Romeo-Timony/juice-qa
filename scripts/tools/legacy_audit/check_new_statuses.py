import os
import sys
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')
u = os.getenv('ATLASSIAN_BASE_URL').rstrip('/')
a = (os.getenv('ATLASSIAN_USER_EMAIL'), os.getenv('ATLASSIAN_API_TOKEN'))

for key in ['JS-39', 'JS-40', 'JS-41', 'JS-42']:
    r = requests.get(f"{u}/rest/api/2/issue/{key}?fields=status,summary", auth=a)
    if r.ok:
        d = r.json()
        s_name = d['fields']['status']['name']
        s_id = d['fields']['status']['id']
        summ = d['fields']['summary']
        print(f"{key} | Status: {s_name} ({s_id}) | {summ}")
