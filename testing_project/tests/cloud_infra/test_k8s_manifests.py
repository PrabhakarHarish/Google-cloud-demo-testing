"""
Cloud Infrastructure Tests: Kubernetes Manifest Linting & Architecture Validation.
Validates rendered Kubernetes manifests (kustomize / helm / overlays) using
kubeconform schema validation, kube-score best-practice linting, and comprehensive
container inspections across all pods, init containers, and sidecars.
"""
import json
import shutil
import subprocess
import pytest
from testing_project.config import (
    K8S_MANIFEST_PATH,
    KUBECONFORM_CACHE_DIR,
    get_rendered_manifest_path,
    get_parsed_manifests,
)


EXPECTED_MICROSERVICES = {
    "frontend", "cartservice", "productcatalogservice", "currencyservice", "paymentservice",
    "shippingservice", "emailservice", "checkoutservice", "recommendationservice", "adservice",
    "loadgenerator"
}


@pytest.fixture(scope="module")
def rendered_manifest_path():
    """Provides path to dynamically rendered Kubernetes manifests."""
    path = get_rendered_manifest_path()
    assert path.exists(), f"Rendered manifest file not found at {path}"
    return path


@pytest.fixture(scope="module")
def parsed_manifests():
    """Provides list of parsed YAML resource documents from rendered manifests."""
    docs = get_parsed_manifests()
    assert len(docs) > 0, "No Kubernetes resources parsed from rendered manifests"
    return docs


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
    """
    Verifies all containers (including main containers, init containers, and sidecars)
    use pinned release images and never use mutable :latest tags.
    """
    total_containers_checked = 0
    for doc in parsed_manifests:
        if doc.get("kind") == "Deployment":
            name = doc["metadata"]["name"]
            pod_spec = doc["spec"]["template"]["spec"]
            all_containers = pod_spec.get("containers", []) + pod_spec.get("initContainers", [])
            assert len(all_containers) > 0, f"Deployment {name} has no containers defined"

            for c in all_containers:
                total_containers_checked += 1
                cname = c.get("name", "unknown")
                image = c.get("image", "")
                assert image, f"Service {name} container '{cname}' is missing an image reference"
                assert ":latest" not in image, (
                    f"Service {name} container '{cname}' uses mutable :latest tag ({image})"
                )

                if name == "redis-cart":
                    assert "redis" in image, (
                        f"Service redis-cart container '{cname}' uses unexpected image ({image})"
                    )
                elif cname == "frontend-check":
                    assert "busybox" in image, (
                        f"Service {name} init container '{cname}' uses unexpected image ({image})"
                    )
                else:
                    assert "microservices-demo" in image, (
                        f"Service {name} container '{cname}' uses unexpected image repository ({image})"
                    )

    assert total_containers_checked >= 13, f"Expected at least 13 containers checked, got {total_containers_checked}"


def test_kubeconform_schema_validation(rendered_manifest_path):
    """
    Validates rendered Kubernetes manifests against official Kubernetes JSON schemas
    using the kubeconform schema validator.
    """
    kubeconform_bin = shutil.which("kubeconform")
    if not kubeconform_bin:
        pytest.skip("kubeconform binary not found in PATH")

    cmd = [
        kubeconform_bin,
        "-summary",
        "-verbose",
        "-cache", str(KUBECONFORM_CACHE_DIR),
        "-schema-location", "default",
        "-ignore-missing-schemas",
        str(rendered_manifest_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, (
        f"kubeconform schema validation failed with exit code {result.returncode}:\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
    assert "Invalid: 0" in result.stdout, f"kubeconform reported invalid resources:\n{result.stdout}"
    assert "Errors: 0" in result.stdout, f"kubeconform reported schema errors:\n{result.stdout}"


def test_kube_score_linting(rendered_manifest_path):
    """
    Validates Kubernetes manifests against best-practice rules using kube-score.
    Enforces security context, stable API versions, image tagging, and valid selectors.
    """
    kube_score_bin = shutil.which("kube-score")
    if not kube_score_bin:
        pytest.skip("kube-score binary not found in PATH")

    # 1. Structured JSON Inspection for Critical Security & Reliability Policies
    json_cmd = [kube_score_bin, "score", "--output-format", "json", str(rendered_manifest_path)]
    json_res = subprocess.run(json_cmd, capture_output=True, text=True)

    try:
        audit_results = json.loads(json_res.stdout)
    except json.JSONDecodeError as err:
        pytest.fail(f"Failed to parse kube-score JSON output: {err}\nSTDOUT:\n{json_res.stdout}")

    assert len(audit_results) > 0, "kube-score produced empty audit results"

    critical_checks = [
        "container-security-context-privileged",
        "container-image-tag",
        "stable-version",
        "deployment-pod-selector-labels-match-template-metadata-labels",
        "service-targets-pod",
    ]

    for obj in audit_results:
        name = obj.get("object_meta", {}).get("name")
        kind = obj.get("type_meta", {}).get("kind")
        for check in obj.get("checks", []):
            cid = check.get("check", {}).get("id")
            if cid in critical_checks:
                grade = check.get("grade", 0)
                comments = check.get("comments")
                assert grade == 10, (
                    f"Resource {kind}/{name} failed critical kube-score check '{cid}': {comments}"
                )

    # 2. CLI Clean Run with Standard Configured Rule Exclusions
    cli_cmd = [
        kube_score_bin, "score",
        "--ignore-test", "deployment-has-poddisruptionbudget",
        "--ignore-test", "deployment-has-host-podantiaffinity",
        "--ignore-test", "deployment-replicas",
        "--ignore-test", "pod-networkpolicy",
        "--ignore-test", "container-ephemeral-storage-request-and-limit",
        "--ignore-test", "container-security-context-user-group-id",
        "--ignore-test", "container-cpu-requests-equal-limits",
        "--ignore-test", "container-memory-requests-equal-limits",
        "--ignore-test", "container-resource-requests-equal-limits",
        "--ignore-test", "container-image-pull-policy",
        "--ignore-test", "container-seccomp-profile",
        "--ignore-test", "pod-probes-identical",
        "--ignore-test", "container-resources",
        "--ignore-test", "deployment-strategy",
        str(rendered_manifest_path)
    ]
    cli_res = subprocess.run(cli_cmd, capture_output=True, text=True)
    assert cli_res.returncode == 0, (
        f"kube-score CLI linting encountered rule failures:\n{cli_res.stdout}\n{cli_res.stderr}"
    )
