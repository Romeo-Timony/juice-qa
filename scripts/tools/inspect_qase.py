import os
import requests
import json
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

QASE_TOKEN = os.getenv("QASE_API_TOKEN")
QASE_PROJECT = os.getenv("QASE_PROJECT_CODE", "JS")
QASE_URL = os.getenv("QASE_API_URL", "https://api.qase.io/v1")

headers = {"Token": QASE_TOKEN, "Accept": "application/json"}

# 1. Suites
res = requests.get(f"{QASE_URL}/suite/{QASE_PROJECT}?limit=100", headers=headers)
print("Suites status:", res.status_code)
if res.ok:
    suites = res.json().get("result", {}).get("entities", [])
    for s in suites:
        print(f"Suite ID: {s.get('id')} | Title: {s.get('title')}")

# 2. Cases for JS-41
res_cases = requests.get(f"{QASE_URL}/case/{QASE_PROJECT}?limit=100", headers=headers)
if res_cases.ok:
    cases = res_cases.json().get("result", {}).get("entities", [])
    print(f"\nTotal cases in project: {len(cases)}")
    js41_cases = [c for c in cases if "JS-41" in c.get("title", "") or "JS-41" in str(c.get("suite_id", ""))]
    print(f"JS-41 cases count: {len(js41_cases)}")
    for c in js41_cases[:10]:
        print(f"Case ID: {c.get('id')} | Suite: {c.get('suite_id')} | Title: {c.get('title')}")
