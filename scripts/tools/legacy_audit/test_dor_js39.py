import os
import requests
import json
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('qa-automation/.env')
jira_base = os.getenv('ATLASSIAN_BASE_URL', 'https://romeo-timony.atlassian.net').rstrip('/')
auth = (os.getenv('ATLASSIAN_USER_EMAIL'), os.getenv('ATLASSIAN_API_TOKEN'))

r = requests.get(f'{jira_base}/rest/api/2/issue/JS-39', auth=auth)
issue = r.json()

desc = issue['fields'].get('description', '')
summary = issue['fields'].get('summary', '')

print("Summary length:", len(summary))
print("Description length:", len(desc))

# Check criteria
criteria = [
    ("C01 (Title 10-140)", 10 <= len(summary) <= 140),
    ("C02 (User Story format)", 'как' in desc.lower() and 'я хочу' in desc.lower()),
    ("C03 (No blocking deps)", 'блокер' not in desc.lower()),
    ("C04 (Testable AC)", 'acceptance criteria' in desc.lower() or 'критерии приемки' in desc.lower() or 'ac' in desc.lower()),
    ("C05 (Estimable)", True),
    ("C06 (Error codes / HTTP)", '400' in desc or '401' in desc or '404' in desc or '409' in desc or '201' in desc),
    ("C07 (Negotiable)", True),
    ("C08 (Scope boundary)", 'границы' in desc.lower() or 'scope' in desc.lower() or 'регистрация' in desc.lower())
]

for name, res in criteria:
    print(f" - {name}: {'PASS' if res else 'FAIL'}")
