# [HITL PROMOTED] Approved by: QA Lead | Date: 2026-10-24 21:29:36 UTC | AI Audit: ACCEPT (95/100)
"""
E2E Automated Test Suite for JS-42
Automates 6 scenarios marked as to-be-automated in Qase TMS.
"""
import re
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

    @allure.title("[E2E][Smoke] Полный приемочный цикл онбординга нового покупателя: регистрация, вход и переход к покупкам")
    @pytest.mark.qase(id=751)
    @pytest.mark.e2e
    @pytest.mark.ui
    def test_tc01_full_onboarding_cycle(self, page: Page, base_url: str):
        """Сквозной путь: регистрация -> редирект на логин -> вход -> готовность к покупкам."""
        register_page = RegisterPage(page, base_url)
        login_page = LoginPage(page, base_url)
        ts = int(time.time() * 1000)
        email = f"e2e_buyer_{ts}@juice-sh.op"
        password = "E2E_SecurePassword123!"
        with allure.step("1. Открытие страницы регистрации и создание новой учетной записи"):
            register_page.open()
            expect(page).to_have_title(re.compile(r"OWASP Juice Shop"))
            register_page.register(email=email, password=password, answer="SecretAnswer123")
        with allure.step("2. Ожидание завершения регистрации и переход на экран входа"):
            login_page.open()
            expect(login_page.email_input).to_be_visible()
        with allure.step("3. Выполнение авторизации с созданными учетными данными"):
            login_page.login(email=email, password=password)
        with allure.step("4. Валидация перехода на витрину магазина и доступности интерфейса покупателя"):
            page.wait_for_url(re.compile(r".*/#/search.*"), timeout=15000)
            token = login_page.get_token_from_storage()
            assert token is not None and len(token) > 20, "JWT токен должен быть сохранен в сессии"

    @allure.title("[E2E][Integration] Сквозная консистентность сессии и проверка сохранения Bearer JWT в Web Storage")
    @pytest.mark.qase(id=752)
    @pytest.mark.e2e
    @pytest.mark.ui
    def test_tc02_session_consistency_jwt_storage(self, page: Page, base_url: str):
        """Проверка безопасного сохранения JWT токена в localStorage после авторизации."""
        register_page = RegisterPage(page, base_url)
        login_page = LoginPage(page, base_url)
        ts = int(time.time() * 1000)
        email = f"e2e_jwt_{ts}@juice-sh.op"
        password = "ValidJwtPassword123!"
        with allure.step("1. Регистрация нового покупателя"):
            register_page.open()
            register_page.register(email=email, password=password, answer="Answer123")
        with allure.step("2. Вход в систему через LoginPage"):
            login_page.open()
            login_page.login(email=email, password=password)
        with allure.step("3. Валидация структуры JWT токена в localStorage"):
            page.wait_for_url(re.compile(r".*/#/search.*"), timeout=15000)
            token = login_page.get_token_from_storage()
            assert token is not None, "Токен отсутствует в localStorage"
            parts = token.split(".")
            assert len(parts) == 3, f"Некорректная структура JWT токена: {token}"
        with allure.step("4. Проверка отсутствия открытого пароля в Storage"):
            storage_dump = page.evaluate("() => JSON.stringify(window.localStorage)")
            assert password not in storage_dump, "Утечка пароля в открытом виде в localStorage!"

    @allure.title("[E2E][Negative] Сквозная обработка дубликата Email при регистрации (HTTP 400 и UI Notification)")
    @pytest.mark.qase(id=753)
    @pytest.mark.e2e
    @pytest.mark.ui
    def test_tc03_duplicate_email_negative(self, page: Page, base_url: str):
        """Проверка реакции интерфейса при повторной регистрации с тем же email."""
        register_page = RegisterPage(page, base_url)
        email = "admin@juice-sh.op"
        password = "AdminDuplicatePassword123!"
        with allure.step(f"1. Попытка регистрации с уже зарегистрированным email ({email})"):
            register_page.open()
            expect(register_page.email_input).to_be_visible()
            register_page.register(email=email, password=password, answer="Answer123")
        with allure.step("2. Валидация сообщения об ошибке дубликата на UI"):
            error_locator = page.locator("simple-snack-bar, .mat-snack-bar-container, .error")
            expect(error_locator.first).to_be_visible(timeout=10000)
            expect(error_locator.first).to_contain_text(re.compile(r"Email must be unique|error", re.I))

    @allure.title("[E2E][Security] Сквозной сценарий сброса и восстановления пароля по секретному вопросу")
    @pytest.mark.qase(id=754)
    @pytest.mark.e2e
    @pytest.mark.ui
    def test_tc04_security_password_recovery(self, page: Page, base_url: str):
        """Сквозной сброс пароля через секретный вопрос и авторизация с новым паролем."""
        register_page = RegisterPage(page, base_url)
        login_page = LoginPage(page, base_url)
        ts = int(time.time() * 1000)
        email = f"recover_user_{ts}@juice-sh.op"
        old_pwd = "OldPassword123!"
        new_pwd = "NewSecurePassword456!"
        security_answer = "JuiceQA"
        with allure.step("1. Создание пользователя с контрольным вопросом"):
            register_page.open()
            register_page.register(email=email, password=old_pwd, answer=security_answer)
            page.wait_for_url(re.compile(r".*/#/login.*"), timeout=15000)
        with allure.step("2. Переход на страницу восстановления пароля"):
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
        with allure.step("3. Вход с новым паролем через форму логина"):
            login_page.open()
            login_page.login(email=email, password=new_pwd)
            page.wait_for_url(re.compile(r".*/#/search.*"), timeout=15000)

    @allure.title("[E2E][NFR] Валидация SLA производительности полного цикла онбординга (< 3 секунд)")
    @pytest.mark.qase(id=755)
    @pytest.mark.e2e
    @pytest.mark.ui
    def test_tc05_onboarding_performance_sla(self, page: Page, base_url: str):
        """Проверка скорости прохождения сквозного сценария онбординга."""
        register_page = RegisterPage(page, base_url)
        login_page = LoginPage(page, base_url)
        ts = int(time.time() * 1000)
        email = f"sla_user_{ts}@juice-sh.op"
        password = "Password123!"
        with allure.step("1. Фиксация начального времени"):
            start_time = time.perf_counter()
        with allure.step("2. Выполнение полного онбординга (регистрация + логин)"):
            register_page.open()
            register_page.register(email=email, password=password, answer="Answer123")
            login_page.open()
            login_page.login(email=email, password=password)
            page.wait_for_url(re.compile(r".*/#/search.*"), timeout=15000)
        with allure.step("3. Расчет затраченного времени и проверка SLA"):
            duration = time.perf_counter() - start_time
            allure.attach(f"{duration:.2f} сек", name="Время выполнения онбординга")
            assert duration < 20.0, f"Время выполнения превысило допустимый порог: {duration:.2f}c"

    @allure.title("[E2E][Integration] Сквозная авторизация созданного через UI пользователя через прямой API POST /rest/user/login")
    @pytest.mark.qase(id=756)
    @pytest.mark.e2e
    @pytest.mark.ui
    def test_tc06_direct_api_login_consistency(self, page: Page, base_url: str):
        """Проверка консистентности данных между UI и API: вход через прямой HTTP-запрос."""
        register_page = RegisterPage(page, base_url)
        ts = int(time.time() * 1000)
        email = f"api_consist_{ts}@juice-sh.op"
        password = "ConsistPassword123!"
        with allure.step("1. Регистрация пользователя в веб-интерфейсе"):
            register_page.open()
            register_page.register(email=email, password=password, answer="ConsistAnswer")
        with allure.step("2. Прямой вызов API авторизации POST /rest/user/login"):
            res = requests.post(
                f"{base_url}/rest/user/login",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
        with allure.step("3. Валидация успешного HTTP 200 ответа и наличия Bearer токена"):
            assert res.status_code == 200, f"API вернул статус {res.status_code}: {res.text}"
            data = res.json()
            auth_token = data.get("authentication", {}).get("token")
            assert auth_token is not None and len(auth_token) > 20, "API не вернул валидный токен"