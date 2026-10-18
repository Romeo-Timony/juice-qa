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
    files = glob.glob("tests/backend/test_js16*.py") + glob.glob("tests/frontend/test_js16*.py") + glob.glob("tests/review/**/*.py", recursive=True)
    for f in files:
        if os.path.exists(f):
            os.remove(f)
            print(f"Deleted {f}")

    # Remove review reports if any
    for r_f in ["tests/review/REVIEW_REPORT.md", "tests/review/.review_state.json", "n8n_execution.json"]:
        if os.path.exists(r_f):
            os.remove(r_f)
            print(f"Deleted {r_f}")

    print("--- 🗑️ Wiping Qase ---")
    headers = {"Token": QASE_TOKEN}
    res = requests.get("https://api.qase.io/v1/case/JS?limit=100", headers=headers)
    if res.ok:
        cases = res.json().get('result', {}).get('entities', [])
        for c in cases:
            requests.delete(f"https://api.qase.io/v1/case/JS/{c['id']}", headers=headers)
            print(f"Deleted Qase case {c['id']}")

    res = requests.get("https://api.qase.io/v1/suite/JS?limit=100", headers=headers)
    if res.ok:
        suites = res.json().get('result', {}).get('entities', [])
        suites.sort(key=lambda s: 0 if s.get('parent_id') else 1)
        for s in suites:
            requests.delete(f"https://api.qase.io/v1/suite/JS/{s['id']}", headers=headers)
            print(f"Deleted Qase suite {s['id']}")

    print("--- 🗑️ Clearing SQLite & QAOps tables ---")
    conn = sqlite3.connect("data/qa_pipeline.db")
    for tbl in ["pipeline_tasks", "pipeline_stages", "test_cases", "task_stages"]:
        try:
            conn.execute(f"DELETE FROM {tbl} WHERE issue_key = 'JS-16'")
        except Exception:
            pass

    # Clear QAOps tables
    try:
        conn.execute("DELETE FROM qaops_idempotency WHERE idem_key LIKE '%JS-16%'")
        conn.execute("DELETE FROM qaops_spans WHERE issue_key = 'JS-16'")
        conn.execute("DELETE FROM qaops_metrics WHERE issue_key = 'JS-16'")
        conn.execute("DELETE FROM qaops_outbox WHERE url LIKE '%JS-16%' OR idem_key LIKE '%JS-16%'")
    except Exception as qe:
        print(f"Note on QAOps cleanup: {qe}")
    conn.commit()
    conn.close()

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

    # 4. Delete Qase Remote Links (keep Confluence / Figma)
    r_links = requests.get(f"{JIRA_URL}/rest/api/2/issue/JS-16/remotelink", auth=auth)
    if r_links.ok and isinstance(r_links.json(), list):
        for rl in r_links.json():
            rl_id = rl.get("id")
            title = rl.get("object", {}).get("title", "")
            url = rl.get("object", {}).get("url", "")
            app_name = rl.get("application", {}).get("name", "")
            global_id = rl.get("globalId", "")
            if any("qase" in str(x).lower() for x in [title, url, app_name, global_id]):
                requests.delete(f"{JIRA_URL}/rest/api/2/issue/JS-16/remotelink/{rl_id}", auth=auth)
                print(f"Deleted Qase remote link {rl_id}")

def start_js16():
    print("--- 🚀 Transitioning JS-16 to 'В работе' ---")
    auth = (JIRA_USER, JIRA_TOKEN)
    res = requests.post(f"{JIRA_URL}/rest/api/3/issue/JS-16/transitions", json={"transition": {"id": "21"}}, auth=auth)
    print("Transition response:", res.status_code)

if __name__ == "__main__":
    reset_js16()
    start_js16()
