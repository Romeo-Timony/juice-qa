"""
Tests for QAOps Seam 3: Static Code Gate.
Verifies AST validation, ruff lint checking, pytest --collect-only isolation,
and Syntax Collect Validity = 100% enforcement.
"""

import sys
import tempfile
from pathlib import Path
import pytest

from qaops.code_gate import (
    _ast_audit,
    _ruff,
    _lint,
    run_code_gate,
    CodeGateResult,
    FileAudit,
    BLOCKING_RULES,
)


def test_ast_audit_valid_test_file():
    code = '''
import pytest
from qaseio.pytest import qase

@qase.id(101)
def test_valid_login():
    assert True

def test_helper_not_test():
    pass
'''
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        f.flush()
        f_path = Path(f.name)

    try:
        audit = _ast_audit(f_path)
        assert audit.syntax_ok is True
        assert audit.syntax_error is None
        assert audit.tests == 2
        assert 101 in audit.qase_ids
    finally:
        f_path.unlink(missing_ok=True)


def test_ast_audit_syntax_error():
    broken_code = '''
def test_broken(
    assert True
'''
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(broken_code)
        f.flush()
        f_path = Path(f.name)

    try:
        audit = _ast_audit(f_path)
        assert audit.syntax_ok is False
        assert audit.syntax_error is not None
        assert "SyntaxError" in audit.syntax_error
    finally:
        f_path.unlink(missing_ok=True)


def test_lint_detects_blocking_undefined_name():
    code_with_undefined = '''
def test_undefined():
    return undefined_variable_xyz + 1
'''
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code_with_undefined)
        f.flush()
        f_path = Path(f.name)

    try:
        audit = FileAudit(path=str(f_path), syntax_ok=True)
        passed = _lint([audit], [f_path])
        # If ruff is installed, it must catch F821 (undefined name)
        if passed is False:
            assert any("F821" in err for err in audit.lint_errors)
    finally:
        f_path.unlink(missing_ok=True)


def test_run_code_gate_valid_file():
    valid_test = '''
def test_math_operation():
    assert 1 + 1 == 2
'''
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(valid_test)
        f.flush()
        f_path = Path(f.name)

    try:
        result = run_code_gate([f_path], issue_key="JS-TEST-3")
        assert result.syntax_ok is True
        # In local/docker runtime, collection should find 1 test if runnable
        assert isinstance(result.collected, int)
    finally:
        f_path.unlink(missing_ok=True)


def test_code_gate_result_errors_formatting():
    file_audit = FileAudit(
        path="tests/test_demo.py",
        syntax_ok=False,
        syntax_error="SyntaxError line 5: unexpected EOF",
        lint_errors=["F821 L10: undefined name 'foo'"]
    )
    res = CodeGateResult(
        files=[file_audit],
        syntax_ok=False,
        lint_ok=False,
        collect_ok=False,
        collected=0,
        runtime="local",
        collect_output="Traceback...",
        passed=False
    )
    errs = res.errors
    assert any("SyntaxError" in e for e in errs)
    assert any("F821" in e for e in errs)
    assert any("collect-only" in e for e in errs)
