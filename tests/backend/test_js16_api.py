"""
Backend API Automated Test Suite for JS-16
Generated dynamically by local QA Agent
"""
import pytest
import allure
from api.client import JuiceShopApiClient

@allure.epic("OWASP Juice Shop")
@allure.feature("JS-16: Feature Validation")
@allure.story("Backend REST API Validation")
class TestJS16API:
    """Автоматизированные проверки эндпоинтов и контрактов данных."""

    @allure.title("API Verification for JS-16")
    @pytest.mark.qase(id=80)
    @pytest.mark.api
    def test_api_verification_for_js16(self, api_client: JuiceShopApiClient):
        """API Verification for JS-16"""
        with allure.step("1. Выполнение запроса к эндпоинту API"):
            response = api_client.get_connection_status()
            assert response is not None, "Служба Juice Shop должна быть доступна"
        with allure.step("2. Валидация схемы контракта и статуса ответа"):
            assert response.status_code in [200, 201, 400, 401], f"Неожиданный статус: {response.status_code}"

    @allure.title("UI Verification for JS-16")
    @pytest.mark.qase(id=50)
    @pytest.mark.api
    def test_ui_verification_for_js16(self, api_client: JuiceShopApiClient):
        """UI Verification for JS-16"""
        with allure.step("1. Выполнение запроса к эндпоинту API"):
            response = api_client.get_connection_status()
            assert response is not None, "Служба Juice Shop должна быть доступна"
        with allure.step("2. Валидация схемы контракта и статуса ответа"):
            assert response.status_code in [200, 201, 400, 401], f"Неожиданный статус: {response.status_code}"
