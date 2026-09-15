"""
Base Page Object containing common methods and locators across Online Boutique pages.
"""
from playwright.sync_api import Page, expect
from testing_project.config import FRONTEND_URL


class BasePage:
    def __init__(self, page: Page, base_url: str = FRONTEND_URL):
        self.page = page
        self.base_url = base_url.rstrip("/")

        # Header Locators
        self.logo = page.locator(".top-left-logo, .top-left-logo-cymbal")
        self.currency_select = page.locator("#currency_code, select[name='currency_code']")
        self.cart_link = page.locator("a[href*='/cart']")
        self.cart_badge = page.locator("#cart-count, .cart-size-circle")

    def navigate(self, path: str = ""):
        target = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        self.page.goto(target, wait_until="domcontentloaded")

    def get_title(self) -> str:
        return self.page.title()

    def select_currency(self, currency_code: str):
        """Changes the store currency via the header selector."""
        with self.page.expect_navigation():
            self.currency_select.select_option(value=currency_code)
        self.page.wait_for_load_state("domcontentloaded")

    def get_selected_currency(self) -> str:
        return self.currency_select.input_value()

    def get_cart_count(self) -> int:
        """Returns the number displayed in the cart icon badge, or 0 if empty."""
        if self.cart_badge.is_visible():
            text = self.cart_badge.inner_text().strip()
            return int(text) if text.isdigit() else 0
        return 0

    def click_cart(self):
        """Clicks the cart icon in the header."""
        self.cart_link.first.click()
        self.page.wait_for_load_state("domcontentloaded")

    def take_screenshot(self, filepath: str):
        self.page.screenshot(path=filepath, full_page=True)
