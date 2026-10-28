"""
Verification tests for OpenAPI / Swagger contract validation (Seam 1 & API Drift).
"""

import pytest
from qaops.openapi_validator import fetch_openapi_spec, get_endpoint_schema, validate_contract_fields
from schemas.models import UserRegistrationResponse, LoginResponse


def test_fetch_openapi_spec_has_endpoints():
    spec = fetch_openapi_spec()
    assert spec is not None
    assert "paths" in spec
    paths = spec["paths"]
    assert len(paths) > 0
    # Juice Shop native OpenAPI documents /orders and components
    assert "/orders" in paths
    schemas = spec.get("components", {}).get("schemas", {})
    assert "Order" in schemas or "OrderConfirmation" in schemas


def test_validate_contract_fields_helper():
    actual_data = {"id": 1, "email": "test@juice-sh.op", "role": "customer"}
    expected = ["id", "email"]
    missing = validate_contract_fields(expected, actual_data)
    assert len(missing) == 0

    expected_with_missing = ["id", "email", "nonexistent_field"]
    missing = validate_contract_fields(expected_with_missing, actual_data)
    assert missing == ["nonexistent_field"]


def test_pydantic_models_schema_fidelity():
    """Verify that UserRegistrationResponse and LoginResponse models are valid Pydantic v2 schemas."""
    mock_reg = {
        "status": "success",
        "data": {
            "id": 101,
            "email": "auto_test@juice-sh.op",
            "role": "customer",
            "isActive": True,
            "deluxeToken": "",
            "lastLoginIp": "0.0.0.0",
            "profileImage": "/assets/public/images/uploads/default.svg",
            "updatedAt": "2026-10-25T18:00:00.000Z",
            "createdAt": "2026-10-25T18:00:00.000Z"
        }
    }
    model = UserRegistrationResponse.model_validate(mock_reg)
    assert model.data.id == 101
    assert model.data.email == "auto_test@juice-sh.op"

    mock_login = {
        "authentication": {
            "token": "valid-jwt-token-string",
            "bid": 2,
            "umail": "auto_test@juice-sh.op"
        }
    }
    login_model = LoginResponse.model_validate(mock_login)
    assert login_model.authentication.token == "valid-jwt-token-string"
