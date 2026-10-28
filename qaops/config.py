import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    base_dir: Path = BASE_DIR
    db_path: Path = Path(os.getenv("QAOPS_DB_PATH") or BASE_DIR / "data" / "qa_pipeline.db")
    trace_log: Path = Path(os.getenv("QAOPS_TRACE_LOG") or BASE_DIR / "logs" / "qaops_traces.jsonl")

    jira_url: str = (os.getenv("ATLASSIAN_BASE_URL") or "https://romeo-timony.atlassian.net").rstrip("/")
    jira_email: str = os.getenv("ATLASSIAN_USER_EMAIL", "")
    jira_token: str = os.getenv("ATLASSIAN_API_TOKEN", "")

    gemini_key: str = os.getenv("N8N_ASSISTANT_KEY") or os.getenv("GEMINI_API_KEY", "")
    judge_model: str = os.getenv("QAOPS_JUDGE_MODEL") or os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    judge_backend: str = os.getenv("QAOPS_JUDGE_BACKEND", "native")

    langfuse_host: str = (os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com").rstrip("/")
    langfuse_public_key: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret_key: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    langfuse_project_id: str = os.getenv("LANGFUSE_PROJECT_ID", "")

    # Quality thresholds (targets from the QAOps assignment)
    design_integrity_min: float = _float("QAOPS_DESIGN_INTEGRITY_MIN", 0.90)
    groundedness_min: float = _float("QAOPS_GROUNDEDNESS_MIN", 0.70)
    recovery_rate_min: float = _float("QAOPS_RECOVERY_RATE_MIN", 0.85)

    # Resilience
    retry_attempts: int = _int("QAOPS_RETRY_ATTEMPTS", 5)
    retry_base_delay: float = _float("QAOPS_RETRY_BASE_DELAY", 1.0)
    retry_max_delay: float = _float("QAOPS_RETRY_MAX_DELAY", 30.0)
    breaker_threshold: int = _int("QAOPS_BREAKER_THRESHOLD", 5)
    breaker_cooldown: float = _float("QAOPS_BREAKER_COOLDOWN", 60.0)

    # Code gate: auto | docker | local
    collect_runtime: str = os.getenv("QAOPS_COLLECT_RUNTIME", "auto")
    require_docker: bool = os.getenv("QAOPS_REQUIRE_DOCKER", "0") == "1"
    collect_image: str = os.getenv("QAOPS_COLLECT_IMAGE", "juice-qa-collect:latest")

    paused_label: str = "qa-paused"
    rework_label: str = "qa-code-rework"
    required_suite_tags: frozenset = field(default_factory=lambda: frozenset({"smoke", "regress", "regression", "fast-regression", "full-regression"}))

    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)

    @property
    def jira_auth(self):
        return (self.jira_email, self.jira_token)


settings = Settings()
