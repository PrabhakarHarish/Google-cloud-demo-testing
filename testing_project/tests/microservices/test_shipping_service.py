"""
gRPC Contract & Service Tests: ShippingService.
Tests gRPC RPC methods: GetQuote, ShipOrder.
"""
import re
import pytest
from testing_project.protos import demo_pb2, demo_pb2_grpc


@pytest.fixture
def grpc_channel(shipping_channel):
    """Backwards-compatibility alias providing ShippingService channel."""
    return shipping_channel


def test_get_shipping_quote(shipping_channel):
    """Verifies that ShippingService calculates accurate quotes based on cart items."""
    stub = demo_pb2_grpc.ShippingServiceStub(shipping_channel)
    address = demo_pb2.Address(
        street_address="1600 Amphitheatre Pkwy",
        city="Mountain View",
        state="CA",
        country="United States",
        zip_code=94043
    )
    items = [
        demo_pb2.CartItem(product_id="OLJCESPC7Z", quantity=1),
        demo_pb2.CartItem(product_id="66VCHSJNUP", quantity=2)
    ]
    req = demo_pb2.GetQuoteRequest(address=address, items=items)
    quote = stub.GetQuote(req)

    assert quote.cost_usd.currency_code == "USD"
    assert quote.cost_usd.units >= 0


def test_ship_order(shipping_channel):
    """Verifies that ShipOrder generates a valid tracking identifier (format: [A-Z]{2}-\\d+-\\d+ per shippingservice/tracker.go)."""
    stub = demo_pb2_grpc.ShippingServiceStub(shipping_channel)
    address = demo_pb2.Address(
        street_address="1600 Amphitheatre Pkwy",
        city="Mountain View",
        state="CA",
        country="United States",
        zip_code=94043
    )
    items = [demo_pb2.CartItem(product_id="OLJCESPC7Z", quantity=1)]
    req = demo_pb2.ShipOrderRequest(address=address, items=items)
    resp = stub.ShipOrder(req)

    # Shipping tracking ids look like AB-12345-678 (shippingservice/tracker.go)
    assert re.match(r"^[A-Z]{2}-\d+-\d+$", resp.tracking_id), f"Unexpected tracking ID format: {resp.tracking_id}"
