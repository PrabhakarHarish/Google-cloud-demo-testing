"""
Product Detail Page Object for Online Boutique.
"""
from typing import List
from playwright.sync_api import Page
from testing_project.pages.base_page import BasePage


class ProductPage(BasePage):
    def __init__(self, page: Page, base_url: str = None):
        super().__init__(page, base_url or "")
        self.product_name = page.locator("#product-name, .product-info h2")
        self.product_price = page.locator("#product-price, .product-price")
        self.product_description = page.locator("#product-description, .product-info p")
        self.quantity_select = page.locator("#quantity, select[name='quantity']")
        self.add_to_cart_btn = page.locator("#add-to-cart-btn, button[type='submit']:has-text('Add To Cart'), .cymbal-button-primary:has-text('Add To Cart')")
        self.recommendations_section = page.locator(".recommendations, .product-wrapper + div")

    def get_title_text(self) -> str:
        return self.product_name.inner_text().strip()

    def get_price_text(self) -> str:
        return self.product_price.first.inner_text().strip()

    def get_description_text(self) -> str:
        return self.product_description.first.inner_text().strip()

    def set_quantity(self, quantity: int):
        self.quantity_select.select_option(value=str(quantity))

    def add_to_cart(self):
        self.add_to_cart_btn.click()
        self.page.wait_for_load_state("domcontentloaded")
