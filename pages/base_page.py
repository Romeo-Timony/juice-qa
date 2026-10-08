from playwright.sync_api import Page, expect

class BasePage:
    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        self.page = page
        self.base_url = base_url.rstrip("/")

    def navigate_to(self, route: str):
        url = f"{self.base_url}/#/{route.lstrip('/')}"
        self.page.goto(url, wait_until="domcontentloaded")
        self.dismiss_banners()

    def dismiss_banners(self):
        try:
            welcome_btn = self.page.locator("button.close-dialog, button[aria-label='Close Welcome Banner']").first
            if welcome_btn.is_visible():
                welcome_btn.click()
            else:
                welcome_btn.click(timeout=1000)
        except Exception:
            pass

        try:
            cookie_btn = self.page.locator("a.cc-dismiss, a[aria-label='dismiss cookie message']").first
            if cookie_btn.is_visible():
                cookie_btn.click()
            else:
                cookie_btn.click(timeout=1000)
        except Exception:
            pass

    def get_snackbar_text(self) -> str:
        snack = self.page.locator("simple-snack-bar, .mat-snack-bar-container")
        expect(snack).to_be_visible(timeout=5000)
        return snack.inner_text()
