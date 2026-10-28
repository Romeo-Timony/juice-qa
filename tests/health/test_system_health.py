"""Pre-flight Infrastructure & System Readiness Autotests (SDET Best Practices).

Verifies that all distributed services, databases, orchestrators, webhooks,
and daemons are live, responsive, and ready before any task is processed.
"""

import allure

from qaops import health


@allure.epic("QAOps Infrastructure")
@allure.feature("Pre-flight Readiness Gate")
class TestInfrastructureHealth:

    @allure.story("Juice Shop SUT Liveness")
    def test_juice_shop_sut_is_ready(self):
        result = health.check_juice_shop()
        assert result.status == "PASS", f"Juice Shop SUT is not ready: {result.details}"
        assert result.latency_ms < 3000, f"Juice Shop SUT response latency too high: {result.latency_ms}ms"

    @allure.story("n8n Orchestrator & Workflows Readiness")
    def test_n8n_main_workflow_is_active(self):
        result = health.check_n8n()
        assert result.status == "PASS", f"n8n Main Workflow is not active: {result.details}"

    @allure.story("n8n Global Error Handler Readiness")
    def test_n8n_global_error_handler_is_active(self):
        result = health.check_n8n_error_handler()
        assert result.is_ok, f"n8n Error Handler failed: {result.details}"

    @allure.story("ngrok Ingress Webhook Tunnel")
    def test_ngrok_ingress_tunnel_is_online(self):
        result = health.check_ngrok_ingress()
        assert result.status == "PASS", f"ngrok ingress tunnel down: {result.details}"

    @allure.story("Jira Cloud REST API & Permissions")
    def test_jira_api_is_reachable(self):
        result = health.check_jira_api()
        assert result.status == "PASS", f"Jira Cloud API connection failed: {result.details}"

    @allure.story("Telegram QA Bot Connectivity")
    def test_telegram_bot_is_online(self):
        result = health.check_telegram_bot()
        assert result.status == "PASS", f"Telegram bot check failed: {result.details}"

    @allure.story("Qase TMS API Access")
    def test_qase_tms_is_accessible(self):
        result = health.check_qase_tms()
        assert result.status == "PASS", f"Qase TMS connection failed: {result.details}"

    @allure.story("Gemini LLM Judge Readiness")
    def test_gemini_llm_judge_is_responsive(self):
        result = health.check_gemini_llm()
        assert result.status in ("PASS", "WARN"), f"Gemini LLM Judge blocked: {result.details}"

    @allure.story("Event Store Database Integrity")
    def test_sqlite_event_store_integrity(self):
        result = health.check_sqlite_event_store()
        assert result.status == "PASS", f"SQLite Event Store failed: {result.details}"

    @allure.story("QA Agent Daemon Heartbeat")
    def test_qa_agent_daemon_is_looping(self):
        result = health.check_qa_agent_daemon()
        assert result.status == "PASS", f"QA Agent Daemon is not running or heartbeat is stale: {result.details}"

    @allure.story("Full System Aggregated Gate")
    def test_full_system_readiness_gate(self):
        report = health.run_all_health_checks()
        assert report.is_healthy, f"System readiness gate rejected: {report.critical_failures}"
