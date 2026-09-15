import os
import uuid
from flask import Flask, request, redirect, render_template_string, make_response, send_from_directory
from testing_project.config import REPO_ROOT
from testing_project.mock_services.mock_grpc_server import load_catalog_data, load_currency_data

app = Flask(__name__, static_folder=str(REPO_ROOT / "src" / "frontend" / "static"))
app.secret_key = "online-boutique-test-secret-key"

# In-memory session carts: session_id -> list of {"product_id": pid, "quantity": qty}
CARTS = {}

CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "CAD": "$",
    "JPY": "¥",
    "GBP": "£",
    "TRY": "₺"
}

def get_product_by_id(pid):
    for p in load_catalog_data():
        if p["id"] == pid:
            return p
    return None

def format_price(price_usd, target_currency="USD"):
    rates = load_currency_data()
    units = price_usd.get("units", 0)
    nanos = price_usd.get("nanos", 0)
    usd_val = units + (nanos / 1e9)
    rate = rates.get(target_currency, 1.0)
    converted = usd_val * rate
    sym = CURRENCY_SYMBOLS.get(target_currency, "$")
    if target_currency == "JPY":
        return f"{sym}{int(round(converted))}"
    return f"{sym}{converted:.2f}"

def get_session_id(req):
    sid = req.cookies.get("shop_session-id")
    if not sid:
        sid = str(uuid.uuid4())
    return sid

def get_currency(req):
    return req.cookies.get("shop_currency", "USD")


BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, shrink-to-fit=no">
    <title>Online Boutique</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" type="text/css" href="/static/styles/styles.css">
    <link rel="stylesheet" type="text/css" href="/static/styles/cart.css">
    <link rel="stylesheet" type="text/css" href="/static/styles/order.css">
</head>
<body>
    <header>
        <div class="navbar sub-navbar">
            <div class="container d-flex justify-content-between">
                <a href="/" class="navbar-brand d-flex align-items-center">
                    <img src="/static/icons/Hipster_NavLogo.svg" alt="Online Boutique" class="top-left-logo" style="height:40px;">
                </a>
                <div class="controls d-flex align-items-center">
                    <div class="h-controls mr-3">
                        <form method="POST" class="controls-form" action="/setCurrency" id="currency_form">
                            <select name="currency_code" id="currency_code" onchange="document.getElementById('currency_form').submit();" class="form-control form-control-sm">
                                {% for cur in ['USD', 'EUR', 'CAD', 'JPY', 'GBP', 'TRY'] %}
                                <option value="{{ cur }}" {% if cur == current_currency %}selected{% endif %}>{{ cur }}</option>
                                {% endfor %}
                            </select>
                        </form>
                    </div>
                    <a href="/cart" class="cart-link d-flex align-items-center">
                        <img src="/static/icons/Hipster_CartIcon.svg" alt="Cart" class="logo" style="height:24px;">
                        {% if cart_count > 0 %}
                        <span class="cart-size-circle badge badge-danger ml-1" id="cart-count">{{ cart_count }}</span>
                        {% endif %}
                    </a>
                </div>
            </div>
        </div>
    </header>
    <div class="platform-flag bg-light py-1 text-center border-bottom">
        <small class="text-muted">Online Boutique Cloud Microservices Environment: <strong>GCP/K8s Emulation</strong></small>
    </div>
    <main role="main" class="container mt-4">
        {% block content %}{% endblock %}
    </main>
    <footer class="footer mt-5 py-3 bg-light border-top text-center text-muted">
        <div class="container">
            <small>&copy; 2026 Google Cloud Microservices Demo - Online Boutique Testing Suite</small>
        </div>
    </footer>
</body>
</html>
"""

HOME_TEMPLATE = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
<div class="home">
    <div class="row hot-products-row">
        <div class="col-12 mb-3">
            <h3 class="hot-products-title">Hot Products</h3>
        </div>
        {% for product in products %}
        <div class="col-md-4 mb-4 hot-product-card">
            <div class="card h-100 product-card-inner">
                <a href="/product/{{ product.id }}">
                    <img src="{{ product.picture }}" class="card-img-top hot-product-img" alt="{{ product.name }}" style="max-height: 220px; object-fit: cover;">
                </a>
                <div class="card-body">
                    <h5 class="card-title hot-product-card-name">
                        <a href="/product/{{ product.id }}" class="text-dark">{{ product.name }}</a>
                    </h5>
                    <p class="card-text hot-product-card-price text-muted font-weight-bold">{{ product.formatted_price }}</p>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
""")

PRODUCT_TEMPLATE = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
<div class="h-product">
    <div class="row">
        <div class="col-md-6 text-center">
            <img class="product-image img-fluid rounded" alt="{{ product.name }}" src="{{ product.picture }}" style="max-height: 380px;">
        </div>
        <div class="product-info col-md-6">
            <div class="product-wrapper">
                <h2 id="product-name">{{ product.name }}</h2>
                <p class="product-price h4 text-primary font-weight-bold" id="product-price">{{ product.formatted_price }}</p>
                <p class="product-description mt-3" id="product-description">{{ product.description }}</p>
                
                <form method="POST" action="/cart" id="add-to-cart-form" class="mt-4">
                    <input type="hidden" name="product_id" value="{{ product.id }}">
                    <div class="form-group row align-items-center">
                        <label for="quantity" class="col-sm-3 col-form-label font-weight-bold">Quantity:</label>
                        <div class="col-sm-4">
                            <select name="quantity" id="quantity" class="form-control">
                                <option value="1">1</option>
                                <option value="2">2</option>
                                <option value="3">3</option>
                                <option value="4">4</option>
                                <option value="5">5</option>
                                <option value="10">10</option>
                            </select>
                        </div>
                    </div>
                    <button type="submit" id="add-to-cart-btn" class="cymbal-button-primary btn btn-primary btn-lg mt-2">Add To Cart</button>
                </form>
            </div>
        </div>
    </div>
    <div class="recommendations mt-5 pt-4 border-top">
        <h4>You May Also Like</h4>
        <div class="row">
            {% for rec in recommendations %}
            <div class="col-md-3 col-6 text-center">
                <a href="/product/{{ rec.id }}">
                    <img src="{{ rec.picture }}" class="img-thumbnail mb-2" style="height: 120px;">
                    <div class="small font-weight-bold">{{ rec.name }}</div>
                </a>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
""")

CART_TEMPLATE = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
<div class="cart-sections">
    {% if items|length == 0 %}
    <div class="empty-cart-section text-center py-5">
        <h3 id="empty-cart-header">Your shopping cart is empty!</h3>
        <p class="text-muted">Items you add to your shopping cart will appear here.</p>
        <a class="cymbal-button-primary btn btn-primary mt-3" href="/" id="continue-shopping-link" role="button">Continue Shopping</a>
    </div>
    {% else %}
    <div class="row">
        <!-- Cart Items Summary -->
        <div class="col-lg-6 cart-summary-section">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h3 id="cart-header">Cart ({{ cart_count }})</h3>
                <div>
                    <form method="POST" action="/cart/empty" class="d-inline">
                        <button class="cymbal-button-secondary btn btn-outline-danger btn-sm" id="empty-cart-btn" type="submit">Empty Cart</button>
                    </form>
                    <a class="cymbal-button-primary btn btn-outline-secondary btn-sm ml-2" href="/" role="button">Continue Shopping</a>
                </div>
            </div>
            <ul class="list-group mb-3">
                {% for item in items %}
                <li class="list-group-item d-flex justify-content-between lh-condensed cart-summary-item-row">
                    <div class="d-flex">
                        <img src="{{ item.product.picture }}" alt="{{ item.product.name }}" style="width: 50px; height: 50px; object-fit: cover;" class="mr-3 rounded">
                        <div>
                            <h6 class="my-0 cart-item-name">{{ item.product.name }}</h6>
                            <small class="text-muted">Qty: {{ item.quantity }} | SKU: {{ item.product.id }}</small>
                        </div>
                    </div>
                    <span class="text-muted font-weight-bold cart-item-price">{{ item.formatted_total }}</span>
                </li>
                {% endfor %}
                <li class="list-group-item d-flex justify-content-between bg-light">
                    <div class="text-success">
                        <h6 class="my-0">Shipping</h6>
                        <small>Standard Shipping</small>
                    </div>
                    <span class="text-success" id="shipping-cost">{{ shipping_formatted }}</span>
                </li>
                <li class="list-group-item d-flex justify-content-between">
                    <span>Total ({{ current_currency }})</span>
                    <strong id="cart-total-price">{{ total_formatted }}</strong>
                </li>
            </ul>
        </div>

        <!-- Checkout Form -->
        <div class="col-lg-6">
            <div class="card p-4">
                <h4 class="mb-3">Shipping & Checkout</h4>
                <form class="cart-checkout-form" action="/cart/checkout" method="POST" id="checkout-form">
                    <div class="form-group">
                        <label for="email">Email Address</label>
                        <input type="email" class="form-control" id="email" name="email" value="tester@google-online-boutique.test" required>
                    </div>
                    <div class="form-group">
                        <label for="street_address">Street Address</label>
                        <input type="text" class="form-control" id="street_address" name="street_address" value="1600 Amphitheatre Pkwy" required>
                    </div>
                    <div class="form-row">
                        <div class="form-group col-md-6">
                            <label for="city">City</label>
                            <input type="text" class="form-control" id="city" name="city" value="Mountain View" required>
                        </div>
                        <div class="form-group col-md-3">
                            <label for="state">State</label>
                            <input type="text" class="form-control" id="state" name="state" value="CA" required>
                        </div>
                        <div class="form-group col-md-3">
                            <label for="zip_code">Zip Code</label>
                            <input type="text" class="form-control" id="zip_code" name="zip_code" value="94043" required pattern="\\d{4,5}">
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="country">Country</label>
                        <input type="text" class="form-control" id="country" name="country" value="United States" required>
                    </div>
                    
                    <h5 class="mt-4 mb-2">Payment Details</h5>
                    <div class="form-group">
                        <label for="credit_card_number">Credit Card Number</label>
                        <input type="text" class="form-control" id="credit_card_number" name="credit_card_number" value="4432801561520454" required pattern="\\d{16}">
                    </div>
                    <div class="form-row">
                        <div class="form-group col-md-4">
                            <label for="credit_card_expiration_month">Exp Month</label>
                            <select class="form-control" id="credit_card_expiration_month" name="credit_card_expiration_month">
                                {% for m in range(1, 13) %}<option value="{{ m }}" {% if m == 12 %}selected{% endif %}>{{ "%02d"|format(m) }}</option>{% endfor %}
                            </select>
                        </div>
                        <div class="form-group col-md-4">
                            <label for="credit_card_expiration_year">Exp Year</label>
                            <select class="form-control" id="credit_card_expiration_year" name="credit_card_expiration_year">
                                <option value="2026">2026</option>
                                <option value="2027" selected>2027</option>
                                <option value="2028">2028</option>
                            </select>
                        </div>
                        <div class="form-group col-md-4">
                            <label for="credit_card_cvv">CVV</label>
                            <input type="password" class="form-control" id="credit_card_cvv" name="credit_card_cvv" value="123" required pattern="\\d{3,4}">
                        </div>
                    </div>
                    <button class="cymbal-button-primary btn btn-primary btn-block btn-lg mt-3" type="submit" id="place-order-btn">Place Order</button>
                </form>
            </div>
        </div>
    </div>
    {% endif %}
</div>
""")

ORDER_TEMPLATE = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
<div class="order py-5 text-center">
    <div class="order-complete-section card p-5 mx-auto shadow-sm" style="max-width: 650px;">
        <div class="text-success mb-3">
            <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="currentColor" class="bi bi-check-circle-fill text-success" viewBox="0 0 16 16">
              <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
            </svg>
        </div>
        <h2 id="order-complete-heading" class="text-success font-weight-bold">Your order is complete!</h2>
        <p class="lead text-muted">We've sent you a confirmation email with all details.</p>
        
        <div class="table-responsive mt-4 text-left">
            <table class="table table-bordered">
                <tbody>
                    <tr>
                        <th scope="row">Confirmation #</th>
                        <td id="order-id" class="font-weight-bold">{{ order_id }}</td>
                    </tr>
                    <tr>
                        <th scope="row">Tracking #</th>
                        <td id="tracking-id" class="text-primary">{{ tracking_id }}</td>
                    </tr>
                    <tr>
                        <th scope="row">Total Paid</th>
                        <td id="total-paid" class="font-weight-bold text-success">{{ total_paid }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="mt-4">
            <a href="/" class="cymbal-button-primary btn btn-primary btn-lg" id="order-continue-shopping">Continue Shopping</a>
        </div>
    </div>
</div>
""")


@app.route("/_healthz")
def healthz():
    """Online Boutique frontend liveness and readiness probe endpoint."""
    return "ok", 200


@app.route("/")
def home():
    sid = get_session_id(request)
    currency = get_currency(request)
    raw_products = load_catalog_data()
    products = []
    for p in raw_products:
        p_copy = dict(p)
        p_copy["formatted_price"] = format_price(p["priceUsd"], currency)
        products.append(p_copy)
    
    cart = CARTS.get(sid, [])
    cart_count = sum(item["quantity"] for item in cart)

    resp = make_response(render_template_string(
        HOME_TEMPLATE,
        products=products,
        current_currency=currency,
        cart_count=cart_count
    ))
    resp.set_cookie("shop_session-id", sid)
    resp.set_cookie("shop_currency", currency)
    return resp


@app.route("/product/<product_id>")
def product_detail(product_id):
    sid = get_session_id(request)
    currency = get_currency(request)
    product = get_product_by_id(product_id)
    if not product:
        return "Product Not Found", 404
    
    prod_data = dict(product)
    prod_data["formatted_price"] = format_price(product["priceUsd"], currency)
    
    # Recommendations
    catalog = load_catalog_data()
    recs = [dict(p) for p in catalog if p["id"] != product_id][:4]

    cart = CARTS.get(sid, [])
    cart_count = sum(item["quantity"] for item in cart)

    resp = make_response(render_template_string(
        PRODUCT_TEMPLATE,
        product=prod_data,
        recommendations=recs,
        current_currency=currency,
        cart_count=cart_count
    ))
    resp.set_cookie("shop_session-id", sid)
    return resp


@app.route("/cart", methods=["GET", "POST"])
def cart_handler():
    sid = get_session_id(request)
    currency = get_currency(request)
    if sid not in CARTS:
        CARTS[sid] = []

    if request.method == "POST":
        product_id = request.form.get("product_id")
        quantity = int(request.form.get("quantity", 1))
        # Add to cart
        found = False
        for item in CARTS[sid]:
            if item["product_id"] == product_id:
                item["quantity"] += quantity
                found = True
                break
        if not found:
            CARTS[sid].append({"product_id": product_id, "quantity": quantity})
        return redirect("/cart")

    # GET /cart
    rates = load_currency_data()
    cur_rate = rates.get(currency, 1.0)
    items_view = []
    subtotal_usd = 0.0

    for item in CARTS[sid]:
        prod = get_product_by_id(item["product_id"])
        if prod:
            price_usd = prod["priceUsd"]["units"] + (prod["priceUsd"]["nanos"] / 1e9)
            line_total_usd = price_usd * item["quantity"]
            subtotal_usd += line_total_usd
            items_view.append({
                "product": prod,
                "quantity": item["quantity"],
                "formatted_total": format_price(
                    {"units": int(line_total_usd), "nanos": int((line_total_usd - int(line_total_usd)) * 1e9)},
                    currency
                )
            })

    shipping_usd = 8.99 if items_view else 0.0
    total_usd = subtotal_usd + shipping_usd

    shipping_formatted = format_price(
        {"units": int(shipping_usd), "nanos": int((shipping_usd - int(shipping_usd)) * 1e9)},
        currency
    )
    total_formatted = format_price(
        {"units": int(total_usd), "nanos": int((total_usd - int(total_usd)) * 1e9)},
        currency
    )

    cart_count = sum(item["quantity"] for item in CARTS[sid])

    resp = make_response(render_template_string(
        CART_TEMPLATE,
        items=items_view,
        cart_count=cart_count,
        current_currency=currency,
        shipping_formatted=shipping_formatted,
        total_formatted=total_formatted
    ))
    resp.set_cookie("shop_session-id", sid)
    return resp


@app.route("/cart/empty", methods=["POST"])
def empty_cart():
    sid = get_session_id(request)
    CARTS[sid] = []
    return redirect("/cart")


@app.route("/setCurrency", methods=["POST"])
def set_currency():
    new_currency = request.form.get("currency_code", "USD")
    ref = request.referrer or "/"
    resp = redirect(ref)
    resp.set_cookie("shop_currency", new_currency)
    return resp


@app.route("/cart/checkout", methods=["POST"])
def checkout():
    sid = get_session_id(request)
    currency = get_currency(request)
    cart = CARTS.get(sid, [])
    
    # Calculate order total before emptying cart
    rates = load_currency_data()
    subtotal_usd = 0.0
    for item in cart:
        prod = get_product_by_id(item["product_id"])
        if prod:
            price = prod["priceUsd"]["units"] + (prod["priceUsd"]["nanos"] / 1e9)
            subtotal_usd += price * item["quantity"]
    shipping_usd = 8.99
    total_usd = subtotal_usd + shipping_usd
    total_paid_str = format_price(
        {"units": int(total_usd), "nanos": int((total_usd - int(total_usd)) * 1e9)},
        currency
    )

    # Empty cart on successful order
    CARTS[sid] = []

    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    tracking_id = f"TRK-{uuid.uuid4().hex[:8].upper()}"

    resp = make_response(render_template_string(
        ORDER_TEMPLATE,
        order_id=order_id,
        tracking_id=tracking_id,
        total_paid=total_paid_str,
        current_currency=currency,
        cart_count=0
    ))
    return resp


def create_frontend_app():
    return app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
