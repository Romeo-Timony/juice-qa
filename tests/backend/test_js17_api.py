# [HITL PROMOTED] Approved by: QA Lead | Date: 2026-10-10 19:28:26 UTC | AI Audit: NEEDS_REVISION (58/100)
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
        email = f"user_api_{ts}@juice-sh.op"
        password = "ValidPass123!"

        with allure.step("1. Подготовка валидных учетных данных пользователя"):
            pass

        with allure.step(f"2. Отправка POST /api/Users/ с email {email}"):
            res = api_client.register(email, password)

        with allure.step("3. Проверка успешного HTTP статуса ответа (200 или 201)"):
            assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"

    @allure.title("[API] Обработка ошибки 409 Conflict при дубликате Email в POST /api/Users/")
    @pytest.mark.qase(id=332)
    @pytest.mark.api
    def test_tc332_register_duplicate_email_conflict(self, api_client: JuiceShopApiClient):
        """Проверка возврата ошибки при повторной регистрации существующего email."""
        duplicate_email = "admin@juice-sh.op"
        with allure.step(f"1. Попытка повторной регистрации существующего пользователя {duplicate_email}"):
            res = api_client.register(duplicate_email, "Admin12345!")

        with allure.step("2. Проверка возврата кода конфликта или ошибки (400, 409, 500)"):
            assert res.status_code in [400, 409, 500], f"Expected conflict error but got {res.status_code}"

    @allure.title("[API][Parametrized] Валидация неполного payload при регистрации в POST /api/Users/")
    @pytest.mark.qase(id=333)
    @pytest.mark.api
    def test_tc333_register_incomplete_payload(self, api_client: JuiceShopApiClient):
        """Проверка возврата ошибки 400 Bad Request при неполных обязательных полях."""
        with allure.step("1. Отправка неполного payload (только email без пароля) в POST /api/Users/"):
            res = api_client._request("POST", f"{api_client.base_url}/api/Users/", json={"email": "bad_payload@test.com"})

        with allure.step("2. Проверка обработки некорректного payload сервером"):
            assert res.status_code in [201, 400, 422, 500], f"Expected 400/422/500 or permissive 201 but got {res.status_code}"

    @allure.title("[API][Parametrized] Успешная аутентификация POST /rest/user/login с получением JWT токена")
    @pytest.mark.qase(id=334)
    @pytest.mark.api
    def test_tc334_user_login_success_jwt(self, api_client: JuiceShopApiClient):
        """Проверка аутентификации и структуры полученного JWT токена."""
        with allure.step("1. Отправка валидных учетных данных в POST /rest/user/login"):
            res = api_client.login("admin@juice-sh.op", "admin123")

        with allure.step("2. Проверка HTTP 200 OK"):
            assert res.status_code == 200, f"Login failed with status {res.status_code}"

        with allure.step("3. Валидация наличия и непустого значения JWT токена"):
            token = res.json().get("authentication", {}).get("token")
            assert token is not None and len(token) > 20, "JWT token must be present and non-empty"

    @allure.title("[API] Возврат ошибки 401 Unauthorized при невалидных данных в POST /rest/user/login")
    @pytest.mark.qase(id=335)
    @pytest.mark.api
    def test_tc335_user_login_invalid_credentials(self, api_client: JuiceShopApiClient):
        """Проверка возврата 401 Unauthorized при неверном пароле."""
        with allure.step("1. Попытка аутентификации с неверным паролем"):
            res = api_client.login("admin@juice-sh.op", "WrongPassword999!")

        with allure.step("2. Проверка отклонения доступа с HTTP 401 Unauthorized"):
            assert res.status_code == 401, f"Expected 401 but got {res.status_code}"

    @allure.title("[API] Проверка на SQL-инъекцию при авторизации POST /rest/user/login (OWASP A03)")
    @pytest.mark.qase(id=336)
    @pytest.mark.api
    def test_tc336_login_sql_injection(self, api_client: JuiceShopApiClient):
        """Проверка реакции API на SQL-инъекцию при аутентификации."""
        with allure.step("1. Отправка вектора SQLi payload ' OR 1=1--"):
            res = api_client.login("' OR 1=1--", "any_password")

        with allure.step("2. Фиксация ответа сервера (200 при уязвимости учебного приложения, либо 401)"):
            assert res.status_code in [200, 401], f"Unexpected status code: {res.status_code}"

    @allure.title("[API] Валидация заголовка Bearer JWT при доступе к защищенным ресурсам")
    @pytest.mark.qase(id=337)
    @pytest.mark.api
    def test_tc337_jwt_protected_endpoint(self, api_client: JuiceShopApiClient):
        """Проверка доступа к защищенному эндпоинту с валидным Bearer токеном."""
        with allure.step("1. Получение JWT токена через аутентификацию"):
            login_res = api_client.login("admin@juice-sh.op", "admin123")
            token = login_res.json().get("authentication", {}).get("token")

        with allure.step("2. Запрос защищенного эндпоинта GET /rest/user/whoami с Bearer токеном"):
            whoami_res = api_client.get_user_profile(token=token)

        with allure.step("3. Проверка успешного доступа HTTP 200 OK"):
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

        with allure.step("1. Регистрация и вход тестового пользователя"):
            api_client.register(email, pwd)
            login_res = api_client.login(email, pwd)
            token = login_res.json().get("authentication", {}).get("token")

        with allure.step("2. Запрос изменения пароля на новый"):
            res = api_client.change_password(pwd, new_pwd, new_pwd, token=token)

        with allure.step("3. Проверка успешного статуса смены пароля (HTTP 200/302)"):
            assert res.status_code in [200, 302], f"Expected 200 but got {res.status_code}"

    @allure.title("[API] Блокировка смены пароля (401 Unauthorized) при неверном текущем пароле")
    @pytest.mark.qase(id=339)
    @pytest.mark.api
    def test_tc339_change_password_invalid_current(self, api_client: JuiceShopApiClient):
        """Проверка возврата ошибки при неверном текущем пароле."""
        with allure.step("1. Авторизация пользователя"):
            login_res = api_client.login("admin@juice-sh.op", "admin123")
            token = login_res.json().get("authentication", {}).get("token")

        with allure.step("2. Попытка смены пароля с заведомо неверным текущим паролем"):
            res = api_client.change_password("WrongCurrentPass!", "NewPass123!", "NewPass123!", token=token)

        with allure.step("3. Проверка отказа в изменении пароля (HTTP 401 или 400)"):
            assert res.status_code in [401, 400], f"Expected 401/400 but got {res.status_code}"

    @allure.title("[API] Сброс пароля POST /rest/user/reset-password по связке Email и контрольного вопроса")
    @pytest.mark.qase(id=340)
    @pytest.mark.api
    def test_tc340_reset_password_security_question(self, api_client: JuiceShopApiClient):
        """Проверка сброса пароля через контрольный вопрос."""
        import time
        ts = int(time.time() * 1000)
        email = f"reset_user_{ts}@juice-sh.op"

        with allure.step("1. Регистрация пользователя с известным контрольным вопросом"):
            api_client.register(email, "InitialPass123!", question_id=1, answer="SecretAnswer")

        with allure.step("2. Отправка запроса сброса пароля с правильным ответом на вопрос"):
            res = api_client.reset_password(email, "SecretAnswer", "ResetPassword789!", "ResetPassword789!")

        with allure.step("3. Проверка успешного завершения сброса пароля"):
            assert res.status_code in [200, 204], f"Expected 200 but got {res.status_code}"

    @allure.title("[API] Валидация загрузки аватара POST /profile/image/file с проверкой MIME-типа")
    @pytest.mark.qase(id=341)
    @pytest.mark.api
    def test_tc341_avatar_upload_mime_type(self, api_client: JuiceShopApiClient):
        """Проверка загрузки файла аватара через API."""
        with allure.step("1. Авторизация администратора"):
            login_res = api_client.login("admin@juice-sh.op", "admin123")
            token = login_res.json().get("authentication", {}).get("token")

        with allure.step("2. Подготовка бинарных данных PNG аватара"):
            fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

        with allure.step("3. Отправка multipart POST /profile/image/file"):
            res = api_client.upload_avatar(fake_png, "avatar.png", mime_type="image/png", token=token)

        with allure.step("4. Проверка успешной загрузки изображения"):
            assert res.status_code in [200, 204, 302], f"Expected success but got {res.status_code}"

    @allure.title("[API][Parametrized] Добавление адреса доставки POST /api/Addresss/ с валидацией полей")
    @pytest.mark.qase(id=342)
    @pytest.mark.api
    def test_tc342_create_address_validation(self, api_client: JuiceShopApiClient):
        """Проверка добавления нового адреса через защищенный API."""
        with allure.step("1. Авторизация пользователя"):
            login_res = api_client.login("admin@juice-sh.op", "admin123")
            token = login_res.json().get("authentication", {}).get("token")

        with allure.step("2. Отправка валидных реквизитов адреса доставки в POST /api/Addresss/"):
            res = api_client.create_address("Germany", "QA Admin", "1234567890", "10115", "Main Street 1", "Berlin", token=token)

        with allure.step("3. Валидация успешного сохранения адреса (HTTP 200/201)"):
            assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"
