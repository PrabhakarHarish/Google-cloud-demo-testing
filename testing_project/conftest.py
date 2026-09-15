"""
Pytest configuration and shared fixtures for Online Boutique test suite.
Supports dual-mode execution:
1. Live Kubernetes / Cloud cluster (GKE, Minikube, Docker) via BOUTIQUE_BASE_URL
2. In-process Mock Microservices & Frontend server if no external cluster is reachable.
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
    FRONTEND_URL,
    GRPC_HOST,
    GRPC_PORT,
    HEADLESS,
    DEFAULT_VIEWPORT,
    BROWSER_TIMEOUT
)
from testing_project.mock_services.mock_grpc_server import create_grpc_server
from testing_project.mock_services.mock_frontend_server import create_frontend_app


def is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def is_url_reachable(url: str, timeout: float = 1.0) -> bool:
    try:
        resp = requests.get(f"{url}/_healthz", timeout=timeout)
        return resp.status_code == 200
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
def test_environment_setup():
    """
    Session-wide fixture that ensures microservices and frontend are running.
    If external cluster is already reachable at FRONTEND_URL, it uses the live cluster.
    Otherwise, it spins up high-fidelity local mock servers for gRPC and HTTP frontend.
    """
    frontend_server_thread = None
    grpc_srv = None

    # Check if frontend is already running
    if not is_url_reachable(FRONTEND_URL, timeout=1.0):
        print(f"\n[SETUP] No live cluster reachable at {FRONTEND_URL}. Starting integrated test environment...")
        # Start gRPC mock microservices server if port is available
        if not is_port_open(GRPC_HOST, GRPC_PORT):
            grpc_srv = create_grpc_server(GRPC_PORT)
            grpc_srv.start()
            print(f"[SETUP] Started mock gRPC microservices on {GRPC_HOST}:{GRPC_PORT}")

        # Start Frontend server
        app = create_frontend_app()
        frontend_server_thread = ServerThread(app, host="127.0.0.1", port=8080)
        frontend_server_thread.start()
        print(f"[SETUP] Started frontend server on {FRONTEND_URL}")

        # Wait for frontend to be ready
        retries = 20
        while retries > 0:
            if is_url_reachable(FRONTEND_URL, timeout=0.5):
                break
            time.sleep(0.2)
            retries -= 1
        print("[SETUP] Test environment is ready.\n")
    else:
        print(f"\n[SETUP] Connected to live Online Boutique instance at {FRONTEND_URL}\n")

    yield

    # Teardown local servers if we started them
    if frontend_server_thread:
        print("\n[TEARDOWN] Stopping test frontend server...")
        frontend_server_thread.shutdown()
    if grpc_srv:
        print("[TEARDOWN] Stopping test gRPC microservices...")
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


@pytest.fixture(scope="session")
def grpc_channel():
    """Returns an insecure gRPC channel to the target microservices."""
    target = f"{GRPC_HOST}:{GRPC_PORT}"
    channel = grpc.insecure_channel(target)
    yield channel
    channel.close()

# the configuration above allows the tests to setup everything needed before the tests run, such as the browser, frontend URL and microservice connection.
# it also starts the local mock services if needed and cleans them up after all the tests finish.
