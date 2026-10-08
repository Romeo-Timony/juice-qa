import allure
from playwright.sync_api import Page, expect
from .base_page import BasePage

class ProfilePage(BasePage):
    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        super().__init__(page, base_url)
        self.file_input = page.locator("#picture")
        self.upload_button = page.locator("button.fill[type='submit']:has-text('Upload Picture'), button:has-text('Upload Picture')")
        self.profile_image = page.locator("img.img-rounded")

    @allure.step("Открыть серверную страницу профиля (/profile)")
    def open(self):
        url = f"{self.base_url}/profile"
        self.page.goto(url, wait_until="domcontentloaded")

    @allure.step("Выбрать локальный файл и нажать Upload Picture: {file_path}")
    def upload_picture(self, file_path: str):
        self.file_input.set_input_files(file_path)
        self.upload_button.click()
