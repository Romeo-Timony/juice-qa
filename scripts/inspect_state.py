import os
import sys
import requests
import json
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

JIRA_URL = (os.getenv("ATLASSIAN_BASE_URL") or "https://romeo-timony.atlassian.net").rstrip('/')
JIRA_EMAIL = os.getenv("ATLASSIAN_USER_EMAIL")
JIRA_TOKEN = os.getenv("ATLASSIAN_API_TOKEN")
QASE_TOKEN = os.getenv("QASE_API_TOKEN")
QASE_PROJECT = os.getenv("QASE_PROJECT_CODE", "JS")

auth = (JIRA_EMAIL, JIRA_TOKEN)
qase_headers = {"Token": QASE_TOKEN, "Content-Type": "application/json"}

print("=== JIRA ISSUES ===")
url = f"{JIRA_URL}/rest/api/3/search/jql"
res = requests.get(url, auth=auth, params={"jql": "project = JS ORDER BY key ASC", "fields": "summary,status,labels"})
if res.ok:
    for iss in res.json().get("issues", []):
        print(f"Key: {iss['key']} | Status: {iss['fields']['status']['name']} (ID {iss['fields']['status']['id']}) | Labels: {iss['fields'].get('labels')} | Summary: {iss['fields']['summary']}")
else:
    print("Error querying Jira:", res.status_code, res.text)

print("\n=== QASE SUITES ===")
s_res = requests.get(f"https://api.qase.io/v1/suite/{QASE_PROJECT}?limit=100", headers=qase_headers)
if s_res.ok:
    suites = s_res.json().get("result", {}).get("entities", [])
    for s in suites:
        print(f"Suite ID {s['id']} | Parent: {s.get('parent_id')} | Title: {s.get('title')}")
else:
    print("Error querying Qase suites:", s_res.status_code)

print("\n=== QASE CASES ===")
c_res = requests.get(f"https://api.qase.io/v1/case/{QASE_PROJECT}?limit=100", headers=qase_headers)
if c_res.ok:
    cases = c_res.json().get("result", {}).get("entities", [])
    print(f"Total cases: {len(cases)}")
    for c in cases:
        print(f"Case ID {c['id']} | Suite ID: {c.get('suite_id')} | Title: {c.get('title')}")
else:
    print("Error querying Qase cases:", c_res.status_code)

print("\n=== SQLITE qa_pipeline.db ===")
db_path = BASE_DIR / "data" / "qa_pipeline.db"
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print("Tables:", tables)
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cur.fetchone()[0]
        print(f"Table {t}: {cnt} rows")
        if cnt > 0 and t in ["pipeline_tasks", "pipeline_stages", "test_cases"]:
            cur.execute(f"SELECT DISTINCT issue_key FROM {t}")
            keys = [r[0] for r in cur.fetchall()]
            print(f"  issue_keys in {t}: {keys}")
    conn.close()

print("\n=== SQLITE qaops.db ===")
qaops_db = BASE_DIR / "qaops.db"
if qaops_db.exists():
    conn = sqlite3.connect(qaops_db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print("Tables:", tables)
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cur.fetchone()[0]
        print(f"Table {t}: {cnt} rows")
    conn.close()
