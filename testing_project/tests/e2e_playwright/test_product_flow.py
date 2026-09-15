"""
Playwright End-to-End Tests: Product Catalog Browsing & Detail Inspection.
"""
from playwright.sync_api import Page
from testing_project.pages.home_page import HomePage
from testing_project.pages.product_page import ProductPage


def test_view_product_detail_page(page: Page, base_url):
    """Verifies navigating from homepage to product detail page displays correct data."""
    home = HomePage(page, base_url)
    home.load()

    first_product_name = home.get_all_product_names()[0]
    home.click_product_by_index(0)

    prod = ProductPage(page, base_url)
    assert prod.product_name.first.is_visible()
    assert first_product_name in prod.get_title_text()
    assert len(prod.get_price_text()) > 0
    assert len(prod.get_description_text()) > 0
    assert prod.add_to_cart_btn.first.is_visible()


def test_product_quantity_selector(page: Page, base_url):
    """Verifies that the quantity dropdown contains standard ordering tiers."""
    home = HomePage(page, base_url)
    home.load()
    home.click_product_by_index(0)

    prod = ProductPage(page, base_url)
    prod.set_quantity(3)
    assert prod.quantity_select.input_value() == "3"


def test_product_recommendations(page: Page, base_url):
    """Verifies that the recommendations microservice output is rendered on product page."""
    home = HomePage(page, base_url)
    home.load()
    home.click_product_by_index(0)

    prod = ProductPage(page, base_url)
    assert prod.recommendations_section.first.is_visible()
