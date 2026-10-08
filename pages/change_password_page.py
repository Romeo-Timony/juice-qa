import allure
from playwright.sync_api import Page, expect
from .base_page import BasePage

class ChangePasswordPage(BasePage):
    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        super().__init__(page, base_url)
        self.current_password_input = page.locator("#currentPassword")
        self.new_password_input = page.locator("#newPassword")
        self.repeat_password_input = page.locator("#newPasswordRepeat")
        self.change_button = page.locator("#changeButton")
        self.confirmation_msg = page.locator("mat-card p.confirmation")
        self.error_msg = page.locator("mat-card p.error")

    @allure.step("Открыть форму смены пароля (/#/privacy-security/change-password)")
    def open(self):
        self.navigate_to("privacy-security/change-password")

    @allure.step("Заполнить форму смены пароля и отправить")
    def change_password(self, current_pass: str, new_pass: str, repeat_pass: str = None):
        if repeat_pass is None:
            repeat_pass = new_pass
        self.current_password_input.fill(current_pass)
        self.new_password_input.fill(new_pass)
        self.repeat_password_input.fill(repeat_pass)
        self.change_button.click()
