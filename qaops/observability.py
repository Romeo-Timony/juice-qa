"""
Seam 6: observability-first tracing.

Every seam opens a span via `trace()` / `span()`. Spans are always persisted locally
(JSONL + SQLite `qaops_spans`) and, when LANGFUSE_PUBLIC_KEY/SECRET_KEY are set,
shipped to Langfuse through its public ingestion API. Inputs/outputs are PII-redacted.
"""

import contextvars
import functools
import json
import re
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

import requests

from qaops import store
from qaops.config import settings

_MAX_STR = 4000
_REDACTIONS = [
    (re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"), "<JWT>"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{12,}"), "Bearer <TOKEN>"),
    (re.compile(r"ATATT[A-Za-z0-9_\-=]{20,}"), "<ATLASSIAN_TOKEN>"),
    (re.compile(r"(?i)([?&](?:key|token|api_key)=)[^&\s\"']+"), r"\1<SECRET>"),
    (re.compile(r"\bAQ\.[A-Za-z0-9_\-]{20,}"), "<API_KEY>"),
    (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "<EMAIL>"),
    (re.compile(r"(?<!\d)\+?\d[\d\s\-()]{9,16}\d(?!\d)"), "<PHONE>"),
]

_current: contextvars.ContextVar = contextvars.ContextVar("qaops_current", default=None)


def redact(value: Any) -> Any:
    if isinstance(value, str):
        for pattern, repl in _REDACTIONS:
            value = pattern.sub(repl, value)
        return value if len(value) <= _MAX_STR else value[:_MAX_STR] + f"…<truncated {len(value) - _MAX_STR}>"
    if isinstance(value, dict):
        return {k: ("<SECRET>" if re.search(r"(?i)token|secret|password|api_key|authorization", str(k)) else redact(v)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value[:200]]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return redact(str(value))


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


class Span:
    def __init__(self, tracer: "Trace", name: str, parent_id: Optional[str], kind: str, input: Any, metadata: Optional[Dict[str, Any]]):
        self.tracer = tracer
        self.id = uuid.uuid4().hex
        self.name = name
        self.parent_id = parent_id
        self.kind = kind
        self.input = input
        self.output: Any = None
        self.metadata: Dict[str, Any] = dict(metadata or {})
        self.level = "DEFAULT"
        self.status_message: Optional[str] = None
        self.iterations = 1
        self.model: Optional[str] = None
        self.input_tokens = 0
        self.output_tokens = 0
        self.start = time.time()
        self.end: Optional[float] = None

    def set_output(self, output: Any) -> None:
        self.output = output

    def usage(self, model: str, input_tokens: int = 0, output_tokens: int = 0) -> None:
        self.kind = "generation"
        self.model = model
        self.input_tokens += int(input_tokens or 0)
        self.output_tokens += int(output_tokens or 0)

    def error(self, message: str) -> None:
        self.level = "ERROR"
        self.status_message = message[:1000]

    def warn(self, message: str) -> None:
        if self.level != "ERROR":
            self.level = "WARNING"
        self.status_message = message[:1000]

    @property
    def latency_ms(self) -> float:
        return ((self.end or time.time()) - self.start) * 1000

    def to_event(self) -> Dict[str, Any]:
        body = {
            "id": self.id,
            "traceId": self.tracer.id,
            "parentObservationId": self.parent_id,
            "name": self.name,
            "startTime": _iso(self.start),
            "endTime": _iso(self.end or time.time()),
            "input": redact(self.input),
            "output": redact(self.output),
            "metadata": redact({**self.metadata, "iterations": self.iterations, "latency_ms": round(self.latency_ms, 1)}),
            "level": self.level,
            "statusMessage": self.status_message,
        }
        if self.kind == "generation":
            body["model"] = self.model
            body["usage"] = {"input": self.input_tokens, "output": self.output_tokens, "total": self.input_tokens + self.output_tokens, "unit": "TOKENS"}
        return {"id": uuid.uuid4().hex, "timestamp": _iso(time.time()), "type": f"{self.kind}-create", "body": body}


class Trace:
    def __init__(self, name: str, issue_key: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None, tags: Optional[List[str]] = None):
        self.id = uuid.uuid4().hex
        self.name = name
        self.issue_key = issue_key
        self.metadata = dict(metadata or {})
        self.tags = list(tags or [])
        self.input: Any = None
        self.output: Any = None
        self.start = time.time()
        self._events: List[Dict[str, Any]] = []

    @property
    def url(self) -> str:
        if settings.langfuse_enabled:
            if settings.langfuse_project_id:
                return f"{settings.langfuse_host}/project/{settings.langfuse_project_id}/traces/{self.id}"
            return f"{settings.langfuse_host}/trace/{self.id}"
        return f"local://{settings.trace_log.name}#{self.id}"

    def _record(self, span: Span) -> None:
        event = span.to_event()
        self._events.append(event)
        _write_local(event, span, self)

    def trace_event(self) -> Dict[str, Any]:
        return {
            "id": uuid.uuid4().hex,
            "timestamp": _iso(self.start),
            "type": "trace-create",
            "body": {
                "id": self.id,
                "name": self.name,
                "sessionId": self.issue_key,
                "timestamp": _iso(self.start),
                "input": redact(self.input),
                "output": redact(self.output),
                "metadata": redact({**self.metadata, "issue_key": self.issue_key}),
                "tags": self.tags + (["issue:" + self.issue_key] if self.issue_key else []),
            },
        }

    def flush(self) -> bool:
        batch = [self.trace_event()] + self._events
        _append_jsonl(batch[0])
        self._events = []
        if not settings.langfuse_enabled:
            return False
        try:
            res = requests.post(
                f"{settings.langfuse_host}/api/public/ingestion",
                auth=(settings.langfuse_public_key, settings.langfuse_secret_key),
                json={"batch": batch},
                timeout=10,
            )
            return res.status_code in (200, 207)
        except requests.RequestException:
            return False


def _append_jsonl(event: Dict[str, Any]) -> None:
    try:
        settings.trace_log.parent.mkdir(parents=True, exist_ok=True)
        with settings.trace_log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass


def _write_local(event: Dict[str, Any], span: Span, tr: Trace) -> None:
    _append_jsonl(event)
    try:
        with store.connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO qaops_spans
                (id, trace_id, parent_id, issue_key, name, kind, level, latency_ms, iterations, input_tokens, output_tokens, model, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (span.id, tr.id, span.parent_id, tr.issue_key, span.name, span.kind, span.level, span.latency_ms, span.iterations,
                 span.input_tokens, span.output_tokens, span.model, json.dumps(redact(span.metadata), ensure_ascii=False, default=str), store.now_iso()),
            )
    except Exception:
        pass


@contextmanager
def trace(name: str, issue_key: Optional[str] = None, input: Any = None, metadata: Optional[Dict[str, Any]] = None, tags: Optional[List[str]] = None) -> Iterator[Trace]:
    """Root trace for one pipeline run of an issue. Nested `span()` calls attach to it automatically."""
    tr = Trace(name, issue_key, metadata, tags)
    tr.input = input
    token = _current.set((tr, None))
    try:
        yield tr
    finally:
        _current.reset(token)
        tr.flush()


def current_trace() -> Optional[Trace]:
    cur = _current.get()
    return cur[0] if cur else None


@contextmanager
def span(name: str, input: Any = None, metadata: Optional[Dict[str, Any]] = None, kind: str = "span") -> Iterator[Span]:
    """Span within the current trace. Without an active trace, opens an ad-hoc one so nothing is lost."""
    cur = _current.get()
    if cur is None:
        with trace(name, metadata={"adhoc": True}) as tr:
            with span(name, input, metadata, kind) as s:
                yield s
                tr.output = s.output
        return
    tr, parent_id = cur
    s = Span(tr, name, parent_id, kind, input, metadata)
    token = _current.set((tr, s.id))
    try:
        yield s
    except Exception as exc:
        s.error(f"{type(exc).__name__}: {exc}")
        raise
    finally:
        _current.reset(token)
        s.end = time.time()
        tr._record(s)


def traced(name: Optional[str] = None):
    """Decorator: wraps a function call into a span with redacted args/result."""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with span(name or fn.__qualname__, input={"args": args[:5], "kwargs": kwargs}) as s:
                result = fn(*args, **kwargs)
                s.set_output(result)
                return result
        return wrapper
    return deco
