"""
gRPC Contract & Service Tests: PaymentService.
Tests gRPC RPC methods: Charge.
"""
import uuid
import grpc
import pytest
from testing_project.protos import demo_pb2, demo_pb2_grpc


@pytest.fixture
def grpc_channel(payment_channel):
    """Backwards-compatibility alias providing PaymentService channel."""
    return payment_channel


def test_charge_valid_credit_card(payment_channel):
    """Verifies successful payment authorization and transaction ID generation (UUID format from paymentservice/charge.js)."""
    stub = demo_pb2_grpc.PaymentServiceStub(payment_channel)
    cc = demo_pb2.CreditCardInfo(
        credit_card_number="4432801561520454",
        credit_card_cvv=123,
        credit_card_expiration_year=2027,
        credit_card_expiration_month=12
    )
    amount = demo_pb2.Money(currency_code="USD", units=29, nanos=990000000)
    req = demo_pb2.ChargeRequest(amount=amount, credit_card=cc)

    resp = stub.Charge(req)
    # Payment returns a UUID as transaction_id (paymentservice/charge.js: { transaction_id: uuidv4() })
    parsed_uuid = uuid.UUID(resp.transaction_id)
    assert str(parsed_uuid) == resp.transaction_id.lower()


def test_charge_invalid_credit_card(payment_channel):
    """
    Verifies that PaymentService rejects invalid card numbers with UNKNOWN.
    The real Node service passes the CreditCardError back without an explicit
    gRPC status code, which @grpc/grpc-js surfaces as grpc.StatusCode.UNKNOWN.
    """
    stub = demo_pb2_grpc.PaymentServiceStub(payment_channel)
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
    assert exc_info.value.code() == grpc.StatusCode.UNKNOWN
