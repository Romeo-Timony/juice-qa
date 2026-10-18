"""
Seam 1 (DoR) & Seam 2 (test design) data contracts.

Pydantic v2 models are the single source of truth. `python -m qaops.contracts --export`
writes their JSON Schema to n8n/dor-workflow/contracts/, from which build_workflow.js
injects them into the n8n guard nodes, so both runtimes enforce the same contract.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from qaops.config import BASE_DIR

ISSUE_KEY_PATTERN = r"^[A-Z][A-Z0-9]+-\d+$"

# INVEST dimension -> DoR criteria that evidence it. Every dimension must be evaluated.
INVEST_MAP: Dict[str, List[str]] = {
    "I": ["C03"],          # Independent: traceability to parent story/spec
    "N": ["C07"],          # Negotiable: consistency with parent/spec, no contradictions
    "V": ["C02"],          # Valuable: business goal and context
    "E": ["C05"],          # Estimable: unambiguous wording, explicit limits
    "S": ["C01", "C08"],   # Small: focused summary / scope boundaries
    "T": ["C04", "C06"],   # Testable: acceptance criteria + negative scenarios
}

SUITE_TAGS = ["smoke", "regress", "regression", "fast-regression", "full-regression"]
SUITE_TYPES = ["smoke", "regression"]
AUTOMATION_FLAGS = ["to-be-automated", "manual", "automated"]

CONTRACTS_DIR = BASE_DIR / "n8n" / "dor-workflow" / "contracts"


def _invest_all_of() -> List[Dict[str, Any]]:
    return [
        {"properties": {"results": {"contains": {"properties": {"id": {"enum": ids}}, "required": ["id"]}}},
         "errorMessage": f"INVEST '{dim}' не подтверждён: нет оценки критериев {', '.join(ids)}"}
        for dim, ids in INVEST_MAP.items()
    ]


# ---------------------------------------------------------------- Seam 1: Jira input

class JiraIssueType(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str = Field(min_length=1)


class JiraIssueFields(BaseModel):
    model_config = ConfigDict(extra="allow")
    summary: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    issuetype: JiraIssueType
    labels: List[str] = Field(default_factory=list)


class JiraIssueContract(BaseModel):
    """Structure of `GET /rest/api/2/issue/{key}` that the DoR gate relies on."""
    model_config = ConfigDict(extra="allow")
    key: str = Field(pattern=ISSUE_KEY_PATTERN)
    fields: JiraIssueFields


# ---------------------------------------------------------------- Seam 1: DoR LLM/rules output

class DorCriterionResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str = Field(pattern=r"^[A-Z]{1,2}\d{2}$")
    title: str = Field(min_length=1)
    mandatory: bool
    status: Literal["pass", "partial", "fail"]
    comment: str = Field(min_length=1)


class DorVerdictContract(BaseModel):
    model_config = ConfigDict(extra="allow", json_schema_extra={"allOf": _invest_all_of()})
    issueKey: str = Field(pattern=ISSUE_KEY_PATTERN)
    passed: bool
    score: int = Field(ge=0, le=100)
    results: List[DorCriterionResult] = Field(min_length=7)
    commentBody: str = Field(min_length=50, pattern=r"\[Этап 1 из \d+\]")
    commentMethod: Literal["POST", "PUT"]
    commentUrl: str = Field(pattern=r"^https://[^\s]+/rest/api/2/issue/[A-Z][A-Z0-9]+-\d+/comment(/\d+)?$")

    @model_validator(mode="after")
    def _invest_coverage(self):
        evaluated = {r.id for r in self.results}
        missing = [f"{dim}({'/'.join(ids)})" for dim, ids in INVEST_MAP.items() if not evaluated.intersection(ids)]
        if missing:
            raise ValueError(f"INVEST-критерии не оценены: {', '.join(missing)}")
        return self


# ---------------------------------------------------------------- Seam 2: test design

class CaseStep(BaseModel):
    model_config = ConfigDict(extra="allow")
    action: str = Field(min_length=3)
    data: str = ""
    expected_result: str = Field(min_length=3)


class CaseContract(BaseModel):
    """Test case as produced by 08_format_testcases.js before it is written to Qase."""
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "anyOf": [
                {"properties": {"tags": {"contains": {"enum": SUITE_TAGS}}}},
                {"properties": {"type": {"enum": SUITE_TYPES}}},
            ],
            "errorMessage": "Нет обязательного тега набора (Smoke/Regress)",
        },
    )
    title: str = Field(min_length=10)
    description: str = Field(min_length=20)
    covers: List[str] = Field(min_length=1)
    type: Literal["functional", "smoke", "regression", "security", "usability", "performance", "acceptance", "compatibility", "integration"]
    severity: Literal["blocker", "critical", "major", "normal", "minor", "trivial"]
    priority: Literal["high", "medium", "low"]
    layer: Literal["e2e", "api", "unit"]
    behavior: Literal["positive", "negative", "destructive"] = "positive"
    automation: Literal["to-be-automated", "manual", "automated"]
    tags: List[str] = Field(min_length=1)
    preconditions: str = ""
    steps: List[CaseStep] = Field(min_length=1)

    @model_validator(mode="after")
    def _suite_tag(self):
        tags = {t.lower() for t in self.tags}
        if not tags.intersection(SUITE_TAGS) and self.type not in SUITE_TYPES:
            raise ValueError("Нет обязательного тега набора (Smoke/Regress)")
        return self


class QaseCaseContract(BaseModel):
    """A case fetched from Qase TMS (GET /v1/case) — the input of the Python design gate."""
    model_config = ConfigDict(extra="allow")
    id: int
    title: str = Field(min_length=5)
    automation: int = Field(ge=0, le=2)
    priority: int = Field(ge=0, le=3)
    severity: int = Field(ge=0, le=6)
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[Dict[str, Any]] = Field(default_factory=list)


CONTRACTS = {
    "jira_issue": JiraIssueContract,
    "dor_verdict": DorVerdictContract,
    "test_case": CaseContract,
}


class ContractResult(BaseModel):
    contract: str
    valid: bool
    violations: List[str] = Field(default_factory=list)


def validate(contract: str, payload: Any) -> ContractResult:
    model = CONTRACTS[contract]
    try:
        model.model_validate(payload)
        return ContractResult(contract=contract, valid=True)
    except ValidationError as exc:
        violations = [f"{'.'.join(str(p) for p in err['loc']) or '<root>'}: {err['msg']}" for err in exc.errors()]
        return ContractResult(contract=contract, valid=False, violations=violations)


def export_schemas(target: Path = CONTRACTS_DIR) -> List[Path]:
    target.mkdir(parents=True, exist_ok=True)
    written = []
    for name, model in CONTRACTS.items():
        path = target / f"{name}.schema.json"
        path.write_text(json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(path)
    meta = {"investMap": INVEST_MAP, "suiteTags": SUITE_TAGS, "suiteTypes": SUITE_TYPES, "automationFlags": AUTOMATION_FLAGS}
    meta_path = target / "contract_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    written.append(meta_path)
    return written


def main():
    parser = argparse.ArgumentParser(description="QAOps data contracts")
    parser.add_argument("--export", action="store_true", help="Export JSON Schemas for n8n guard nodes")
    parser.add_argument("--validate", choices=list(CONTRACTS), help="Validate a JSON file against a contract")
    parser.add_argument("--file", type=Path)
    args = parser.parse_args()

    if args.export:
        for p in export_schemas():
            print(f"✅ {p.relative_to(BASE_DIR)}")
    elif args.validate and args.file:
        res = validate(args.validate, json.loads(args.file.read_text(encoding="utf-8")))
        print(res.model_dump_json(indent=2))
        raise SystemExit(0 if res.valid else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
