"""
Playwright End-to-End Tests: Currency Service & Dynamic Currency Conversion.
"""
import re
from playwright.sync_api import Page
from testing_project.pages.home_page import HomePage
from testing_project.pages.product_page import ProductPage


def parse_price_amount(price_str: str) -> float:
    """Extracts the numeric float value from a formatted price string (e.g. '€17.68' -> 17.68)."""
    match = re.search(r"[\d]+(?:\.\d+)?", price_str.replace(",", ""))
    if not match:
        raise ValueError(f"No numeric price found in: {price_str}")
    return float(match.group())


def test_currency_switch_to_eur(page: Page, base_url):
    """
    Verifies that switching currency to EUR updates prices with € symbol
    AND converts prices accurately against EUR-based exchange rates (EUR=1.0, USD=1.1305).
    Sunglasses ($19.99 USD) must convert to approximately €17.68 (not €19.99 or $22.60).
    """
    home = HomePage(page, base_url)
    home.load()

    # Switch to EUR
    home.select_currency("EUR")

    # Assert prices on homepage display €
    prices = home.get_all_product_prices()
    names = home.get_all_product_names()
    assert len(prices) > 0
    assert all("€" in p for p in prices), f"Expected all prices to have Euro symbol '€': {prices}"

    name_to_price = dict(zip(names, prices))

    # Sunglasses at $19.99 USD must convert to ~€17.68 (19.99 / 1.1305)
    if "Sunglasses" in name_to_price:
        val = parse_price_amount(name_to_price["Sunglasses"])
        assert abs(val - 17.68) <= 0.05, f"Expected Sunglasses ~€17.68, got {name_to_price['Sunglasses']}"
    else:
        val = parse_price_amount(prices[0])
        assert abs(val - 17.68) <= 0.05, f"Expected first product ~€17.68, got {prices[0]}"

    # Tank Top at $18.99 USD must convert to ~€16.80 (18.99 / 1.1305)
    if "Tank Top" in name_to_price:
        val = parse_price_amount(name_to_price["Tank Top"])
        assert abs(val - 16.80) <= 0.05, f"Expected Tank Top ~€16.80, got {name_to_price['Tank Top']}"

    # Watch at $109.99 USD must convert to ~€97.29 (109.99 / 1.1305)
    if "Watch" in name_to_price:
        val = parse_price_amount(name_to_price["Watch"])
        assert abs(val - 97.29) <= 0.05, f"Expected Watch ~€97.29, got {name_to_price['Watch']}"


def test_currency_switch_to_jpy(page: Page, base_url):
    """
    Verifies that switching currency to JPY updates prices with ¥ symbol
    AND converts prices accurately against EUR-based rates (JPY=126.40, USD=1.1305).
    Sunglasses ($19.99 USD) must convert to approximately ¥2235 ((19.99 / 1.1305) * 126.40).
    """
    home = HomePage(page, base_url)
    home.load()

    # Switch to JPY
    home.select_currency("JPY")

    # Assert prices display ¥
    prices = home.get_all_product_prices()
    names = home.get_all_product_names()
    assert len(prices) > 0
    assert all("¥" in p for p in prices), f"Expected all prices to have Yen symbol '¥': {prices}"

    name_to_price = dict(zip(names, prices))
    if "Sunglasses" in name_to_price:
        val = parse_price_amount(name_to_price["Sunglasses"])
        assert abs(val - 2235.03) <= 1.0, f"Expected Sunglasses ~¥2235, got {name_to_price['Sunglasses']}"
    else:
        val = parse_price_amount(prices[0])
        assert abs(val - 2235.03) <= 1.0, f"Expected first product ~¥2235, got {prices[0]}"


def test_currency_persists_on_product_page(page: Page, base_url):
    """Verifies that the chosen currency persists across page navigations with accurate converted price."""
    home = HomePage(page, base_url)
    home.load()
    home.select_currency("EUR")

    home.click_product_by_index(0)
    prod = ProductPage(page, base_url)
    price_text = prod.get_price_text()
    assert "€" in price_text, f"Expected Euro symbol '€' in product price: {price_text}"
    # Sunglasses at index 0 ($19.99 USD) must display as ~€17.68
    val = parse_price_amount(price_text)
    assert abs(val - 17.68) <= 0.05, f"Expected product page ~€17.68, got {price_text}"
