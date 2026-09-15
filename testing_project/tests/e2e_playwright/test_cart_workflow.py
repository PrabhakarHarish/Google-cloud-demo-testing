"""
Playwright End-to-End Tests: Cart Microservice Integration & Cart Operations.
"""
from playwright.sync_api import Page
from testing_project.pages.home_page import HomePage
from testing_project.pages.product_page import ProductPage
from testing_project.pages.cart_page import CartPage


def test_add_product_to_cart(page: Page, base_url):
    """Verifies adding a product to the cart increments cart count and displays item."""
    home = HomePage(page, base_url)
    home.load()

    prod_name = home.get_all_product_names()[0]
    home.click_product_by_index(0)

    prod = ProductPage(page, base_url)
    prod.set_quantity(2)
    prod.add_to_cart()

    cart = CartPage(page, base_url)
    assert "/cart" in page.url
    assert not cart.is_empty()

    cart_items = cart.get_cart_item_names()
    assert any(prod_name in item for item in cart_items)
    assert cart.get_cart_count() == 2


def test_empty_cart_functionality(page: Page, base_url):
    """Verifies emptying the cart resets cart state and displays empty notice."""
    home = HomePage(page, base_url)
    home.load()
    home.click_product_by_index(0)

    prod = ProductPage(page, base_url)
    prod.add_to_cart()

    cart = CartPage(page, base_url)
    assert not cart.is_empty()

    cart.empty_cart()
    assert cart.is_empty()
    assert cart.continue_shopping_btn.first.is_visible()
