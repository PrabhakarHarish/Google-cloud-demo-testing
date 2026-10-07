"""
gRPC Contract & Service Tests: CurrencyService.
Tests gRPC RPC methods: GetSupportedCurrencies, Convert.
"""
import pytest
from testing_project.protos import demo_pb2, demo_pb2_grpc


@pytest.fixture
def grpc_channel(currency_channel):
    """Backwards-compatibility alias providing CurrencyService channel."""
    return currency_channel


def test_get_supported_currencies(currency_channel):
    """Verifies that CurrencyService lists supported world currencies."""
    stub = demo_pb2_grpc.CurrencyServiceStub(currency_channel)
    resp = stub.GetSupportedCurrencies(demo_pb2.Empty())

    assert len(resp.currency_codes) > 0
    expected = ["USD", "EUR", "CAD", "JPY", "GBP"]
    for code in expected:
        assert code in resp.currency_codes, f"Missing expected currency: {code}"


def test_currency_conversion(currency_channel):
    """Verifies converting Money from USD to EUR returns valid amounts matching exchange rates."""
    stub = demo_pb2_grpc.CurrencyServiceStub(currency_channel)
    
    # 1. Convert 100 USD to EUR (currency_conversion.json: EUR=1.0, USD=1.1305 -> 100 / 1.1305 ≈ 88.46 EUR)
    from_money = demo_pb2.Money(currency_code="USD", units=100, nanos=0)
    req = demo_pb2.CurrencyConversionRequest(to_code="EUR")
    getattr(req, "from").CopyFrom(from_money)
    
    converted = stub.Convert(req)
    assert converted.currency_code == "EUR"
    total_eur = converted.units + (converted.nanos / 1e9)
    assert converted.units == 88
    assert abs(total_eur - (100.0 / 1.1305)) <= 0.05

    # 2. Convert Sunglasses catalog price ($19.99 USD) to EUR (19.99 / 1.1305 ≈ €17.68)
    sunglasses_money = demo_pb2.Money(currency_code="USD", units=19, nanos=990000000)
    req_sg = demo_pb2.CurrencyConversionRequest(to_code="EUR")
    getattr(req_sg, "from").CopyFrom(sunglasses_money)
    conv_sg = stub.Convert(req_sg)
    assert conv_sg.currency_code == "EUR"
    sg_eur = conv_sg.units + (conv_sg.nanos / 1e9)
    assert abs(sg_eur - 17.68) <= 0.05, f"Expected Sunglasses ~€17.68, got €{sg_eur:.2f}"

    # 3. Convert Sunglasses ($19.99 USD) to JPY ((19.99 / 1.1305) * 126.40 ≈ ¥2235.03)
    req_jpy = demo_pb2.CurrencyConversionRequest(to_code="JPY")
    getattr(req_jpy, "from").CopyFrom(sunglasses_money)
    conv_jpy = stub.Convert(req_jpy)
    assert conv_jpy.currency_code == "JPY"
    sg_jpy = conv_jpy.units + (conv_jpy.nanos / 1e9)
    assert abs(sg_jpy - 2235.03) <= 1.0, f"Expected Sunglasses ~¥2235.03, got ¥{sg_jpy:.2f}"
