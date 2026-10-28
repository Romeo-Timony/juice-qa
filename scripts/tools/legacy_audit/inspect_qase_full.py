import os
import sys
import requests
import dotenv

sys.stdout.reconfigure(encoding='utf-8')
dotenv.load_dotenv('.env')
token = os.getenv('QASE_API_TOKEN')
url = os.getenv('QASE_API_URL', 'https://api.qase.io/v1')
headers = {'Token': token}

r_suites = requests.get(f"{url}/suite/JS", headers=headers)
print("=== Qase Suites ===")
for s in r_suites.json().get('result', {}).get('entities', []):
    print(f"ID: {s['id']} | Title: {s['title']} | Parent: {s.get('parent_id')}")

r_cases = requests.get(f"{url}/case/JS?limit=30", headers=headers)
print("\n=== Qase Cases ===")
for c in r_cases.json().get('result', {}).get('entities', []):
    print(f"ID: {c['id']} | Suite ID: {c.get('suite_id')} | Title: {c['title']}")
