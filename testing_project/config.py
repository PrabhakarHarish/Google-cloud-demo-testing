import os
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTING_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_ROOT / "microservices-demo"

# Target Environment Configuration
DEFAULT_FRONTEND_URL = "http://127.0.0.1:8080"
FRONTEND_URL = os.getenv("BOUTIQUE_BASE_URL", DEFAULT_FRONTEND_URL).rstrip("/")

# gRPC Microservice Ports / Addresses (defaulting to local or cluster services)
GRPC_HOST = os.getenv("BOUTIQUE_GRPC_HOST", "127.0.0.1")
GRPC_PORT = int(os.getenv("BOUTIQUE_GRPC_PORT", "50051"))

PRODUCT_CATALOG_ADDR = os.getenv("PRODUCT_CATALOG_SERVICE_ADDR", f"{GRPC_HOST}:{GRPC_PORT}")
CART_SERVICE_ADDR = os.getenv("CART_SERVICE_ADDR", f"{GRPC_HOST}:{GRPC_PORT}")
CURRENCY_SERVICE_ADDR = os.getenv("CURRENCY_SERVICE_ADDR", f"{GRPC_HOST}:{GRPC_PORT}")
RECOMMENDATION_SERVICE_ADDR = os.getenv("RECOMMENDATION_SERVICE_ADDR", f"{GRPC_HOST}:{GRPC_PORT}")
SHIPPING_SERVICE_ADDR = os.getenv("SHIPPING_SERVICE_ADDR", f"{GRPC_HOST}:{GRPC_PORT}")
PAYMENT_SERVICE_ADDR = os.getenv("PAYMENT_SERVICE_ADDR", f"{GRPC_HOST}:{GRPC_PORT}")
CHECKOUT_SERVICE_ADDR = os.getenv("CHECKOUT_SERVICE_ADDR", f"{GRPC_HOST}:{GRPC_PORT}")
AD_SERVICE_ADDR = os.getenv("AD_SERVICE_ADDR", f"{GRPC_HOST}:{GRPC_PORT}")

# Playwright Browser Settings
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
SLOW_MO = int(os.getenv("SLOW_MO", "0" if HEADLESS else "1000")) # ms delay between actions
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "20000")) # ms
DEFAULT_VIEWPORT = {"width": 1280, "height": 800}
MOBILE_VIEWPORT = {"width": 375, "height": 667}

# Kubernetes Manifest Path
K8S_MANIFEST_PATH = REPO_ROOT / "release" / "kubernetes-manifests.yaml"
PRODUCTS_JSON_PATH = REPO_ROOT / "src" / "productcatalogservice" / "products.json"
CURRENCY_JSON_PATH = REPO_ROOT / "src" / "currencyservice" / "data" / "currency_conversion.json"

#
#Configuration settings for the Online Boutique Cloud & Microservices Testing Framework.
#Supports running against:
#1. A live deployed cluster (Google Cloud GKE, Minikube, Kind, Docker) via BOUTIQUE_BASE_URL
#2. A local test simulator / mock service environment (default when no cluster URL is provided)

