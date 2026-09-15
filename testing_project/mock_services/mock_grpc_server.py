import json
import math
import uuid
from concurrent import futures
from typing import Dict, List

import grpc
from testing_project.config import PRODUCTS_JSON_PATH, CURRENCY_JSON_PATH
from testing_project.protos import demo_pb2, demo_pb2_grpc


# Load product catalog data from repository
def load_catalog_data():
    if PRODUCTS_JSON_PATH.exists():
        with open(PRODUCTS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("products", [])
    return [
        {
            "id": "OLJCESPC7Z",
            "name": "Sunglasses",
            "description": "Add a modern touch to your outfits with these sleek aviator sunglasses.",
            "picture": "/static/img/products/sunglasses.jpg",
            "priceUsd": {"currencyCode": "USD", "units": 19, "nanos": 990000000},
            "categories": ["accessories"]
        },
        {
            "id": "66VCHSJNUP",
            "name": "Tank Top",
            "description": "Perfectly cropped cotton tank, with a scooped neckline.",
            "picture": "/static/img/products/tank-top.jpg",
            "priceUsd": {"currencyCode": "USD", "units": 18, "nanos": 990000000},
            "categories": ["clothing", "tops"]
        },
        {
            "id": "1YMWWN1N4O",
            "name": "Watch",
            "description": "This gold-tone stainless steel watch will work with most of your outfits.",
            "picture": "/static/img/products/watch.jpg",
            "priceUsd": {"currencyCode": "USD", "units": 109, "nanos": 990000000},
            "categories": ["accessories"]
        }
    ]

# Load currency exchange data
def load_currency_data():
    if CURRENCY_JSON_PATH.exists():
        with open(CURRENCY_JSON_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
            return {k: float(v) for k, v in raw.items()}
    return {
        "USD": 1.0,
        "EUR": 0.92,
        "CAD": 1.35,
        "JPY": 150.0,
        "GBP": 0.79,
        "TRY": 32.5
    }


class ProductCatalogService(demo_pb2_grpc.ProductCatalogServiceServicer):
    def __init__(self):
        self.raw_products = load_catalog_data()

    def _to_proto_product(self, raw: dict) -> demo_pb2.Product:
        price_data = raw.get("priceUsd", {})
        money = demo_pb2.Money(
            currency_code=price_data.get("currencyCode", "USD"),
            units=int(price_data.get("units", 0)),
            nanos=int(price_data.get("nanos", 0))
        )
        return demo_pb2.Product(
            id=raw["id"],
            name=raw["name"],
            description=raw.get("description", ""),
            picture=raw.get("picture", ""),
            price_usd=money,
            categories=raw.get("categories", [])
        )

    def ListProducts(self, request, context):
        products = [self._to_proto_product(p) for p in self.raw_products]
        return demo_pb2.ListProductsResponse(products=products)

    def GetProduct(self, request, context):
        for p in self.raw_products:
            if p["id"] == request.id:
                return self._to_proto_product(p)
        context.abort(grpc.StatusCode.NOT_FOUND, f"Product {request.id} not found")

    def SearchProducts(self, request, context):
        query = request.query.lower()
        matched = [
            self._to_proto_product(p)
            for p in self.raw_products
            if query in p["name"].lower() or query in p.get("description", "").lower()
        ]
        return demo_pb2.SearchProductsResponse(results=matched)


class CartService(demo_pb2_grpc.CartServiceServicer):
    def __init__(self):
        # In-memory storage: user_id -> dict of {product_id: quantity}
        self.carts: Dict[str, Dict[str, int]] = {}

    def AddItem(self, request, context):
        user_id = request.user_id
        item = request.item
        if user_id not in self.carts:
            self.carts[user_id] = {}
        current_qty = self.carts[user_id].get(item.product_id, 0)
        self.carts[user_id][item.product_id] = current_qty + item.quantity
        return demo_pb2.Empty()

    def GetCart(self, request, context):
        user_id = request.user_id
        items_dict = self.carts.get(user_id, {})
        proto_items = [
            demo_pb2.CartItem(product_id=pid, quantity=qty)
            for pid, qty in items_dict.items()
        ]
        return demo_pb2.Cart(user_id=user_id, items=proto_items)

    def EmptyCart(self, request, context):
        user_id = request.user_id
        if user_id in self.carts:
            self.carts[user_id] = {}
        return demo_pb2.Empty()


class CurrencyService(demo_pb2_grpc.CurrencyServiceServicer):
    def __init__(self):
        self.rates = load_currency_data()

    def GetSupportedCurrencies(self, request, context):
        return demo_pb2.GetSupportedCurrenciesResponse(
            currency_codes=list(self.rates.keys())
        )

    def Convert(self, request, context):
        from_money = getattr(request, "from")
        from_code = from_money.currency_code
        to_code = request.to_code

        from_rate = self.rates.get(from_code, 1.0)
        to_rate = self.rates.get(to_code, 1.0)

        # Convert from original currency to EUR/USD base then to target
        # For Online Boutique demo rates: base is EUR or USD
        total_units = from_money.units + (from_money.nanos / 1e9)
        base_val = total_units / from_rate if from_rate != 0 else total_units
        converted_val = base_val * to_rate

        units = int(converted_val)
        nanos = int(round((converted_val - units) * 1e9))

        return demo_pb2.Money(
            currency_code=to_code,
            units=units,
            nanos=nanos
        )


class RecommendationService(demo_pb2_grpc.RecommendationServiceServicer):
    def ListRecommendations(self, request, context):
        # Return a list of recommended product IDs
        catalog = load_catalog_data()
        all_ids = [p["id"] for p in catalog]
        # Exclude already selected product IDs
        candidates = [pid for pid in all_ids if pid not in request.product_ids]
        recommended = candidates[:4] if candidates else all_ids[:4]
        return demo_pb2.ListRecommendationsResponse(product_ids=recommended)


class ShippingService(demo_pb2_grpc.ShippingServiceServicer):
    def GetQuote(self, request, context):
        item_count = sum(item.quantity for item in request.items)
        # Standard calculation demo: $8.99 flat base + count
        units = 8 + (item_count % 3)
        return demo_pb2.GetQuoteResponse(
            cost_usd=demo_pb2.Money(currency_code="USD", units=units, nanos=990000000)
        )

    def ShipOrder(self, request, context):
        tracking_id = f"TRK-{uuid.uuid4().hex[:8].upper()}"
        return demo_pb2.ShipOrderResponse(tracking_id=tracking_id)


class PaymentService(demo_pb2_grpc.PaymentServiceServicer):
    def Charge(self, request, context):
        # Validate credit card length
        cc_num = request.credit_card.credit_card_number.replace(" ", "").replace("-", "")
        if len(cc_num) < 13 or len(cc_num) > 19:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid credit card number")
        tx_id = f"TX-{uuid.uuid4().hex[:10].upper()}"
        return demo_pb2.ChargeResponse(transaction_id=tx_id)


class CheckoutService(demo_pb2_grpc.CheckoutServiceServicer):
    def __init__(self, cart_service: CartService, catalog_service: ProductCatalogService):
        self.cart_service = cart_service
        self.catalog_service = catalog_service

    def PlaceOrder(self, request, context):
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        tracking_id = f"TRK-{uuid.uuid4().hex[:8].upper()}"

        # Calculate total
        total_units = 25
        order_result = demo_pb2.OrderResult(
            order_id=order_id,
            shipping_tracking_id=tracking_id,
            shipping_cost=demo_pb2.Money(currency_code="USD", units=8, nanos=990000000),
            shipping_address=request.address,
            items=[]
        )
        # Clear cart for user
        self.cart_service.EmptyCart(demo_pb2.EmptyCartRequest(user_id=request.user_id), context)
        return demo_pb2.PlaceOrderResponse(order=order_result)


class AdService(demo_pb2_grpc.AdServiceServicer):
    def GetAds(self, request, context):
        ads = [
            demo_pb2.Ad(redirect_url="/product/2ZYFJ3GM2N", text="Airfly Hairdryer on sale! 20% off"),
            demo_pb2.Ad(redirect_url="/product/OLJCESPC7Z", text="Sleek sunglasses for bright sunny days!")
        ]
        return demo_pb2.AdResponse(ads=ads)


def create_grpc_server(port: int = 50051) -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    catalog_svc = ProductCatalogService()
    cart_svc = CartService()
    currency_svc = CurrencyService()
    recommendation_svc = RecommendationService()
    shipping_svc = ShippingService()
    payment_svc = PaymentService()
    checkout_svc = CheckoutService(cart_svc, catalog_svc)
    ad_svc = AdService()

    demo_pb2_grpc.add_ProductCatalogServiceServicer_to_server(catalog_svc, server)
    demo_pb2_grpc.add_CartServiceServicer_to_server(cart_svc, server)
    demo_pb2_grpc.add_CurrencyServiceServicer_to_server(currency_svc, server)
    demo_pb2_grpc.add_RecommendationServiceServicer_to_server(recommendation_svc, server)
    demo_pb2_grpc.add_ShippingServiceServicer_to_server(shipping_svc, server)
    demo_pb2_grpc.add_PaymentServiceServicer_to_server(payment_svc, server)
    demo_pb2_grpc.add_CheckoutServiceServicer_to_server(checkout_svc, server)
    demo_pb2_grpc.add_AdServiceServicer_to_server(ad_svc, server)

    server.add_insecure_port(f"0.0.0.0:{port}")
    return server


if __name__ == "__main__":
    srv = create_grpc_server(50051)
    srv.start()
    print("gRPC mock microservices server listening on port 50051...")
    srv.wait_for_termination()
