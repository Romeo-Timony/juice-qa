import os
import requests
import sys
from dotenv import load_dotenv

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
load_dotenv()

from qaops.design_gate import run_design_gate, deterministic_review

QASE_URL = os.getenv('QASE_API_URL')
QASE_PROJECT = os.getenv('QASE_PROJECT_CODE')
headers = {'Token': os.getenv('QASE_API_TOKEN'), 'Accept': 'application/json'}
res = requests.get(f'{QASE_URL}/case/{QASE_PROJECT}?suite_id=87&limit=100', headers=headers)
cases = res.json().get('result', {}).get('entities', [])

print(f"Total UI cases: {len(cases)}")
det_passed = 0
for c in cases:
    rev = deterministic_review(c)
    if rev.deterministic_ok:
        det_passed += 1
    else:
        print(f"Case #{c.get('id')} failed deterministic review: {rev.reasons}")

print(f"Deterministic passed: {det_passed}/{len(cases)}")
