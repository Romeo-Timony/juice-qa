"""
Isolated Integration Tests using WireMock Standalone Server.
Validates:
1. Hermetic HTTP API interactions (JuiceShopApiClient against WireMock stubs).
2. Fault injection testing for Seam 4 (Circuit Breaker & Outbox resilience).
3. Request verification and contract fidelity.
"""

import os
import time
import pytest
import requests

from wiremock.server import WireMockServer
from api.client import JuiceShopApiClient
from qaops import resilience, store
from qaops.resilience import resilient_request


@pytest.fixture(scope="module")
def wiremock_instance():
    from qaops.observability import Trace
    orig_flush = Trace.flush
    Trace.flush = lambda self: True
    server = WireMockServer()
    server.start(timeout_sec=15.0)
    yield server
    server.stop()
    Trace.flush = orig_flush


def test_wiremock_health_and_mappings(wiremock_instance: WireMockServer):
    assert wiremock_instance.is_running()
    req = requests.get(f"{wiremock_instance.admin_url}/mappings", timeout=3.0)
    assert req.status_code == 200
    data = req.json()
    assert "mappings" in data
    names = [m.get("name") for m in data["mappings"]]
    assert "Juice Shop - User Login" in names
    assert "Juice Shop - User Registration" in names


def test_isolated_api_client_login(wiremock_instance: WireMockServer):
    client = JuiceShopApiClient(base_url=wiremock_instance.base_url)
    res = client.login("admin@juice-sh.op", "any_password")
    
    assert res.status_code == 200
    json_data = res.json()
    assert "authentication" in json_data
    token = json_data["authentication"]["token"]
    assert token == "wiremock-mock-jwt-token-sdet-633"
    assert client.token == token
    assert client.session.headers["Authorization"] == f"Bearer {token}"
    assert wiremock_instance.verify_request("POST", "/rest/user/login", count=1)


def test_isolated_api_client_registration(wiremock_instance: WireMockServer):
    client = JuiceShopApiClient(base_url=wiremock_instance.base_url)
    res = client.register("new_shopper@juice-sh.op", "Pass1234!", 1, "Answer")
    
    assert res.status_code == 201
    json_data = res.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["email"] == "new_shopper@juice-sh.op"
    assert wiremock_instance.verify_request("POST", "/api/Users/", count=1)


def test_isolated_circuit_breaker_fault_injection(wiremock_instance: WireMockServer):
    fault_path = "/api/fault-test"
    wiremock_instance.stub_fault_injection(fault_path, status_code=503, retry_after=1)
    
    url = f"{wiremock_instance.base_url}{fault_path}"
    
    # Store initial state
    service = resilience.service_of(url)
    
    # Execute resilient request with attempts=2 and no-op sleep
    with pytest.raises(resilience.TransientFailure) as exc_info:
        resilient_request("GET", url, attempts=2, sleep=lambda _: None)
    
    assert "failed after 2 attempts: HTTP 503" in str(exc_info.value)
    
    # WireMock verified that 2 attempts were received
    requests_received = wiremock_instance.get_requests()
    matching = [r for r in requests_received if r["request"]["url"] == fault_path]
    assert len(matching) == 2
