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

res = requests.get(f"{QASE_URL}/case/{QASE_PROJECT}?suite_id=87&limit=100", headers=headers)
if res.ok:
    cases = res.json().get("result", {}).get("entities", [])
    print(f"Total cases in Suite 87 (UI): {len(cases)}")
    for c in cases:
        print(f"ID: {c.get('id')} | Title: {c.get('title')}")
