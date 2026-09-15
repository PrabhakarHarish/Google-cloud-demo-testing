# Google Online Boutique - Codebase Directory & File Guide

This document provides a comprehensive, detailed breakdown of the directories and files within this workspace. It serves as an architectural blueprint to help you understand how the **Google Online Boutique** microservices application and its associated **Advanced Cloud & Microservices Testing Framework** are structured and how they interact.

---

## Workspace Root Directory Layout

```text
/home/harish/Desktop/Cloud-micrservice-google/
├── CODEBASE_GUIDE.md           <-- This document (Detailed guide)
├── main.py                     <-- Boilerplate placeholder script (can be ignored)
├── pytest.ini                  <-- Pytest test runner global configuration
├── requirements.txt            <-- Testing framework Python dependencies
├── microservices-demo/         <-- Official Google Online Boutique codebase
└── testing_project/            <-- Cloud & Microservices Advanced Testing Framework
```

---

## 1. Root Configuration Files

### `pytest.ini`
* **Purpose:** Sets the standard run-time behavior of the `pytest` runner.
* **Key Contents:**
  * Defines the search paths (`testing_project/tests`) and file/class/function naming patterns (`test_*.py`, `Test*`, `test_*`).
  * Automatically applies custom CLI arguments (`addopts = -v -s`) for verbose terminal output without generating HTML reports.
  * Registers custom metadata markers (`e2e`, `grpc`, `cloud`) to categorize and isolate test suites.

### `requirements.txt`
* **Purpose:** Lists all Python dependencies needed to execute the testing framework, including UI test execution, contract validation, and load generation.
* **Key Packages:**
  * `pytest`: The core testing engine.
  * `playwright` & `pytest-playwright`: Headless/headed browser automation for End-to-End user journeys.
  * `grpcio` & `grpcio-tools` & `protobuf`: Compiles and invokes gRPC requests to interact directly with microservice RPC endpoints.
  * `locust`: Simulates real-world user load to benchmark web servers and microservices.
  * `flask` & `werkzeug`: Serves the integrated local high-fidelity mock web environment.

---

## 2. `microservices-demo/` (The Application Core)

This directory contains the original, multi-language **Google Online Boutique** microservices application code. Online Boutique is a 3-tier, cloud-native shopping application.

```text
microservices-demo/
├── src/                        <-- Source code & Dockerfiles for the 11 microservices
├── kubernetes-manifests/       <-- Individual K8s resource definition files
├── istio-manifests/            <-- Traffic policies and service routing
├── protos/                     <-- Protocol Buffer (.proto) service definitions
├── helm-chart/                 <-- Helm charts for cluster packaging
├── terraform/                  <-- Infrastructure-as-Code for GCP (GKE, Redis)
└── release/                    <-- Combined deployment yaml files
```

### Detailed Breakdown:

* **`src/` (The 11 Core Microservices + Shopping Assistant):**
  * **`frontend/` (Go):** Exposes an HTTP server for user browsing, template rendering, and session handling. Forwards requests to respective backend services via gRPC.
  * **`cartservice/` (C# / .NET):** Manages user shopping carts, persisting items locally or to Redis (Memorystore).
  * **`productcatalogservice/` (Go):** Loads product details from `products.json` and exposes endpoints to list, search, or retrieve items.
  * **`currencyservice/` (Node.js):** Provides exchange rates and converts monetary values between currencies.
  * **`paymentservice/` (Node.js):** Charges credit cards; validates card details and billing addresses.
  * **`shippingservice/` (Go):** Calculates shipping charges and generates tracking labels for orders.
  * **`recommendationservice/` (Python):** Analyzes cart items and product details to suggest related items.
  * **`checkoutservice/` (Go):** Coordinates the cart lookup, shipping quotes, currency conversion, card charges, and cart clearing.
  * **`emailservice/` (Python):** Sends confirmation emails upon successful checkouts.
  * **`adservice/` (Java):** Serves targeted contextual advertising based on product categories.
  * **`shoppingassistantservice/` (Go/Python):** AI-powered shopping assistant component.

* **`kubernetes-manifests/` & `release/`:**
  * **Individual service YAMLs** (e.g., `cartservice.yaml`, `frontend.yaml`): Describe the Kubernetes `Deployment`, `Service`, container image name, environment variables, resource allocations, and startup/health probes for each microservice.
  * **`release/kubernetes-manifests.yaml`**: A pre-processed, concatenated file of all microservices, facilitating simple, single-command deployments (`kubectl apply -f ...`).

* **`protos/` (`demo.proto`):**
  * The authoritative contract file written in Protocol Buffers v3 language. It outlines the message structures (e.g., `CartItem`, `Money`, `Product`) and RPC service interfaces (e.g., `GetCart`, `EmptyCart`, `ListProducts`) connecting all backends.

* **`helm-chart/` & `terraform/`:**
  * Used to deploy the entire stack dynamically to live Kubernetes environments (Minikube or Google Kubernetes Engine) and configure managed Google Cloud services (such as Memorystore Redis).

---

## 3. `testing_project/` (The Advanced Testing Framework)

This is the bespoke, industrial-grade test framework designed to validate every aspect of the Cloud Microservices application. It is constructed in Python using a highly modular design pattern (such as Page Object Model for the front-end).

```text
testing_project/
├── config.py                   <-- Holds URL, port, timeouts, and file path parameters
├── conftest.py                 <-- Setup/Teardown fixtures & dual-mode orchestrator
├── mock_services/              <-- In-process mock implementations of front & backend
├── pages/                      <-- Page Object Models (POM) for UI tests
├── performance/                <-- Locust performance scenario profiles
├── protos/                     <-- Python-compiled gRPC code compiled from demo.proto
└── tests/                      <-- Tests structured into logical groups (E2E, API, Cloud)
```

### Detailed Breakdown:

#### `config.py`
Establishes environment variables, default host URLs (`http://127.0.0.1:8080`), gRPC port settings (`50051`), default viewport specifications, timeouts, and paths to manifests (`kubernetes-manifests.yaml` and `products.json`). This centralized configuration allows tests to transition seamlessly between a mock local server and a live GKE environment.

#### `conftest.py`
Orchestrates Pytest's session lifecycle.
* **Dual-Mode execution logic:** When running the test suite, it checks if a live cluster is reachable at `BOUTIQUE_BASE_URL`.
  * **If yes:** Executes tests directly against the live environment.
  * **If no:** Dynamically starts an **in-process high-fidelity test environment** (Flask mock frontend server + gRPC mock backend server), executes tests, and cleans up (stops servers) afterwards automatically.
* Defines shared Playwright fixtures (`playwright_instance`, `browser`, `context`, `page`, `mobile_page`) configured with anti-sandbox capabilities to run smoothly in headless CI/CD environments.

#### `mock_services/`
Provides a zero-dependency, local testing environment.
* **`mock_frontend_server.py`:** A complete Flask-based implementation mimicking the Online Boutique's layout, templates, and RESTful routing. It transforms user HTTP requests into corresponding gRPC calls and renders clean templates.
* **`mock_grpc_server.py`:** An in-process gRPC server mimicking the 11 backend microservices. It intercepts gRPC calls and serves reliable, structured dummy mock responses to simulate microservices behavior without spinning up Docker containers.

#### `pages/` (Page Object Models for Playwright UI testing)
Encapsulates UI interactions, separating element locators from test logic.
* **`base_page.py`:** Standard utilities for navigation, finding elements, wait times, clicking, and form-input entry.
* **`home_page.py`:** Handles page load checks, header verification, currency switching dropdowns, and retrieving lists of featured products.
* **`product_page.py`:** Models product detailed information, quantity increments, recommendation panels, and clicking the "Add to Cart" CTA.
* **`cart_page.py`:** Handles cart calculations, checking items, clearing cart contents, and filling in checkout shipping details.
* **`order_page.py`:** Represents the checkout confirmation screen, asserting purchase orders, totals, shipping addresses, and confirmation numbers.

#### `performance/` (`locustfile.py`)
* Written in Python using the Locust library.
* Simulates concurrent, realistic user behavioral pathways: viewing the home page, examining random product details, adding items to the cart, modifying session currency, and executing final checkouts.

#### `protos/` (`demo_pb2.py`, `demo_pb2_grpc.py`)
* Autogenerated Python classes compiled directly from `demo.proto`.
* Translates the microservices interface contract into native Python classes and gRPC service stubs, enabling Pytest to execute direct API contract validations.

#### `tests/` (The Automated Testing Suites)
* **`cloud_infra/`**:
  * `test_k8s_manifests.py`: Parses the yaml configuration to verify that all 11 microservices are defined, expose matching services, and employ standardized container naming conventions.
  * `test_security_resilience.py`: Inspects manifests to ensure security contexts adhere to the principle of least-privilege (disallowing root escalation, defining read-only filesystems where possible) and verifies resource limits and requests are defined for memory and CPU.
  * `test_health_probes.py`: Inspects manifests to confirm liveness and readiness probes are assigned to critical endpoints.
* **`microservices/`**:
  * Execute fast, targeted contract validation tests. They directly establish gRPC connections to backend microservices (like Cart, Currency, Catalog, Payment, and Shipping) to verify that requested data matches strict schema expectations, and failure edge cases are properly captured (e.g., charging invalid cards or getting a non-existent product ID).
* **`e2e_playwright/`**:
  * Executes standard, browser-level integration flows across the frontend UI.
  * Verifies product flows, adding to carts, empty-cart operations, entire checkout user journeys, currency synchronization across tabs, and responsive mobile layouts (using mobile viewports).

---

## Technical Flow Summary

To see how everything fits together when you run the framework, here is the lifecycle flow of an E2E test run:

```text
[Pytest Runner starts]
       │
       ▼
[conftest.py detects no live cluster]
       │
       ├───> Starts mock_grpc_server.py (gRPC backend stub)
       └───> Starts mock_frontend_server.py (Flask HTTP server)
       │
       ▼
[Playwright launches chromium browser]
       │
       ▼
[Test case is invoked (e.g., checkout_workflow)]
       │
       ├───> Navigates to frontend (http://127.0.0.1:8080)
       ├───> Uses Page Objects (pages/*_page.py) to click and fill forms
       ├───> Flask frontend routes calls to gRPC mock services
       └───> Asserts checkout completes successfully
       │
       ▼
[Pytest records success and prints results in the terminal]
       │
       ▼
[conftest.py cleans up and shuts down local mock servers]
```
