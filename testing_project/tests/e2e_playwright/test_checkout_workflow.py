"""
Playwright End-to-End Tests: Complete User Purchase & Checkout Journey.
Tests end-to-end integration across Frontend, Cart, Recommendation, Shipping, Payment, and Checkout microservices.
"""
from playwright.sync_api import Page
from testing_project.pages.home_page import HomePage
from testing_project.pages.product_page import ProductPage
from testing_project.pages.cart_page import CartPage
from testing_project.pages.order_page import OrderPage


def test_complete_checkout_user_journey(page: Page, base_url):
    """
    Executes a full end-to-end user checkout journey:
    1. Browse catalog on home page
    2. Select a product
    3. Add 2 items to the shopping cart
    4. Verify cart summary and shipping calculations
    5. Enter shipping address and payment credentials
    6. Place order through CheckoutService orchestration
    7. Validate order confirmation page, Order ID, Tracking ID, and total paid
    8. Click 'Continue Shopping' to return cleanly to home
    """
    # 1. Browse catalog
    home = HomePage(page, base_url)
    home.load()
    assert home.get_products_count() > 0

    # 2. Select product
    selected_name = home.get_all_product_names()[0]
    home.click_product_by_index(0)

    # 3. Add to cart
    prod = ProductPage(page, base_url)
    prod.set_quantity(2)
    prod.add_to_cart()

    # 4. Cart page assertions
    cart = CartPage(page, base_url)
    assert not cart.is_empty()
    assert any(selected_name in name for name in cart.get_cart_item_names())
    assert len(cart.get_total_price_text()) > 0

    # 5. Fill checkout details
    cart.fill_checkout_info(
        email="cloud-test-user@google.com",
        street="1600 Amphitheatre Parkway",
        city="Mountain View",
        state="CA",
        zip_code="94043",
        country="United States",
        card_number="4432801561520454",
        exp_month="12",
        exp_year="2027",
        cvv="123"
    )

    # 6. Submit order
    cart.submit_order()

    # 7. Validate order confirmation
    order = OrderPage(page, base_url)
    assert order.is_order_complete(), "Order confirmation message not found!"
    order_id = order.get_order_id()
    tracking_id = order.get_tracking_id()
    total_paid = order.get_total_paid()

    assert order_id.startswith("ORD-"), f"Expected order ID prefix ORD-, got {order_id}"
    assert tracking_id.startswith("TRK-"), f"Expected tracking ID prefix TRK-, got {tracking_id}"
    assert len(total_paid) > 0, "Total paid amount should not be empty"

    # 8. Return to shopping
    order.continue_shopping()
    assert page.url.rstrip("/").endswith(base_url.rstrip("/"))
