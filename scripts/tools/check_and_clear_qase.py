import os
import requests
from dotenv import load_dotenv

load_dotenv('.env')
token = os.getenv('QASE_API_TOKEN')
url = os.getenv('QASE_API_URL', 'https://api.qase.io/v1')
headers = {'Token': token}

r = requests.get(f'{url}/case/JS?limit=100', headers=headers)
if r.ok:
    cases = r.json().get('result', {}).get('entities', [])
    print(f'Total cases in Qase: {len(cases)}')
    for c in cases:
        print(f"[{c.get('id')}] {c.get('title')}")
else:
    print('Error:', r.status_code, r.text)
