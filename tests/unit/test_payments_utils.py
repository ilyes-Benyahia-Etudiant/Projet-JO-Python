import json
import types
import builtins
import pytest
import sys
from pathlib import Path

# Ajouter la racine du projet au path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.payments import (
    aggregate_quantities,
    to_line_items,
    extract_metadata,
    process_cart_purchase,
)

from fastapi import HTTPException


def test_aggregate_quantities_ok():
    items = [
        {"id": "1", "quantity": 1},
        {"id": "2", "quantity": 2},
        {"id": "1", "quantity": 3},  # agrégé
        {"id": "", "quantity": 5},   # ignoré
        {"id": "3", "quantity": 0},  # ignoré
    ]
    result = aggregate_quantities(items)
    assert result == {"1": 4, "2": 2}


def test_aggregate_quantities_empty_raises():
    with pytest.raises(HTTPException) as exc:
        aggregate_quantities([])
    assert exc.value.status_code == 400


def test_to_line_items_builds_valid_entries():
    offers_by_id = {
        "1": {"id": "1", "title": "Offre A", "price": 12.5},
        "2": {"id": "2", "title": "Offre B", "price": 0},      # ignoré (prix 0)
        "3": {"id": "3", "title": "Offre C", "price": "7.3"},
    }
    quantities = {"1": 2, "2": 5, "3": 1}
    line_items = to_line_items(offers_by_id, quantities)
    # "2" ignoré car prix <= 0
    assert len(line_items) == 2
    # Vérifier unit_amount et titres
    li_a = next(li for li in line_items if li["price_data"]["product_data"]["name"] == "Offre A")
    assert li_a["price_data"]["unit_amount"] == 1250
    assert li_a["quantity"] == 2
    li_c = next(li for li in line_items if li["price_data"]["product_data"]["name"] == "Offre C")
    assert li_c["price_data"]["unit_amount"] == 730
    assert li_c["quantity"] == 1


def test_process_checkout_completed_inserts(monkeypatch):
    # Event simulé Stripe
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

    # Mock des offres: adapter à get_offers_map (retourne un dict {id: offre})
    def fake_get_offers_map(ids):
        return {
            "1": {"id": "1", "title": "Offre A", "price": 10.0},
            "2": {"id": "2", "title": "Offre B", "price": 5.5},
        }

    calls = {"count": 0}

    def fake_insert_commande(user_id, offre_id, token, price_paid):
        # Valider quelques champs
        assert user_id == "user-123"
        assert offre_id in ("1", "2")
        assert isinstance(token, str) and len(token) > 0
        assert price_paid in ("10.00", "5.50")
        calls["count"] += 1
        return True

    # Patch sur les bons symboles utilisés par le service
    import backend.payments as payments_mod
    monkeypatch.setattr("backend.payments.service.get_offers_map", fake_get_offers_map)
    monkeypatch.setattr("backend.payments.repository.insert_commande", fake_insert_commande)

    user_id, cart = payments_mod.extract_metadata(event)
    created = payments_mod.process_cart_purchase(user_id, cart)
    # 2 tickets pour l'offre 1 + 1 ticket pour l'offre 2 = 3 lignes
    assert created == 3
    assert calls["count"] == 3