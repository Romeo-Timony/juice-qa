import sys, time
from pathlib import Path

BASE_DIR = Path('qa-automation').resolve()
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'scripts'))

issue_key = 'JS-16'
task_kind = 'frontend'

print("Step 5: check_issue_contract")
from qaops.seams import check_issue_contract
c_ok = check_issue_contract(issue_key)
print("check_issue_contract:", c_ok)

print("Step 6: fetch_qase_cases")
from scaffold_dynamic import fetch_qase_cases
cases = fetch_qase_cases(issue_key)
print(f"fetch_qase_cases: {len(cases)} cases")

print("Step 7: run_design_seam")
from qaops.seams import run_design_seam
d_ok = run_design_seam(issue_key, cases)
print("run_design_seam:", d_ok)

print("Step 8: generate_tests")
from scaffold_dynamic import generate_tests
generate_tests(issue_key, kind=task_kind, target_dir=BASE_DIR / "tests" / "review")
print("generate_tests: done")

print("Step 9: run_staging_review")
from hitl_review_gate import run_staging_review
r_ok = run_staging_review(issue_key)
print("run_staging_review:", r_ok)
