"""
Cloud Infrastructure Tests: Cloud Security Posture & Resource Governance.
Validates least-privilege securityContext and CPU/Memory resource requests and limits
across all containers in all pods, including main serving containers, init containers, and sidecars.
"""
import pytest
from testing_project.config import get_parsed_manifests


@pytest.fixture(scope="module")
def deployments():
    """Returns a list of Deployment resource documents from rendered manifests."""
    docs = get_parsed_manifests()
    return [
        doc for doc in docs
        if doc and doc.get("kind") == "Deployment"
    ]


def test_least_privilege_security_context(deployments):
    """
    Asserts least-privilege security settings across EVERY container, init container, and sidecar:
    - runAsNonRoot: true enforced at pod or container level
    - allowPrivilegeEscalation: false enforced on every container
    """
    total_containers_checked = 0
    for doc in deployments:
        name = doc["metadata"]["name"]
        pod_spec = doc["spec"]["template"]["spec"]
        pod_security = pod_spec.get("securityContext", {})

        all_containers = pod_spec.get("containers", []) + pod_spec.get("initContainers", [])
        assert len(all_containers) > 0, f"Microservice {name} has no containers defined"

        for container in all_containers:
            total_containers_checked += 1
            cname = container.get("name", "unknown")
            container_security = container.get("securityContext", {})

            # Assert non-root execution (configured at pod level or container level)
            is_non_root = pod_security.get("runAsNonRoot", False) or container_security.get("runAsNonRoot", False)
            assert is_non_root is True, (
                f"Microservice {name} container '{cname}' does not enforce runAsNonRoot: true"
            )

            # Assert privilege escalation disabled
            assert container_security.get("allowPrivilegeEscalation") is False, (
                f"Microservice {name} container '{cname}' must set allowPrivilegeEscalation: false"
            )

    assert total_containers_checked >= 13, f"Expected at least 13 containers checked, got {total_containers_checked}"


def test_resource_requests_and_limits_defined(deployments):
    """
    Asserts CPU and memory requests and limits are explicitly defined on EVERY container,
    including main application containers, init containers, and sidecars.
    """
    total_containers_checked = 0
    for doc in deployments:
        name = doc["metadata"]["name"]
        pod_spec = doc["spec"]["template"]["spec"]
        all_containers = pod_spec.get("containers", []) + pod_spec.get("initContainers", [])
        assert len(all_containers) > 0, f"Microservice {name} has no containers defined"

        for container in all_containers:
            total_containers_checked += 1
            cname = container.get("name", "unknown")
            resources = container.get("resources")

            assert resources is not None, (
                f"Microservice {name} container '{cname}' is missing resources block entirely"
            )
            assert "requests" in resources, (
                f"Microservice {name} container '{cname}' is missing resource requests"
            )
            assert "limits" in resources, (
                f"Microservice {name} container '{cname}' is missing resource limits"
            )
            assert "cpu" in resources["requests"] and "memory" in resources["requests"], (
                f"Microservice {name} container '{cname}' missing CPU/memory requests"
            )
            assert "cpu" in resources["limits"] and "memory" in resources["limits"], (
                f"Microservice {name} container '{cname}' missing CPU/memory limits"
            )

    assert total_containers_checked >= 13, f"Expected at least 13 containers checked, got {total_containers_checked}"
