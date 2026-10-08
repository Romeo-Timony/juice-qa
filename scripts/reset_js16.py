import os
import requests
import sqlite3
from dotenv import load_dotenv

load_dotenv('.env')

JIRA_URL = "https://romeo-timony.atlassian.net"
JIRA_USER = os.getenv('ATLASSIAN_USER_EMAIL')
JIRA_TOKEN = os.getenv('ATLASSIAN_API_TOKEN')
QASE_TOKEN = os.getenv('QASE_API_TOKEN')

def reset_js16():
    print("--- 🗑️ Deleting local files ---")
    files = [
        "tests/backend/test_js16_user_profile.py",
        "tests/frontend/test_js16_user_profile.py"
    ]
    for f in files:
        if os.path.exists(f):
            os.remove(f)
            print(f"Deleted {f}")

    print("--- 🗑️ Wiping Qase ---")
    headers = {"Token": QASE_TOKEN}
    res = requests.get("https://api.qase.io/v1/case/JS?limit=100", headers=headers)
    if res.ok:
        cases = res.json().get('result', {}).get('entities', [])
        for c in cases:
            requests.delete(f"https://api.qase.io/v1/case/JS/{c['id']}", headers=headers)
            print(f"Deleted Qase case {c['id']}")
            
    # Also delete suites to completely wipe
    res = requests.get("https://api.qase.io/v1/suite/JS?limit=100", headers=headers)
    if res.ok:
        suites = res.json().get('result', {}).get('entities', [])
        for s in suites:
            requests.delete(f"https://api.qase.io/v1/suite/JS/{s['id']}", headers=headers)
            print(f"Deleted Qase suite {s['id']}")

    print("--- 🗑️ Clearing SQLite ---")
    conn = sqlite3.connect("data/qa_pipeline.db")
    conn.execute("DELETE FROM pipeline_tasks WHERE issue_key = 'JS-16'")
    conn.execute("DELETE FROM task_stages WHERE issue_key = 'JS-16'")
    conn.commit()

    print("--- 🗑️ Resetting Jira JS-16 ---")
    auth = (JIRA_USER, JIRA_TOKEN)
    
    # 1. Clear labels
    requests.put(f"{JIRA_URL}/rest/api/2/issue/JS-16", json={"update": {"labels": [{"set": []}]}}, auth=auth)
    print("Cleared Jira labels")
    
    # 2. Delete comments
    res = requests.get(f"{JIRA_URL}/rest/api/2/issue/JS-16", auth=auth)
    comments = res.json().get('fields', {}).get('comment', {}).get('comments', [])
    for c in comments:
        requests.delete(f"{JIRA_URL}/rest/api/2/issue/JS-16/comment/{c['id']}", auth=auth)
        print(f"Deleted Jira comment {c['id']}")

    # 3. Transition to 'К выполнению' (Status ID: 11) or 'В работе'
    # requests.post(f"{JIRA_URL}/rest/api/2/issue/JS-16/transitions", json={"transition": {"id": "11"}}, auth=auth)

if __name__ == "__main__":
    reset_js16()
