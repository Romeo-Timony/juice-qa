"""
Seam 3: static gate for generated autotest code, executed before "tests created" is reported.

1. ast.parse          — syntax validity of every staged file
2. ruff               — blocking set (E9, F63, F7, F82: syntax/undefined names), advisory set (E, F, W)
3. pytest --collect-only inside Docker (`--network none`), local venv as an explicit fallback
Syntax Collect Validity must be 100%; otherwise the code goes back for rework.
"""

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from qaops import store
from qaops.config import BASE_DIR, settings
from qaops.observability import span

BLOCKING_RULES = "E9,F63,F7,F82"
ADVISORY_RULES = "E,F,W"
DOCKERFILE = BASE_DIR / "qaops" / "docker" / "collect.Dockerfile"


@dataclass
class FileAudit:
    path: str
    syntax_ok: bool
    syntax_error: Optional[str] = None
    lint_errors: List[str] = field(default_factory=list)
    lint_warnings: List[str] = field(default_factory=list)
    tests: int = 0
    qase_ids: List[int] = field(default_factory=list)


@dataclass
class CodeGateResult:
    files: List[FileAudit]
    syntax_ok: bool
    lint_ok: bool
    collect_ok: bool
    collected: int
    runtime: str
    collect_output: str
    passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def errors(self) -> List[str]:
        out = []
        for f in self.files:
            if f.syntax_error:
                out.append(f"{Path(f.path).name}: {f.syntax_error}")
            out += [f"{Path(f.path).name}: {e}" for e in f.lint_errors]
        if not self.collect_ok:
            out.append(f"pytest --collect-only ({self.runtime}): {self.collect_output[-800:]}")
        return out


def _ast_audit(path: Path) -> FileAudit:
    audit = FileAudit(path=str(path), syntax_ok=True)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        audit.syntax_ok = False
        audit.syntax_error = f"SyntaxError line {exc.lineno}: {exc.msg}"
        return audit
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            audit.tests += 1
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call):
                    if isinstance(dec.func, ast.Attribute) and dec.func.attr == "qase":
                        for kw in dec.keywords:
                            if kw.arg == "id" and isinstance(kw.value, ast.Constant):
                                audit.qase_ids.append(kw.value.value)
                    elif isinstance(dec.func, ast.Attribute) and dec.func.attr == "id":
                        if dec.args and isinstance(dec.args[0], ast.Constant):
                            audit.qase_ids.append(dec.args[0].value)
                        for kw in dec.keywords:
                            if kw.arg == "id" and isinstance(kw.value, ast.Constant):
                                audit.qase_ids.append(kw.value.value)
    return audit


def _ruff(files: List[Path], select: str, extra: Optional[List[str]] = None) -> Optional[List[Dict[str, Any]]]:
    cmd = [sys.executable, "-m", "ruff", "check", "--no-cache", "--output-format", "json", "--select", select, *(extra or []), *map(str, files)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode not in (0, 1) or not proc.stdout.strip().startswith("["):
        return None
    return json.loads(proc.stdout)


def _lint(audits: List[FileAudit], files: List[Path]) -> bool:
    blocking = _ruff(files, BLOCKING_RULES)
    if blocking is None:
        for a in audits:
            a.lint_warnings.append("ruff недоступен — lint пропущен (pip install ruff)")
        return True
    advisory = _ruff(files, ADVISORY_RULES, ["--ignore", "E501"]) or []
    by_path = {str(Path(a.path).resolve()): a for a in audits}
    blocking_ids = set()
    for item in blocking:
        a = by_path.get(str(Path(item["filename"]).resolve()))
        if a:
            a.lint_errors.append(f"{item['code']} L{item['location']['row']}: {item['message']}")
            blocking_ids.add((item["filename"], item["code"], item["location"]["row"]))
    for item in advisory:
        if (item["filename"], item["code"], item["location"]["row"]) in blocking_ids:
            continue
        a = by_path.get(str(Path(item["filename"]).resolve()))
        if a:
            a.lint_warnings.append(f"{item['code']} L{item['location']['row']}: {item['message']}")
    return not blocking


def _docker_available() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        return subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"], capture_output=True, timeout=20).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def ensure_image() -> None:
    if subprocess.run(["docker", "image", "inspect", settings.collect_image], capture_output=True).returncode == 0:
        return
    with tempfile.TemporaryDirectory() as ctx:
        shutil.copy(DOCKERFILE, Path(ctx) / "Dockerfile")
        shutil.copy(BASE_DIR / "requirements.txt", Path(ctx) / "requirements.txt")
        proc = subprocess.run(["docker", "build", "-t", settings.collect_image, ctx], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1200)
        if proc.returncode != 0:
            raise RuntimeError(f"docker build failed: {proc.stderr[-1500:]}")


def _collect(files: List[Path]) -> Dict[str, Any]:
    rel = []
    for f in files:
        resolved = Path(f).resolve()
        try:
            rel.append(resolved.relative_to(BASE_DIR).as_posix())
        except ValueError:
            rel.append(str(resolved))
    pytest_args = ["-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "-o", "addopts=", *rel]

    runtime = settings.collect_runtime
    if runtime == "auto":
        runtime = "docker" if _docker_available() else "local"
    if runtime == "local" and settings.require_docker:
        return {"ok": False, "collected": 0, "runtime": "local", "output": "Docker недоступен, а QAOPS_REQUIRE_DOCKER=1"}

    if runtime == "docker":
        ensure_image()
        cmd = ["docker", "run", "--rm", "--network", "none", "-e", "PYTHONDONTWRITEBYTECODE=1",
               "-v", f"{BASE_DIR}:/work", "-w", "/work", settings.collect_image, "python", *pytest_args]
    else:
        cmd = [sys.executable, *pytest_args]

    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=BASE_DIR, timeout=600)
    output = (proc.stdout + "\n" + proc.stderr).strip()
    m = re.search(r"(\d+) tests? collected", output) or re.search(r"collected (\d+) items?", output)
    collected = int(m.group(1)) if m else 0
    ok = proc.returncode == 0 and collected > 0 and not re.search(r"\b\d+ errors?\b", output)
    return {"ok": ok, "collected": collected, "runtime": runtime, "output": output[-4000:]}


def run_code_gate(files: List[Path], issue_key: Optional[str] = None) -> CodeGateResult:
    files = [Path(f) for f in files]
    with span("seam3.code_gate", input={"files": [f.name for f in files]}) as s:
        audits = [_ast_audit(f) for f in files]
        syntax_ok = bool(files) and all(a.syntax_ok for a in audits)
        lint_ok = _lint(audits, files) if syntax_ok else False
        collect = _collect(files) if syntax_ok and lint_ok else {"ok": False, "collected": 0, "runtime": "skipped", "output": "пропущено: синтаксис/линтер не пройдены"}

        result = CodeGateResult(
            files=audits,
            syntax_ok=syntax_ok,
            lint_ok=lint_ok,
            collect_ok=collect["ok"],
            collected=collect["collected"],
            runtime=collect["runtime"],
            collect_output=collect["output"],
            passed=syntax_ok and lint_ok and collect["ok"],
        )
        if issue_key:
            store.record_metric(issue_key, "syntax_collect_validity", 1.0 if result.passed else 0.0, result.passed,
                                {"collected": result.collected, "runtime": result.runtime, "errors": result.errors[:20]})
        s.set_output({"passed": result.passed, "collected": result.collected, "runtime": result.runtime, "errors": result.errors[:10]})
        if not result.passed:
            s.error("; ".join(result.errors)[:1000])
        return result


def format_jira_rework(result: CodeGateResult, issue_key: str, trace_url: str) -> str:
    lines = [
        "h3. 🛑 QAOps Seam 3: Код автотестов не прошёл статическую сборку — возвращён на доработку",
        f"*Задача:* {issue_key} | *Syntax:* {'(/)' if result.syntax_ok else '(x)'} | *Ruff:* {'(/)' if result.lint_ok else '(x)'} | "
        f"*pytest --collect-only ({result.runtime}):* {'(/) ' + str(result.collected) + ' тестов' if result.collect_ok else '(x)'}",
        "",
        "h4. Ошибки:",
        "{noformat}",
        *result.errors[:30],
        "{noformat}",
        f"🔭 Трейс: {trace_url}",
        "_Gate 2 (HITL) не будет запрошен, пока Syntax Collect Validity < 100%._",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="QAOps Seam 3: static gate for generated autotests")
    parser.add_argument("paths", nargs="*", type=Path, default=[BASE_DIR / "tests" / "review"])
    parser.add_argument("--issue")
    args = parser.parse_args()
    files = [p for root in args.paths for p in ([root] if root.is_file() else sorted(root.rglob("test_*.py")))]
    result = run_code_gate(files, args.issue)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
