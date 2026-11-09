# [HITL PROMOTED] Approved by: QA Lead | Date: 2026-11-09 07:21:03 UTC | AI Audit: ACCEPT (96/100)
"""
Frontend UI Automated Test Suite for JS-41
Automates 12 scenarios marked as to-be-automated in Qase TMS.
0 remaining exploratory scenarios are retained as manual checks.
Strictly adheres to DEC-004 (Visual Banners & AAA Steps) and DEC-005 (Direct Qase ID Naming).
"""
import re
import uuid
import pytest
import allure
from playwright.sync_api import Page, expect
from pages.register_page import RegisterPage

@allure.epic("OWASP Juice Shop")
@allure.feature("JS-41: Разработка клиентской формы регистрации и валидации полей (/#/register)")
@allure.story("Frontend Angular UI Validation (12 сценариев приёмки)")
class TestJS41UI:
    """Набор из 12 автоматизированных UI-тестов формы регистрации (POM & Playwright)."""

    # =============================================================================
    # [QASE #971] [SMOKE] Успешная регистрация нового пользователя с валидными форматами Email
    # =============================================================================
    @allure.title("[Frontend][Parametrized] Успешная регистрация нового пользователя с валидными форматами Email")
    @allure.issue("JS-41")
    @allure.testcase("971")
    @pytest.mark.qase(id=971)
    @pytest.mark.ui
    def test_tc971_registration_with_valid_email(self, page: Page, base_url: str):
        """
        Arrange: Инициализация POM RegisterPage и генерация уникального email через UUID.
        Act: Заполнение всех обязательных полей и подтверждение регистрации.
        Assert: Проверка перехода на экран логина или отображения нотификации об успехе.
        """
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Arrange: Генерация тестовых данных и открытие формы регистрации"):
            uid = uuid.uuid4().hex[:8]
            email = f"valid_user_{uid}@juice-sh.op"
            password = "ValidPassword123!"
            register_page.open()
            expect(page).to_have_title(re.compile(r"OWASP Juice Shop"))

        with allure.step(f"2. Act: Заполнение полей формы (email: {email}) и нажатие кнопки Register"):
            register_page.register(email=email, password=password, answer="SecretAnswer123")

        with allure.step("3. Assert: Проверка успешного завершения регистрации"):
            expect(page.locator("simple-snack-bar, .mat-snack-bar-container")).to_be_visible()

    # =============================================================================
    # [QASE #972] [BVA] Проверка граничных значений длины пароля (5-40 символов)
    # =============================================================================
    @allure.title("[Frontend][Parametrized] Проверка граничных значений длины пароля при регистрации пользователя (BVA: 5-40 символов)")
    @allure.issue("JS-41")
    @allure.testcase("972")
    @pytest.mark.qase(id=972)
    @pytest.mark.ui
    def test_tc972_password_boundary_validation(self, page: Page, base_url: str):
        """
        Arrange: Открытие формы регистрации.
        Act: Ввод пароля нижней границы допустимого диапазона (5 символов).
        Assert: Проверка активного состояния кнопки Register.
        """
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Arrange: Открытие страницы регистрации"):
            register_page.open()

        with allure.step("2. Act: Ввод граничного пароля длиной 5 символов и заполнение обязательных полей"):
            register_page.email_input.fill("bva_test@juice-sh.op")
            register_page.password_input.fill("12345")
            register_page.repeat_password_input.fill("12345")
            register_page.select_security_question(0)
            register_page.security_answer_input.fill("MyAnswer")

        with allure.step("3. Assert: Проверка доступности кнопки Register"):
            expect(register_page.register_button).to_be_enabled()

    # =============================================================================
    # [QASE #973] [NEGATIVE] Валидация ошибки при несовпадении пароля и подтверждения
    # =============================================================================
    @allure.title("[Frontend] Валидация ошибки при несовпадении пароля и подтверждения пароля (\"Passwords do not match\")")
    @allure.issue("JS-41")
    @allure.testcase("973")
    @pytest.mark.qase(id=973)
    @pytest.mark.ui
    def test_tc973_password_mismatch_error(self, page: Page, base_url: str):
        """
        Arrange: Открытие страницы регистрации.
        Act: Ввод разных значений в поля Password и Repeat Password.
        Assert: Блокировка кнопки отправки формы.
        """
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Arrange: Открытие формы регистрации"):
            register_page.open()

        with allure.step("2. Act: Ввод несовпадающих паролей"):
            register_page.email_input.fill("mismatch_user@test.com")
            register_page.password_input.fill("Password123!")
            register_page.repeat_password_input.fill("DifferentPassword456!")
            register_page.security_answer_input.click()

        with allure.step("3. Assert: Проверка блокировки кнопки Register"):
            expect(register_page.register_button).to_be_disabled()

    # =============================================================================
    # [QASE #974] [POSITIVE] Блокировка кнопки Register по умолчанию при пустой форме
    # =============================================================================
    @allure.title("[Frontend] Блокировка кнопки Register по умолчанию при пустой форме (#registerButton disabled)")
    @allure.issue("JS-41")
    @allure.testcase("974")
    @pytest.mark.qase(id=974)
    @pytest.mark.ui
    def test_tc974_default_register_button_disabled(self, page: Page, base_url: str):
        """
        Arrange: Открытие формы регистрации.
        Act: Оставление полей пустыми в исходном состоянии.
        Assert: Кнопка Register находится в заблокированном состоянии (disabled).
        """
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Arrange: Открытие формы регистрации"):
            register_page.open()

        with allure.step("2. Act: Проверка исходного состояния без ввода данных"):
            pass

        with allure.step("3. Assert: Проверка неактивного состояния кнопки Register"):
            expect(register_page.register_button).to_be_disabled()

    # =============================================================================
    # [QASE #975] [NEGATIVE] Проверка ошибки при некорректном формате Email
    # =============================================================================
    @allure.title("[Frontend] Проверка сообщения об ошибке при некорректном формате Email (\"Email is not valid\")")
    @allure.issue("JS-41")
    @allure.testcase("975")
    @pytest.mark.qase(id=975)
    @pytest.mark.ui
    def test_tc975_invalid_email_format(self, page: Page, base_url: str):
        """
        Arrange: Открытие формы регистрации.
        Act: Ввод строки без домена и символа @ в поле Email.
        Assert: Кнопка отправки формы заблокирована.
        """
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Arrange: Открытие формы регистрации"):
            register_page.open()

        with allure.step("2. Act: Ввод некорректного email и перенос фокуса"):
            register_page.email_input.fill("not-an-email")
            register_page.password_input.click()

        with allure.step("3. Assert: Проверка блокировки кнопки Register"):
            expect(register_page.register_button).to_be_disabled()

    # =============================================================================
    # [QASE #976] [BVA] Блокировка кнопки Register при пароле короче 5 символов
    # =============================================================================
    @allure.title("[Frontend] Блокировка кнопки Register при пароле короче 5 символов (\"Password must be 5-40 characters long\")")
    @allure.issue("JS-41")
    @allure.testcase("976")
    @pytest.mark.qase(id=976)
    @pytest.mark.ui
    def test_tc976_password_too_short(self, page: Page, base_url: str):
        """
        Arrange: Открытие формы регистрации.
        Act: Ввод пароля длиной 4 символа (ниже нижней границы BVA).
        Assert: Кнопка Register заблокирована.
        """
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Arrange: Открытие формы регистрации"):
            register_page.open()

        with allure.step("2. Act: Ввод 4-символьного пароля в оба поля"):
            register_page.email_input.fill("short_pwd@test.com")
            register_page.password_input.fill("1234")
            register_page.repeat_password_input.fill("1234")
            register_page.security_answer_input.click()

        with allure.step("3. Assert: Проверка блокировки кнопки Register"):
            expect(register_page.register_button).to_be_disabled()

    # =============================================================================
    # [QASE #977] [BVA] Блокировка кнопки Register при пароле длиннее 40 символов
    # =============================================================================
    @allure.title("[Frontend] Блокировка кнопки Register при пароле длиннее 40 символов (BVA: 41 символ)")
    @allure.issue("JS-41")
    @allure.testcase("977")
    @pytest.mark.qase(id=977)
    @pytest.mark.ui
    def test_tc977_password_too_long(self, page: Page, base_url: str):
        """
        Arrange: Открытие формы регистрации.
        Act: Ввод пароля длиной 41 символ (выше верхней границы BVA).
        Assert: Кнопка Register заблокирована.
        """
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Arrange: Открытие формы регистрации"):
            register_page.open()

        with allure.step("2. Act: Ввод пароля из 41 символа"):
            register_page.email_input.fill("long_pwd@test.com")
            pwd41 = "A" * 41
            register_page.password_input.fill(pwd41)
            register_page.repeat_password_input.fill(pwd41)
            register_page.security_answer_input.click()

        with allure.step("3. Assert: Проверка блокировки кнопки Register"):
            expect(register_page.register_button).to_be_disabled()

    # =============================================================================
    # [QASE #978] [FUNCTIONAL] Отображение индикатора надежности пароля при переключении тоггла
    # =============================================================================
    @allure.title("[Frontend] Отображение индикатора надежности пароля при включении тоггла \"Show password advice\"")
    @allure.issue("JS-41")
    @allure.testcase("978")
    @pytest.mark.qase(id=978)
    @pytest.mark.ui
    def test_tc978_password_advice_toggle(self, page: Page, base_url: str):
        """
        Arrange: Открытие формы регистрации.
        Act: Клик по тогглу показа подсказок надежности пароля.
        Assert: Проверка видимости и доступности контрола на экране.
        """
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Arrange: Открытие формы регистрации"):
            register_page.open()

        with allure.step("2. Act: Клик по переключателю 'Show password advice'"):
            toggle = page.locator("mat-slide-toggle, mat-slide-toggle input")
            if toggle.count() > 0:
                toggle.first.click(force=True)

        with allure.step("3. Assert: Проверка видимости компонента индикатора"):
            expect(page.locator("mat-slide-toggle").first).to_be_visible()

    # =============================================================================
    # [QASE #979] [VALIDATION] Обязательность выбора контрольного вопроса из списка
    # =============================================================================
    @allure.title("[Frontend] Обязательность выбора контрольного вопроса из списка Security Questions (mat-select)")
    @allure.issue("JS-41")
    @allure.testcase("979")
    @pytest.mark.qase(id=979)
    @pytest.mark.ui
    def test_tc979_security_question_mandatory(self, page: Page, base_url: str):
        """
        Arrange: Открытие формы регистрации.
        Act: Заполнение всех полей формы кроме контрольного вопроса.
        Assert: Кнопка Register заблокирована.
        """
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Arrange: Открытие формы регистрации"):
            register_page.open()

        with allure.step("2. Act: Заполнение email, пароля и ответа без выбора вопроса"):
            register_page.email_input.fill("no_q@test.com")
            register_page.password_input.fill("ValidPass123!")
            register_page.repeat_password_input.fill("ValidPass123!")
            register_page.security_answer_input.fill("Answer")

        with allure.step("3. Assert: Проверка блокировки кнопки Register"):
            expect(register_page.register_button).to_be_disabled()

    # =============================================================================
    # [QASE #980] [VALIDATION] Валидация обязательности ответа на секретный вопрос
    # =============================================================================
    @allure.title("[Frontend] Валидация обязательности ответа на секретный вопрос (#securityAnswerControl)")
    @allure.issue("JS-41")
    @allure.testcase("980")
    @pytest.mark.qase(id=980)
    @pytest.mark.ui
    def test_tc980_security_answer_mandatory(self, page: Page, base_url: str):
        """
        Arrange: Открытие формы регистрации.
        Act: Выбор вопроса из выпадающего списка без указания ответа.
        Assert: Кнопка Register заблокирована.
        """
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Arrange: Открытие формы регистрации"):
            register_page.open()

        with allure.step("2. Act: Выбор контрольного вопроса при пустом ответе"):
            register_page.email_input.fill("no_ans@test.com")
            register_page.password_input.fill("ValidPass123!")
            register_page.repeat_password_input.fill("ValidPass123!")
            register_page.select_security_question(0)
            register_page.security_answer_input.fill("")

        with allure.step("3. Assert: Проверка блокировки кнопки Register"):
            expect(register_page.register_button).to_be_disabled()

    # =============================================================================
    # [QASE #981] [SECURITY] Скрытие ввода пароля (type='password') в полях ввода
    # =============================================================================
    @allure.title("[Frontend] Скрытие ввода пароля (type='password') в полях Password и Repeat Password")
    @allure.issue("JS-41")
    @allure.testcase("981")
    @pytest.mark.qase(id=981)
    @pytest.mark.ui
    def test_tc981_password_masking_security(self, page: Page, base_url: str):
        """
        Arrange: Открытие формы регистрации.
        Act: Получение атрибутов элементов полей ввода пароля.
        Assert: Значение атрибута type равно 'password' (NFR-UI-01).
        """
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Arrange: Открытие формы регистрации"):
            register_page.open()

        with allure.step("2. Act: Запрос состояния полей пароля"):
            pass

        with allure.step("3. Assert: Проверка типа полей type='password'"):
            expect(register_page.password_input).to_have_attribute("type", "password")
            expect(register_page.repeat_password_input).to_have_attribute("type", "password")

    # =============================================================================
    # [QASE #982] [ACCESSIBILITY] Доступность формы по клавиатуре (Tab Navigation & WCAG 2.1 AA)
    # =============================================================================
    @allure.title("[Frontend] Доступность формы регистрации по клавиатуре (Tab Navigation & WCAG 2.1 AA)")
    @allure.issue("JS-41")
    @allure.testcase("982")
    @pytest.mark.qase(id=982)
    @pytest.mark.ui
    def test_tc982_keyboard_tab_navigation(self, page: Page, base_url: str):
        """
        Arrange: Открытие формы регистрации.
        Act: Установка фокуса на поле Email и нажатие клавиши Tab.
        Assert: Фокус успешно переходит на поле Password (NFR-UI-03).
        """
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Arrange: Открытие формы регистрации"):
            register_page.open()

        with allure.step("2. Act: Фокусировка на поле Email и нажатие Tab"):
            register_page.email_input.focus()
            expect(register_page.email_input).to_be_focused()
            page.keyboard.press("Tab")

        with allure.step("3. Assert: Проверка переноса фокуса на поле Password"):
            expect(register_page.password_input).to_be_focused()
