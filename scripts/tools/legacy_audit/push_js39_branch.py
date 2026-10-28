import subprocess
import shutil
from pathlib import Path

base_dir = Path('.').resolve()
issue_key = 'JS-39'
branch_name = f'qa/{issue_key.lower()}'
wt_dir = base_dir / '.worktrees' / f'qa-{issue_key.lower()}'
wt_dir.parent.mkdir(parents=True, exist_ok=True)

print("Fetching qa remote...")
subprocess.run(['git', 'fetch', 'qa'], cwd=base_dir, check=True)
if wt_dir.exists():
    subprocess.run(['git', 'worktree', 'remove', '--force', str(wt_dir)], cwd=base_dir, capture_output=True)

print(f"Creating worktree {wt_dir} on branch {branch_name} from qa/main...")
subprocess.run(['git', 'worktree', 'add', '-B', branch_name, str(wt_dir), 'qa/main'], cwd=base_dir, check=True)

promoted_backend = list((base_dir / 'qa-automation' / 'tests' / 'backend').glob(f'*{issue_key.lower().replace("-", "")}*.py'))
print('Files to copy:', [f.name for f in promoted_backend])

(wt_dir / 'tests' / 'backend').mkdir(parents=True, exist_ok=True)
for f in promoted_backend:
    shutil.copy(f, wt_dir / 'tests' / 'backend' / f.name)

subprocess.run(['git', 'add', 'tests/'], cwd=wt_dir, check=False)
subprocess.run(['git', 'commit', '-m', f'🤖 Автоматическая генерация тестов для {issue_key}'], cwd=wt_dir, check=False)

print("Pushing to qa remote...")
push_res = subprocess.run(['git', 'push', '-u', '--force', 'qa', branch_name], cwd=wt_dir, capture_output=True, text=True)
print('Push returncode:', push_res.returncode)
print('Push stdout:', push_res.stdout)
print('Push stderr:', push_res.stderr)

subprocess.run(['git', 'worktree', 'remove', '--force', str(wt_dir)], cwd=base_dir, capture_output=True)
print("Worktree cleaned up.")
