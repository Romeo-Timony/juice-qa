import allure
from playwright.sync_api import Page, expect
from .base_page import BasePage

class CheckoutPage(BasePage):
    """Page Object для процесса оформления и оплаты заказа (Checkout flow)."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        super().__init__(page, base_url)
        # Корзина
        self.basket_checkout_btn = page.locator("#checkoutButton")
        # Выбор адреса
        self.address_rows = page.locator("mat-table.address-table mat-row, mat-table mat-row")
        self.address_radios = page.locator("mat-table.address-table mat-radio-button, mat-table mat-radio-button")
        self.address_next_btn = page.locator("button.btn-next, button[aria-label='Proceed to payment selection']")
        self.new_address_btn = page.locator("button.btn-new-address, button[aria-label='Add a new address']")
        # Выбор метода доставки
        self.delivery_radios = page.locator("mat-table mat-radio-button, mat-row mat-radio-button")
        self.delivery_next_btn = page.locator("button.nextButton, button[aria-label='Proceed to delivery method selection']")
        # Оплата
        self.pay_with_wallet_btn = page.locator("button:has-text('Pay'), button.btn-float-right")
        self.payment_radios = page.locator("app-payment-method mat-radio-button, mat-table mat-radio-button")
        self.payment_next_btn = page.locator("button.nextButton, button[aria-label='Proceed to review']")
        # Финальное подтверждение заказа
        self.place_order_btn = page.locator("#checkoutButton, button.btn-pay")
        # Подтверждение
        self.confirmation_header = page.locator("h1.confirmation, h1:has-text('Thank you')")

    @allure.step("Перейти к оформлению заказа из корзины")
    def start_checkout_from_basket(self):
        self.basket_checkout_btn.click()

    @allure.step("Выбрать адрес доставки")
    def select_address_and_proceed(self, country: str = "France", name: str = "Jim Kirk", address: str = "Rue de la Pomme", city: str = "Paris", zipcode: str = "75001"):
        # Если адресов нет в списке, создаем новый
        if self.address_radios.count() == 0:
            self.new_address_btn.click()
            self.page.locator("#mat-input-1, input[data-placeholder='Please provide a country.']").fill(country)
            self.page.locator("#mat-input-2, input[data-placeholder='Please provide a name.']").fill(name)
            self.page.locator("#mat-input-3, input[data-placeholder='Please provide a mobile number.']").fill("0612345678")
            self.page.locator("#mat-input-4, input[data-placeholder='Please provide a ZIP code.']").fill(zipcode)
            self.page.locator("#address, textarea[data-placeholder='Please provide an address.']").fill(address)
            self.page.locator("#mat-input-6, input[data-placeholder='Please provide a city.']").fill(city)
            self.page.locator("#submitButton").click()
            self.page.wait_for_timeout(1000)

        # Выбираем первый радио-баттон адреса
        first_radio = self.address_radios.first
        first_radio.click()
        self.address_next_btn.click()

    @allure.step("Выбрать способ доставки")
    def select_delivery_speed_and_proceed(self):
        first_delivery = self.delivery_radios.first
        first_delivery.click()
        self.delivery_next_btn.click()

    @allure.step("Выбрать метод оплаты и перейти к ревью заказа")
    def select_payment_and_proceed(self):
        # Если доступна кнопка оплаты из цифрового кошелька, используем её
        if self.pay_with_wallet_btn.is_visible() and self.pay_with_wallet_btn.is_enabled():
            self.pay_with_wallet_btn.click()
            self.page.wait_for_timeout(500)
            self.payment_next_btn.click()
        elif self.payment_radios.count() > 0:
            self.payment_radios.first.click()
            self.payment_next_btn.click()
        else:
            # Fallback - клик далее
            self.payment_next_btn.click()

    @allure.step("Разместить и оплатить заказ (Place Order)")
    def place_order(self):
        expect(self.place_order_btn).to_be_visible()
        self.place_order_btn.click()

    @allure.step("Проверить подтверждение заказа")
    def verify_order_completion(self):
        expect(self.confirmation_header).to_be_visible(timeout=10000)
