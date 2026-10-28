"""
OpenAPI / Swagger Contract Validator for OWASP Juice Shop.
Protects against API Drift by fetching the live OpenAPI 3.0 spec from
/api-docs/swagger-ui-init.js (or cached fallback), and verifying that
responses and Pydantic models conform to the expected schema.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger("openapi_validator")
BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_FILE = BASE_DIR / "wiremock" / "__files" / "openapi_spec.json"


def fetch_openapi_spec(base_url: str = "http://localhost:3000") -> Dict[str, Any]:
    """Fetches OpenAPI 3.0 spec from Juice Shop's Swagger endpoint or cached file."""
    url = f"{base_url.rstrip('/')}/api-docs/swagger-ui-init.js"
    try:
        r = requests.get(url, timeout=5.0)
        if r.status_code == 200 and "swaggerDoc" in r.text:
            idx = r.text.find('"swaggerDoc":')
            if idx != -1:
                brace_start = r.text.find('{', idx)
                custom_opt = r.text.find('"customOptions":', brace_start)
                if brace_start != -1 and custom_opt != -1:
                    brace_end = r.text.rfind('}', brace_start, custom_opt)
                    if brace_end != -1:
                        raw = r.text[brace_start:brace_end + 1]
                        doc = json.loads(raw)
                        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
                        CACHE_FILE.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
                        return doc
    except Exception as exc:
        logger.warning("Could not fetch live OpenAPI spec: %s", exc)

    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))

    return {"openapi": "3.0.0", "paths": {}}


def get_endpoint_schema(spec: Dict[str, Any], path: str, method: str = "get", status_code: int = 200) -> Optional[Dict[str, Any]]:
    """Retrieves the JSON schema for an endpoint response from OpenAPI spec."""
    paths = spec.get("paths", {})
    # Match exact or normalized path
    path_item = paths.get(path)
    if not path_item and not path.endswith("/"):
        path_item = paths.get(path + "/")
    if not path_item and path.endswith("/"):
        path_item = paths.get(path.rstrip("/"))

    if not path_item:
        return None

    op = path_item.get(method.lower(), {})
    responses = op.get("responses", {})
    status_resp = responses.get(str(status_code)) or responses.get("default")
    if not status_resp:
        return None

    content = status_resp.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema")
    return schema


def validate_contract_fields(expected_fields: List[str], actual_data: Dict[str, Any]) -> List[str]:
    """Validates that all expected fields exist in the actual response data."""
    missing = []
    for field in expected_fields:
        if field not in actual_data:
            missing.append(field)
    return missing
