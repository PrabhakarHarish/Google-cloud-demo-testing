"""
gRPC Contract & Service Tests: CartService.
Tests gRPC RPC methods: AddItem, GetCart, EmptyCart.
"""
import uuid
import pytest
from testing_project.protos import demo_pb2, demo_pb2_grpc


def test_cart_add_and_retrieve(grpc_channel):
    """Verifies adding items to a user's shopping cart and retrieving cart contents."""
    stub = demo_pb2_grpc.CartServiceStub(grpc_channel)
    user_id = f"test-user-{uuid.uuid4().hex[:6]}"

    # Add item
    item = demo_pb2.CartItem(product_id="OLJCESPC7Z", quantity=2)
    add_req = demo_pb2.AddItemRequest(user_id=user_id, item=item)
    stub.AddItem(add_req)

    # Retrieve cart
    cart = stub.GetCart(demo_pb2.GetCartRequest(user_id=user_id))
    assert cart.user_id == user_id
    assert len(cart.items) >= 1
    cart_item = next((i for i in cart.items if i.product_id == "OLJCESPC7Z"), None)
    assert cart_item is not None
    assert cart_item.quantity == 2


def test_cart_empty_action(grpc_channel):
    """Verifies that EmptyCart clears all items from the user's cart."""
    stub = demo_pb2_grpc.CartServiceStub(grpc_channel)
    user_id = f"test-user-{uuid.uuid4().hex[:6]}"

    # Add item first
    item = demo_pb2.CartItem(product_id="66VCHSJNUP", quantity=1)
    stub.AddItem(demo_pb2.AddItemRequest(user_id=user_id, item=item))

    # Empty cart
    stub.EmptyCart(demo_pb2.EmptyCartRequest(user_id=user_id))

    # Retrieve cart and assert empty
    cart = stub.GetCart(demo_pb2.GetCartRequest(user_id=user_id))
    assert len(cart.items) == 0
