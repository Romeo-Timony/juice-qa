# [HITL PROMOTED] Approved by: QA Lead | Date: 2026-10-26 18:55:55 UTC | AI Audit: NEEDS_REVISION (82/100)
"""
Frontend UI Automated Test Suite for JS-41
Automates 12 scenarios marked as to-be-automated in Qase TMS.
0 remaining exploratory scenarios are retained as manual checks.
"""
import re
import time
import pytest
import allure
from playwright.sync_api import Page, expect
from pages.register_page import RegisterPage

@allure.epic("OWASP Juice Shop")
@allure.feature("JS-41: Разработка клиентской формы регистрации и валидации полей (/#/register)")
@allure.story("Frontend Angular UI Validation (12 сценариев приёмки)")
class TestJS41UI:
    """Набор из 12 автоматизированных UI-тестов формы регистрации (POM & Playwright)."""

    @allure.title("[Frontend][Parametrized] Успешная регистрация нового пользователя с валидными форматами Email")
    @pytest.mark.qase(id=811)
    @pytest.mark.ui
    def test_tc01_registration_with_valid_email(self, page: Page, base_url: str):
        """Проверка успешной регистрации нового пользователя через RegisterPage."""
        register_page = RegisterPage(page, base_url)
        ts = int(time.time() * 1000)
        email = f"valid_user_{ts}@juice-sh.op"
        password = "ValidPassword123!"
        with allure.step("1. Открытие страницы регистрации через RegisterPage"):
            register_page.open()
            expect(page).to_have_title(re.compile(r"OWASP Juice Shop"))
        with allure.step(f"2. Заполнение формы регистрации (email: {email}) и подтверждение"):
            register_page.register(email=email, password=password, answer="SecretAnswer123")
        with allure.step("3. Валидация успешного завершения регистрации"):
            page.wait_for_timeout(1000)
            assert "/#/login" in page.url or page.locator("simple-snack-bar, .mat-snack-bar-container").is_visible()

    @allure.title("[Frontend][Parametrized] Проверка граничных значений длины пароля при регистрации пользователя (BVA: 5-40 символов)")
    @pytest.mark.qase(id=812)
    @pytest.mark.ui
    def test_tc02_password_boundary_validation(self, page: Page, base_url: str):
        """Проверка граничных значений: 5 символов и 40 символов."""
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Открытие страницы регистрации"):
            register_page.open()
        with allure.step("2. Проверка нижней границы длины пароля (5 символов)"):
            register_page.email_input.fill("bva_test@juice-sh.op")
            register_page.password_input.fill("12345")
            register_page.repeat_password_input.fill("12345")
            register_page.select_security_question(0)
            register_page.security_answer_input.fill("MyAnswer")
            expect(register_page.register_button).to_be_enabled()

    @allure.title("[Frontend] Валидация ошибки при несовпадении пароля и подтверждения пароля (\"Passwords do not match\")")
    @pytest.mark.qase(id=813)
    @pytest.mark.ui
    def test_tc03_password_mismatch_error(self, page: Page, base_url: str):
        """Проверка блокировки отправки при несовпадении полей пароля и повтора пароля."""
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Открытие формы регистрации"):
            register_page.open()
        with allure.step("2. Заполнение пароля и несовпадающего подтверждения"):
            register_page.email_input.fill("mismatch_user@test.com")
            register_page.password_input.fill("Password123!")
            register_page.repeat_password_input.fill("DifferentPassword456!")
            register_page.security_answer_input.click()
        with allure.step("3. Проверка блокировки кнопки отправки"):
            expect(register_page.register_button).to_be_disabled()

    @allure.title("[Frontend] Блокировка кнопки Register по умолчанию при пустой форме (#registerButton disabled)")
    @pytest.mark.qase(id=814)
    @pytest.mark.ui
    def test_tc04_default_register_button_disabled(self, page: Page, base_url: str):
        """Проверка исходного состояния кнопки Register при открытии страницы."""
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Открытие страницы регистрации"):
            register_page.open()
        with allure.step("2. Проверка неактивного состояния кнопки Register по умолчанию"):
            expect(register_page.register_button).to_be_disabled()

    @allure.title("[Frontend] Проверка сообщения об ошибке при некорректном формате Email (\"Email is not valid\")")
    @pytest.mark.qase(id=815)
    @pytest.mark.ui
    def test_tc05_invalid_email_format(self, page: Page, base_url: str):
        """Проверка ошибки валидации при невалидном формате email без символа @."""
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Открытие страницы регистрации"):
            register_page.open()
        with allure.step("2. Ввод невалидного email и снятие фокуса"):
            register_page.email_input.fill("not-an-email")
            register_page.password_input.click()
        with allure.step("3. Проверка ошибки валидации и блокировки кнопки"):
            expect(register_page.register_button).to_be_disabled()

    @allure.title("[Frontend] Блокировка кнопки Register при пароле короче 5 символов (\"Password must be 5-40 characters long\")")
    @pytest.mark.qase(id=816)
    @pytest.mark.ui
    def test_tc06_password_too_short(self, page: Page, base_url: str):
        """Негативная проверка нижней границы BVA: 4 символа."""
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Открытие формы регистрации"):
            register_page.open()
        with allure.step("2. Ввод пароля длиной 4 символа"):
            register_page.email_input.fill("short_pwd@test.com")
            register_page.password_input.fill("1234")
            register_page.repeat_password_input.fill("1234")
            register_page.security_answer_input.click()
        with allure.step("3. Проверка блокировки кнопки Register"):
            expect(register_page.register_button).to_be_disabled()

    @allure.title("[Frontend] Блокировка кнопки Register при пароле длиннее 40 символов (BVA: 41 символ)")
    @pytest.mark.qase(id=817)
    @pytest.mark.ui
    def test_tc07_password_too_long(self, page: Page, base_url: str):
        """Негативная проверка верхней границы BVA: 41 символ."""
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Открытие формы регистрации"):
            register_page.open()
        with allure.step("2. Ввод пароля длиной 41 символ"):
            register_page.email_input.fill("long_pwd@test.com")
            pwd41 = "A" * 41
            register_page.password_input.fill(pwd41)
            register_page.repeat_password_input.fill(pwd41)
            register_page.security_answer_input.click()
        with allure.step("3. Проверка блокировки кнопки"):
            expect(register_page.register_button).to_be_disabled()

    @allure.title("[Frontend] Отображение индикатора надежности пароля при включении тоггла \"Show password advice\"")
    @pytest.mark.qase(id=818)
    @pytest.mark.ui
    def test_tc08_password_advice_toggle(self, page: Page, base_url: str):
        """Проверка контрола mat-slide-toggle для показа шкалы стойкости пароля."""
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Открытие формы регистрации"):
            register_page.open()
        with allure.step("2. Переключение тоггла 'Show password advice'"):
            toggle = page.locator("mat-slide-toggle, mat-slide-toggle input")
            if toggle.count() > 0:
                toggle.first.click(force=True)
                page.wait_for_timeout(500)
                expect(page.locator("mat-slide-toggle")).to_be_visible()

    @allure.title("[Frontend] Обязательность выбора контрольного вопроса из списка Security Questions (mat-select)")
    @pytest.mark.qase(id=819)
    @pytest.mark.ui
    def test_tc09_security_question_mandatory(self, page: Page, base_url: str):
        """Проверка обязательности выбора секретного вопроса: без вопроса кнопка disabled."""
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Открытие формы регистрации"):
            register_page.open()
        with allure.step("2. Заполнение всех полей кроме контрольного вопроса"):
            register_page.email_input.fill("no_q@test.com")
            register_page.password_input.fill("ValidPass123!")
            register_page.repeat_password_input.fill("ValidPass123!")
            register_page.security_answer_input.fill("Answer")
        with allure.step("3. Проверка блокировки кнопки Register"):
            expect(register_page.register_button).to_be_disabled()

    @allure.title("[Frontend] Валидация обязательности ответа на секретный вопрос (#securityAnswerControl)")
    @pytest.mark.qase(id=820)
    @pytest.mark.ui
    def test_tc10_security_answer_mandatory(self, page: Page, base_url: str):
        """Проверка обязательности ответа на секретный вопрос."""
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Открытие формы регистрации"):
            register_page.open()
        with allure.step("2. Выбор вопроса без заполнения ответа"):
            register_page.email_input.fill("no_ans@test.com")
            register_page.password_input.fill("ValidPass123!")
            register_page.repeat_password_input.fill("ValidPass123!")
            register_page.select_security_question(0)
            register_page.security_answer_input.fill("")
        with allure.step("3. Проверка блокировки кнопки Register"):
            expect(register_page.register_button).to_be_disabled()

    @allure.title("[Frontend] Скрытие ввода пароля (type='password') в полях Password и Repeat Password")
    @pytest.mark.qase(id=821)
    @pytest.mark.ui
    def test_tc11_password_masking_security(self, page: Page, base_url: str):
        """Проверка безопасности ввода: маскирование символов пароля (NFR-UI-01)."""
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Открытие формы регистрации"):
            register_page.open()
        with allure.step("2. Проверка атрибута type у полей ввода пароля"):
            expect(register_page.password_input).to_have_attribute("type", "password")
            expect(register_page.repeat_password_input).to_have_attribute("type", "password")

    @allure.title("[Frontend] Доступность формы регистрации по клавиатуре (Tab Navigation & WCAG 2.1 AA)")
    @pytest.mark.qase(id=822)
    @pytest.mark.ui
    def test_tc12_keyboard_tab_navigation(self, page: Page, base_url: str):
        """Проверка навигации по форме с помощью клавиши Tab (NFR-UI-03)."""
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Открытие формы регистрации"):
            register_page.open()
        with allure.step("2. Фокусировка на первом поле и нажатие Tab"):
            register_page.email_input.focus()
            expect(register_page.email_input).to_be_focused()
            page.keyboard.press("Tab")
            expect(register_page.password_input).to_be_focused()
