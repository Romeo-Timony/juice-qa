import allure
from playwright.sync_api import Page, expect
from .base_page import BasePage

class CatalogPage(BasePage):
    """Page Object для каталога товаров и поиска OWASP Juice Shop."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        super().__init__(page, base_url)
        self.search_icon = page.locator("mat-icon:has-text('search')")
        self.search_input = page.locator("#mat-input-0, input.mat-input-element")
        self.basket_button = page.locator("button[routerlink='/basket']")

    @allure.step("Открыть каталог товаров (/#/search)")
    def open(self):
        self.navigate_to("search")

    @allure.step("Добавить товар '{product_name}' в корзину")
    def add_product_to_basket(self, product_name: str = "Apple Juice"):
        card = self.page.locator("mat-card", has_text=product_name).first
        expect(card).to_be_visible()
        add_btn = card.locator("button.btn-basket, button[aria-label*='basket' i], button:has(.icon-basket)").first
        add_btn.click()

    @allure.step("Перейти в корзину покупок")
    def go_to_basket(self):
        self.basket_button.click()
