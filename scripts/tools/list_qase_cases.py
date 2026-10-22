import os, sys, requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')

qase_token = os.getenv('QASE_API_TOKEN')
qase_url = os.getenv('QASE_API_URL', 'https://api.qase.io/v1')
headers = {'Token': qase_token}

r = requests.get(f"{qase_url}/case/JS?suite_id=76&limit=20", headers=headers)
if r.ok:
    cases = r.json().get('result', {}).get('entities', [])
    print(f"Кейсы в Qase TMS (Suite 76, всего {len(cases)}):")
    for c in cases:
        print(f"  [ID {c.get('id')}] {c.get('title')} (Type: {c.get('type')}, Priority: {c.get('priority')})")
