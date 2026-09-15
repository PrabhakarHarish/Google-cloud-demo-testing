"""
gRPC Contract & Service Tests: ProductCatalogService.
Tests gRPC RPC methods: ListProducts, GetProduct, SearchProducts.
"""
import grpc
import pytest
from testing_project.protos import demo_pb2, demo_pb2_grpc


def test_list_products(grpc_channel):
    """Verifies that ListProducts returns all catalog products with required fields."""
    stub = demo_pb2_grpc.ProductCatalogServiceStub(grpc_channel)
    response = stub.ListProducts(demo_pb2.Empty())

    assert len(response.products) > 0, "Catalog should contain products"
    first = response.products[0]
    assert len(first.id) > 0
    assert len(first.name) > 0
    assert first.price_usd.currency_code == "USD"
    assert first.price_usd.units >= 0


def test_get_product_by_id(grpc_channel):
    """Verifies fetching an existing product by unique ID."""
    stub = demo_pb2_grpc.ProductCatalogServiceStub(grpc_channel)
    # First get catalog list
    list_resp = stub.ListProducts(demo_pb2.Empty())
    target_id = list_resp.products[0].id

    product = stub.GetProduct(demo_pb2.GetProductRequest(id=target_id))
    assert product.id == target_id
    assert len(product.name) > 0


def test_get_product_not_found(grpc_channel):
    """Verifies that querying a non-existent product ID returns NOT_FOUND status code."""
    stub = demo_pb2_grpc.ProductCatalogServiceStub(grpc_channel)
    with pytest.raises(grpc.RpcError) as exc_info:
        stub.GetProduct(demo_pb2.GetProductRequest(id="NON_EXISTENT_SKU_123"))
    assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND


def test_search_products(grpc_channel):
    """Verifies product searching functionality by text query."""
    stub = demo_pb2_grpc.ProductCatalogServiceStub(grpc_channel)
    response = stub.SearchProducts(demo_pb2.SearchProductsRequest(query="sun"))

    assert len(response.results) > 0
    assert any("sun" in p.name.lower() or "sun" in p.description.lower() for p in response.results)
