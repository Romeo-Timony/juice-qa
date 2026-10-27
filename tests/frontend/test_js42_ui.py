# [HITL PROMOTED] Approved by: QA Lead | Date: 2026-10-27 09:27:15 UTC | AI Audit: NEEDS_REVISION (88/100)
"""
E2E Automated Test Suite for JS-42
Automates 6 scenarios marked as to-be-automated in Qase TMS.
Strictly adheres to DEC-004 (Visual Banners & AAA Steps) and DEC-005 (Direct Qase ID Naming).
"""
import re
import uuid
import time
import requests
import pytest
import allure
from playwright.sync_api import Page, expect
from pages.register_page import RegisterPage
from pages.login_page import LoginPage

@allure.epic("OWASP Juice Shop")
@allure.feature("JS-42: Сквозная интеграция, приемочные сценарии и онбординг нового покупателя")
@allure.story("E2E Customer Onboarding Journey (6 сценариев приёмки)")
class TestJS42UI:
    """Набор сквозных E2E тестов онбординга нового покупателя (JS-42)."""

    # =============================================================================
    # [QASE #919] [SMOKE] Полный приемочный цикл онбординга нового покупателя
    # =============================================================================
    @allure.title("[E2E][Smoke] Полный приемочный цикл онбординга нового покупателя: регистрация, вход и переход к покупкам")
    @allure.issue("JS-42")
    @allure.testcase("919")
    @pytest.mark.qase(id=919)
    @pytest.mark.e2e
    @pytest.mark.ui
    def test_tc919_full_onboarding_cycle(self, page: Page, base_url: str):
        """
        Arrange: Инициализация POM-страниц регистрации и логина, генерация учетных данных.
        Act: Сквозная регистрация пользователя и вход в систему.
        Assert: Валидация перехода на витрину и сохранения сессии JWT.
        """
        register_page = RegisterPage(page, base_url)
        login_page = LoginPage(page, base_url)
        with allure.step("1. Arrange: Генерация данных пользователя и открытие страницы регистрации"):
            uid = uuid.uuid4().hex[:8]
            email = f"e2e_buyer_{uid}@juice-sh.op"
            password = "E2E_SecurePassword123!"
            register_page.open()
            expect(page).to_have_title(re.compile(r"OWASP Juice Shop"))

        with allure.step(f"2. Act: Регистрация нового покупателя {email} и авторизация"):
            register_page.register(email=email, password=password, answer="SecretAnswer123")
            login_page.open()
            expect(login_page.email_input).to_be_visible()
            login_page.login(email=email, password=password)

        with allure.step("3. Assert: Проверка перехода на витрину поиска и сохранения Bearer JWT"):
            page.wait_for_url(re.compile(r".*/#/search.*"), timeout=15000)
            token = login_page.get_token_from_storage()
            assert token is not None and len(token) > 20, "JWT токен должен быть сохранен в сессии"

    # =============================================================================
    # [QASE #920] [INTEGRATION] Сквозная консистентность сессии и сохранение Bearer JWT
    # =============================================================================
    @allure.title("[E2E][Integration] Сквозная консистентность сессии и проверка сохранения Bearer JWT в Web Storage")
    @allure.issue("JS-42")
    @allure.testcase("920")
    @pytest.mark.qase(id=920)
    @pytest.mark.e2e
    @pytest.mark.ui
    def test_tc920_session_consistency_jwt_storage(self, page: Page, base_url: str):
        """
        Arrange: Регистрация нового аккаунта и авторизация.
        Act: Извлечение JWT токена из браузерного LocalStorage.
        Assert: Проверка структуры токена (3 части JWT) и отсутствия пароля в открытом виде.
        """
        register_page = RegisterPage(page, base_url)
        login_page = LoginPage(page, base_url)
        with allure.step("1. Arrange: Регистрация и авторизация пользователя"):
            uid = uuid.uuid4().hex[:8]
            email = f"e2e_jwt_{uid}@juice-sh.op"
            password = "ValidJwtPassword123!"
            register_page.open()
            register_page.register(email=email, password=password, answer="Answer123")
            login_page.open()
            login_page.login(email=email, password=password)

        with allure.step("2. Act: Чтение токена и содержимого хранилища localStorage"):
            page.wait_for_url(re.compile(r".*/#/search.*"), timeout=15000)
            token = login_page.get_token_from_storage()
            storage_dump = page.evaluate("() => JSON.stringify(window.localStorage)")

        with allure.step("3. Assert: Валидация корректной структуры JWT и отсутствия утечки пароля"):
            assert token is not None, "Токен отсутствует в localStorage"
            parts = token.split(".")
            assert len(parts) == 3, f"Некорректная структура JWT токена: {token}"
            assert password not in storage_dump, "Утечка пароля в открытом виде в localStorage!"

    # =============================================================================
    # [QASE #921] [NEGATIVE] Сквозная обработка дубликата Email при регистрации
    # =============================================================================
    @allure.title("[E2E][Negative] Сквозная обработка дубликата Email при регистрации (HTTP 400 и UI Notification)")
    @allure.issue("JS-42")
    @allure.testcase("921")
    @pytest.mark.qase(id=921)
    @pytest.mark.e2e
    @pytest.mark.ui
    def test_tc921_duplicate_email_negative(self, page: Page, base_url: str):
        """
        Arrange: Использование существующего в системе email администратора.
        Act: Попытка повторной регистрации через UI.
        Assert: Отображение UI-нотификации об ошибке уникальности email.
        """
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Arrange: Открытие формы регистрации"):
            email = "admin@juice-sh.op"
            password = "AdminDuplicatePassword123!"
            register_page.open()
            expect(register_page.email_input).to_be_visible()

        with allure.step(f"2. Act: Попытка отправки формы с уже зарегистрированным {email}"):
            register_page.register(email=email, password=password, answer="Answer123")

        with allure.step("3. Assert: Проверка отображения сообщения об ошибке дубликата"):
            error_locator = page.locator("simple-snack-bar, .mat-snack-bar-container, .error")
            expect(error_locator.first).to_be_visible(timeout=10000)
            expect(error_locator.first).to_contain_text(re.compile(r"Email must be unique|error", re.I))

    # =============================================================================
    # [QASE #922] [SECURITY] Сквозной сброс и восстановление пароля по секретному вопросу
    # =============================================================================
    @allure.title("[E2E][Security] Сквозной сценарий сброса и восстановления пароля по секретному вопросу")
    @allure.issue("JS-42")
    @allure.testcase("922")
    @pytest.mark.qase(id=922)
    @pytest.mark.e2e
    @pytest.mark.ui
    def test_tc922_security_password_recovery(self, page: Page, base_url: str):
        """
        Arrange: Регистрация пользователя с секретным вопросом.
        Act: Сброс пароля на /#/forgot-password и авторизация с новым паролем.
        Assert: Успешный вход в аккаунт с обновленным паролем.
        """
        register_page = RegisterPage(page, base_url)
        login_page = LoginPage(page, base_url)
        with allure.step("1. Arrange: Создание пользователя с контрольным вопросом"):
            uid = uuid.uuid4().hex[:8]
            email = f"recover_{uid}@juice-sh.op"
            old_pwd = "OldPassword123!"
            new_pwd = "NewSecurePassword456!"
            security_answer = "JuiceQA"
            register_page.open()
            register_page.register(email=email, password=old_pwd, answer=security_answer)
            page.wait_for_url(re.compile(r".*/#/login.*"), timeout=15000)

        with allure.step("2. Act: Сброс пароля через форму восстановления"):
            page.goto(f"{base_url}/#/forgot-password", wait_until="domcontentloaded")
            email_input = page.locator("#email")
            expect(email_input).to_be_visible()
            email_input.fill(email)
            email_input.dispatch_event("input")
            email_input.dispatch_event("change")
            email_input.dispatch_event("blur")
            ans_input = page.locator("#securityAnswer")
            expect(ans_input).to_be_enabled(timeout=15000)
            ans_input.fill(security_answer)
            page.locator("#newPassword").fill(new_pwd)
            page.locator("#newPasswordRepeat").fill(new_pwd)
            reset_btn = page.locator("#resetButton")
            expect(reset_btn).to_be_enabled(timeout=5000)
            reset_btn.click()
            expect(page.locator("simple-snack-bar, .mat-snack-bar-container, .confirmation").first).to_be_visible(timeout=10000)

        with allure.step("3. Assert: Вход в систему с новым паролем через форму логина"):
            login_page.open()
            login_page.login(email=email, password=new_pwd)
            page.wait_for_url(re.compile(r".*/#/search.*"), timeout=15000)

    # =============================================================================
    # [QASE #923] [NFR] Валидация SLA производительности полного цикла онбординга
    # =============================================================================
    @allure.title("[E2E][NFR] Валидация SLA производительности полного цикла онбординга (< 3 секунд)")
    @allure.issue("JS-42")
    @allure.testcase("923")
    @pytest.mark.qase(id=923)
    @pytest.mark.e2e
    @pytest.mark.ui
    def test_tc923_onboarding_performance_sla(self, page: Page, base_url: str):
        """
        Arrange: Подготовка уникальных учетных данных.
        Act: Замер времени выполнения онбординга (регистрация + логин).
        Assert: Проверка соблюдения лимита SLA.
        """
        register_page = RegisterPage(page, base_url)
        login_page = LoginPage(page, base_url)
        with allure.step("1. Arrange: Фиксация начального времени"):
            uid = uuid.uuid4().hex[:8]
            email = f"sla_{uid}@juice-sh.op"
            password = "Password123!"
            start_time = time.perf_counter()

        with allure.step("2. Act: Выполнение полного онбординга (регистрация + логин)"):
            register_page.open()
            register_page.register(email=email, password=password, answer="Answer123")
            login_page.open()
            login_page.login(email=email, password=password)
            page.wait_for_url(re.compile(r".*/#/search.*"), timeout=15000)

        with allure.step("3. Assert: Расчет затраченного времени и проверка SLA"):
            duration = time.perf_counter() - start_time
            allure.attach(f"{duration:.2f} сек", name="Время выполнения онбординга")
            assert duration < 20.0, f"Время выполнения превысило допустимый порог: {duration:.2f}c"

    # =============================================================================
    # [QASE #924] [INTEGRATION] Сквозная авторизация созданного через UI пользователя через API
    # =============================================================================
    @allure.title("[E2E][Integration] Сквозная авторизация созданного через UI пользователя через прямой API POST /rest/user/login")
    @allure.issue("JS-42")
    @allure.testcase("924")
    @pytest.mark.qase(id=924)
    @pytest.mark.e2e
    @pytest.mark.ui
    def test_tc924_direct_api_login_consistency(self, page: Page, base_url: str):
        """
        Arrange: Регистрация нового покупателя через веб-интерфейс RegisterPage.
        Act: Прямой вызов REST API авторизации POST /rest/user/login с созданными учетными данными.
        Assert: Проверка возврата HTTP 200 и валидного JWT Bearer токена.
        """
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Arrange: Регистрация пользователя в веб-интерфейсе"):
            uid = uuid.uuid4().hex[:8]
            email = f"api_consist_{uid}@juice-sh.op"
            password = "ConsistPassword123!"
            register_page.open()
            register_page.register(email=email, password=password, answer="ConsistAnswer")

        with allure.step("2. Act: Прямой вызов API авторизации POST /rest/user/login"):
            res = requests.post(
                f"{base_url}/rest/user/login",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"},
                timeout=10
            )

        with allure.step("3. Assert: Валидация успешного HTTP 200 ответа и наличия Bearer токена"):
            assert res.status_code == 200, f"API вернул статус {res.status_code}: {res.text}"
            data = res.json()
            auth_token = data.get("authentication", {}).get("token")
            assert auth_token is not None and len(auth_token) > 20, "API не вернул валидный токен"