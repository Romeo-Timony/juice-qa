"""
Frontend UI Automated Test Suite for JS-16
Generated dynamically by local QA Agent (Playwright)
"""
import re
import pytest
import allure
from playwright.sync_api import Page, expect

@allure.epic("OWASP Juice Shop")
@allure.feature("JS-16: Регистрация и аутентификация пользователя (Frontend)")
@allure.story("Frontend Angular UI Validation")
class TestJS16UI:
    """Пользовательские сценарии интерфейса (Page Object Model & Playwright)."""

    @allure.title("[Frontend] Отображение главной страницы OWASP Juice Shop")
    @pytest.mark.qase(id=57)
    @pytest.mark.ui
    def test_homepage_loads(self, page: Page):
        """Проверка доступности веб-приложения и заголовка страницы."""
        with allure.step("1. Открытие главной страницы приложения"):
            page.goto("http://localhost:3000/#/")
        with allure.step("2. Проверка заголовка страницы"):
            expect(page).to_have_title(re.compile(r"OWASP Juice Shop"))

    @allure.title("[Frontend] Доступность страницы регистрации нового пользователя")
    @pytest.mark.qase(id=58)
    @pytest.mark.ui
    def test_registration_page_accessible(self, page: Page):
        """Проверка перехода на форму регистрации /#/register."""
        with allure.step("1. Переход на форму регистрации"):
            page.goto("http://localhost:3000/#/register")
        with allure.step("2. Проверка URL и заголовка страницы"):
            expect(page).to_have_title(re.compile(r"OWASP Juice Shop"))
            assert "/#/register" in page.url
