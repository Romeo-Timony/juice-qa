"""
Unit-тесты для утилит работы с токенами (utils/jwt.py).
Проверяют корректное декодирование, обработку невалидных форматов, пустых строк и padding.
Время выполнения: < 10 мс.
"""
import json
import base64
import pytest
import allure
from core_utils.jwt import decode_jwt_payload

@allure.epic("AQA Framework")
@allure.feature("Unit Testing: JWT Utilities")
@pytest.mark.unit
class TestJwtUtilsUnit:

    def test_decode_valid_jwt_payload(self):
        """Проверка корректного декодирования валидного payload."""
        payload_data = {"data": {"id": 1, "role": "admin", "email": "admin@juice-sh.op"}, "iat": 123456}
        header_b64 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).decode().rstrip("=")
        fake_token = f"{header_b64}.{payload_b64}.fake_signature"

        decoded = decode_jwt_payload(fake_token)
        assert decoded.get("data", {}).get("role") == "admin"
        assert decoded.get("data", {}).get("email") == "admin@juice-sh.op"

    @pytest.mark.parametrize("invalid_token", [
        None,
        "",
        "not_a_jwt",
        "header.invalid_base64!!!.sig",
        "single_part"
    ])
    def test_decode_invalid_tokens_gracefully(self, invalid_token):
        """Проверка устойчивости: невалидные токены не вызывают необработанных исключений."""
        res = decode_jwt_payload(invalid_token)
        assert res == {}
