"""
REST API тесты для подсистемы аутентификации и регистрации пользователей (JS-40).
Эндпоинты:
- POST /api/Users/ (Регистрация, уникальность email, хеширование паролей)
- GET /api/SecurityQuestions/ (Справочник контрольных вопросов)
- POST /api/SecurityAnswers/ (Привязка контрольного ответа для сброса пароля)
- POST /rest/user/login (Аутентификация, выдача JWT Bearer)
- GET /rest/user/change-password (Ротация пароля пользователя)
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

    @allure.title("[API] Получение справочника контрольных вопросов GET /api/SecurityQuestions/ (200 OK)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_security_questions_catalog(self, api_client: JuiceShopApiClient):
        """Проверка доступности справочника секретных вопросов для формы регистрации."""
        with allure.step("1. Запрос GET /api/SecurityQuestions/"):
            res = api_client._request("GET", f"{api_client.base_url}/api/SecurityQuestions/")
            assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

        with allure.step("2. Проверка наличия элементов справочника"):
            questions = res.json().get("data", [])
            assert len(questions) > 0, "Справочник вопросов не должен быть пустым"
            assert "question" in questions[0] and "id" in questions[0]

    @allure.title("[API] Успешная регистрация нового покупателя через POST /api/Users/ (201 Created)")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_successful_user_registration(self, api_client: JuiceShopApiClient):
        """Проверка регистрации пользователя с валидными параметрами и сохранением в БД."""
        timestamp = int(time.time() * 1000)
        email = f"qa_buyer_{timestamp}@juice-sh.op"
        password = "SecurePassword123!"

        with allure.step(f"1. Отправка POST /api/Users/ для {email}"):
            res = api_client.register(email=email, password=password, question_id=1, answer="JuiceQA")
            assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"

        with allure.step("2. Проверка структуры ответа регистрации"):
            body = res.json()
            assert body.get("status") == "success"
            data = body.get("data", {})
            assert data.get("id") is not None
            assert data.get("email") == email
            assert data.get("role") == "customer"
            assert "password" not in data or data.get("password") != password, "Пароль не должен утекать в открытом виде"

    @allure.title("[API] Отказ в повторной регистрации при дубликате Email (400 Bad Request)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_duplicate_email_registration_rejected(self, api_client: JuiceShopApiClient):
        """Проверка уникальности email: повторная регистрация возвращает 400 Bad Request."""
        timestamp = int(time.time() * 1000)
        email = f"duplicate_{timestamp}@juice-sh.op"
        password = "Password123!"

        with allure.step("1. Первичная успешная регистрация"):
            res1 = api_client.register(email=email, password=password)
            assert res1.status_code == 201

        with allure.step("2. Повторная регистрация с тем же email"):
            res2 = api_client.register(email=email, password=password)
            assert res2.status_code == 400, f"Expected 400 Validation Error, got {res2.status_code}"
            assert "must be unique" in res2.text.lower() or "validation error" in res2.text.lower()

    @allure.title("[API] Привязка ответа на контрольный вопрос (POST /api/SecurityAnswers/)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_security_answer_linkage(self, api_client: JuiceShopApiClient):
        """Проверка связи учетной записи с секретным вопросом для функции восстановления."""
        timestamp = int(time.time() * 1000)
        email = f"sec_ans_{timestamp}@juice-sh.op"
        password = "Password123!"

        with allure.step("1. Создание пользователя"):
            reg_res = api_client.register(email=email, password=password, link_security_answer=False)
            assert reg_res.status_code == 201
            user_id = reg_res.json().get("data", {}).get("id")
            assert user_id is not None

        with allure.step(f"2. Сохранение контрольного ответа для UserId={user_id}"):
            ans_res = api_client.set_security_answer(user_id=user_id, question_id=1, answer="SecretAnswer123")
            assert ans_res.status_code == 201

    @allure.title("[API] Логин зарегистрированного пользователя и получение JWT (POST /rest/user/login)")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_login_and_jwt_verification(self, api_client: JuiceShopApiClient):
        """Сквозная проверка: регистрация -> авторизация -> валидация JWT клеймов."""
        timestamp = int(time.time() * 1000)
        email = f"jwt_user_{timestamp}@juice-sh.op"
        password = "ValidPassword123!"

        with allure.step("1. Регистрация нового аккаунта"):
            reg_res = api_client.register(email=email, password=password)
            assert reg_res.status_code == 201

        with allure.step("2. Аутентификация через POST /rest/user/login"):
            login_res = api_client.login(email=email, password=password)
            assert login_res.status_code == 200, f"Login failed: {login_res.text}"

        with allure.step("3. Проверка наличия и структуры JWT"):
            token = login_res.json().get("authentication", {}).get("token")
            assert token is not None and len(token) > 20

            payload = decode_jwt_payload(token)
            jwt_data = payload.get("data", {})
            assert jwt_data.get("email") == email
            assert jwt_data.get("role") == "customer"

    @allure.title("[API] Отказ в доступе при неверных учетных данных (401 Unauthorized)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_invalid_password_rejected(self, api_client: JuiceShopApiClient):
        """Проверка защиты от несанкционированного доступа при неверном пароле."""
        timestamp = int(time.time() * 1000)
        email = f"auth_reject_{timestamp}@juice-sh.op"
        password = "CorrectPassword123!"

        with allure.step("1. Регистрация аккаунта"):
            assert api_client.register(email=email, password=password).status_code == 201

        with allure.step("2. Попытка входа с некорректным паролем"):
            res = api_client.login(email=email, password="WrongPassword999!")
            assert res.status_code == 401, f"Expected 401 Unauthorized, got {res.status_code}"

    @allure.title("[API] Смена пароля пользователя через GET /rest/user/change-password")
    @allure.severity(allure.severity_level.NORMAL)
    def test_change_password_flow(self, api_client: JuiceShopApiClient):
        """Проверка ротации пароля аутентифицированного пользователя."""
        timestamp = int(time.time() * 1000)
        email = f"pwd_change_{timestamp}@juice-sh.op"
        old_pwd = "OldPassword123!"
        new_pwd = "NewPassword456!"

        with allure.step("1. Регистрация и получение токена"):
            assert api_client.register(email=email, password=old_pwd).status_code == 201
            login_res = api_client.login(email=email, password=old_pwd)
            token = login_res.json().get("authentication", {}).get("token")

        with allure.step("2. Смена пароля"):
            res = api_client.change_password(old_pwd, new_pwd, new_pwd, token=token)
            assert res.status_code == 200, f"Change password failed: {res.text}"

        with allure.step("3. Проверка авторизации с новым паролем"):
            new_client = JuiceShopApiClient(base_url=api_client.base_url)
            assert new_client.login(email=email, password=new_pwd).status_code == 200
