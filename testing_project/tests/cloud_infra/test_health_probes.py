"""
Cloud Infrastructure Tests: Kubernetes Health Probe Validation.
Validates liveness and readiness probe configurations on every serving container
and sidecar across frontend and backend microservices.
"""
import pytest
from testing_project.config import get_parsed_manifests


@pytest.fixture(scope="module")
def deployments():
    """Returns a mapping of deployment names to Deployment resource documents."""
    docs = get_parsed_manifests()
    return {
        doc["metadata"]["name"]: doc
        for doc in docs
        if doc and doc.get("kind") == "Deployment"
    }


def test_frontend_health_probe_configuration(deployments):
    """Verifies that every container in the Frontend deployment uses HTTP probes with /_healthz path."""
    frontend = deployments.get("frontend")
    assert frontend is not None, "Deployment 'frontend' not found in rendered manifests"

    containers = frontend["spec"]["template"]["spec"].get("containers", [])
    assert len(containers) > 0, "Frontend deployment has no containers"

    for container in containers:
        cname = container.get("name", "unknown")

        # Readiness probe
        readiness = container.get("readinessProbe")
        assert readiness is not None, f"Frontend container '{cname}' missing readinessProbe"
        assert readiness.get("httpGet") is not None, f"Frontend container '{cname}' readiness probe must use httpGet"
        assert readiness["httpGet"]["path"] == "/_healthz"
        assert readiness["httpGet"]["port"] == 8080

        # Liveness probe
        liveness = container.get("livenessProbe")
        assert liveness is not None, f"Frontend container '{cname}' missing livenessProbe"
        assert liveness.get("httpGet") is not None, f"Frontend container '{cname}' liveness probe must use httpGet"
        assert liveness["httpGet"]["path"] == "/_healthz"
        assert liveness["httpGet"]["port"] == 8080


def test_backend_microservices_probes_exist(deployments):
    """
    Verifies that every backend microservice specifies liveness and readiness probes
    for every serving container and sidecar.
    """
    # loadgenerator is an ephemeral job/load runner, not a long-running server
    services_to_check = [
        "cartservice", "productcatalogservice", "currencyservice",
        "paymentservice", "shippingservice", "emailservice",
        "checkoutservice", "recommendationservice", "adservice"
    ]

    for svc in services_to_check:
        deployment = deployments.get(svc)
        assert deployment is not None, f"Deployment {svc} not found in rendered manifests"

        containers = deployment["spec"]["template"]["spec"].get("containers", [])
        assert len(containers) > 0, f"Service {svc} has no containers defined"

        for container in containers:
            cname = container.get("name", "unknown")
            readiness = container.get("readinessProbe")
            liveness = container.get("livenessProbe")

            assert readiness is not None, f"Service {svc} container '{cname}' is missing readinessProbe"
            assert liveness is not None, f"Service {svc} container '{cname}' is missing livenessProbe"
