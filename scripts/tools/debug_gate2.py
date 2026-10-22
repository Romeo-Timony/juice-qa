import sys, time
from pathlib import Path

BASE_DIR = Path('qa-automation').resolve()
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'scripts'))

issue_key = 'JS-16'
task_kind = 'frontend'

print("1. Testing check_issue_contract...")
t0 = time.time()
try:
    from qaops.seams import check_issue_contract, run_design_seam
    from scaffold_dynamic import fetch_qase_cases, generate_tests
    print(f"Imports done in {time.time()-t0:.2f}s")
    
    contract_ok = check_issue_contract(issue_key)
    print(f"check_issue_contract: {contract_ok} ({time.time()-t0:.2f}s)")
    
    qase_cases = fetch_qase_cases(issue_key)
    print(f"fetch_qase_cases: found {len(qase_cases)} cases ({time.time()-t0:.2f}s)")
    
    design_ok = run_design_seam(issue_key, qase_cases)
    print(f"run_design_seam: {design_ok} ({time.time()-t0:.2f}s)")
    
    print("Testing generate_tests...")
    generate_tests(issue_key, kind=task_kind, target_dir=BASE_DIR / "tests" / "review")
    print(f"generate_tests done in {time.time()-t0:.2f}s")
    
    print("Testing run_staging_review...")
    from hitl_review_gate import run_staging_review
    review_ok = run_staging_review(issue_key)
    print(f"run_staging_review: {review_ok} in {time.time()-t0:.2f}s")
except Exception as e:
    print("Exception occurred:", type(e), e)
    import traceback
    traceback.print_exc()
