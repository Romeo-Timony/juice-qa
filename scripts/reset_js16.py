import os
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

import glob

def reset_js16():
    print("--- 🗑️ Deleting local files ---")
    files = glob.glob("tests/backend/test_js16*.py") + glob.glob("tests/frontend/test_js16*.py")
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
            
    # Also delete suites to completely wipe (children first)
    res = requests.get("https://api.qase.io/v1/suite/JS?limit=100", headers=headers)
    if res.ok:
        suites = res.json().get('result', {}).get('entities', [])
        suites.sort(key=lambda s: 0 if s.get('parent_id') else 1)
        for s in suites:
            requests.delete(f"https://api.qase.io/v1/suite/JS/{s['id']}", headers=headers)
            print(f"Deleted Qase suite {s['id']}")

    print("--- 🗑️ Clearing SQLite ---")
    conn = sqlite3.connect("data/qa_pipeline.db")
    conn.execute("DELETE FROM pipeline_tasks WHERE issue_key = 'JS-16'")
    # Delete execution marker
    if os.path.exists("n8n_execution.json"):
        os.remove("n8n_execution.json")
        print("Deleted n8n_execution.json")

    # Check if task_stages exists first or ignore error
    try:
        conn.execute("DELETE FROM task_stages WHERE issue_key = 'JS-16'")
    except:
        pass
    conn.commit()

    print("--- 🗑️ Resetting Jira JS-16 ---")
    auth = (JIRA_USER, JIRA_TOKEN)

    # 1. Transition to 'К выполнению' (Status ID: 11)
    requests.post(f"{JIRA_URL}/rest/api/3/issue/JS-16/transitions", json={"transition": {"id": "11"}}, auth=auth)
    print("Transitioned JS-16 to 'К выполнению'")
    
    # 2. Clear labels
    requests.put(f"{JIRA_URL}/rest/api/3/issue/JS-16", json={"update": {"labels": [{"set": []}]}}, auth=auth)
    print("Cleared Jira labels")
    
    # 3. Delete comments
    res = requests.get(f"{JIRA_URL}/rest/api/3/issue/JS-16", auth=auth)
    comments = res.json().get('fields', {}).get('comment', {}).get('comments', [])
    for c in comments:
        requests.delete(f"{JIRA_URL}/rest/api/3/issue/JS-16/comment/{c['id']}", auth=auth)
        print(f"Deleted Jira comment {c['id']}")

def start_js16():
    print("--- 🚀 Transitioning JS-16 to 'В работе' ---")
    auth = (JIRA_USER, JIRA_TOKEN)
    res = requests.post(f"{JIRA_URL}/rest/api/3/issue/JS-16/transitions", json={"transition": {"id": "21"}}, auth=auth)
    print("Transition response:", res.status_code)

if __name__ == "__main__":
    reset_js16()
    start_js16()
