import yaml
import pytest
from testing_project.config import K8S_MANIFEST_PATH


@pytest.fixture(scope="module")
def deployments():
    with open(K8S_MANIFEST_PATH, "r", encoding="utf-8") as f:
        docs = list(yaml.safe_load_all(f))
    return {
        doc["metadata"]["name"]: doc
        for doc in docs
        if doc and doc.get("kind") == "Deployment"
    }


def test_frontend_health_probe_configuration(deployments):
    """Verifies that Frontend deployment uses HTTP probes with /_healthz path."""
    frontend = deployments.get("frontend")
    assert frontend is not None
    container = frontend["spec"]["template"]["spec"]["containers"][0]

    # Readiness probe
    readiness = container.get("readinessProbe")
    assert readiness is not None, "Frontend missing readinessProbe"
    assert readiness["httpGet"]["path"] == "/_healthz"
    assert readiness["httpGet"]["port"] == 8080

    # Liveness probe
    liveness = container.get("livenessProbe")
    assert liveness is not None, "Frontend missing livenessProbe"
    assert liveness["httpGet"]["path"] == "/_healthz"
    assert liveness["httpGet"]["port"] == 8080


def test_backend_microservices_probes_exist(deployments):
    """Verifies that every backend microservice specifies liveness and readiness probes."""
    # loadgenerator is an ephemeral job/load runner, not a long-running server
    services_to_check = [
        "cartservice", "productcatalogservice", "currencyservice",
        "paymentservice", "shippingservice", "emailservice",
        "checkoutservice", "recommendationservice", "adservice"
    ]

    for svc in services_to_check:
        deployment = deployments.get(svc)
        assert deployment is not None, f"Deployment {svc} not found"
        container = deployment["spec"]["template"]["spec"]["containers"][0]
        
        readiness = container.get("readinessProbe")
        liveness = container.get("livenessProbe")
        
        assert readiness is not None, f"Service {svc} is missing readinessProbe"
        assert liveness is not None, f"Service {svc} is missing livenessProbe"
