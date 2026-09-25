"""
Cloud Infrastructure Tests: Kubernetes Manifest Linting & Architecture Validation.
Validates all 11 Online Boutique microservice Deployments, Services, and container specifications.
"""
import yaml
import pytest
from testing_project.config import K8S_MANIFEST_PATH


EXPECTED_MICROSERVICES = {
    "frontend","cartservice","productcatalogservice","currencyservice","paymentservice","shippingservice","emailservice",
    "checkoutservice","recommendationservice","adservice","loadgenerator" }


@pytest.fixture(scope="module")
def parsed_manifests():
    assert K8S_MANIFEST_PATH.exists(), f"Manifest file not found at {K8S_MANIFEST_PATH}"
    with open(K8S_MANIFEST_PATH, "r", encoding="utf-8") as f:
        docs = list(yaml.safe_load_all(f))
    # Filter non-empty YAML documents
    return [doc for doc in docs if doc]


def test_all_11_microservices_deployments_exist(parsed_manifests):
    """Verifies that all 11 required microservices have a Kubernetes Deployment resource."""
    deployment_names = {
        doc["metadata"]["name"]
        for doc in parsed_manifests
        if doc.get("kind") == "Deployment"
    }

    missing = EXPECTED_MICROSERVICES - deployment_names
    assert not missing, f"Missing microservice Deployments: {missing}"


def test_all_microservices_expose_k8s_services(parsed_manifests):
    """Verifies that core microservices have corresponding Kubernetes Service definitions."""
    service_names = {
        doc["metadata"]["name"]
        for doc in parsed_manifests
        if doc.get("kind") == "Service"
    }
    # loadgenerator is a client only and doesn't expose a Service
    services_to_check = EXPECTED_MICROSERVICES - {"loadgenerator"}
    missing = services_to_check - service_names
    assert not missing, f"Missing microservice Kubernetes Services: {missing}"


def test_container_image_tags_and_naming(parsed_manifests):
    """Verifies all microservices use pinned release images from secure registries."""
    for doc in parsed_manifests:
        if doc.get("kind") == "Deployment":
            name = doc["metadata"]["name"]
            containers = doc["spec"]["template"]["spec"]["containers"]
            for c in containers:
                image = c["image"]
                assert ":latest" not in image, f"Service {name} uses mutable :latest tag ({image})"
                if name == "redis-cart":
                    assert "redis" in image, f"Service redis-cart uses unexpected image ({image})"
                else:
                    assert "microservices-demo" in image, f"Service {name} uses unexpected image repository ({image})"
