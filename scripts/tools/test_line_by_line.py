import sys
from pathlib import Path

BASE_DIR = Path('qa-automation').resolve()
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'scripts'))

print("Step 1: import settings")
from qaops.config import settings
print(f"Jira URL: {settings.jira_url}, auth: {settings.jira_auth[0]}")

print("Step 2: requests.get directly")
import requests
t0 = requests.get(f"{settings.jira_url}/rest/api/2/issue/JS-16", params={"fields": "summary,description,issuetype,labels"}, auth=settings.jira_auth, timeout=10)
print(f"Direct request status: {t0.status_code}")

print("Step 3: import qaops.store")
from qaops import store
with store.connect() as conn:
    print("Store connected ok!")

print("Step 4: test resilient_request")
from qaops.resilience import resilient_request
resp = resilient_request("GET", f"{settings.jira_url}/rest/api/2/issue/JS-16", params={"fields": "summary,description,issuetype,labels"}, auth=settings.jira_auth, timeout=10)
print(f"Resilient request status: {resp.status_code}")
