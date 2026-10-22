"""
REST API тесты для тестовых персон и разграничения прав доступа (RBAC).
Проверяет аутентификацию, структуру JWT-токенов, соответствие ролей и балансы кошелька.
"""
import pytest
import allure
from api.client import JuiceShopApiClient
from data.users import UserPersonas, UserPersona
from core_utils.jwt import decode_jwt_payload

@allure.epic("OWASP Juice Shop")
@allure.feature("Тестовые персоны и профили пользователей")
@allure.story("Параметризованная верификация учетных записей, ролей и балансов")
@pytest.mark.api
class TestUserPersonasAPI:

    @allure.title("[Параметризация] Успешная аутентификация персоны: {any_seeded_user.name}")
    def test_seeded_user_login(self, api_client: JuiceShopApiClient, any_seeded_user: UserPersona):
        """Проверка входа в систему и генерации токена для каждой из 3 тестовых персон."""
        with allure.step(f"1. Логин пользователя {any_seeded_user.name} ({any_seeded_user.email})"):
            res = api_client.login(any_seeded_user.email, any_seeded_user.password)
            assert res.status_code == 200, f"Login failed for {any_seeded_user.email}: {res.text}"

        with allure.step("2. Проверка генерации валидного JWT токена"):
            auth_data = res.json().get("authentication", {})
            token = auth_data.get("token")
            assert token is not None and len(token) > 20

        with allure.step(f"3. Проверка соответствия роли в JWT ({any_seeded_user.role})"):
            payload = decode_jwt_payload(token)
            jwt_user_data = payload.get("data", {})
            assert jwt_user_data.get("role") == any_seeded_user.role, (
                f"Expected role {any_seeded_user.role}, but got {jwt_user_data.get('role')}"
            )
            assert jwt_user_data.get("email") == any_seeded_user.email

    @allure.title("[Параметризация] Проверка профиля сессии GET /rest/user/whoami для покупателей")
    def test_customer_whoami_profile(self, base_url: str, customer_user: UserPersona):
        """Параметризованная проверка профиля сессии для покупателей с деньгами и без денег."""
        client = JuiceShopApiClient(base_url=base_url)
        login_res = client.login(customer_user.email, customer_user.password)
        token = login_res.json().get("authentication", {}).get("token")

        with allure.step(f"1. Запрос /rest/user/whoami с кукой сессии для {customer_user.name}"):
            res = client._request("GET", f"{base_url}/rest/user/whoami", cookies={"token": token})
            assert res.status_code == 200
            user_data = res.json().get("user", {})
            assert user_data.get("email") == customer_user.email

    @allure.title("[Кошелек][Параметризация] Проверка баланса цифрового кошелька: $100 у Jim против $0 у Bender")
    def test_wallet_balance_personas(self, user_with_money_client: JuiceShopApiClient, user_without_money_client: JuiceShopApiClient):
        """Сравнение балансов пользователей: положительный баланс vs нулевой."""
        with allure.step("1. Проверка баланса кошелька Jim (ожидается положительный баланс > 0)"):
            res_jim = user_with_money_client._request("GET", f"{user_with_money_client.base_url}/rest/wallet/balance")
            assert res_jim.status_code == 200
            balance_jim = res_jim.json().get("data", 0)
            assert balance_jim > 0, f"Expected Jim's balance > 0, got {balance_jim}"

        with allure.step("2. Проверка баланса кошелька Bender (ожидается 0 или отсутствие кошелька)"):
            res_bender = user_without_money_client._request("GET", f"{user_without_money_client.base_url}/rest/wallet/balance")
            if res_bender.status_code == 200:
                assert res_bender.json().get("data", 0) == 0
            else:
                assert res_bender.status_code in [400, 404]
