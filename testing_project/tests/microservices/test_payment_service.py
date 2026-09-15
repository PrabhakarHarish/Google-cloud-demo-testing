"""
gRPC Contract & Service Tests: PaymentService.
Tests gRPC RPC methods: Charge.
"""
import grpc
import pytest
from testing_project.protos import demo_pb2, demo_pb2_grpc


def test_charge_valid_credit_card(grpc_channel):
    """Verifies successful payment authorization and transaction ID generation."""
    stub = demo_pb2_grpc.PaymentServiceStub(grpc_channel)
    cc = demo_pb2.CreditCardInfo(
        credit_card_number="4432801561520454",
        credit_card_cvv=123,
        credit_card_expiration_year=2027,
        credit_card_expiration_month=12
    )
    amount = demo_pb2.Money(currency_code="USD", units=29, nanos=990000000)
    req = demo_pb2.ChargeRequest(amount=amount, credit_card=cc)

    resp = stub.Charge(req)
    assert resp.transaction_id.startswith("TX-")


def test_charge_invalid_credit_card(grpc_channel):
    """Verifies that PaymentService rejects invalid card numbers with INVALID_ARGUMENT."""
    stub = demo_pb2_grpc.PaymentServiceStub(grpc_channel)
    cc = demo_pb2.CreditCardInfo(
        credit_card_number="1234",  # Invalid short card number
        credit_card_cvv=123,
        credit_card_expiration_year=2027,
        credit_card_expiration_month=12
    )
    amount = demo_pb2.Money(currency_code="USD", units=29, nanos=0)
    req = demo_pb2.ChargeRequest(amount=amount, credit_card=cc)

    with pytest.raises(grpc.RpcError) as exc_info:
        stub.Charge(req)
    assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT
