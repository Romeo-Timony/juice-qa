import os
import sys
import re
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()

qase_token = os.getenv("QASE_API_TOKEN")
headers = {"Token": qase_token, "accept": "application/json"}

cases_res = requests.get("https://api.qase.io/v1/case/JS?limit=100", headers=headers).json()
all_cases = cases_res.get("result", {}).get("entities", [])
api_cases = [c for c in all_cases if c.get("suite_id") == 86]

print("=== SUITE 86 (API) CASES IN QASE ===")
for c in api_cases:
    print(f"ID {c['id']}: auto={c.get('automation')} | {c['title']}")

print("\n=== TESTS IN tests/backend/test_js40_api.py ===")
with open("tests/backend/test_js40_api.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for line in lines:
    line = line.strip()
    if line.startswith("@pytest.mark.qase") or line.startswith("def test_"):
        print("  ", line)
