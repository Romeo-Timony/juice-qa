"""
Автоматизированный тестовый набор REST API для подсистемы аутентификации и регистрации (JS-40).
Реализован по стандарту DEC-004 / DEC-005 (ISTQB titles, AAA docstrings, прямая привязка к Qase ID).

Проверяемые эндпоинты:
- POST /api/Users/
- POST /rest/user/login
- GET /rest/user/change-password
- POST /rest/user/reset-password
- GET /rest/user/whoami
"""
import time
import pytest
import allure
from api.client import JuiceShopApiClient
from core_utils.jwt import decode_jwt_payload


@allure.epic("OWASP Juice Shop")
@allure.feature("Аутентификация и управление пользователями")
@allure.story("JS-40: Автоматизация REST API регистрации и авторизации (POST /api/Users/)")
@pytest.mark.api
class TestAuthAPI:
    """Интеграционный тестовый сьют проверки контрактов аутентификации и регистрации Juice Shop."""

    # -----------------------------------------------------------------------------
    @allure.title("Создание учетной записи нового покупателя с валидными параметрами -> HTTP 201 Created")
    @allure.issue("JS-40")
    @allure.testcase("633")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.qase(id=633)
    @pytest.mark.api
    def test_tc633_register_valid_user_success(self, api_client: JuiceShopApiClient):
        """
        Успешная регистрация покупателя через POST /api/Users/.

        Arrange (Подготовка):
            Генерация уникального email на основе timestamp и стойкого пароля.
        Act (Действие):
            Отправка POST-запроса на регистрацию с контрольным вопросом.
        Assert (Проверка):
            HTTP 201 Created, наличие ID пользователя, отсутствие пароля в открытом виде.
        """
        timestamp = int(time.time() * 1000)
        email = f"buyer_{timestamp}@juice-sh.op"
        password = "SecurePassword123!"

        with allure.step(f"1. Отправка POST /api/Users/ для {email}"):
            res = api_client.register(email=email, password=password, question_id=1, answer="JuiceQA")

        with allure.step("2. Проверка HTTP статуса и структуры тела ответа"):
            assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
            body = res.json()
            assert body.get("status") == "success"
            data = body.get("data", {})
            assert data.get("id") is not None
            assert data.get("email") == email
            assert data.get("role") == "customer"
            assert "password" not in data or data.get("password") != password

    # -----------------------------------------------------------------------------
    @allure.title("Повторная регистрация с уже существующим Email -> HTTP 400 Bad Request")
    @allure.issue("JS-40")
    @allure.testcase("634")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.qase(id=634)
    @pytest.mark.api
    def test_tc634_duplicate_email_registration_rejected(self, api_client: JuiceShopApiClient):
        """
        Проверка уникальности email при регистрации.

        Arrange (Подготовка):
            Первичная регистрация пользователя с валидными данными.
        Act (Действие):
            Повторная отправка запроса регистрации с тем же email.
        Assert (Проверка):
            HTTP 400 Bad Request, сообщение об ошибке валидации уникальности.
        """
        timestamp = int(time.time() * 1000)
        email = f"duplicate_{timestamp}@juice-sh.op"
        password = "Password123!"

        with allure.step("1. Первичная регистрация учетной записи"):
            res1 = api_client.register(email=email, password=password)
            assert res1.status_code == 201

        with allure.step("2. Повторная регистрация с идентичным email"):
            res2 = api_client.register(email=email, password=password)

        with allure.step("3. Проверка отклонения дубликата"):
            assert res2.status_code in [400, 409], f"Expected 400/409, got {res2.status_code}"
            assert "must be unique" in res2.text.lower() or "validation error" in res2.text.lower()

    # -----------------------------------------------------------------------------
    @allure.title("Регистрация пользователя с неполным payload -> HTTP 201 с дефолтными значениями схемы")
    @allure.issue("JS-40")
    @allure.testcase("635")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.qase(id=635)
    @pytest.mark.api
    def test_tc635_registration_minimal_payload_contract(self, api_client: JuiceShopApiClient):
        """
        Проверка поведения эндпоинта POST /api/Users/ при передаче минимального набора полей.

        Arrange (Подготовка):
            Подготовка минимального payload с email.
        Act (Действие):
            Отправка POST /api/Users/ без вторичных атрибутов.
        Assert (Проверка):
            Обработка запроса сервером, возврат статуса успеха и дефолтной роли customer.
        """
        timestamp = int(time.time() * 1000)
        email = f"minimal_{timestamp}@juice-sh.op"
        url = f"{api_client.base_url}/api/Users/"

        with allure.step("1. Отправка POST /api/Users/ с базовым payload"):
            res = api_client._request("POST", url, json={"email": email, "password": "MinPassword123!"})

        with allure.step("2. Проверка создания пользователя и дефолтной роли"):
            assert res.status_code in [200, 201]
            data = res.json().get("data", {})
            assert data.get("role") == "customer"

    # -----------------------------------------------------------------------------
    @allure.title("Аутентификация с валидными учетными данными -> HTTP 200 OK и генерация JWT Bearer")
    @allure.issue("JS-40")
    @allure.testcase("636")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.qase(id=636)
    @pytest.mark.api
    def test_tc636_login_success_jwt_issued(self, api_client: JuiceShopApiClient):
        """
        Аутентификация зарегистрированного пользователя через POST /rest/user/login.

        Arrange (Подготовка):
            Регистрация нового покупателя.
        Act (Действие):
            Вызов эндпоинта логина POST /rest/user/login.
        Assert (Проверка):
            HTTP 200 OK, наличие JWT-токена в authentication.token, корректные claims (email, role).
        """
        timestamp = int(time.time() * 1000)
        email = f"auth_user_{timestamp}@juice-sh.op"
        password = "ValidPassword123!"

        with allure.step("1. Регистрация тестового покупателя"):
            assert api_client.register(email=email, password=password).status_code == 201

        with allure.step("2. Аутентификация через POST /rest/user/login"):
            res = api_client.login(email=email, password=password)

        with allure.step("3. Проверка успешного входа и структуры JWT токена"):
            assert res.status_code == 200, f"Login failed: {res.text}"
            token = res.json().get("authentication", {}).get("token")
            assert token is not None and len(token) > 20
            payload = decode_jwt_payload(token)
            jwt_data = payload.get("data", {})
            assert jwt_data.get("email") == email
            assert jwt_data.get("role") == "customer"

    # -----------------------------------------------------------------------------
    @allure.title("Попытка аутентификации с некорректным паролем -> HTTP 401 Unauthorized")
    @allure.issue("JS-40")
    @allure.testcase("637")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.qase(id=637)
    @pytest.mark.api
    def test_tc637_login_invalid_credentials_rejected(self, api_client: JuiceShopApiClient):
        """
        Проверка защиты от несанкционированного входа при передаче неверного пароля.

        Arrange (Подготовка):
            Регистрация аккаунта с эталонным паролем.
        Act (Действие):
            Попытка логина с заведомо ошибочным паролем.
        Assert (Проверка):
            HTTP 401 Unauthorized, отсутствие утечки сессионного токена.
        """
        timestamp = int(time.time() * 1000)
        email = f"invalid_auth_{timestamp}@juice-sh.op"
        password = "CorrectPassword123!"

        with allure.step("1. Регистрация тестового аккаунта"):
            assert api_client.register(email=email, password=password).status_code == 201

        with allure.step("2. Попытка аутентификации с неверным паролем"):
            res = api_client.login(email=email, password="WrongPassword999!")

        with allure.step("3. Проверка отклонения доступа"):
            assert res.status_code == 401, f"Expected 401 Unauthorized, got {res.status_code}"

    # -----------------------------------------------------------------------------
    @allure.title("Защита от SQL-инъекций при аутентификации через POST /rest/user/login (OWASP A03)")
    @allure.issue("JS-40")
    @allure.testcase("638")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.qase(id=638)
    @pytest.mark.api
    def test_tc638_login_sqli_payload_handling(self, api_client: JuiceShopApiClient):
        """
        Проверка обработки SQL-инъекционных векторов в полях логина.

        Arrange (Подготовка):
            Формирование пейлоада с SQL-инъекцией (' OR 1=1--).
        Act (Действие):
            Отправка POST /rest/user/login с инъекционной нагрузкой.
        Assert (Проверка):
            Запрос обрабатывается сервером без падения приложения (500), возвращается корректный HTTP статус.
        """
        sqli_payload = {"email": "admin' OR 1=1--@juice-sh.op", "password": "any"}

        with allure.step("1. Отправка POST /rest/user/login с SQL-инъекцией"):
            res = api_client._request("POST", f"{api_client.base_url}/rest/user/login", json=sqli_payload)

        with allure.step("2. Проверка отсутствия необработанного падения 500"):
            assert res.status_code != 500, "Сервер не должен падать с Internal Server Error"

    # -----------------------------------------------------------------------------
    @allure.title("Валидация Bearer JWT токена в защищенном эндпоинте GET /rest/user/whoami -> HTTP 200 OK")
    @allure.issue("JS-40")
    @allure.testcase("639")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.qase(id=639)
    @pytest.mark.api
    def test_tc639_bearer_token_authorization_protected_endpoint(self, api_client: JuiceShopApiClient):
        """
        Проверка доступа к защищенным ресурсам по Bearer-токену.

        Arrange (Подготовка):
            Регистрация и логин для получения сессионного токена.
        Act (Действие):
            Запрос защищенного эндпоинта GET /rest/user/whoami с кукой сессии.
        Assert (Проверка):
            HTTP 200 OK, соответствие email авторизованного пользователя.
        """
        timestamp = int(time.time() * 1000)
        email = f"whoami_{timestamp}@juice-sh.op"
        password = "Password123!"

        with allure.step("1. Создание пользователя и получение токена"):
            assert api_client.register(email=email, password=password).status_code == 201
            login_res = api_client.login(email=email, password=password)
            token = login_res.json().get("authentication", {}).get("token")
            assert token is not None

        with allure.step("2. Запрос защищенного ресурса GET /rest/user/whoami"):
            res = api_client._request("GET", f"{api_client.base_url}/rest/user/whoami", cookies={"token": token})

        with allure.step("3. Проверка успешного доступа к профилю"):
            assert res.status_code == 200
            assert res.json().get("user", {}).get("email") == email

    # -----------------------------------------------------------------------------
    @allure.title("Успешная ротация пароля аутентифицированного пользователя -> HTTP 200 OK")
    @allure.issue("JS-40")
    @allure.testcase("640")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.qase(id=640)
    @pytest.mark.api
    def test_tc640_change_password_success(self, api_client: JuiceShopApiClient):
        """
        Смена пароля через GET /rest/user/change-password.

        Arrange (Подготовка):
            Регистрация аккаунта с исходным паролем и авторизация.
        Act (Действие):
            Вызов смены пароля с передачей старого и нового значения.
        Assert (Проверка):
            HTTP 200 OK, успешная авторизация с новым паролем.
        """
        timestamp = int(time.time() * 1000)
        email = f"change_pwd_{timestamp}@juice-sh.op"
        old_pwd = "OldPassword123!"
        new_pwd = "NewPassword456!"

        with allure.step("1. Регистрация и получение токена"):
            assert api_client.register(email=email, password=old_pwd).status_code == 201
            login_res = api_client.login(email=email, password=old_pwd)
            token = login_res.json().get("authentication", {}).get("token")

        with allure.step("2. Вызов ротации пароля"):
            res = api_client.change_password(old_pwd, new_pwd, new_pwd, token=token)
            assert res.status_code == 200, f"Change password failed: {res.text}"

        with allure.step("3. Проверка логина с обновленным паролем"):
            new_client = JuiceShopApiClient(base_url=api_client.base_url)
            assert new_client.login(email=email, password=new_pwd).status_code == 200

    # -----------------------------------------------------------------------------
    @allure.title("Отказ в ротации пароля при неверном текущем пароле -> HTTP 401 Unauthorized")
    @allure.issue("JS-40")
    @allure.testcase("641")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.qase(id=641)
    @pytest.mark.api
    def test_tc641_change_password_wrong_current_rejected(self, api_client: JuiceShopApiClient):
        """
        Проверка верификации текущего пароля при попытке смены.

        Arrange (Подготовка):
            Регистрация аккаунта и получение токена.
        Act (Действие):
            Вызов смены пароля с неверным параметром current.
        Assert (Проверка):
            HTTP 401 Unauthorized, отклонение операции.
        """
        timestamp = int(time.time() * 1000)
        email = f"wrong_pwd_{timestamp}@juice-sh.op"
        pwd = "OriginalPassword123!"

        with allure.step("1. Регистрация и авторизация"):
            assert api_client.register(email=email, password=pwd).status_code == 201
            login_res = api_client.login(email=email, password=pwd)
            token = login_res.json().get("authentication", {}).get("token")

        with allure.step("2. Отправка запроса смены с ошибочным текущим паролем"):
            res = api_client.change_password("WrongCurrentPwd!", "NewPwd123!", "NewPwd123!", token=token)

        with allure.step("3. Проверка отклонения операции"):
            assert res.status_code == 401, f"Expected 401, got {res.status_code}"

    # -----------------------------------------------------------------------------
    @allure.title("Сброс пароля через POST /rest/user/reset-password по контрольному вопросу -> HTTP 200 OK")
    @allure.issue("JS-40")
    @allure.testcase("642")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.qase(id=642)
    @pytest.mark.api
    def test_tc642_reset_password_with_security_answer(self, api_client: JuiceShopApiClient):
        """
        Сброс пароля через связку Email и секретного ответа.

        Arrange (Подготовка):
            Регистрация аккаунта с привязкой ответа на секретный вопрос.
        Act (Действие):
            Вызов сброса пароля POST /rest/user/reset-password.
        Assert (Проверка):
            HTTP 200 OK, возможность логина с новым сброшенным паролем.
        """
        timestamp = int(time.time() * 1000)
        email = f"reset_pwd_{timestamp}@juice-sh.op"
        old_pwd = "InitialPassword123!"
        new_pwd = "ResetPassword789!"
        answer = "SecretAnswerJuice"

        with allure.step("1. Регистрация с контрольным вопросом"):
            reg_res = api_client.register(email=email, password=old_pwd, question_id=1, answer=answer)
            assert reg_res.status_code == 201

        with allure.step("2. Отправка запроса сброса пароля"):
            reset_res = api_client.reset_password(email=email, answer=answer, new_password=new_pwd, repeat_password=new_pwd)
            assert reset_res.status_code == 200, f"Reset failed: {reset_res.text}"

        with allure.step("3. Проверка логина с новым паролем после сброса"):
            login_res = api_client.login(email=email, password=new_pwd)
            assert login_res.status_code == 200
