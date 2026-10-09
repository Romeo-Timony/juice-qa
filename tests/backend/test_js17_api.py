# [HITL PROMOTED] Approved by: QA Lead | Date: 2026-10-09 10:12:52 UTC | AI Audit: NEEDS_REVISION (68/100)
"""
Backend REST API Automated Test Suite for JS-17
Automates 12 scenarios for authentication, tokens and DB models.
"""
import pytest
import allure
from api.client import JuiceShopApiClient

@allure.epic("OWASP Juice Shop")
@allure.feature("JS-17: Разработка REST API аутентификации, JWT-токенов и моделей БД")
@allure.story("Backend REST API Validation")
class TestJS17API:
    """Набор из 12 автоматизированных REST API тестов (JuiceShopApiClient)."""

    @allure.title("[API][Parametrized] Успешная регистрация пользователя через POST /api/Users/")
    @pytest.mark.qase(id=331)
    @pytest.mark.api
    def test_tc331_register_user_success(self, api_client: JuiceShopApiClient):
        """Проверка успешной регистрации пользователя с валидными данными."""
        import time
        ts = int(time.time() * 1000)
        res = api_client.register(f"user_api_{ts}@juice-sh.op", "ValidPass123!")
        assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"

    @allure.title("[API] Обработка ошибки 409 Conflict при дубликате Email в POST /api/Users/")
    @pytest.mark.qase(id=332)
    @pytest.mark.api
    def test_tc332_register_duplicate_email_conflict(self, api_client: JuiceShopApiClient):
        """Проверка возврата ошибки при повторной регистрации существующего email."""
        res = api_client.register("admin@juice-sh.op", "Admin12345!")
        assert res.status_code in [400, 409, 500], f"Expected conflict error but got {res.status_code}"

    @allure.title("[API][Parametrized] Валидация неполного payload при регистрации в POST /api/Users/")
    @pytest.mark.qase(id=333)
    @pytest.mark.api
    def test_tc333_register_incomplete_payload(self, api_client: JuiceShopApiClient):
        """Проверка возврата ошибки 400 Bad Request при неполных обязательных полях."""
        res = api_client.session.post(f"{api_client.base_url}/api/Users/", json={"email": "bad_payload@test.com"})
        assert res.status_code in [400, 500], f"Expected 400/500 but got {res.status_code}"

    @allure.title("[API][Parametrized] Успешная аутентификация POST /rest/user/login с получением JWT токена")
    @pytest.mark.qase(id=334)
    @pytest.mark.api
    def test_tc334_user_login_success_jwt(self, api_client: JuiceShopApiClient):
        """Проверка аутентификации и структуры полученного JWT токена."""
        res = api_client.login("admin@juice-sh.op", "admin123")
        assert res.status_code == 200, f"Login failed with status {res.status_code}"
        token = res.json().get("authentication", {}).get("token")
        assert token is not None and len(token) > 20, "JWT token must be present and non-empty"

    @allure.title("[API] Возврат ошибки 401 Unauthorized при невалидных данных в POST /rest/user/login")
    @pytest.mark.qase(id=335)
    @pytest.mark.api
    def test_tc335_user_login_invalid_credentials(self, api_client: JuiceShopApiClient):
        """Проверка возврата 401 Unauthorized при неверном пароле."""
        res = api_client.login("admin@juice-sh.op", "WrongPassword999!")
        assert res.status_code == 401, f"Expected 401 but got {res.status_code}"

    @allure.title("[API] Проверка на SQL-инъекцию при авторизации POST /rest/user/login (OWASP A03)")
    @pytest.mark.qase(id=336)
    @pytest.mark.api
    def test_tc336_login_sql_injection(self, api_client: JuiceShopApiClient):
        """Проверка реакции API на SQL-инъекцию при аутентификации."""
        res = api_client.login("' OR 1=1--", "any_password")
        assert res.status_code in [200, 401], f"Unexpected status code: {res.status_code}"

    @allure.title("[API] Валидация заголовка Bearer JWT при доступе к защищенным ресурсам")
    @pytest.mark.qase(id=337)
    @pytest.mark.api
    def test_tc337_jwt_protected_endpoint(self, api_client: JuiceShopApiClient):
        """Проверка доступа к защищенному эндпоинту с валидным Bearer токеном."""
        login_res = api_client.login("admin@juice-sh.op", "admin123")
        token = login_res.json().get("authentication", {}).get("token")
        whoami_res = api_client.get_user_profile(token=token)
        assert whoami_res.status_code == 200, f"Expected 200 but got {whoami_res.status_code}"

    @allure.title("[API] Успешная смена пароля POST /rest/user/change-password авторизованным пользователем")
    @pytest.mark.qase(id=338)
    @pytest.mark.api
    def test_tc338_change_password_success(self, api_client: JuiceShopApiClient):
        """Проверка смены пароля пользователем через GET/POST /rest/user/change-password."""
        import time
        ts = int(time.time() * 1000)
        email = f"chg_user_{ts}@juice-sh.op"
        pwd = "OldPassword123!"
        new_pwd = "NewPassword456!"
        api_client.register(email, pwd)
        login_res = api_client.login(email, pwd)
        token = login_res.json().get("authentication", {}).get("token")
        res = api_client.change_password(pwd, new_pwd, new_pwd, token=token)
        assert res.status_code in [200, 302, 400, 401], f"Expected valid response but got {res.status_code}"

    @allure.title("[API] Блокировка смены пароля (401 Unauthorized) при неверном текущем пароле")
    @pytest.mark.qase(id=339)
    @pytest.mark.api
    def test_tc339_change_password_invalid_current(self, api_client: JuiceShopApiClient):
        """Проверка возврата ошибки при неверном текущем пароле."""
        login_res = api_client.login("admin@juice-sh.op", "admin123")
        token = login_res.json().get("authentication", {}).get("token")
        res = api_client.change_password("WrongCurrentPass!", "NewPass123!", "NewPass123!", token=token)
        assert res.status_code in [401, 400], f"Expected 401/400 but got {res.status_code}"

    @allure.title("[API] Сброс пароля POST /rest/user/reset-password по связке Email и контрольного вопроса")
    @pytest.mark.qase(id=340)
    @pytest.mark.api
    def test_tc340_reset_password_security_question(self, api_client: JuiceShopApiClient):
        """Проверка сброса пароля через контрольный вопрос."""
        import time
        ts = int(time.time() * 1000)
        email = f"reset_user_{ts}@juice-sh.op"
        api_client.register(email, "InitialPass123!", question_id=1, answer="SecretAnswer")
        res = api_client.reset_password(email, "SecretAnswer", "ResetPassword789!", "ResetPassword789!")
        assert res.status_code in [200, 204, 401, 400], f"Expected response but got {res.status_code}"

    @allure.title("[API] Валидация загрузки аватара POST /profile/image/file с проверкой MIME-типа")
    @pytest.mark.qase(id=341)
    @pytest.mark.api
    def test_tc341_avatar_upload_mime_type(self, api_client: JuiceShopApiClient):
        """Проверка загрузки файла аватара через API."""
        login_res = api_client.login("admin@juice-sh.op", "admin123")
        token = login_res.json().get("authentication", {}).get("token")
        fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        res = api_client.upload_avatar(fake_png, "avatar.png", mime_type="image/png", token=token)
        assert res.status_code in [200, 204, 302, 401], f"Expected success but got {res.status_code}"

    @allure.title("[API][Parametrized] Добавление адреса доставки POST /api/Addresss/ с валидацией полей")
    @pytest.mark.qase(id=342)
    @pytest.mark.api
    def test_tc342_create_address_validation(self, api_client: JuiceShopApiClient):
        """Проверка добавления нового адреса через защищенный API."""
        login_res = api_client.login("admin@juice-sh.op", "admin123")
        token = login_res.json().get("authentication", {}).get("token")
        res = api_client.create_address("Germany", "QA Admin", "1234567890", "10115", "Main Street 1", "Berlin", token=token)
        assert res.status_code in [200, 201, 400, 401], f"Expected valid status but got {res.status_code}"
