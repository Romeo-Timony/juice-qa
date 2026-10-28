import os
import sys
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()

# --- Jira Inspection ---
jira_url = (os.getenv("ATLASSIAN_BASE_URL") or "https://romeo-timony.atlassian.net").rstrip("/")
jira_auth = (os.getenv("ATLASSIAN_USER_EMAIL"), os.getenv("ATLASSIAN_API_TOKEN"))

print("=" * 60)
print("1. JIRA COMMENTS INSPECTION")
print("=" * 60)

for key in ["JS-40", "JS-41", "JS-42"]:
    r = requests.get(f"{jira_url}/rest/api/2/issue/{key}?fields=summary,status,comment", auth=jira_auth)
    if r.status_code != 200:
        continue
    data = r.json()
    summary = data["fields"]["summary"]
    status = data["fields"]["status"]["name"]
    comments = data["fields"]["comment"]["comments"]
    print(f"\n--- {key}: {summary} [Status: {status}] | Comments: {len(comments)} ---")
    for idx, c in enumerate(comments, 1):
        cid = c["id"]
        body = c.get("body", "")
        first_line = body.split("\n")[0][:100] if body else "(empty)"
        print(f"  #{idx} [ID: {cid}]: {first_line}")

# --- Qase TMS Inspection ---
qase_token = os.getenv("QASE_API_TOKEN")
qase_project = os.getenv("QASE_PROJECT_CODE", "JS")

print("\n" + "=" * 60)
print(f"2. QASE TMS CASES INSPECTION (Project: {qase_project})")
print("=" * 60)

headers = {"Token": qase_token, "accept": "application/json"}
# Fetch all suites
suites_res = requests.get(f"https://api.qase.io/v1/suite/{qase_project}?limit=100", headers=headers)
if suites_res.status_code == 200:
    suites = suites_res.json().get("result", {}).get("entities", [])
    print(f"Total suites found: {len(suites)}")
    for s in suites:
        print(f"  Suite #{s['id']}: '{s['title']}' (parent: {s.get('parent_id')}, cases_count: {s.get('cases_count')})")
else:
    print(f"Error fetching suites: {suites_res.status_code} {suites_res.text}")

# Fetch cases
cases_res = requests.get(f"https://api.qase.io/v1/case/{qase_project}?limit=100", headers=headers)
if cases_res.status_code == 200:
    cases = cases_res.json().get("result", {}).get("entities", [])
    print(f"\nTotal test cases found: {len(cases)}")
    for c in cases:
        cid = c["id"]
        title = c["title"]
        suite_id = c.get("suite_id")
        automation = c.get("automation") # 0 = not automated, 1 = to-be-automated, 2 = automated
        status = c.get("status")
        print(f"  Case #{cid} [Suite #{suite_id}] [auto={automation}, status={status}]: {title[:80]}")
else:
    print(f"Error fetching cases: {cases_res.status_code} {cases_res.text}")
