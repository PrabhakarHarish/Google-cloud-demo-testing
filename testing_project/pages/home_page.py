"""
Home Page Object for Online Boutique.
"""
from typing import List
from playwright.sync_api import Page
from testing_project.pages.base_page import BasePage


class HomePage(BasePage):
    def __init__(self, page: Page, base_url: str = None):
        super().__init__(page, base_url or "")
        self.hot_products_heading = page.locator(".hot-products-title, h3:has-text('Hot Products')")
        self.product_cards = page.locator(".hot-product-card")
        self.product_links = page.locator(".hot-product-card a[href*='/product/']")
        self.product_names = page.locator(".hot-product-card-name, .card-title")
        self.product_prices = page.locator(".hot-product-card-price")

    def load(self):
        self.navigate("/")
        self.page.wait_for_selector(".hot-product-card")

    def get_products_count(self) -> int:
        return self.product_cards.count()

    def get_all_product_names(self) -> List[str]:
        count = self.product_names.count()
        return [self.product_names.nth(i).inner_text().strip() for i in range(count)]

    def get_all_product_prices(self) -> List[str]:
        count = self.product_prices.count()
        return [self.product_prices.nth(i).inner_text().strip() for i in range(count)]

    def click_product_by_index(self, index: int = 0):
        self.product_links.nth(index).click()
        self.page.wait_for_load_state("domcontentloaded")

    def click_product_by_name(self, name: str):
        self.page.locator(f".hot-product-card:has-text('{name}') a[href*='/product/']").first.click()
        self.page.wait_for_load_state("domcontentloaded")
