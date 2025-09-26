import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from backend.payments.service import confirm_session_by_id

def test_confirm_session_success(monkeypatch):
    # Arrange
    monkeypatch.setattr("backend.payments.service.stripe_client.require_stripe", lambda: None)
    monkeypatch.setattr("backend.payments.service.stripe_client.get_session", lambda sid: {"id": sid, "payment_status": "paid"})
    # meta.extract_metadata_from_session retourne (user_id, cart_list)
    monkeypatch.setattr("backend.payments.service.meta.extract_metadata_from_session", lambda session: ("u1", [{"id": "A", "quantity": 2}]))
    monkeypatch.setattr("backend.payments.service.process_cart_purchase", lambda *a, **kw: 2)

    # Act
    created = confirm_session_by_id("sess_123", current_user_id="u1", user_token="jwt")
    # Assert
    assert created == 2

def test_confirm_session_not_paid(monkeypatch):
    monkeypatch.setattr("backend.payments.service.stripe_client.require_stripe", lambda: None)
    monkeypatch.setattr("backend.payments.service.stripe_client.get_session", lambda sid: {"id": sid, "payment_status": "unpaid"})
    with pytest.raises(HTTPException) as exc:
        confirm_session_by_id("sess_123", current_user_id="u1", user_token="jwt")
    assert exc.value.status_code == 400
    assert "Paiement non confirmé" in str(exc.value.detail)

def test_confirm_session_user_mismatch(monkeypatch):
    monkeypatch.setattr("backend.payments.service.stripe_client.require_stripe", lambda: None)
    monkeypatch.setattr("backend.payments.service.stripe_client.get_session", lambda sid: {"id": sid, "payment_status": "paid"})
    monkeypatch.setattr("backend.payments.service.meta.extract_metadata_from_session", lambda session: ("other_user", [{"id": "A", "quantity": 1}]))
    with pytest.raises(HTTPException) as exc:
        confirm_session_by_id("sess_123", current_user_id="u1", user_token=None)
    assert exc.value.status_code == 403
    assert "autre utilisateur" in str(exc.value.detail)