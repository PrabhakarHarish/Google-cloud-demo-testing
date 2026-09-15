"""
Playwright End-to-End Tests: Cloud UI Responsiveness & Mobile Viewport Emulation.
"""
from playwright.sync_api import Page
from testing_project.pages.home_page import HomePage
from testing_project.pages.product_page import ProductPage


def test_mobile_viewport_layout(mobile_page: Page, base_url):
    """
    Verifies that the Online Boutique renders properly on mobile devices (e.g. iPhone).
    Validates responsive container scaling and functional touch/click flows.
    """
    home = HomePage(mobile_page, base_url)
    home.load()

    # Verify elements are visible and within mobile viewport
    assert home.logo.first.is_visible()
    assert home.get_products_count() > 0

    # Ensure clicking a product on mobile successfully opens product page
    home.click_product_by_index(0)
    prod = ProductPage(mobile_page, base_url)
    assert prod.product_name.first.is_visible()
    assert prod.add_to_cart_btn.first.is_visible()
