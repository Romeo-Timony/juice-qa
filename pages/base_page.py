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
            btn = self.page.locator("button[aria-label='Close Welcome Banner'], button.close-dialog").first
            btn.wait_for(state="visible", timeout=4000)
            btn.click()
        except Exception:
            pass

        try:
            cookie_btn = self.page.locator("a.cc-dismiss, a[aria-label='dismiss cookie message']").first
            cookie_btn.wait_for(state="visible", timeout=2000)
            cookie_btn.click()
        except Exception:
            pass

    def get_snackbar_text(self) -> str:
        snack = self.page.locator("simple-snack-bar, .mat-snack-bar-container")
        expect(snack).to_be_visible(timeout=5000)
        return snack.inner_text()
