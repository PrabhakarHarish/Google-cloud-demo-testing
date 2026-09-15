"""
gRPC Contract & Service Tests: CurrencyService.
Tests gRPC RPC methods: GetSupportedCurrencies, Convert.
"""
import pytest
from testing_project.protos import demo_pb2, demo_pb2_grpc


def test_get_supported_currencies(grpc_channel):
    """Verifies that CurrencyService lists supported world currencies."""
    stub = demo_pb2_grpc.CurrencyServiceStub(grpc_channel)
    resp = stub.GetSupportedCurrencies(demo_pb2.Empty())

    assert len(resp.currency_codes) > 0
    expected = ["USD", "EUR", "CAD", "JPY", "GBP"]
    for code in expected:
        assert code in resp.currency_codes, f"Missing expected currency: {code}"


def test_currency_conversion(grpc_channel):
    """Verifies converting Money from USD to EUR returns valid non-zero amounts."""
    stub = demo_pb2_grpc.CurrencyServiceStub(grpc_channel)
    
    # Convert 100 USD to EUR
    from_money = demo_pb2.Money(currency_code="USD", units=100, nanos=0)
    req = demo_pb2.CurrencyConversionRequest(to_code="EUR")
    getattr(req, "from").CopyFrom(from_money)
    
    converted = stub.Convert(req)
    assert converted.currency_code == "EUR"
    assert converted.units > 0 or converted.nanos > 0
