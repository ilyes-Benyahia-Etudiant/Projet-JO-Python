import pytest
from unittest.mock import MagicMock

from backend.payments.service import process_cart_purchase as process_cart

def _patch_common(monkeypatch, offers_map, price=10.0):
    # get_offers_map utilisé dans service
    monkeypatch.setattr("backend.payments.service.get_offers_map", lambda ids: offers_map)
    # price_from_offer est référencé via le module cart importé par service
    monkeypatch.setattr("backend.payments.service.cart.price_from_offer", lambda offer: price)

def test_process_cart_purchase_default_client(monkeypatch):
    # Arrange
    offers_map = {
        "A": {"id": "A", "price": 10},
        "B": {"id": "B", "price": 20},
    }
    _patch_common(monkeypatch, offers_map, price=15.0)

    inserted = MagicMock(return_value={"ok": True})
    monkeypatch.setattr("backend.payments.service.repository.insert_commande", lambda **kw: inserted())
    monkeypatch.setattr("backend.payments.service.repository.insert_commande_with_token", MagicMock())
    monkeypatch.setattr("backend.payments.service.repository.insert_commande_service", MagicMock())

    cart_list = [{"id": "A", "quantity": 2}, {"id": "B", "quantity": 1}]
    # Act
    created = process_cart(user_id="u1", cart_list=cart_list, user_token=None, use_service=False)
    # Assert
    assert created == 3

def test_process_cart_purchase_with_user_token(monkeypatch):
    # Arrange
    offers_map = {"A": {"id": "A", "price": 10}}
    _patch_common(monkeypatch, offers_map, price=10.0)

    calls = {"cnt": 0}
    def inc_with_token(**kw):
        calls["cnt"] += 1
        return {"ok": True}

    monkeypatch.setattr("backend.payments.service.repository.insert_commande_with_token", inc_with_token)
    monkeypatch.setattr("backend.payments.service.repository.insert_commande", MagicMock())
    monkeypatch.setattr("backend.payments.service.repository.insert_commande_service", MagicMock())

    cart_list = [{"id": "A", "quantity": 3}]
    # Act
    created = process_cart(user_id="u1", cart_list=cart_list, user_token="jwt", use_service=False)
    # Assert
    assert created == 3
    assert calls["cnt"] == 3

def test_process_cart_purchase_use_service(monkeypatch):
    # Arrange
    offers_map = {"A": {"id": "A", "price": 10}}
    _patch_common(monkeypatch, offers_map, price=9.99)

    calls = {"cnt": 0}
    def inc_service(**kw):
        calls["cnt"] += 1
        return {"ok": True}

    monkeypatch.setattr("backend.payments.service.repository.insert_commande_service", inc_service)
    monkeypatch.setattr("backend.payments.service.repository.insert_commande_with_token", MagicMock())
    monkeypatch.setattr("backend.payments.service.repository.insert_commande", MagicMock())

    cart_list = [{"id": "A", "quantity": 2}]
    # Act
    created = process_cart(user_id="u1", cart_list=cart_list, user_token=None, use_service=True)
    # Assert
    assert created == 2
    assert calls["cnt"] == 2

def test_process_cart_purchase_skips_invalid_entries(monkeypatch):
    # Arrange: id manquant, qty <= 0, offre introuvable, prix <= 0
    offers_map = {"A": {"id": "A", "price": 10}}
    # prix à 0 pour forcer le skip de l’offre A
    _patch_common(monkeypatch, offers_map, price=0.0)

    repo_calls = {"default": 0, "with_token": 0, "service": 0}
    monkeypatch.setattr("backend.payments.service.repository.insert_commande", lambda **kw: (repo_calls.__setitem__("default", repo_calls["default"] + 1)))
    monkeypatch.setattr("backend.payments.service.repository.insert_commande_with_token", lambda **kw: (repo_calls.__setitem__("with_token", repo_calls["with_token"] + 1)))
    monkeypatch.setattr("backend.payments.service.repository.insert_commande_service", lambda **kw: (repo_calls.__setitem__("service", repo_calls["service"] + 1)))

    cart_list = [
        {"id": "", "quantity": 1},          # id manquant
        {"id": "A", "quantity": 0},         # qty <= 0
        {"id": "B", "quantity": 1},         # offre introuvable
        {"id": "A", "quantity": 1},         # prix <= 0 -> skip
    ]
    # Act
    created = process_cart(user_id="u1", cart_list=cart_list)
    # Assert
    assert created == 0
    assert repo_calls["default"] == 0 and repo_calls["with_token"] == 0 and repo_calls["service"] == 0