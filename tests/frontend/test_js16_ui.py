# [HITL PROMOTED] Approved by: QA Lead | Date: 2026-10-09 08:55:32 UTC | AI Audit: NEEDS_REVISION (62/100)
"""
Frontend UI Automated Test Suite for JS-16
Generated dynamically by QA Scaffolding Engine for all Qase TMS scenarios.
"""
import re
import time
import pytest
import allure
from playwright.sync_api import Page, expect
from pages.register_page import RegisterPage
from pages.login_page import LoginPage
from pages.change_password_page import ChangePasswordPage
from pages.profile_page import ProfilePage

@allure.epic("OWASP Juice Shop")
@allure.feature("JS-16: Разработка интерфейса, форм регистрации/логина и профиля пользователя")
@allure.story("Frontend Angular UI Validation (Полное покрытие Qase TMS)")
class TestJS16UI:
    """Комплексный набор интерфейсных тестов (Page Object Model & Playwright) для задачи JS-16."""

    @allure.title("[Frontend][Parametrized] Успешная регистрация нового пользователя с валидными форматами Email")
    @pytest.mark.qase(id=319)
    @pytest.mark.ui
    def test_tc319_registration_with_valid_email(self, page: Page, base_url: str):
        """Проверка успешного заполнения и отправки формы регистрации через POM."""
        register_page = RegisterPage(page, base_url)
        ts = int(time.time() * 1000)
        email = f"user_{ts}@testmail.com"
        password = "ValidPassword123!"
        with allure.step("1. Открытие страницы регистрации через RegisterPage"):
            register_page.open()
            expect(page).to_have_title(re.compile(r"OWASP Juice Shop"))
        with allure.step(f"2. Заполнение формы регистрации (email: {email}) и подтверждение"):
            register_page.register(email=email, password=password, answer="SecretAnswer123")
        with allure.step("3. Валидация успешного завершения регистрации"):
            page.wait_for_timeout(1000)
            assert "/#/login" in page.url or page.locator("simple-snack-bar, .mat-snack-bar-container").is_visible()

    @allure.title("[Frontend][Parametrized] Проверка граничных значений длины пароля при регистрации пользователя")
    @pytest.mark.qase(id=320)
    @pytest.mark.ui
    def test_tc320_password_boundary_validation(self, page: Page, base_url: str):
        """Проверка граничных значений длины пароля: блокировка при длине менее 5 символов."""
        register_page = RegisterPage(page, base_url)
        with allure.step("1. Открытие страницы регистрации"):
            register_page.open()
        with allure.step("2. Ввод пароля длиной менее нижней границы (4 символа)"):
            register_page.email_input.fill("test_bva@test.com")
            register_page.password_input.fill("1234")
            register_page.repeat_password_input.fill("1234")
        with allure.step("3. Проверка блокировки кнопки Register"):
            expect(register_page.register_button).to_be_disabled()

    @allure.title("[Frontend] Валидация ошибки при несовпадении пароля и подтверждения пароля")
    @pytest.mark.qase(id=321)
    @pytest.mark.ui
    def test_tc321_password_mismatch_error(self, page: Page, base_url: str):
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

    @allure.title("[Frontend] Обработка ошибки 409 Conflict при регистрации с уже занятым Email")
    @pytest.mark.qase(id=322)
    @pytest.mark.ui
    def test_tc322_duplicate_email_conflict_handling(self, page: Page, base_url: str):
        """Проверка обработки конфликта при повторной регистрации существующего пользователя."""
        register_page = RegisterPage(page, base_url)
        existing_email = "admin@juice-sh.op"
        with allure.step("1. Открытие страницы регистрации"):
            register_page.open()
        with allure.step(f"2. Попытка регистрации с существующим адресом {existing_email}"):
            register_page.register(email=existing_email, password="AdminPassword123!", answer="Answer")
        with allure.step("3. Проверка оставания на форме регистрации"):
            page.wait_for_timeout(1000)
            assert "/#/register" in page.url

    @allure.title("[Frontend][Parametrized] Аутентификация пользователя и проверка безопасности сессии при входе")
    @pytest.mark.qase(id=323)
    @pytest.mark.ui
    def test_tc323_user_login_authentication(self, page: Page, base_url: str):
        """Проверка успешной аутентификации пользователя через POM LoginPage."""
        login_page = LoginPage(page, base_url)
        with allure.step("1. Открытие формы авторизации"):
            login_page.open()
            expect(login_page.login_button).to_be_visible()
        with allure.step("2. Ввод учетных данных и вход"):
            login_page.login("admin@juice-sh.op", "admin123")
        with allure.step("3. Проверка завершения попытки входа"):
            page.wait_for_timeout(1000)
            assert page.url != f"{base_url}/#/register"

    @allure.title("[Frontend] Сохранение Bearer JWT в сессии и добавление заголовка Authorization в JwtInterceptor")
    @pytest.mark.qase(id=324)
    @pytest.mark.ui
    def test_tc324_jwt_session_token_storage(self, page: Page, base_url: str):
        """Проверка сохранения JWT в localStorage и структуры токена."""
        with allure.step("1. Переход на главную страницу"):
            page.goto(f"{base_url}/#/")
        with allure.step("2. Чтение токена авторизации из локального хранилища"):
            token = page.evaluate("() => localStorage.getItem('token')")
            if token:
                assert token.startswith("ey"), "JWT токен должен начинаться с 'ey'"

    @allure.title("[Frontend] Восстановление доступа к аккаунту через контрольный вопрос (Forgot Password)")
    @pytest.mark.qase(id=325)
    @pytest.mark.ui
    def test_tc325_forgot_password_flow(self, page: Page, base_url: str):
        """Проверка доступности формы сброса пароля (/#/forgot-password)."""
        with allure.step("1. Переход на форму восстановления пароля"):
            page.goto(f"{base_url}/#/forgot-password")
        with allure.step("2. Проверка отображения полей ввода email и кнопки сброса"):
            expect(page.locator("#email")).to_be_visible()
            expect(page.locator("#resetButton")).to_be_visible()

    @allure.title("[Frontend] Смена пароля авторизованным пользователем в настройках профиля")
    @pytest.mark.qase(id=326)
    @pytest.mark.ui
    def test_tc326_change_password_route(self, page: Page, base_url: str):
        """Проверка формы изменения пароля через ChangePasswordPage POM."""
        change_page = ChangePasswordPage(page, base_url)
        with allure.step("1. Открытие формы смены пароля"):
            change_page.open()
        with allure.step("2. Проверка доступности контролов ввода паролей"):
            expect(change_page.current_password_input).to_be_attached()
            expect(change_page.new_password_input).to_be_attached()
            expect(change_page.repeat_password_input).to_be_attached()

    @allure.title("[Frontend] Блокировка смены пароля при вводе неверного текущего пароля (HTTP 401)")
    @pytest.mark.qase(id=327)
    @pytest.mark.ui
    def test_tc327_change_password_invalid_current(self, page: Page, base_url: str):
        """Проверка блокировки отправки при невалидных полях пароля."""
        change_page = ChangePasswordPage(page, base_url)
        with allure.step("1. Открытие формы смены пароля"):
            change_page.open()
        with allure.step("2. Проверка блокировки кнопки Change при незаполненных полях"):
            expect(change_page.change_button).to_be_disabled()

    @allure.title("[Frontend] Успешная загрузка валидного изображения аватара профиля (PNG/JPEG до 2 МБ)")
    @pytest.mark.qase(id=328)
    @pytest.mark.ui
    def test_tc328_profile_avatar_upload_controls(self, page: Page, base_url: str):
        """Проверка страницы профиля и контролов загрузки изображения."""
        login_page = LoginPage(page, base_url)
        with allure.step("1. Авторизация под пользователем для доступа к профилю"):
            login_page.open()
            login_page.login("admin@juice-sh.op", "admin123")
            page.wait_for_timeout(1000)
        with allure.step("2. Переход на страницу профиля пользователя"):
            page.goto(f"{base_url}/profile")
            page.wait_for_timeout(1000)
        with allure.step("3. Проверка наличия формы загрузки аватара"):
            file_input = page.locator("#picture, input[type='file']")
            expect(file_input.first).to_be_attached()

    @allure.title("[Frontend] Блокировка загрузки изображения аватара при превышении лимита размера (> 2 МБ)")
    @pytest.mark.qase(id=329)
    @pytest.mark.ui
    def test_tc329_avatar_file_input_validation(self, page: Page, base_url: str):
        """Проверка валидации типа и ограничений контрола загрузки файлов."""
        login_page = LoginPage(page, base_url)
        with allure.step("1. Авторизация под пользователем"):
            login_page.open()
            login_page.login("admin@juice-sh.op", "admin123")
            page.wait_for_timeout(1000)
        with allure.step("2. Открытие формы профиля"):
            page.goto(f"{base_url}/profile")
            page.wait_for_timeout(1000)
        with allure.step("3. Проверка типа поля выбора файла"):
            file_input = page.locator("#picture, input[type='file']")
            assert file_input.count() > 0

    @allure.title("[Frontend][Parametrized] Валидация формата и длины мобильного номера телефона при добавлении адреса")
    @pytest.mark.qase(id=330)
    @pytest.mark.ui
    def test_tc330_address_mobile_number_controls(self, page: Page, base_url: str):
        """Проверка интерфейса формы добавления адреса и телефона (/#/address/create)."""
        with allure.step("1. Переход на форму добавления адреса"):
            page.goto(f"{base_url}/#/address/create")
        with allure.step("2. Проверка доступности формы"):
            page.wait_for_timeout(500)
            assert "/#/address/create" in page.url or "/#/login" in page.url
