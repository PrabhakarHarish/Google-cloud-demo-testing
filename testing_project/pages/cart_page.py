"""
Cart Page Object for Online Boutique.
"""
from typing import Dict, List
from playwright.sync_api import Page
from testing_project.pages.base_page import BasePage


class CartPage(BasePage):
    def __init__(self, page: Page, base_url: str = None):
        super().__init__(page, base_url or "")
        # Cart View Locators
        self.cart_heading = page.locator("#cart-header, .cart-summary-section h3")
        self.empty_cart_section = page.locator(".empty-cart-section")
        self.empty_cart_button = page.locator("#empty-cart-btn, button:has-text('Empty Cart'), .cart-summary-empty-cart-button")
        self.continue_shopping_btn = page.locator("a:has-text('Continue Shopping')")
        self.cart_items = page.locator(".cart-summary-item-row")
        self.item_names = page.locator(".cart-item-name, .cart-summary-item-row h4, .cart-summary-item-row h6")
        self.total_price = page.locator("#cart-total-price, .cart-summary-total-row strong, strong:has-text('$'), strong:has-text('€')")
        self.shipping_price = page.locator("#shipping-cost, .cart-summary-shipping-row .col:last-child")

        # Checkout Form Locators
        self.email_input = page.locator("#email, input[name='email']")
        self.street_input = page.locator("#street_address, input[name='street_address']")
        self.city_input = page.locator("#city, input[name='city']")
        self.state_input = page.locator("#state, input[name='state']")
        self.zip_input = page.locator("#zip_code, input[name='zip_code']")
        self.country_input = page.locator("#country, input[name='country']")
        self.card_number_input = page.locator("#credit_card_number, input[name='credit_card_number']")
        self.card_month_select = page.locator("#credit_card_expiration_month, select[name='credit_card_expiration_month']")
        self.card_year_select = page.locator("#credit_card_expiration_year, select[name='credit_card_expiration_year']")
        self.card_cvv_input = page.locator("#credit_card_cvv, input[name='credit_card_cvv']")
        self.place_order_button = page.locator("#place-order-btn, button[type='submit']:has-text('Place Order'), button:has-text('Order')")

    def is_empty(self) -> bool:
        return self.empty_cart_section.first.is_visible()

    def get_cart_item_names(self) -> List[str]:
        count = self.item_names.count()
        return [self.item_names.nth(i).inner_text().strip() for i in range(count)]

    def empty_cart(self):
        with self.page.expect_navigation():
            self.empty_cart_button.first.click()
        self.page.wait_for_selector(".empty-cart-section, #empty-cart-header", timeout=5000)

    def get_total_price_text(self) -> str:
        return self.total_price.first.inner_text().strip()

    def fill_checkout_info(
        self,
        email: str = "tester@google-online-boutique.test",
        street: str = "1600 Amphitheatre Parkway",
        city: str = "Mountain View",
        state: str = "CA",
        zip_code: str = "94043",
        country: str = "United States",
        card_number: str = "4432801561520454",
        exp_month: str = "12",
        exp_year: str = "2027",
        cvv: str = "123"
    ):
        self.email_input.fill(email)
        self.street_input.fill(street)
        self.city_input.fill(city)
        self.state_input.fill(state)
        self.zip_input.fill(zip_code)
        self.country_input.fill(country)
        self.card_number_input.fill(card_number)
        if self.card_month_select.is_visible():
            self.card_month_select.select_option(str(int(exp_month)))
        if self.card_year_select.is_visible():
            self.card_year_select.select_option(exp_year)
        if self.card_cvv_input.is_visible():
            self.card_cvv_input.fill(cvv)

    def submit_order(self):
        self.place_order_button.first.click()
        self.page.wait_for_load_state("domcontentloaded")
