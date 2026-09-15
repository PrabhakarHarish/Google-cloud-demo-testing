"""
Order Confirmation Page Object for Online Boutique.
"""
from playwright.sync_api import Page
from testing_project.pages.base_page import BasePage


class OrderPage(BasePage):
    def __init__(self, page: Page, base_url: str = None):
        super().__init__(page, base_url or "")
        self.confirmation_heading = page.locator("#order-complete-heading, h3:has-text('Your order is complete!'), h2:has-text('Your order is complete!')")
        self.order_id = page.locator("#order-id, .order-complete-section .col-6:has-text('ORD-'), td:has-text('ORD-')")
        self.tracking_id = page.locator("#tracking-id, .order-complete-section .col-6:has-text('TRK-'), td:has-text('TRK-')")
        self.total_paid = page.locator("#total-paid, .order-complete-section td:has-text('$'), .order-complete-section td:has-text('€')")
        self.continue_shopping_btn = page.locator("#order-continue-shopping, a:has-text('Continue Shopping')")

    def is_order_complete(self) -> bool:
        return self.confirmation_heading.first.is_visible()

    def get_order_id(self) -> str:
        if self.order_id.is_visible():
            return self.order_id.first.inner_text().strip()
        return ""

    def get_tracking_id(self) -> str:
        if self.tracking_id.is_visible():
            return self.tracking_id.first.inner_text().strip()
        return ""

    def get_total_paid(self) -> str:
        if self.total_paid.is_visible():
            return self.total_paid.first.inner_text().strip()
        return ""

    def continue_shopping(self):
        self.continue_shopping_btn.first.click()
        self.page.wait_for_load_state("domcontentloaded")
