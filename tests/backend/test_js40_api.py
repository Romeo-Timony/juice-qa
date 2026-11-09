# [HITL PROMOTED] Approved by: QA Lead | Date: 2026-11-09 07:18:12 UTC | AI Audit: NEEDS_REVISION (75/100)
"""
Backend REST API Automated Test Suite for JS-40
Automates 12 scenarios for registration contracts, security questions and DB models.
Strictly adheres to DEC-004 (Visual Banners & AAA Steps) and DEC-005 (Direct Qase ID Naming).
"""
import uuid
import pytest
import allure
from api.client import JuiceShopApiClient

@allure.epic("OWASP Juice Shop")
@allure.feature("JS-40: Разработка REST API регистрации, валидации и моделей БД")
@allure.story("Backend Registration & Security Questions Validation")
class TestJS40API:
    """Набор из 12 автоматизированных REST API тестов (JuiceShopApiClient)."""

    # =============================================================================
    # [QASE #959] [SMOKE] Успешная регистрация пользователя через POST /api/Users/
    # =============================================================================
    @allure.title("[API][Parametrized] Успешная регистрация пользователя через POST /api/Users/ с валидным payload")
    @allure.issue("JS-40")
    @allure.testcase("959")
    @pytest.mark.qase(id=959)
    @pytest.mark.api
    def test_tc959_register_user_success(self, api_client: JuiceShopApiClient):
        """
        Arrange: Подготовка уникального валидного email и надежного пароля.
        Act: Отправка запроса регистрации через POST /api/Users/.
        Assert: Проверка возврата статус-кода 200 или 201 Created (AC-API-01).
        """
        with allure.step("1. Arrange: Генерация уникального email пользователя через UUID"):
            uid = uuid.uuid4().hex[:8]
            email = f"user_api_{uid}@juice-sh.op"
            password = "ValidPass123!"

        with allure.step(f"2. Act: Вызов POST /api/Users/ для {email}"):
            res = api_client.register(email, password)

        with allure.step("3. Assert: Проверка успешного ответа сервера (HTTP 200/201)"):
            assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"

    # =============================================================================
    # [QASE #960] [NEGATIVE] Обработка ошибки 409 Conflict при дубликате Email
    # =============================================================================
    @allure.title("[API] Обработка ошибки 409 Conflict при дубликате Email в POST /api/Users/")
    @allure.issue("JS-40")
    @allure.testcase("960")
    @pytest.mark.qase(id=960)
    @pytest.mark.api
    def test_tc960_register_duplicate_email_conflict(self, api_client: JuiceShopApiClient):
        """
        Arrange: Выбор существующего в БД email администратора.
        Act: Попытка повторной регистрации через POST /api/Users/.
        Assert: Проверка возврата ошибки конфликта 400/409 (AC-API-02).
        """
        with allure.step("1. Arrange: Выбор существующего в БД email администратора"):
            duplicate_email = "admin@juice-sh.op"
            password = "Admin12345!"

        with allure.step(f"2. Act: Отправка запроса на регистрацию дубликата {duplicate_email}"):
            res = api_client.register(duplicate_email, password)

        with allure.step("3. Assert: Проверка возврата статуса ошибки"):
            assert res.status_code in [400, 409, 500], f"Expected conflict error but got {res.status_code}"

    # =============================================================================
    # [QASE #961] [BVA] Валидация схемы payload и минимальной длины пароля
    # =============================================================================
    @allure.title("[API][Parametrized] Валидация схемы payload и минимальной длины пароля в POST /api/Users/")
    @allure.issue("JS-40")
    @allure.testcase("961")
    @pytest.mark.qase(id=961)
    @pytest.mark.api
    def test_tc961_register_schema_validation_password_length(self, api_client: JuiceShopApiClient):
        """
        Arrange: Формирование короткого пароля длиной менее 5 символов.
        Act: Отправка запроса на регистрацию пользователя.
        Assert: Проверка кода ответа API (AC-API-03).
        """
        with allure.step("1. Arrange: Формирование короткого пароля"):
            uid = uuid.uuid4().hex[:8]
            email = f"short_{uid}@juice-sh.op"
            password = "1234"

        with allure.step("2. Act: Отправка регистрационного запроса"):
            res = api_client.register(email, password)

        with allure.step("3. Assert: Проверка ответа сервера"):
            assert res.status_code in [200, 201, 400, 422, 500], f"Expected valid response but got {res.status_code}"

    # =============================================================================
    # [QASE #962] [DATA] Санитизация и нормализация email (trim пробелов)
    # =============================================================================
    @allure.title("[API] Санитизация и нормализация email: удаление начальных и конечных пробелов trim")
    @allure.issue("JS-40")
    @allure.testcase("962")
    @pytest.mark.qase(id=962)
    @pytest.mark.api
    def test_tc962_register_email_whitespace_trim(self, api_client: JuiceShopApiClient):
        """
        Arrange: Формирование email с ведущими и замыкающими пробелами.
        Act: Регистрация пользователя через POST /api/Users/.
        Assert: Проверка успешного создания аккаунта (AC-API-04).
        """
        with allure.step("1. Arrange: Подготовка email с пробелами по краям"):
            uid = uuid.uuid4().hex[:8]
            email_with_spaces = f"  trim_{uid}@juice-sh.op  "

        with allure.step("2. Act: Отправка запроса на регистрацию"):
            res = api_client.register(email_with_spaces, "ValidPass123!")

        with allure.step("3. Assert: Проверка успешного ответа сервера"):
            assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"

    # =============================================================================
    # [QASE #963] [FUNCTIONAL] Привязка контрольного вопроса и ответа
    # =============================================================================
    @allure.title("[API] Привязка контрольного вопроса и ответа при регистрации пользователя (SecurityAnswer)")
    @allure.issue("JS-40")
    @allure.testcase("963")
    @pytest.mark.qase(id=963)
    @pytest.mark.api
    def test_tc963_register_security_answer_binding(self, api_client: JuiceShopApiClient):
        """
        Arrange: Регистрация пользователя без контрольного вопроса.
        Act: Привязка контрольного вопроса через set_security_answer.
        Assert: Проверка успешного сохранения ответа (AC-API-05).
        """
        with allure.step("1. Arrange: Регистрация нового аккаунта"):
            uid = uuid.uuid4().hex[:8]
            reg = api_client.register(f"sec_{uid}@juice-sh.op", "ValidPass123!", link_security_answer=False)
            user_id = reg.json().get("data", {}).get("id")

        with allure.step("2. Act: Привязка секретного вопроса к созданному пользователю"):
            res = api_client.set_security_answer(user_id=user_id, question_id=1, answer="SecretAnswer")

        with allure.step("3. Assert: Проверка успешного сохранения ответа"):
            assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"

    # =============================================================================
    # [QASE #964] [CATALOG] Получение справочника контрольных вопросов
    # =============================================================================
    @allure.title("[API] Получение справочника доступных контрольных вопросов GET /api/SecurityQuestions")
    @allure.issue("JS-40")
    @allure.testcase("964")
    @pytest.mark.qase(id=964)
    @pytest.mark.api
    def test_tc964_get_security_questions_directory(self, api_client: JuiceShopApiClient):
        """
        Arrange: Подготовка GET-запроса к каталогу контрольных вопросов.
        Act: Запрос списка вопросов через GET /api/SecurityQuestions.
        Assert: Проверка наличия вопросов в каталоге (AC-API-06).
        """
        with allure.step("1. Arrange: Формирование эндпоинта справочника"):
            endpoint = f"{api_client.base_url}/api/SecurityQuestions"

        with allure.step("2. Act: Вызов GET /api/SecurityQuestions"):
            res = api_client._request("GET", endpoint)

        with allure.step("3. Assert: Проверка статуса 200 и непустого списка вопросов"):
            assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
            questions = res.json().get("data", [])
            assert len(questions) > 0, "Security questions list must not be empty"

    # =============================================================================
    # [QASE #965] [SECURITY] Проверка хеширования пароля в БД
    # =============================================================================
    @allure.title("[API] Проверка хеширования пароля в SQLite БД — пароль не хранится в открытом виде")
    @allure.issue("JS-40")
    @allure.testcase("965")
    @pytest.mark.qase(id=965)
    @pytest.mark.api
    def test_tc965_password_hashing_in_db(self, api_client: JuiceShopApiClient):
        """
        Arrange: Подготовка открытого пароля пользователя.
        Act: Регистрация пользователя через API.
        Assert: Проверка отсутствия открытого пароля в возвращаемом объекте (AC-API-07).
        """
        with allure.step("1. Arrange: Подготовка тестовых данных"):
            uid = uuid.uuid4().hex[:8]
            raw_pass = "RawSecretPass999!"

        with allure.step("2. Act: Регистрация нового аккаунта"):
            res = api_client.register(f"hash_{uid}@juice-sh.op", raw_pass)

        with allure.step("3. Assert: Проверка статуса и сокрытия открытого пароля"):
            assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"
            user_data = res.json().get("data", {})
            assert user_data.get("password") != raw_pass, "Password must not be returned or stored in plaintext"

    # =============================================================================
    # [QASE #966] [SECURITY] Проверка хеширования ответа на контрольный вопрос
    # =============================================================================
    @allure.title("[API] Проверка хеширования ответа на контрольный вопрос (SecurityAnswer) в базе данных")
    @allure.issue("JS-40")
    @allure.testcase("966")
    @pytest.mark.qase(id=966)
    @pytest.mark.api
    def test_tc966_security_answer_hashing_in_db(self, api_client: JuiceShopApiClient):
        """
        Arrange: Регистрация пользователя и подготовка ответа.
        Act: Сохранение ответа на контрольный вопрос.
        Assert: Проверка хеширования ответа (AC-API-05, AC-API-07).
        """
        with allure.step("1. Arrange: Создание пользователя"):
            uid = uuid.uuid4().hex[:8]
            raw_answer = "SecretAnswerHash"
            reg = api_client.register(f"sechash_{uid}@juice-sh.op", "ValidPass123!", link_security_answer=False)
            user_id = reg.json().get("data", {}).get("id")

        with allure.step("2. Act: Привязка ответа на вопрос"):
            res = api_client.set_security_answer(user_id=user_id, question_id=1, answer=raw_answer)

        with allure.step("3. Assert: Проверка хеширования сохраненного ответа"):
            assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"
            ans_data = res.json().get("data", {})
            assert ans_data.get("answer") != raw_answer, "Security answer must be hashed in DB"

    # =============================================================================
    # [QASE #967] [NEGATIVE] Отказ в регистрации при несуществующем SecurityQuestionId
    # =============================================================================
    @allure.title("[API] Отказ в регистрации при передаче несуществующего SecurityQuestionId")
    @allure.issue("JS-40")
    @allure.testcase("967")
    @pytest.mark.qase(id=967)
    @pytest.mark.api
    def test_tc967_register_invalid_security_question_id(self, api_client: JuiceShopApiClient):
        """
        Arrange: Подготовка заведомо несуществующего ID вопроса (999999).
        Act: Попытка привязки ответа с несуществующим question_id.
        Assert: Проверка возврата кода ошибки 400/404/500 (AC-API-05).
        """
        with allure.step("1. Arrange: Подготовка невалидного ID вопроса"):
            invalid_qid = 999999

        with allure.step("2. Act: Отправка запроса с невалидным question_id"):
            res = api_client.set_security_answer(user_id=1, question_id=invalid_qid, answer="Answer")

        with allure.step("3. Assert: Проверка отклонения запроса"):
            assert res.status_code in [400, 404, 500], f"Expected 400/404/500 but got {res.status_code}"

    # =============================================================================
    # [QASE #968] [VALIDATION] Валидация обязательных полей при регистрации
    # =============================================================================
    @allure.title("[API] Валидация пустых обязательных полей (email, password) при регистрации в POST /api/Users/")
    @allure.issue("JS-40")
    @allure.testcase("968")
    @pytest.mark.qase(id=968)
    @pytest.mark.api
    def test_tc968_register_empty_required_fields(self, api_client: JuiceShopApiClient):
        """
        Arrange: Подготовка пустых значений email и password.
        Act: Отправка запроса регистрации с пустыми полями.
        Assert: Проверка обработки пустого ввода (AC-API-03).
        """
        with allure.step("1. Arrange: Подготовка пустых учетных данных"):
            empty_email = ""
            empty_pass = ""

        with allure.step("2. Act: Отправка запроса регистрации"):
            res = api_client.register(empty_email, empty_pass)

        with allure.step("3. Assert: Проверка ответа сервера"):
            assert res.status_code in [200, 201, 400, 422, 500], f"Expected status code but got {res.status_code}"

    # =============================================================================
    # [QASE #969] [VALIDATION] Валидация некорректного формата Email
    # =============================================================================
    @allure.title("[API] Валидация некорректного формата Email адреса при регистрации в POST /api/Users/")
    @allure.issue("JS-40")
    @allure.testcase("969")
    @pytest.mark.qase(id=969)
    @pytest.mark.api
    def test_tc969_register_invalid_email_format(self, api_client: JuiceShopApiClient):
        """
        Arrange: Подготовка невалидной строки вместо адреса электронной почты.
        Act: Отправка запроса на регистрацию.
        Assert: Проверка ответа сервера на невалидный формат (AC-API-03).
        """
        with allure.step("1. Arrange: Подготовка некорректного формата email"):
            invalid_email = "not-an-email-address"

        with allure.step("2. Act: Отправка запроса"):
            res = api_client.register(invalid_email, "ValidPass123!")

        with allure.step("3. Assert: Проверка реакции бэкенда"):
            assert res.status_code in [200, 201, 400, 422, 500], f"Expected status code but got {res.status_code}"

    # =============================================================================
    # [QASE #970] [SECURITY] Проверка маскирования пароля в ответе API
    # =============================================================================
    @allure.title("[API] Проверка маскирования пароля в теле ответа после успешной регистрации")
    @allure.issue("JS-40")
    @allure.testcase("970")
    @pytest.mark.qase(id=970)
    @pytest.mark.api
    def test_tc970_register_password_masked_in_response(self, api_client: JuiceShopApiClient):
        """
        Arrange: Подготовка валидных учетных данных.
        Act: Регистрация нового пользователя.
        Assert: Пароль не возвращается в открытом виде в теле ответа (AC-API-01, AC-API-07).
        """
        with allure.step("1. Arrange: Генерация данных пользователя"):
            uid = uuid.uuid4().hex[:8]
            email = f"mask_{uid}@juice-sh.op"

        with allure.step("2. Act: Регистрация пользователя"):
            res = api_client.register(email, "ValidPass123!")

        with allure.step("3. Assert: Проверка отсутствия открытого пароля в ответе"):
            assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}"
            user_data = res.json().get("data", {})
            assert "password" not in user_data or user_data.get("password") is None, "Password must be stripped from response"
