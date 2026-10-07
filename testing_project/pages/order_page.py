"""
Order Confirmation Page Object for Online Boutique.
"""
from playwright.sync_api import Page
from testing_project.pages.base_page import BasePage


class OrderPage(BasePage):
    def __init__(self, page: Page, base_url: str = None):
        super().__init__(page, base_url or "")
        # Real template (microservices-demo/src/frontend/templates/order.html):
        # <h3>Your order is complete!</h3> inside <section class="container order-complete-section">
        self.confirmation_heading = page.locator(
            ".order-complete-section h3, "
            "h3:has-text('Your order is complete!')"
        )
        # Real template structure:
        # <div class="row border-bottom-solid padding-y-24">
        #     <div class="col-6 pl-md-0">Confirmation #</div>
        #     <div class="col-6 pr-md-0 text-right">{{.order.OrderId}}</div>
        # </div>
        self.order_id = page.locator(
            ".order-complete-section .row:has-text('Confirmation #') .text-right, "
            ".order-complete-section div:has-text('Confirmation #') + div, "
            ".row:has-text('Confirmation #') .text-right"
        )
        # Real template structure:
        # <div class="row border-bottom-solid padding-y-24">
        #     <div class="col-6 pl-md-0">Tracking #</div>
        #     <div class="col-6 pr-md-0 text-right">{{.order.ShippingTrackingId}}</div>
        # </div>
        self.tracking_id = page.locator(
            ".order-complete-section .row:has-text('Tracking #') .text-right, "
            ".order-complete-section div:has-text('Tracking #') + div, "
            ".row:has-text('Tracking #') .text-right"
        )
        # Real template structure:
        # <div class="row padding-y-24">
        #     <div class="col-6 pl-md-0">Total Paid</div>
        #     <div class="col-6 pr-md-0 text-right">{{renderMoney .total_paid}}</div>
        # </div>
        self.total_paid = page.locator(
            ".order-complete-section .row:has-text('Total Paid') .text-right, "
            ".order-complete-section div:has-text('Total Paid') + div, "
            ".row:has-text('Total Paid') .text-right"
        )
        # Real template structure:
        # <a class="cymbal-button-primary" href="{{ $.baseUrl }}/" role="button">Continue Shopping</a>
        self.continue_shopping_btn = page.locator(
            ".order-complete-section a.cymbal-button-primary, "
            "a.cymbal-button-primary:has-text('Continue Shopping'), "
            "a:has-text('Continue Shopping')"
        )

    def is_order_complete(self) -> bool:
        return self.confirmation_heading.first.is_visible()

    def get_order_id(self) -> str:
        if self.order_id.count() > 0 and self.order_id.first.is_visible():
            return self.order_id.first.inner_text().strip()
        return ""

    def get_tracking_id(self) -> str:
        if self.tracking_id.count() > 0 and self.tracking_id.first.is_visible():
            return self.tracking_id.first.inner_text().strip()
        return ""

    def get_total_paid(self) -> str:
        if self.total_paid.count() > 0 and self.total_paid.first.is_visible():
            return self.total_paid.first.inner_text().strip()
        return ""

    def continue_shopping(self):
        self.continue_shopping_btn.first.click()
        self.page.wait_for_load_state("domcontentloaded")
