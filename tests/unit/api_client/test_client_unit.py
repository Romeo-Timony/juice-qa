"""
Unit-тесты для JuiceShopApiClient (api/client.py).
Проверяют управление сессией, формирование заголовков, установку токенов и очистку.
Время выполнения: < 10 мс (без внешних сетевых запросов).
"""
import pytest
import allure
from api.client import JuiceShopApiClient

@allure.epic("AQA Framework")
@allure.feature("Unit Testing: API Client")
@pytest.mark.unit
class TestApiClientUnit:

    def test_client_init_strips_trailing_slash(self):
        """Проверка нормализации base_url (удаление слэша на конце)."""
        client = JuiceShopApiClient(base_url="http://test-server:3000/")
        assert client.base_url == "http://test-server:3000"

    def test_set_bearer_token(self):
        """Проверка установки Bearer заголовка авторизации."""
        client = JuiceShopApiClient()
        token = "eyJhbGciOiJIUzI1NiJ9.test.sig"
        client.set_bearer_token(token)
        assert client.token == token
        assert client.session.headers.get("Authorization") == f"Bearer {token}"

    def test_clear_token(self):
        """Проверка очистки токена и заголовка при разлогине/сбросе."""
        client = JuiceShopApiClient()
        client.set_bearer_token("dummy_token")
        client.clear_token()
        assert client.token is None
        assert "Authorization" not in client.session.headers
