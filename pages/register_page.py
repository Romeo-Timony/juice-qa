import allure
from playwright.sync_api import Page, expect
from .base_page import BasePage

class RegisterPage(BasePage):
    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        super().__init__(page, base_url)
        self.email_input = page.locator("#emailControl")
        self.password_input = page.locator("#passwordControl")
        self.repeat_password_input = page.locator("#repeatPasswordControl")
        self.security_question_select = page.locator("mat-select[name='securityQuestion'], .security-container mat-select").first
        self.security_answer_input = page.locator("#securityAnswerControl")
        self.register_button = page.locator("#registerButton")
        self.error_banner = page.locator(".error")

    @allure.step("Открыть страницу регистрации (/#/register)")
    def open(self):
        self.navigate_to("register")

    @allure.step("Выбрать секретный вопрос с индексом {index}")
    def select_security_question(self, index: int = 0):
        self.security_question_select.click(force=True)
        self.page.wait_for_selector("mat-option", state="visible", timeout=3000)
        self.page.locator("mat-option").nth(index).click()

    @allure.step("Заполнить форму регистрации пользователя ({email}) и подтвердить")
    def register(self, email: str, password: str, repeat_password: str = None, answer: str = "JuiceQA"):
        if repeat_password is None:
            repeat_password = password
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.repeat_password_input.fill(repeat_password)

        self.select_security_question(0)
        self.security_answer_input.fill(answer)

        self.register_button.click()

    @allure.step("Проверить доступность кнопки Register (disabled state)")
    def is_register_button_disabled(self) -> bool:
        return self.register_button.is_disabled()
