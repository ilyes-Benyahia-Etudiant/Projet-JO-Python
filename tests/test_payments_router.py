from types import SimpleNamespace
import json
import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.utils.security import require_user
from backend.routers import payments as payments_router


@pytest.fixture(autouse=True)
def override_user_dep():
    # Simule un utilisateur connecté
    app.dependency_overrides[require_user] = lambda: {"id": "user-1"}
    yield
    app.dependency_overrides.pop(require_user, None)


def test_checkout_returns_session_url(monkeypatch):
    client = TestClient(app)

    # Stripe no-op
    monkeypatch.setattr(payments_router.stripe_utils, "require_stripe", lambda: None)

    # Mocks cart
    monkeypatch.setattr(payments_router.cart_utils, "aggregate_quantities", lambda items: {"1": 2})
    monkeypatch.setattr(payments_router.cart_utils, "get_offers_map", lambda ids: {"1": {"id": "1", "title": "Offre A", "price": 10.0}})
    monkeypatch.setattr(
        payments_router.cart_utils,
        "to_line_items",
        lambda offers_by_id, qty: [
            {
                "quantity": 2,
                "price_data": {
                    "currency": "eur",
                    "unit_amount": 1000,
                    "product_data": {"name": "Offre A"},
                },
            }
        ],
    )
    monkeypatch.setattr(
        payments_router.cart_utils,
        "make_metadata",
        lambda user_id, quantities: {"user_id": user_id, "cart": json.dumps([{"id":"1","quantity":2}])}
    )

    # Mock Stripe session
    monkeypatch.setattr(
        payments_router.stripe_utils,
        "create_session",
        lambda base_url, line_items, metadata: SimpleNamespace(url="https://checkout.stripe.test/sess_123")
    )

    resp = client.post("/payments/checkout", json={"items": [{"id": "1", "quantity": 2}]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["url"] == "https://checkout.stripe.test/sess_123"


def test_webhook_invalid_signature_returns_400(monkeypatch):
    client = TestClient(app)

    monkeypatch.setattr(payments_router.stripe_utils, "require_stripe", lambda: None)
    monkeypatch.setattr(payments_router.stripe_utils, "STRIPE_WEBHOOK_SECRET", "whsec_test", raising=False)

    class DummyWebhook:
        @staticmethod
        def construct_event(payload, sig_header, secret):
            raise ValueError("bad signature")

    class DummyStripe:
        Webhook = DummyWebhook

    monkeypatch.setattr(payments_router.stripe_utils, "stripe", DummyStripe, raising=False)

    resp = client.post("/payments/webhook", content="{}", headers={"stripe-signature": "t=123,v1=bad"})
    assert resp.status_code == 400
    assert "Webhook invalid" in resp.text or "bad signature" in resp.text


def test_webhook_success_creates_tickets(monkeypatch):
    client = TestClient(app)

    monkeypatch.setattr(payments_router.stripe_utils, "require_stripe", lambda: None)

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {
                    "user_id": "user-1",
                    "cart": json.dumps([
                        {"id": "1", "quantity": 2},
                        {"id": "2", "quantity": 1},
                    ])
                }
            }
        }
    }
    async def fake_parse_event(req):
        return event
    monkeypatch.setattr(payments_router.stripe_utils, "parse_event", fake_parse_event)

    def fake_process_cart_purchase(user_id, cart):
        # 2 billets (offre 1) + 1 billet (offre 2)
        assert user_id == "user-1"
        assert cart[0]["id"] == "1" and cart[0]["quantity"] == 2
        assert cart[1]["id"] == "2" and cart[1]["quantity"] == 1
        return 3

    monkeypatch.setattr(payments_router.cart_utils, "process_cart_purchase", fake_process_cart_purchase)

    resp = client.post("/payments/webhook", content="{}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["created"] == 3