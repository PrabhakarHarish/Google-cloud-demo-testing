"""
Playwright End-to-End Tests: Online Boutique Home Page & Navigation.
"""
import pytest
import requests
from playwright.sync_api import Page, expect
from testing_project.pages.home_page import HomePage


def test_frontend_healthz_probe(base_url):
    """Verifies the Kubernetes readiness/liveness HTTP probe endpoint (/_healthz)."""
    resp = requests.get(f"{base_url}/_healthz")
    assert resp.status_code == 200
    assert "ok" in resp.text


def test_homepage_loads_successfully(page: Page, base_url):
    """Verifies that the Online Boutique home page loads properly with branding and title."""
    home = HomePage(page, base_url)
    home.load()

    assert "Online Boutique" in home.get_title() or "Cymbal" in home.get_title()
    assert home.logo.first.is_visible()
    assert home.hot_products_heading.first.is_visible()


def test_hot_products_catalog_display(page: Page, base_url):
    """Verifies that the hot products grid is populated with products, names, and prices."""
    home = HomePage(page, base_url)
    home.load()

    count = home.get_products_count()
    assert count > 0, "No products found in Hot Products catalog!"

    names = home.get_all_product_names()
    prices = home.get_all_product_prices()

    assert len(names) == count
    assert len(prices) == count
    for name, price in zip(names, prices):
        assert len(name) > 0, "Product name should not be empty"
        assert any(sym in price for sym in ["$", "€", "¥", "£", "₺"]), f"Price {price} missing currency symbol"


def test_initial_cart_badge(page: Page, base_url):
    """Verifies that the cart icon is present and starts with 0 items for a new session."""
    home = HomePage(page, base_url)
    home.load()

    assert home.cart_link.first.is_visible()
    assert home.get_cart_count() == 0
