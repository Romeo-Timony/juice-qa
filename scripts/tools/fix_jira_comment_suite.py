import os
import requests
import dotenv

dotenv.load_dotenv('.env')
u = os.getenv('ATLASSIAN_BASE_URL').rstrip('/')
a = (os.getenv('ATLASSIAN_USER_EMAIL'), os.getenv('ATLASSIAN_API_TOKEN'))
r_comms = requests.get(f"{u}/rest/api/2/issue/JS-40/comment", auth=a)
for c in r_comms.json().get('comments', []):
    body = c.get('body', '')
    if 'JS-40: [API]' in body:
        new_body = body.replace('API / JS-40: [API] Реализация серверной логики и контрактов регистрации (POST /api/Users)', 'API')
        cid = c['id']
        requests.put(f"{u}/rest/api/2/issue/JS-40/comment/{cid}", auth=a, json={'body': new_body})
        print(f"Updated comment {cid}")
