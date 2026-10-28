"""
WireMock Standalone Management and Client for Hermetic SDET Testing.
Provides lifecycle management for WireMock Java standalone process,
dynamic stub injection, request verification, and fault simulation
(delays, HTTP 429, HTTP 503) for Circuit Breaker & Outbox resilience testing.
"""

import json
import logging
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger("wiremock")

WIREMOCK_DIR = Path(__file__).parent.resolve()
STANDALONE_JAR = WIREMOCK_DIR / "wiremock-standalone.jar"
MAPPINGS_DIR = WIREMOCK_DIR / "mappings"
FILES_DIR = WIREMOCK_DIR / "__files"

MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class WireMockServer:
    def __init__(self, port: Optional[int] = None, root_dir: Optional[Path] = None):
        self.port = port or find_free_port()
        self.root_dir = root_dir or WIREMOCK_DIR
        self.process: Optional[subprocess.Popen] = None
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.admin_url = f"{self.base_url}/__admin"

    def is_running(self) -> bool:
        if self.process is not None and self.process.poll() is None:
            try:
                r = requests.get(f"{self.admin_url}/mappings", timeout=1.0)
                return r.status_code == 200
            except Exception:
                return False
        return False

    def start(self, timeout_sec: float = 15.0) -> "WireMockServer":
        if self.is_running():
            return self

        if not STANDALONE_JAR.exists():
            raise FileNotFoundError(f"WireMock standalone JAR not found at {STANDALONE_JAR}")

        cmd = [
            "java",
            "-jar",
            str(STANDALONE_JAR),
            "--port",
            str(self.port),
            "--root-dir",
            str(self.root_dir),
        ]

        logger.info("Starting WireMock on port %d...", self.port)
        log_file = WIREMOCK_DIR / "wiremock.log"
        self._log_fh = open(log_file, "w", encoding="utf-8")
        self.process = subprocess.Popen(
            cmd,
            stdout=self._log_fh,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )

        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            try:
                r = requests.get(f"{self.admin_url}/mappings", timeout=1.0)
                if r.status_code == 200:
                    logger.info("WireMock is ready at %s", self.base_url)
                    return self
            except Exception:
                time.sleep(0.3)

        self.stop()
        raise TimeoutError(f"WireMock failed to start on port {self.port} within {timeout_sec}s")

    def stop(self) -> None:
        if self.process is not None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5.0)
            except Exception:
                self.process.kill()
            finally:
                self.process = None
                if hasattr(self, "_log_fh") and self._log_fh:
                    try:
                        self._log_fh.close()
                    except Exception:
                        pass
                logger.info("WireMock on port %d stopped", self.port)

    def reset(self) -> None:
        """Clear all in-memory mappings and request logs."""
        requests.post(f"{self.admin_url}/reset", timeout=3.0)

    def stub_for(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamically register a stub mapping in WireMock."""
        r = requests.post(f"{self.admin_url}/mappings", json=mapping, timeout=3.0)
        r.raise_for_status()
        return r.json()

    def get_requests(self) -> List[Dict[str, Any]]:
        """Retrieve recorded requests matching criteria."""
        r = requests.get(f"{self.admin_url}/requests", timeout=3.0)
        r.raise_for_status()
        return r.json().get("requests", [])

    def verify_request(self, method: str, url_path: str, count: int = 1) -> bool:
        """Verify that a request was received `count` times."""
        body = {
            "method": method.upper(),
            "urlPath": url_path,
        }
        r = requests.post(f"{self.admin_url}/requests/count", json=body, timeout=3.0)
        r.raise_for_status()
        actual_count = r.json().get("count", 0)
        return actual_count == count

    def stub_juice_shop_auth(self, email: str = "admin@juice-sh.op", token: str = "mock-jwt-token-12345") -> None:
        """Helper to stub standard Juice Shop login."""
        self.stub_for({
            "request": {
                "method": "POST",
                "urlPath": "/rest/user/login",
                "bodyPatterns": [
                    {"matchesJsonPath": f"$[?(@.email == '{email}')]"}
                ]
            },
            "response": {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "jsonBody": {
                    "authentication": {
                        "token": token,
                        "bid": 1,
                        "umail": email
                    }
                }
            }
        })

    def stub_fault_injection(self, url_path: str, status_code: int = 503, retry_after: int = 2) -> None:
        """Helper to inject 503/429 faults for Circuit Breaker and Retry testing."""
        self.stub_for({
            "request": {
                "urlPath": url_path,
            },
            "response": {
                "status": status_code,
                "headers": {
                    "Content-Type": "application/json",
                    "Retry-After": str(retry_after),
                },
                "jsonBody": {
                    "error": "Simulated Fault Injection by WireMock",
                    "status": status_code,
                }
            }
        })

    def __enter__(self) -> "WireMockServer":
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
