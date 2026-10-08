import allure
from playwright.sync_api import Page, expect
from .base_page import BasePage

class LoginPage(BasePage):
    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        super().__init__(page, base_url)
        self.email_input = page.locator("#email")
        self.password_input = page.locator("#password")
        self.login_button = page.locator("#loginButton")

    @allure.step("Открыть страницу входа (/#/login)")
    def open(self):
        self.navigate_to("login")

    @allure.step("Ввести учетные данные и нажать кнопку Login ({email})")
    def login(self, email: str, password: str):
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.login_button.click()

    @allure.step("Получить Bearer JWT токен из localStorage")
    def get_token_from_storage(self) -> str:
        return self.page.evaluate("() => localStorage.getItem('token')")
