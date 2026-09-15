"""
Playwright End-to-End Tests: Currency Service & Dynamic Currency Conversion.
"""
from playwright.sync_api import Page
from testing_project.pages.home_page import HomePage
from testing_project.pages.product_page import ProductPage


def test_currency_switch_to_eur(page: Page, base_url):
    """Verifies that switching currency to EUR updates prices with € symbol."""
    home = HomePage(page, base_url)
    home.load()

    # Switch to EUR
    home.select_currency("EUR")

    # Assert prices on homepage display €
    prices = home.get_all_product_prices()
    assert len(prices) > 0
    assert any("€" in p for p in prices), f"Expected Euro symbol '€' in prices: {prices}"


def test_currency_switch_to_jpy(page: Page, base_url):
    """Verifies that switching currency to JPY updates prices with ¥ symbol."""
    home = HomePage(page, base_url)
    home.load()

    # Switch to JPY
    home.select_currency("JPY")

    # Assert prices display ¥
    prices = home.get_all_product_prices()
    assert len(prices) > 0
    assert any("¥" in p for p in prices), f"Expected Yen symbol '¥' in prices: {prices}"


def test_currency_persists_on_product_page(page: Page, base_url):
    """Verifies that the chosen currency persists across page navigations."""
    home = HomePage(page, base_url)
    home.load()
    home.select_currency("EUR")

    home.click_product_by_index(0)
    prod = ProductPage(page, base_url)
    assert "€" in prod.get_price_text()
