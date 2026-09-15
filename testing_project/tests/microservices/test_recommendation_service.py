"""
gRPC Contract & Service Tests: RecommendationService.
Tests gRPC RPC methods: ListRecommendations.
"""
import pytest
from testing_project.protos import demo_pb2, demo_pb2_grpc


def test_list_recommendations(grpc_channel):
    """Verifies that RecommendationService returns relevant non-empty recommendations."""
    stub = demo_pb2_grpc.RecommendationServiceStub(grpc_channel)
    req = demo_pb2.ListRecommendationsRequest(
        user_id="sample-user-456",
        product_ids=["OLJCESPC7Z"]
    )
    resp = stub.ListRecommendations(req)

    assert len(resp.product_ids) > 0, "Expected recommended products"
    # Ensure it doesn't recommend the item already in the list if alternatives exist
    assert "OLJCESPC7Z" not in resp.product_ids
