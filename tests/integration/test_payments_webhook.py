import json

def test_process_cart_purchase_inserts(monkeypatch):
    # Ancien: from backend.models import payments as cart_utils
    import backend.payments as cart_utils

    cart = [
        {"id": "1", "quantity": 2},
        {"id": "2", "quantity": 1},
        {"id": "3", "quantity": 0},  # ignoré
    ]

    # Adapter: get_offers_map retourne un dict {id: offre}
    def fake_get_offers_map(ids):
        return {
            "1": {"id": "1", "title": "Offre A", "price": 10.0},
            "2": {"id": "2", "title": "Offre B", "price": 5.5},
        }

    calls = {"count": 0}
    def fake_insert_commande(user_id, offre_id, token, price_paid):
        assert user_id == "user-123"
        assert offre_id in ("1", "2")
        assert isinstance(token, str) and len(token) > 0
        assert price_paid in ("10.00", "5.50")
        calls["count"] += 1
        return True

    # Patch sur les bons symboles utilisés par le service Payments
    monkeypatch.setattr("backend.payments.service.get_offers_map", fake_get_offers_map)
    monkeypatch.setattr("backend.payments.repository.insert_commande", fake_insert_commande)

    created = cart_utils.process_cart_purchase("user-123", cart)
    assert created == 3
    assert calls["count"] == 3

def test_process_checkout_completed_inserts(monkeypatch):
    import backend.payments as payments_mod

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {
                    "user_id": "user-123",
                    "cart": json.dumps([
                        {"id": "1", "quantity": 2},
                        {"id": "2", "quantity": 1},
                        {"id": "3", "quantity": 0},  # ignoré
                    ])
                }
            }
        }
    }

    def fake_get_offers_map(ids):
        return {
            "1": {"id": "1", "title": "Offre A", "price": 10.0},
            "2": {"id": "2", "title": "Offre B", "price": 5.5},
        }

    calls = {"count": 0}
    def fake_insert_commande(user_id, offre_id, token, price_paid):
        assert user_id == "user-123"
        assert offre_id in ("1", "2")
        assert isinstance(token, str) and len(token) > 0
        assert price_paid in ("10.00", "5.50")
        calls["count"] += 1
        return True

    # Patch sur les symboles réellement utilisés par le service
    monkeypatch.setattr("backend.payments.service.get_offers_map", fake_get_offers_map)
    monkeypatch.setattr("backend.payments.repository.insert_commande", fake_insert_commande)

    user_id, cart = payments_mod.extract_metadata(event)
    created = payments_mod.process_cart_purchase(user_id, cart)
    assert created == 3
    assert calls["count"] == 3