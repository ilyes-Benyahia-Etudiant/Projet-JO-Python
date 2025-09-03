import pytest
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient

from backend.app import app as fastapi_app
from backend.utils.security import require_user

# Marquage automatique selon le dossier
def pytest_collection_modifyitems(config, items):
    for item in items:
        nodeid = item.nodeid.replace("\\", "/")
        if "/tests/unit/" in nodeid:
            item.add_marker(pytest.mark.unit)
        elif "/tests/integration/" in nodeid:
            item.add_marker(pytest.mark.integration)
        elif "/tests/functional/" in nodeid:
            item.add_marker(pytest.mark.functional)

@pytest.fixture(scope="session")
def app():
    return fastapi_app

@pytest.fixture()
def client(app) -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c

# Simuler un utilisateur authentifié pour les endpoints protégés
@pytest.fixture(autouse=True)
def _override_require_user(app):
    fake_user: Dict[str, Any] = {
        "id": "test-user",
        "email": "test@example.com",
        "role": "user",
        "metadata": {"full_name": "Test User"},
        "token": "fake-token",
    }
    app.dependency_overrides[require_user] = lambda: fake_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(require_user, None)

# Mocks Stripe + évitement d’accès DB dans la couche Models pour les paiements
@pytest.fixture(autouse=True)
def _mock_payments_and_stripe(monkeypatch):
    import backend.models as models

    # Neutralise la nécessité d'une vraie clé Stripe
    monkeypatch.setattr(models, "require_stripe", lambda: None, raising=True)

    # Fake session Stripe
    class _FakeSession:
        def __init__(self, url="https://example.test/checkout"):
            self.url = url

    def _fake_create_session(base_url: str, line_items, metadata):
        return _FakeSession("https://example.test/checkout")

    # Fake parse_event (webhook)
    async def _fake_parse_event(request):
        return {"type": "checkout.session.completed", "data": {"object": {"metadata": {"user_id": "u1", "cart": "[]"}}}}

    # Éviter d’appeler la base pour les offres
    def _fake_get_offers_map(ids):
        return {str(k): {"title": f"offre-{k}", "price": 10} for k in ids}

    # Générer des line_items sans dépendre d’objets réels
    def _fake_to_line_items(offers_by_id, quantities):
        return [{"price_data": {"currency": "eur", "unit_amount": 1000}, "quantity": int(q)} for _, q in (quantities or {}).items()]

    # Ne pas écrire en base lors du webhook
    def _fake_process_cart_purchase(user_id, cart_list, use_service=True):
        return 1

    monkeypatch.setattr(models, "create_session", _fake_create_session, raising=True)
    monkeypatch.setattr(models, "parse_event", _fake_parse_event, raising=True)
    monkeypatch.setattr(models, "get_offers_map", _fake_get_offers_map, raising=True)
    monkeypatch.setattr(models, "to_line_items", _fake_to_line_items, raising=True)
    monkeypatch.setattr(models, "process_cart_purchase", _fake_process_cart_purchase, raising=True)