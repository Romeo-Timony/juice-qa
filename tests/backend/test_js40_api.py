"""
Автоматизированный тестовый набор REST API для подсистемы аутентификации и регистрации (JS-40).
Реализован по стандарту DEC-004 / DEC-005 (ISTQB titles, AAA docstrings, прямая привязка к Qase ID).

Проверяемые эндпоинты:
- POST /api/Users/
- POST /rest/user/login
- GET /rest/user/whoami
- GET /rest/user/change-password
- POST /rest/user/reset-password
- POST /profile/image/file
- POST /api/Addresss/
"""
import io
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

    # =============================================================================
    # [QASE #871] [BLOCKER] Создание учетной записи нового покупателя (POST /api/Users/)
    # =============================================================================
    @allure.title("Создание учетной записи нового покупателя с валидными параметрами -> HTTP 201 Created")
    @allure.issue("JS-40")
    @allure.testcase("871")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.qase(id=871)
    @pytest.mark.api
    def test_tc871_register_user_success(self, api_client: JuiceShopApiClient):
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

    # =============================================================================
    # [QASE #872] [CRITICAL] Повторная регистрация с уже существующим Email
    # =============================================================================
    @allure.title("Повторная регистрация с уже существующим Email -> HTTP 400 Bad Request")
    @allure.issue("JS-40")
    @allure.testcase("872")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.qase(id=872)
    @pytest.mark.api
    def test_tc872_register_duplicate_email_conflict(self, api_client: JuiceShopApiClient):
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

    # =============================================================================
    # [QASE #873] [NORMAL] Регистрация пользователя с неполным payload
    # =============================================================================
    @allure.title("Регистрация пользователя с неполным payload -> HTTP 201 с дефолтными значениями схемы")
    @allure.issue("JS-40")
    @allure.testcase("873")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.qase(id=873)
    @pytest.mark.api
    def test_tc873_register_incomplete_payload(self, api_client: JuiceShopApiClient):
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
        payload = {"email": email, "password": "Password123!"}

        with allure.step("1. Отправка POST с базовым payload"):
            res = api_client.session.post(url, json=payload)

        with allure.step("2. Проверка успешного создания записи"):
            assert res.status_code in [200, 201], f"Expected 200/201, got {res.status_code}"
            assert res.json().get("data", {}).get("role") == "customer"

    # =============================================================================
    # [QASE #874] [BLOCKER] Успешная аутентификация и получение JWT Bearer токена
    # =============================================================================
    @allure.title("Успешная аутентификация пользователя POST /rest/user/login -> HTTP 200 OK")
    @allure.issue("JS-40")
    @allure.testcase("874")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.qase(id=874)
    @pytest.mark.api
    def test_tc874_user_login_success_jwt(self, api_client: JuiceShopApiClient):
        """
        Проверка авторизации через POST /rest/user/login.

        Arrange (Подготовка):
            Создание учетной записи и фиксация учетных данных.
        Act (Действие):
            Вызов логина с валидным email и паролем.
        Assert (Проверка):
            HTTP 200 OK, наличие непустого JWT токена и валидный payload токена.
        """
        timestamp = int(time.time() * 1000)
        email = f"login_user_{timestamp}@juice-sh.op"
        password = "Password123!"

        with allure.step("1. Регистрация тестового пользователя"):
            assert api_client.register(email=email, password=password).status_code == 201

        with allure.step("2. Выполнение аутентификации"):
            res = api_client.login(email=email, password=password)

        with allure.step("3. Валидация структуры ответа и JWT токена"):
            assert res.status_code == 200
            token = res.json().get("authentication", {}).get("token")
            assert token is not None and len(token) > 20
            payload = decode_jwt_payload(token)
            assert payload.get("data", {}).get("email") == email

    # =============================================================================
    # [QASE #875] [CRITICAL] Аутентификация с неверным паролем
    # =============================================================================
    @allure.title("Отказ в аутентификации при неверном пароле -> HTTP 401 Unauthorized")
    @allure.issue("JS-40")
    @allure.testcase("875")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.qase(id=875)
    @pytest.mark.api
    def test_tc875_user_login_invalid_credentials(self, api_client: JuiceShopApiClient):
        """
        Проверка отклонения невалидных учетных данных.

        Arrange (Подготовка):
            Регистрация пользователя с эталонным паролем.
        Act (Действие):
            Попытка входа с заведомо ошибочным паролем.
        Assert (Проверка):
            HTTP 401 Unauthorized, сообщение Invalid email or password.
        """
        timestamp = int(time.time() * 1000)
        email = f"auth_fail_{timestamp}@juice-sh.op"

        with allure.step("1. Регистрация учетной записи"):
            assert api_client.register(email=email, password="CorrectPassword123!").status_code == 201

        with allure.step("2. Попытка логина с неверным паролем"):
            res = api_client.login(email=email, password="WrongPassword999!")

        with allure.step("3. Проверка статуса 401 Unauthorized"):
            assert res.status_code == 401
            assert "invalid email or password" in res.text.lower()

    # =============================================================================
    # [QASE #876] [CRITICAL] Безопасность: Обработка SQLi инъекции в форме авторизации
    # =============================================================================
    @allure.title("Устойчивость аутентификации к SQL-инъекциям -> Отсутствие 500 ошибок")
    @allure.issue("JS-40")
    @allure.testcase("876")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.qase(id=876)
    @pytest.mark.api
    def test_tc876_login_sql_injection_defense(self, api_client: JuiceShopApiClient):
        """
        Проверка устойчивости аутентификации к типичным SQL-инъекциям (OWASP A03).

        Arrange (Подготовка):
            Подготовка классического вектора инъекции ' OR 1=1--.
        Act (Действие):
            Отправка POST /rest/user/login с инъекцией в поле email.
        Assert (Проверка):
            Сервер возвращает валидный HTTP статус (200 при bypass или 401 при фильтрации),
            полное отсутствие необработанных 500 Internal Server Error.
        """
        sqli_email = "' OR 1=1--"
        with allure.step("1. Отправка логин-запроса с вектором SQLi"):
            res = api_client.login(email=sqli_email, password="random_password")

        with allure.step("2. Проверка корректности HTTP-статуса"):
            assert res.status_code in [200, 401], f"Unexpected status {res.status_code}: {res.text}"

    # =============================================================================
    # [QASE #877] [CRITICAL] Доступ к защищенному ресурсу whoami по сессионному токену
    # =============================================================================
    @allure.title("Доступ к GET /rest/user/whoami с валидной сессией -> HTTP 200 OK")
    @allure.issue("JS-40")
    @allure.testcase("877")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.qase(id=877)
    @pytest.mark.api
    def test_tc877_whoami_authenticated_access(self, api_client: JuiceShopApiClient):
        """
        Проверка сессионной авторизации защищенного эндпоинта whoami.

        Arrange (Подготовка):
            Регистрация пользователя, успешный вход и получение JWT токена.
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

    # =============================================================================
    # [QASE #878] [NORMAL] Успешная ротация пароля аутентифицированного пользователя
    # =============================================================================
    @allure.title("Успешная ротация пароля аутентифицированного пользователя -> HTTP 200 OK")
    @allure.issue("JS-40")
    @allure.testcase("878")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.qase(id=878)
    @pytest.mark.api
    def test_tc878_change_password_success(self, api_client: JuiceShopApiClient):
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

    # =============================================================================
    # [QASE #879] [NORMAL] Отказ в ротации пароля при неверном текущем пароле
    # =============================================================================
    @allure.title("Отказ в ротации пароля при неверном текущем пароле -> HTTP 401 Unauthorized")
    @allure.issue("JS-40")
    @allure.testcase("879")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.qase(id=879)
    @pytest.mark.api
    def test_tc879_change_password_wrong_current_rejected(self, api_client: JuiceShopApiClient):
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

    # =============================================================================
    # [QASE #880] [NORMAL] Сброс пароля по контрольному вопросу
    # =============================================================================
    @allure.title("Сброс пароля через POST /rest/user/reset-password по контрольному вопросу -> HTTP 200 OK")
    @allure.issue("JS-40")
    @allure.testcase("880")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.qase(id=880)
    @pytest.mark.api
    def test_tc880_reset_password_with_security_answer(self, api_client: JuiceShopApiClient):
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

    # =============================================================================
    # [QASE #881] [NORMAL] Загрузка аватара через POST /profile/image/file
    # =============================================================================
    @allure.title("Загрузка аватара пользователя POST /profile/image/file -> HTTP 200 OK")
    @allure.issue("JS-40")
    @allure.testcase("881")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.qase(id=881)
    @pytest.mark.api
    def test_tc881_upload_avatar_file(self, api_client: JuiceShopApiClient):
        """
        Проверка загрузки файла изображения аватара в профиль пользователя.

        Arrange (Подготовка):
            Регистрация, авторизация и формирование бинарного файла изображения.
        Act (Действие):
            Отправка multipart/form-data запроса на загрузку аватара.
        Assert (Проверка):
            HTTP 200 OK, подтверждение сохранения пути к аватару.
        """
        timestamp = int(time.time() * 1000)
        email = f"avatar_user_{timestamp}@juice-sh.op"
        password = "Password123!"

        with allure.step("1. Регистрация и авторизация"):
            assert api_client.register(email=email, password=password).status_code == 201
            token = api_client.login(email=email, password=password).json().get("authentication", {}).get("token")
            assert token is not None

        with allure.step("2. Загрузка аватара через multipart/form-data"):
            file_data = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4")
            files = {"file": ("avatar.png", file_data, "image/png")}
            headers = {"Authorization": f"Bearer {token}"}
            res = api_client.session.post(f"{api_client.base_url}/profile/image/file", headers=headers, files=files)

        with allure.step("3. Проверка успешного ответа сервера"):
            assert res.status_code in [200, 204], f"Expected 200/204, got {res.status_code}: {res.text}"

    # =============================================================================
    # [QASE #882] [NORMAL] Создание адреса доставки через POST /api/Addresss/
    # =============================================================================
    @allure.title("Создание адреса доставки POST /api/Addresss/ -> HTTP 201 Created")
    @allure.issue("JS-40")
    @allure.testcase("882")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.qase(id=882)
    @pytest.mark.api
    def test_tc882_create_delivery_address(self, api_client: JuiceShopApiClient):
        """
        Проверка создания адреса доставки в профиле покупателя.

        Arrange (Подготовка):
            Регистрация, авторизация и формирование структуры адреса.
        Act (Действие):
            Отправка POST /api/Addresss/ с телом адреса доставки.
        Assert (Проверка):
            HTTP 201 Created, сохранение адреса в БД с присвоением ID.
        """
        timestamp = int(time.time() * 1000)
        email = f"address_user_{timestamp}@juice-sh.op"
        password = "Password123!"

        with allure.step("1. Регистрация и получение токена"):
            assert api_client.register(email=email, password=password).status_code == 201
            token = api_client.login(email=email, password=password).json().get("authentication", {}).get("token")
            assert token is not None

        with allure.step("2. Создание адреса доставки"):
            headers = {"Authorization": f"Bearer {token}"}
            address_payload = {
                "country": "Germany",
                "fullName": f"Test User {timestamp}",
                "mobileNum": 1234567890,
                "zipCode": "10115",
                "streetAddress": "Alexanderplatz 1",
                "city": "Berlin"
            }
            res = api_client.session.post(f"{api_client.base_url}/api/Addresss/", headers=headers, json=address_payload)

        with allure.step("3. Проверка создания адреса"):
            assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
            data = res.json().get("data", {})
            assert data.get("id") is not None
            assert data.get("country") == "Germany"
