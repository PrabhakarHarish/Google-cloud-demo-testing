"""
Performance & Load Testing Suite for Online Boutique Microservices using Locust.
Simulates realistic concurrent user shopping workflows across frontend and backend services.
"""
import random
from locust import HttpUser, task, between


SAMPLE_PRODUCT_IDS = [
    "OLJCESPC7Z",
    "66VCHSJNUP",
    "1YMWWN1N4O",
    "L9ECAV7KIM",
    "2ZYFJ3GM2N",
    "0PUK6TG6LN",
    "9SIQT8TOJO",
    "1YMWWN1N4O"
]

CURRENCIES = ["USD", "EUR", "CAD", "JPY", "GBP"]


class BoutiqueShopper(HttpUser):
    # Wait between 1 and 3 seconds between actions to simulate real human pacing
    wait_time = between(1, 3)

    def on_start(self):
        """Simulate user landing on homepage upon session start."""
        self.client.get("/", name="[Page] 01_Home")

    @task(4)
    def browse_homepage(self):
        """Browses the store front and checks health."""
        self.client.get("/", name="[Page] 01_Home")
        self.client.get("/_healthz", name="[Probe] Healthz")

    @task(3)
    def view_product(self):
        """Views a random product's detail page."""
        pid = random.choice(SAMPLE_PRODUCT_IDS)
        self.client.get(f"/product/{pid}", name="[Page] 02_ProductDetail")

    @task(2)
    def add_to_cart(self):
        """Adds a random product to the shopping cart."""
        pid = random.choice(SAMPLE_PRODUCT_IDS)
        qty = random.choice([1, 2, 3])
        self.client.post(
            "/cart",
            data={"product_id": pid, "quantity": qty},
            name="[Action] 03_AddToCart"
        )

    @task(1)
    def switch_currency(self):
        """Switches display currency."""
        curr = random.choice(CURRENCIES)
        self.client.post(
            "/setCurrency",
            data={"currency_code": curr},
            name="[Action] 04_SetCurrency"
        )

    @task(1)
    def complete_checkout(self):
        """Executes full purchase checkout flow."""
        # Add item first to ensure cart is not empty
        pid = random.choice(SAMPLE_PRODUCT_IDS)
        self.client.post("/cart", data={"product_id": pid, "quantity": 1}, name="[Action] PreCheckout_AddToCart")
        
        # Place order
        order_payload = {
            "email": "loadtester@google-online-boutique.test",
            "street_address": "1600 Amphitheatre Parkway",
            "zip_code": "94043",
            "city": "Mountain View",
            "state": "CA",
            "country": "United States",
            "credit_card_number": "4432801561520454",
            "credit_card_expiration_month": "12",
            "credit_card_expiration_year": "2027",
            "credit_card_cvv": "123"
        }
        self.client.post("/cart/checkout", data=order_payload, name="[Action] 05_Checkout")
