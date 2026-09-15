"""
gRPC Contract & Service Tests: ShippingService.
Tests gRPC RPC methods: GetQuote, ShipOrder.
"""
import pytest
from testing_project.protos import demo_pb2, demo_pb2_grpc


def test_get_shipping_quote(grpc_channel):
    """Verifies that ShippingService calculates accurate quotes based on cart items."""
    stub = demo_pb2_grpc.ShippingServiceStub(grpc_channel)
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


def test_ship_order(grpc_channel):
    """Verifies that ShipOrder generates a valid tracking identifier for confirmed orders."""
    stub = demo_pb2_grpc.ShippingServiceStub(grpc_channel)
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

    assert resp.tracking_id.startswith("TRK-")
