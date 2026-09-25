"""
Cloud Infrastructure Tests: Cloud Security Posture & Resource Governance.
Validates least-privilege securityContext and CPU/Memory limits across pods.
"""
import yaml
import pytest
from testing_project.config import K8S_MANIFEST_PATH


@pytest.fixture(scope="module")
def deployments():
    with open(K8S_MANIFEST_PATH, "r", encoding="utf-8") as f:
        docs = list(yaml.safe_load_all(f))
    return [
        doc for doc in docs
        if doc and doc.get("kind") == "Deployment"
    ]


def test_least_privilege_security_context(deployments):

    for doc in deployments:
        name = doc["metadata"]["name"]
        pod_spec = doc["spec"]["template"]["spec"]
        pod_security = pod_spec.get("securityContext", {})
        container = pod_spec["containers"][0]
        container_security = container.get("securityContext", {})

        # Assert non-root execution (configured at pod level or container level)
        is_non_root = pod_security.get("runAsNonRoot", False) or container_security.get("runAsNonRoot", False)
        assert is_non_root is True, f"Microservice {name} does not enforce runAsNonRoot: true"

        # Assert privilege escalation disabled
        assert container_security.get("allowPrivilegeEscalation") is False, (
            f"Microservice {name} must set allowPrivilegeEscalation: false"
        )


def test_resource_requests_and_limits_defined(deployments):

    for doc in deployments:
        name = doc["metadata"]["name"]
        container = doc["spec"]["template"]["spec"]["containers"][0]
        resources = container.get("resources", {})

        assert "requests" in resources, f"Microservice {name} is missing resource requests"
        assert "limits" in resources, f"Microservice {name} is missing resource limits"
        assert "cpu" in resources["requests"] and "memory" in resources["requests"], (
            f"Microservice {name} missing CPU/memory requests"
        )
        assert "cpu" in resources["limits"] and "memory" in resources["limits"], (
            f"Microservice {name} missing CPU/memory limits"
        )
