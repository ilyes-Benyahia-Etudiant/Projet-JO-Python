import pytest
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from backend.app import app as fastapi_app
from backend.utils.security import require_user
from backend.utils.security import require_admin

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

@pytest.fixture
def authenticated_user(monkeypatch):
    """Un client API avec un utilisateur admin authentifié."""
    admin_user = {
        "id": "admin-user-id",
        "email": "admin@example.com",
        "role": "admin",
        "user_metadata": {"full_name": "Admin User"},
    }
    
    def mock_require_admin():
        return admin_user

    # [SUPPRIMÉ] monkeypatch legacy backend.models.auth.sign_in
    return admin_user

@pytest.fixture
def authenticated_admin_client(app, client):
    def _override_require_admin():
        return {"id": "admin-user-id", "role": "admin", "email": "admin@example.com"}
    app.dependency_overrides[require_admin] = _override_require_admin
    yield client
    app.dependency_overrides.clear()

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

    # Neutralise la nécessité d’une vraie clé Stripe
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


# Mock database dependency for all tests
@pytest.fixture(scope="function", autouse=True)
def mock_db_dependency(monkeypatch):
    """
    Mocks database access for all tests by patching functions in les nouveaux modules.
    """
    # Patch les accès à Supabase
    monkeypatch.setattr("backend.infra.supabase_client.get_supabase", lambda: MagicMock())
    monkeypatch.setattr("backend.infra.supabase_client.get_service_supabase", lambda: MagicMock())

    # Patch les fonctions de users/repository
    monkeypatch.setattr("backend.users.repository.get_user_by_email", lambda email: None)
    monkeypatch.setattr("backend.users.repository.get_user_by_id", lambda user_id: {"id": user_id, "email": "test@example.com"})
    monkeypatch.setattr("backend.users.repository.upsert_user_profile", lambda user_id, email, role=None: True)
    monkeypatch.setattr("backend.users.repository.get_offers", lambda: [])
    monkeypatch.setattr("backend.users.repository.get_user_orders", lambda user_id: [])

    # Patch les fonctions de admin/service
    monkeypatch.setattr("backend.admin.service.get_offre_by_id", lambda offre_id: {"id": offre_id, "title": "Test Offre", "price": 100})

    # Patch les fonctions de commandes/repository
    monkeypatch.setattr("backend.commandes.repository.fetch_admin_commandes", lambda limit=100: [])
    monkeypatch.setattr("backend.commandes.repository.fetch_user_commandes", lambda user_id, limit=50: [])
    monkeypatch.setattr("backend.commandes.repository.get_commande_by_token", lambda token: None)

    # Patch les fonctions de payments/repository
    monkeypatch.setattr("backend.payments.repository.insert_commande", lambda **kwargs: {"status": "ok"})
    monkeypatch.setattr("backend.payments.repository.insert_commande_with_token", lambda **kwargs: {"status": "ok"})
    monkeypatch.setattr("backend.payments.repository.insert_commande_service", lambda **kwargs: {"status": "ok"})
    monkeypatch.setattr("backend.payments.repository.fetch_offres_by_ids", lambda ids: [])

    # Patch la health info
    monkeypatch.setattr("backend.health.service.health_supabase_info", lambda: {"connect_ok": True})