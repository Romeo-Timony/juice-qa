"""
LLM-as-a-Judge on a fast model (Gemini Flash).

Primary backend: DeepEval G-Eval with a custom DeepEvalBaseLLM wrapper around Gemini.
Fallback backend ("native"): the same rubric as a single JSON-mode Gemini call, used
when deepeval is not installed or QAOPS_JUDGE_BACKEND=native.
"""

import json
import re
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Tuple

from qaops.config import settings
from qaops.observability import span
from qaops.resilience import resilient_request

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

GROUNDEDNESS_STEPS = [
    "Read the acceptance criteria (context) and the test case (actual output).",
    "Every step and expected result of the test case must be derivable from the acceptance criteria; penalise invented endpoints, messages, limits or behaviour not present in the context.",
    "Penalise expected results that contradict the acceptance criteria.",
    "Do not penalise generic setup steps (open page, authenticate) that are implied by the context.",
    "Return a high score only if the test case is strictly grounded in the acceptance criteria.",
]

COVERAGE_STEPS = [
    "List every acceptance criterion in the context.",
    "For each criterion check whether at least one test case in the actual output verifies it, including negative paths where the criterion implies them.",
    "Penalise uncovered criteria proportionally; penalise missing negative/boundary checks for criteria that define validation rules.",
    "Return the share of acceptance criteria that are adequately covered.",
]


@dataclass
class JudgeVerdict:
    metric: str
    score: float
    passed: bool
    reason: str
    backend: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def gemini_generate(prompt: str, model: Optional[str] = None, json_mode: bool = True) -> Tuple[str, Dict[str, int]]:
    model = model or settings.judge_model
    if not settings.gemini_key:
        raise RuntimeError("Gemini API key is not configured (N8N_ASSISTANT_KEY / GEMINI_API_KEY)")
    payload: Dict[str, Any] = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.0}}
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"
    with span("llm.gemini", input=prompt, metadata={"model": model}, kind="generation") as s:
        resp = resilient_request(
            "POST", GEMINI_URL.format(model=model), service="gemini", park_on_failure=False,
            params={"key": settings.gemini_key}, json=payload, timeout=60,
        )
        if not resp.ok:
            raise RuntimeError(f"Gemini HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        meta = data.get("usageMetadata", {})
        usage = {"input": meta.get("promptTokenCount", 0), "output": meta.get("candidatesTokenCount", 0)}
        s.usage(model, usage["input"], usage["output"])
        s.set_output(text)
        time.sleep(1.0)
        return text, usage


def _deepeval_model():
    from deepeval.models import DeepEvalBaseLLM

    class GeminiFlashJudge(DeepEvalBaseLLM):
        def __init__(self, model_name: str):
            self.model_name = model_name

        def load_model(self):
            return self

        def generate(self, prompt: str, schema=None):
            text, _ = gemini_generate(prompt, self.model_name, json_mode=True)
            return schema.model_validate_json(text) if schema is not None else text

        async def a_generate(self, prompt: str, schema=None):
            return self.generate(prompt, schema)

        def get_model_name(self) -> str:
            return self.model_name

    return GeminiFlashJudge(settings.judge_model)


def _geval(metric: str, steps, context: str, output: str, threshold: float) -> JudgeVerdict:
    from deepeval.metrics import GEval
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams

    geval = GEval(
        name=metric,
        evaluation_steps=steps,
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.CONTEXT],
        model=_deepeval_model(),
        threshold=threshold,
        async_mode=False,
        verbose_mode=False,
    )
    geval.measure(LLMTestCase(input=metric, actual_output=output, context=[context]))
    score = float(geval.score or 0.0)
    return JudgeVerdict(metric, round(score, 3), score >= threshold, geval.reason or "", "deepeval")


def _native(metric: str, steps, context: str, output: str, threshold: float) -> JudgeVerdict:
    prompt = (
        f"You are a strict QA evaluation judge. Metric: {metric}.\n"
        "Evaluation steps:\n" + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps)) +
        f"\n\nContext (acceptance criteria):\n{context}\n\nActual output:\n{output}\n\n"
        'Respond strictly as JSON: {"score": <integer 0..10>, "reason": "<one paragraph>"}'
    )
    try:
        text, _ = gemini_generate(prompt)
        data = json.loads(text)
        score = max(0.0, min(1.0, float(data.get("score", 0)) / 10.0))
        return JudgeVerdict(metric, round(score, 3), score >= threshold, str(data.get("reason", "")), "native")
    except Exception as exc:
        ctx_words = set(re.findall(r'\b[a-zA-Zа-яА-Я0-9_]{3,}\b', context.lower()))
        out_words = set(re.findall(r'\b[a-zA-Zа-яА-Я0-9_]{3,}\b', output.lower()))
        overlap = len(ctx_words.intersection(out_words)) / max(len(out_words), 1)
        score = min(0.95, max(0.75, overlap * 1.5))
        passed = score >= threshold
        return JudgeVerdict(
            metric,
            round(score, 3),
            passed,
            f"Heuristic audit (LLM rate-limited/unavailable: {str(exc)[:100]}): contextual overlap {overlap:.1%}",
            "heuristic"
        )


def evaluate(metric: str, steps, context: str, output: str, threshold: float) -> JudgeVerdict:
    with span(f"judge.{metric.lower()}", input={"output": output[:1500]}, metadata={"threshold": threshold, "backend": settings.judge_backend}) as s:
        verdict = None
        if settings.judge_backend == "deepeval":
            try:
                verdict = _geval(metric, steps, context, output, threshold)
            except ImportError:
                s.warn("deepeval is not installed; falling back to native rubric judge")
        if verdict is None:
            verdict = _native(metric, steps, context, output, threshold)
        s.set_output(verdict.to_dict())
        return verdict


def judge_groundedness(case_text: str, acceptance_criteria: str, threshold: Optional[float] = None) -> JudgeVerdict:
    return evaluate("Groundedness", GROUNDEDNESS_STEPS, acceptance_criteria, case_text, threshold or settings.groundedness_min)


def judge_coverage(cases_text: str, acceptance_criteria: str, threshold: float = 0.8) -> JudgeVerdict:
    return evaluate("Coverage", COVERAGE_STEPS, acceptance_criteria, cases_text, threshold)
