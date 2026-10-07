import os
import shutil
import subprocess
from pathlib import Path
import yaml

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTING_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_ROOT / "microservices-demo"

# Target Environment Configuration
DEFAULT_FRONTEND_URL = "http://127.0.0.1:8080"
BOUTIQUE_BASE_URL = os.getenv("BOUTIQUE_BASE_URL")
FRONTEND_URL = (BOUTIQUE_BASE_URL or DEFAULT_FRONTEND_URL).rstrip("/")


def is_live_mode_requested(config=None) -> bool:
    """
    Returns True if live cluster execution is requested.
    Live mode is activated if:
      - Command line option '--live' is passed, OR
      - BOUTIQUE_BASE_URL environment variable is set and non-empty, OR
      - LIVE_MODE environment variable is set to 'true'/'1'/'yes'.
    Can be explicitly disabled if '--mock' or MOCK_MODE=true is set.
    """
    if config is not None:
        try:
            if config.getoption("--live", default=False):
                return True
            if config.getoption("--mock", default=False):
                return False
        except (ValueError, AttributeError):
            pass

    import sys
    if "--mock" in sys.argv:
        return False
    if "--live" in sys.argv:
        return True

    if os.getenv("MOCK_MODE", "").lower() in ("true", "1", "yes"):
        return False
    if BOUTIQUE_BASE_URL:
        return True
    if os.getenv("LIVE_MODE", "").lower() in ("true", "1", "yes"):
        return True

    return False

# Standard Online Boutique microservice ports in production/cluster deployments:
# catalog: 3550, cart: 7070, currency: 7000, checkout: 5050, ad: 9555, recommendation: 8080, payment/shipping: 50051
SERVICE_DEFAULT_PORTS = {
    "productcatalogservice": 3550,
    "cartservice": 7070,
    "currencyservice": 7000,
    "checkoutservice": 5050,
    "adservice": 9555,
    "recommendationservice": 8080,
    "paymentservice": 50051,
    "shippingservice": 50051,
}

# gRPC Microservice Ports / Addresses (defaulting to local or cluster services)
GRPC_HOST = os.getenv("BOUTIQUE_GRPC_HOST", "127.0.0.1")
GRPC_PORT = int(os.getenv("BOUTIQUE_GRPC_PORT", "50051"))


def get_service_addr(service_name: str, config=None) -> str:
    """
    Resolves the target gRPC address (host:port) for a given microservice.
    Respects explicit environment variables first:
      - PRODUCT_CATALOG_SERVICE_ADDR
      - CART_SERVICE_ADDR
      - CURRENCY_SERVICE_ADDR
      - CHECKOUT_SERVICE_ADDR
      - AD_SERVICE_ADDR
      - RECOMMENDATION_SERVICE_ADDR
      - PAYMENT_SERVICE_ADDR
      - SHIPPING_SERVICE_ADDR
    If not explicitly overridden:
      - In LIVE mode, returns {GRPC_HOST}:{service_port} (catalog 3550, cart 7070, etc.)
      - In MOCK mode, returns {GRPC_HOST}:{GRPC_PORT} (50051) where the mock server runs.
    """
    env_keys = {
        "productcatalogservice": "PRODUCT_CATALOG_SERVICE_ADDR",
        "cartservice": "CART_SERVICE_ADDR",
        "currencyservice": "CURRENCY_SERVICE_ADDR",
        "checkoutservice": "CHECKOUT_SERVICE_ADDR",
        "adservice": "AD_SERVICE_ADDR",
        "recommendationservice": "RECOMMENDATION_SERVICE_ADDR",
        "paymentservice": "PAYMENT_SERVICE_ADDR",
        "shippingservice": "SHIPPING_SERVICE_ADDR",
    }
    normalized = service_name.lower().replace("_", "").replace("-", "")
    if not normalized.endswith("service"):
        normalized += "service"

    env_var = env_keys.get(normalized)
    if env_var and os.getenv(env_var):
        return os.environ[env_var]

    if is_live_mode_requested(config):
        default_port = SERVICE_DEFAULT_PORTS.get(normalized, GRPC_PORT)
        return f"{GRPC_HOST}:{default_port}"
    else:
        return f"{GRPC_HOST}:{GRPC_PORT}"


PRODUCT_CATALOG_ADDR = get_service_addr("productcatalogservice")
CART_SERVICE_ADDR = get_service_addr("cartservice")
CURRENCY_SERVICE_ADDR = get_service_addr("currencyservice")
RECOMMENDATION_SERVICE_ADDR = get_service_addr("recommendationservice")
SHIPPING_SERVICE_ADDR = get_service_addr("shippingservice")
PAYMENT_SERVICE_ADDR = get_service_addr("paymentservice")
CHECKOUT_SERVICE_ADDR = get_service_addr("checkoutservice")
AD_SERVICE_ADDR = get_service_addr("adservice")

# Playwright Browser Settings
HEADLESS = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")
SLOW_MO = int(os.getenv("SLOW_MO", "1000")) # ms delay between actions (1 second default)
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "60000")) # 60 seconds (60000 ms) max timeout
DEFAULT_VIEWPORT = {"width": 1280, "height": 800}
MOBILE_VIEWPORT = {"width": 375, "height": 667}

# Kubernetes Manifest & Rendering Configuration
K8S_BASE_PATH = REPO_ROOT / "kustomize"
K8S_DEFAULT_OVERLAY_PATH = PROJECT_ROOT / "k8s" / "overlays" / "production"
HELM_CHART_PATH = REPO_ROOT / "helm-chart"
CACHE_DIR = TESTING_ROOT / ".cache"
KUBECONFORM_CACHE_DIR = CACHE_DIR / "kubeconform"
STATIC_MANIFEST_PATH = REPO_ROOT / "release" / "kubernetes-manifests.yaml"


_rendered_manifest_cache = {}


def render_kubernetes_manifests(
    engine: str | None = None,
    overlay_path: str | Path | None = None,
    chart_path: str | Path | None = None,
    values_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> Path:
    """
    Renders Kubernetes manifests dynamically from Kustomize or Helm.
    - If K8S_RENDERED_MANIFEST_PATH is set and exists, uses that file directly.
    - If engine is 'helm', renders via `helm template boutique <chart_path>`.
    - If engine is 'kustomize', renders via `kubectl kustomize <target_path>` or `kustomize build`.
    - Saves rendered output to CACHE_DIR / 'rendered-manifests.yaml'.
    """
    env_rendered = os.getenv("K8S_RENDERED_MANIFEST_PATH")
    if env_rendered:
        p = Path(env_rendered)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        if p.exists():
            return p

    selected_engine = (engine or os.getenv("K8S_MANIFEST_ENGINE", "kustomize")).lower()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out_file = Path(output_path) if output_path else (CACHE_DIR / "rendered-manifests.yaml")

    if selected_engine == "helm":
        target_chart = Path(chart_path or os.getenv("HELM_CHART_PATH") or HELM_CHART_PATH)
        if not target_chart.is_absolute():
            target_chart = PROJECT_ROOT / target_chart
        cmd = ["helm", "template", "boutique", str(target_chart)]
        val_file = values_path or os.getenv("HELM_VALUES_PATH")
        if val_file:
            vpath = Path(val_file)
            if not vpath.is_absolute():
                vpath = PROJECT_ROOT / vpath
            cmd.extend(["-f", str(vpath)])
        try:
            rendered_bytes = subprocess.check_output(cmd, stderr=subprocess.PIPE)
            out_file.write_bytes(rendered_bytes)
            return out_file
        except (subprocess.CalledProcessError, FileNotFoundError) as err:
            if STATIC_MANIFEST_PATH.exists():
                return STATIC_MANIFEST_PATH
            raise RuntimeError(f"Failed to render Helm chart: {err}") from err

    # Default engine: kustomize
    raw_overlay = overlay_path or os.getenv("K8S_OVERLAY_PATH") or os.getenv("KUSTOMIZE_PATH")
    if raw_overlay:
        p = Path(raw_overlay)
        target_dir = p if p.is_absolute() else (PROJECT_ROOT / p)
    elif K8S_DEFAULT_OVERLAY_PATH.exists():
        target_dir = K8S_DEFAULT_OVERLAY_PATH
    elif K8S_BASE_PATH.exists():
        target_dir = K8S_BASE_PATH
    else:
        target_dir = None

    if target_dir and target_dir.exists():
        kustomize_bin = shutil.which("kustomize")
        kubectl_bin = shutil.which("kubectl")
        if kubectl_bin:
            cmd = [kubectl_bin, "kustomize", str(target_dir)]
        elif kustomize_bin:
            cmd = [kustomize_bin, "build", str(target_dir)]
        else:
            cmd = None

        if cmd:
            try:
                rendered_bytes = subprocess.check_output(cmd, stderr=subprocess.PIPE)
                out_file.write_bytes(rendered_bytes)
                return out_file
            except subprocess.CalledProcessError as err:
                if STATIC_MANIFEST_PATH.exists():
                    return STATIC_MANIFEST_PATH
                raise RuntimeError(f"Failed to render Kustomize manifests: {err}") from err

    # Fallback to static manifest if tools or overlays are unavailable
    if STATIC_MANIFEST_PATH.exists():
        return STATIC_MANIFEST_PATH

    raise FileNotFoundError("Could not render manifests or locate fallback manifest file.")


def get_rendered_manifest_path(
    engine: str | None = None,
    overlay_path: str | Path | None = None,
    chart_path: str | Path | None = None,
    values_path: str | Path | None = None,
    force_rerender: bool = False,
) -> Path:
    """Returns the path to the dynamically rendered Kubernetes manifest file with cache invalidation."""
    cache_key = (
        (engine or os.getenv("K8S_MANIFEST_ENGINE", "kustomize")).lower(),
        str(overlay_path or os.getenv("K8S_OVERLAY_PATH") or os.getenv("KUSTOMIZE_PATH", "")),
        str(chart_path or os.getenv("HELM_CHART_PATH", "")),
        str(values_path or os.getenv("HELM_VALUES_PATH", "")),
        str(os.getenv("K8S_RENDERED_MANIFEST_PATH", ""))
    )
    if not force_rerender and cache_key in _rendered_manifest_cache:
        cached = _rendered_manifest_cache[cache_key]
        if cached.exists() and cached.stat().st_size > 0:
            return cached

    path = render_kubernetes_manifests(
        engine=engine,
        overlay_path=overlay_path,
        chart_path=chart_path,
        values_path=values_path,
    )
    _rendered_manifest_cache[cache_key] = path
    return path


def get_parsed_manifests(
    engine: str | None = None,
    overlay_path: str | Path | None = None,
    chart_path: str | Path | None = None,
    values_path: str | Path | None = None,
    force_rerender: bool = False,
) -> list[dict]:
    """Parses and returns all YAML documents from the rendered Kubernetes manifests."""
    manifest_file = get_rendered_manifest_path(
        engine=engine,
        overlay_path=overlay_path,
        chart_path=chart_path,
        values_path=values_path,
        force_rerender=force_rerender,
    )
    with open(manifest_file, "r", encoding="utf-8") as f:
        docs = list(yaml.safe_load_all(f))
    return [doc for doc in docs if doc]


# Active Kubernetes Manifest Path: points to dynamically rendered deployment manifests
K8S_MANIFEST_PATH = get_rendered_manifest_path()
PRODUCTS_JSON_PATH = REPO_ROOT / "src" / "productcatalogservice" / "products.json"
CURRENCY_JSON_PATH = REPO_ROOT / "src" / "currencyservice" / "data" / "currency_conversion.json"

#
#Configuration settings for the Online Boutique Cloud & Microservices Testing Framework.
#Supports running against:
#1. A live deployed cluster (Google Cloud GKE, Minikube, Kind, Docker) via BOUTIQUE_BASE_URL
#2. A local test simulator / mock service environment (default when no cluster URL is provided)

