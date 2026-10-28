"""Enterprise PromptOps Registry with versioning, rollbacks, and multi-tenant customization."""

import os
from pathlib import Path
from typing import Any, ClassVar


class PromptRegistry:
    """Central registry for managing, versioning, and deploying LLM prompts."""

    DEFAULT_VERSIONS: ClassVar[dict[str, str]] = {
        "dor_evaluation": "v2.0_enterprise",
        "test_design_audit": "v2.0_enterprise",
        "code_review_audit": "v2.0_enterprise",
        "delta_refinement": "v2.0_enterprise",
    }

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = Path(base_dir or Path(__file__).resolve().parent)

    def list_domains(self) -> list[str]:
        """Returns all registered prompt domains."""
        return [
            d.name
            for d in self.base_dir.iterdir()
            if d.is_dir() and not d.name.startswith((".", "_"))
        ]

    def list_versions(self, domain: str) -> list[str]:
        """Lists available versions for a specific domain, sorted chronologically."""
        domain_dir = self.base_dir / domain
        if not domain_dir.exists():
            return []
        versions = [f.stem for f in domain_dir.glob("*.md")]
        return sorted(versions)

    def get_active_version(self, domain: str) -> str:
        """Determines active version for a domain via ENV override or default."""
        env_key = f"PROMPT_VERSION_{domain.upper()}"
        return os.getenv(env_key) or self.DEFAULT_VERSIONS.get(domain, "v2.0_enterprise")

    def get_raw_template(self, domain: str, version: str | None = None) -> str:
        """Loads raw markdown prompt template for a given domain and version."""
        ver = version or self.get_active_version(domain)
        target_file = self.base_dir / domain / f"{ver}.md"

        if not target_file.exists():
            # Fallback to baseline if requested version doesn't exist
            baseline_file = self.base_dir / domain / "v1.0_baseline.md"
            if baseline_file.exists():
                return baseline_file.read_text(encoding="utf-8")
            raise FileNotFoundError(f"Prompt '{ver}' not found in domain '{domain}' at {target_file}")

        return target_file.read_text(encoding="utf-8")

    def render(self, domain: str, version: str | None = None, **kwargs: Any) -> str:
        """Renders prompt template with provided variables."""
        template = self.get_raw_template(domain, version)
        # Safe replacement for variables
        rendered = template
        for key, value in kwargs.items():
            rendered = rendered.replace(f"{{{key}}}", str(value))
        return rendered


# Global singleton instance
registry = PromptRegistry()


def get_prompt(domain: str, version: str | None = None, **kwargs: Any) -> str:
    """Convenience helper to render a prompt."""
    return registry.render(domain, version, **kwargs)
