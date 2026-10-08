import os
import glob
import requests
import sqlite3
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('.env')

JIRA_URL = "https://romeo-timony.atlassian.net"
JIRA_USER = os.getenv('ATLASSIAN_USER_EMAIL')
JIRA_TOKEN = os.getenv('ATLASSIAN_API_TOKEN')
QASE_TOKEN = os.getenv('QASE_API_TOKEN')

def reset_all():
    print("--- 🗑️ Deleting ALL local test files ---")
    files = glob.glob("tests/backend/test_*.py") + glob.glob("tests/frontend/test_*.py")
    for f in files:
        os.remove(f)
        print(f"Deleted {f}")

    print("--- 🗑️ Wiping Qase (All Cases and Suites) ---")
    headers = {"Token": QASE_TOKEN}
    # Delete all cases
    res = requests.get("https://api.qase.io/v1/case/JS?limit=100", headers=headers)
    if res.ok:
        cases = res.json().get('result', {}).get('entities', [])
        for c in cases:
            requests.delete(f"https://api.qase.io/v1/case/JS/{c['id']}", headers=headers)
            print(f"Deleted Qase case {c['id']}")
            
    # Delete all suites
    res = requests.get("https://api.qase.io/v1/suite/JS?limit=100", headers=headers)
    if res.ok:
        suites = res.json().get('result', {}).get('entities', [])
        for s in suites:
            requests.delete(f"https://api.qase.io/v1/suite/JS/{s['id']}", headers=headers)
            print(f"Deleted Qase suite {s['id']}")

    print("--- 🗑️ Clearing SQLite ---")
    conn = sqlite3.connect("data/qa_pipeline.db")
    conn.execute("DELETE FROM pipeline_tasks")
    conn.commit()
    print("Wiped pipeline_tasks table")

    print("--- 🗑️ Resetting Jira Issues ---")
    auth = (JIRA_USER, JIRA_TOKEN)
    
    # Get all JS issues
    res = requests.get(f"{JIRA_URL}/rest/api/3/search/jql?jql=project=JS", auth=auth)
    if res.ok:
        issues = res.json().get('issues', [])
        for issue in issues:
            key = issue['id']
            print(f"Processing Jira issue {key}...")
            
            # Clear labels
            requests.put(f"{JIRA_URL}/rest/api/3/issue/{key}", json={"update": {"labels": [{"set": []}]}}, auth=auth)
            
            # Delete comments
            c_res = requests.get(f"{JIRA_URL}/rest/api/3/issue/{key}", auth=auth)
            comments = c_res.json().get('fields', {}).get('comment', {}).get('comments', [])
            for c in comments:
                requests.delete(f"{JIRA_URL}/rest/api/3/issue/{key}/comment/{c['id']}", auth=auth)
                
            # Transition to 'К выполнению' (Status ID: 11)
            requests.post(f"{JIRA_URL}/rest/api/3/issue/{key}/transitions", json={"transition": {"id": "11"}}, auth=auth)
            print(f"Fully reset Jira issue {key}")
    else:
        print(f"Failed to get Jira issues: {res.text}")

if __name__ == "__main__":
    reset_all()
