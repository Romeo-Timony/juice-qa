"""Unit tests for PromptOps registry and versioning system."""

import pytest

from prompts.registry import PromptRegistry, get_prompt


@pytest.fixture
def custom_registry(tmp_path):
    domain_dir = tmp_path / "custom_domain"
    domain_dir.mkdir()
    (domain_dir / "v1.0_baseline.md").write_text("Hello {name}, baseline v1", encoding="utf-8")
    (domain_dir / "v2.0_enterprise.md").write_text("Greetings {name}, enterprise v2", encoding="utf-8")
    return PromptRegistry(base_dir=tmp_path)


def test_list_domains_and_versions(custom_registry):
    domains = custom_registry.list_domains()
    assert "custom_domain" in domains

    versions = custom_registry.list_versions("custom_domain")
    assert versions == ["v1.0_baseline", "v2.0_enterprise"]


def test_render_default_and_explicit_version(custom_registry):
    # Default is enterprise v2
    text_v2 = custom_registry.render("custom_domain", name="Alice")
    assert text_v2 == "Greetings Alice, enterprise v2"

    # Explicit baseline v1
    text_v1 = custom_registry.render("custom_domain", version="v1.0_baseline", name="Bob")
    assert text_v1 == "Hello Bob, baseline v1"


def test_env_version_override(custom_registry, monkeypatch):
    monkeypatch.setenv("PROMPT_VERSION_CUSTOM_DOMAIN", "v1.0_baseline")
    text = custom_registry.render("custom_domain", name="Charlie")
    assert text == "Hello Charlie, baseline v1"


def test_production_prompts_exist_and_render():
    # Verify all 4 enterprise production domains exist and render properly
    for domain in ["dor_evaluation", "test_design_audit", "code_review_audit", "delta_refinement"]:
        rendered = get_prompt(domain, issue_key="JS-999", context="Test AC", code_snippets="def test_foo(): pass")
        assert len(rendered) > 50
        assert "JS-999" in rendered or "{issue_key}" not in rendered
