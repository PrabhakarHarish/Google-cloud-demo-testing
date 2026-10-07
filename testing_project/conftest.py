"""
Pytest configuration and shared fixtures for Online Boutique test suite.
Supports explicit execution modes:
1. Live Kubernetes / Cloud cluster (GKE, Minikube, Docker) via BOUTIQUE_BASE_URL or --live
2. In-process Mock Microservices & Frontend server (Mock Mode) when no live cluster is requested or --mock

Safety guarantee:
When live mode is requested, the suite will NEVER silently fall back to mock services.
If the live target is unreachable, it will fail loudly immediately.
"""
import os
import socket
import threading
import time
import pytest
import requests
import grpc
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright

from testing_project.config import (
    FRONTEND_URL, GRPC_HOST, GRPC_PORT, HEADLESS, DEFAULT_VIEWPORT, BROWSER_TIMEOUT, SLOW_MO,
    is_live_mode_requested, BOUTIQUE_BASE_URL, get_service_addr,
    PRODUCT_CATALOG_ADDR, CART_SERVICE_ADDR, CURRENCY_SERVICE_ADDR,
    RECOMMENDATION_SERVICE_ADDR, SHIPPING_SERVICE_ADDR, PAYMENT_SERVICE_ADDR,
    CHECKOUT_SERVICE_ADDR, AD_SERVICE_ADDR
)
from testing_project.mock_services.mock_grpc_server import create_grpc_server
from testing_project.mock_services.mock_frontend_server import create_frontend_app


def pytest_addoption(parser):
    """Adds CLI options to explicitly choose execution modes and manifest targets."""
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Enforce testing against a live cluster. Fails loudly if target is unreachable."
    )
    parser.addoption(
        "--mock",
        action="store_true",
        default=False,
        help="Enforce running in mock mode using in-process simulated services."
    )
    parser.addoption(
        "--k8s-overlay",
        action="store",
        default=None,
        help="Path to custom Kustomize overlay to render and validate."
    )
    parser.addoption(
        "--k8s-engine",
        action="store",
        default=None,
        help="Manifest rendering engine: 'kustomize' (default) or 'helm'."
    )


def pytest_configure(config):
    if config.getoption("--live", default=False) and config.getoption("--mock", default=False):
        raise pytest.UsageError("Conflicting options: Cannot specify both --live and --mock.")
    overlay = config.getoption("--k8s-overlay", default=None)
    if overlay:
        os.environ["K8S_OVERLAY_PATH"] = overlay
    engine = config.getoption("--k8s-engine", default=None)
    if engine:
        os.environ["K8S_MANIFEST_ENGINE"] = engine


def pytest_report_header(config):
    """Displays execution mode clearly at the very top of the pytest output."""
    lines = []
    if is_live_mode_requested(config):
        target = os.getenv("BOUTIQUE_BASE_URL", FRONTEND_URL)
        lines.extend([
            "=" * 78,
            "  TEST EXECUTION MODE: [ LIVE CLUSTER MODE ]",
            f"  Target Cluster URL: {target}",
            "  Safety Rule: Fallback to mock is DISABLED (suite will fail loudly if target is down)",
            "=" * 78,
        ])
    else:
        lines.extend([
            "=" * 78,
            "  TEST EXECUTION MODE: [ MOCK MODE ] (Local In-Process Simulated Services)",
            "  Notice: Running against local mock gRPC microservices and mock HTTP frontend.",
            "  NO LIVE CLUSTER IS BEING TESTED.",
            "  To target a live cluster, set BOUTIQUE_BASE_URL or use the --live flag.",
            "=" * 78,
        ])
    return lines


@pytest.hookimpl(optionalhook=True)
def pytest_html_report_title(report):
    """Sets the HTML report title clearly indicating Mock Mode or Live Cluster Mode."""
    if is_live_mode_requested():
        target = os.getenv("BOUTIQUE_BASE_URL", FRONTEND_URL)
        report.title = f"Online Boutique Test Report [LIVE CLUSTER: {target}]"
    else:
        report.title = "Online Boutique Test Report [MOCK MODE - Simulated Services]"


@pytest.hookimpl(optionalhook=True)
def pytest_metadata(metadata, config):
    """Annotates pytest metadata in reports with the execution mode."""
    if is_live_mode_requested(config):
        metadata["Execution Mode"] = "LIVE CLUSTER MODE"
        metadata["Target Cluster URL"] = os.getenv("BOUTIQUE_BASE_URL", FRONTEND_URL)
        metadata["Mock Fallback"] = "DISABLED (Fail loudly)"
    else:
        metadata["Execution Mode"] = "MOCK MODE (Local In-Process Simulated Services)"
        metadata["Target Cluster URL"] = "None (Simulated)"
        metadata["Mock Fallback"] = "N/A"


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Outputs a prominent execution mode summary at the conclusion of the test run."""
    if is_live_mode_requested(config):
        target = os.getenv("BOUTIQUE_BASE_URL", FRONTEND_URL)
        terminalreporter.write_sep("=", "EXECUTION MODE: LIVE CLUSTER MODE", green=True, bold=True)
        terminalreporter.write_line(f"All executed tests targeted live cluster at: {target}")
    else:
        terminalreporter.write_sep("=", "EXECUTION MODE: MOCK MODE (SIMULATED)", yellow=True, bold=True)
        terminalreporter.write_line(
            "NOTE: All tests executed in [MOCK MODE] using local in-process simulated services.\n"
            "Results do NOT prove live cluster readiness or cloud deployment health."
        )


def is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def is_url_reachable(url: str, timeout: float = 2.0) -> bool:
    try:
        resp = requests.get(f"{url}/_healthz", timeout=timeout)
        if resp.status_code == 200:
            return True
    except Exception:
        pass
    try:
        resp = requests.get(url, timeout=timeout)
        return resp.status_code in (200, 301, 302)
    except Exception:
        return False


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8080):
        super().__init__(daemon=True)
        self.server = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


@pytest.fixture(scope="session", autouse=True)
def test_environment_setup(request):
    """
    Session-wide fixture that manages test targets.
    - If live mode is requested (via BOUTIQUE_BASE_URL, LIVE_MODE, or --live):
      Verifies that the live target is reachable. If unreachable, fails loudly immediately
      with a fatal error to avoid false-positive green results.
    - If mock mode:
      Starts in-process mock gRPC and mock HTTP servers, and logs clearly that mock mode is active.
    """
    config = request.config
    live_mode = is_live_mode_requested(config)

    if live_mode:
        # LIVE MODE: Check reachability and FAIL LOUDLY if down. Never fall back to mock.
        if not is_url_reachable(FRONTEND_URL, timeout=3.0):
            error_message = (
                f"\n{'!' * 78}\n"
                f"[FATAL ERROR] Live cluster requested at '{FRONTEND_URL}', but it is UNREACHABLE!\n"
                f"Health check probe failed: GET {FRONTEND_URL}/_healthz\n\n"
                f"A live environment was requested (via BOUTIQUE_BASE_URL or --live).\n"
                f"Failing immediately to prevent false-positive green test results.\n"
                f"The test suite will NEVER silently fall back to mock services when live testing is requested.\n\n"
                f"Troubleshooting:\n"
                f"  1. Verify the cluster or deployment is running and healthy.\n"
                f"  2. Check port-forwarding (e.g., kubectl port-forward deployment/frontend 8080:8080).\n"
                f"  3. Check target address: current target is '{FRONTEND_URL}'.\n"
                f"  4. To run local mock testing instead, unset BOUTIQUE_BASE_URL or run with --mock.\n"
                f"{'!' * 78}\n"
            )
            pytest.exit(error_message, returncode=1)

        print(f"\n[LIVE MODE] Connected to live Online Boutique instance at {FRONTEND_URL}\n")
        yield
        return

    # MOCK MODE: Start in-process mock microservices & mock frontend
    frontend_server_thread = None
    grpc_srv = None

    print(f"\n[MOCK MODE] Starting in-process mock microservices & frontend server...")
    if not is_port_open(GRPC_HOST, GRPC_PORT):
        grpc_srv = create_grpc_server(GRPC_PORT)
        grpc_srv.start()
        print(f"[MOCK MODE] Started mock gRPC microservices on {GRPC_HOST}:{GRPC_PORT}")
    else:
        print(f"[MOCK MODE] gRPC port {GRPC_PORT} is already open; reusing running service.")

    if not is_url_reachable(FRONTEND_URL, timeout=0.5):
        app = create_frontend_app()
        frontend_server_thread = ServerThread(app, host="127.0.0.1", port=8080)
        frontend_server_thread.start()
        print(f"[MOCK MODE] Started mock frontend server on {FRONTEND_URL}")

        # Wait for frontend to be ready
        retries = 20
        while retries > 0:
            if is_url_reachable(FRONTEND_URL, timeout=0.5):
                break
            time.sleep(0.2)
            retries -= 1
    else:
        print(f"[MOCK MODE] Mock frontend is already responsive at {FRONTEND_URL}")

    print("[MOCK MODE] Mock test environment is ready.\n")

    yield

    # Teardown local servers if we started them
    if frontend_server_thread:
        print("\n[TEARDOWN] Stopping mock frontend server...")
        frontend_server_thread.shutdown()
    if grpc_srv:
        print("[TEARDOWN] Stopping mock gRPC microservices...")
        grpc_srv.stop(0)


@pytest.fixture(scope="session")
def base_url():
    return FRONTEND_URL


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="function")
def browser(playwright_instance):
    browser = playwright_instance.chromium.launch(
        headless=HEADLESS,
        slow_mo=SLOW_MO,
        args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
    )
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def context(browser):
    context = browser.new_context(
        viewport=DEFAULT_VIEWPORT,
        user_agent="OnlineBoutique-Playwright-TestAgent/1.0"
    )
    context.set_default_timeout(BROWSER_TIMEOUT)
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context):
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def mobile_page(browser):
    """Playwright page configured for mobile viewport emulation."""
    from testing_project.config import MOBILE_VIEWPORT
    ctx = browser.new_context(
        viewport=MOBILE_VIEWPORT,
        is_mobile=True,
        has_touch=True,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"
    )
    ctx.set_default_timeout(BROWSER_TIMEOUT)
    p = ctx.new_page()
    yield p
    ctx.close()


def _build_service_channel(service_name: str, config=None):
    """Creates an insecure gRPC channel to the resolved target for a given microservice."""
    target = get_service_addr(service_name, config)
    return grpc.insecure_channel(target)


@pytest.fixture(scope="session")
def catalog_channel(request):
    """Returns an insecure gRPC channel for ProductCatalogService."""
    channel = _build_service_channel("productcatalogservice", request.config)
    yield channel
    channel.close()


@pytest.fixture(scope="session")
def product_catalog_channel(catalog_channel):
    """Alias for catalog_channel."""
    return catalog_channel


@pytest.fixture(scope="session")
def cart_channel(request):
    """Returns an insecure gRPC channel for CartService."""
    channel = _build_service_channel("cartservice", request.config)
    yield channel
    channel.close()


@pytest.fixture(scope="session")
def currency_channel(request):
    """Returns an insecure gRPC channel for CurrencyService."""
    channel = _build_service_channel("currencyservice", request.config)
    yield channel
    channel.close()


@pytest.fixture(scope="session")
def recommendation_channel(request):
    """Returns an insecure gRPC channel for RecommendationService."""
    channel = _build_service_channel("recommendationservice", request.config)
    yield channel
    channel.close()


@pytest.fixture(scope="session")
def shipping_channel(request):
    """Returns an insecure gRPC channel for ShippingService."""
    channel = _build_service_channel("shippingservice", request.config)
    yield channel
    channel.close()


@pytest.fixture(scope="session")
def payment_channel(request):
    """Returns an insecure gRPC channel for PaymentService."""
    channel = _build_service_channel("paymentservice", request.config)
    yield channel
    channel.close()


@pytest.fixture(scope="session")
def checkout_channel(request):
    """Returns an insecure gRPC channel for CheckoutService."""
    channel = _build_service_channel("checkoutservice", request.config)
    yield channel
    channel.close()


@pytest.fixture(scope="session")
def ad_channel(request):
    """Returns an insecure gRPC channel for AdService."""
    channel = _build_service_channel("adservice", request.config)
    yield channel
    channel.close()


@pytest.fixture(scope="session")
def grpc_channel():
    """Fallback insecure gRPC channel connecting to GRPC_HOST:GRPC_PORT."""
    target = f"{GRPC_HOST}:{GRPC_PORT}"
    channel = grpc.insecure_channel(target)
    yield channel
    channel.close()

# the configuration above allows the tests to set-up everything needed before the tests run, such as the browser, frontend URL and microservice connection.
# it also starts the local mock services if needed and cleans them up after all the tests finish.