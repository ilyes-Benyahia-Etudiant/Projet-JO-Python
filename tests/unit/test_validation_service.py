import types
import pytest
from backend.validation import service as svc

def _make_ticket(user_key="ukey", ticket_id="tid", offre=None, user=None):
    return {
        "id": ticket_id,
        "offres": offre or {"id": "offre-1"},
        "users": user or {"id": "user-1", "bio": user_key},
    }

def test_invalid_when_no_dot_in_token(monkeypatch):
    status, payload = svc.validate_ticket_token("no_composite", admin_id="admin")
    assert status == "invalid"
    assert payload["reason"] == "user_key_required"

def test_invalid_when_bad_composite(monkeypatch):
    # Vide avant ou après le point
    status1, payload1 = svc.validate_ticket_token(".rawtoken", admin_id="admin")
    status2, payload2 = svc.validate_ticket_token("userkey.", admin_id="admin")
    assert status1 == "invalid" and payload1["reason"] == "invalid_composite_token"
    assert status2 == "invalid" and payload2["reason"] == "invalid_composite_token"

def test_not_found_ticket(monkeypatch):
    monkeypatch.setattr(svc, "get_ticket_by_token", lambda rt: None)
    status, payload = svc.validate_ticket_token("ukey.token123", admin_id="admin")
    assert status == "not_found"
    assert payload["reason"] == "ticket_not_found"

def test_user_key_mismatch(monkeypatch):
    # Ticket avec users.bio différent
    monkeypatch.setattr(svc, "get_ticket_by_token", lambda rt: _make_ticket(user_key="OTHER"))
    status, payload = svc.validate_ticket_token("ukey.token123", admin_id="admin")
    assert status == "invalid"
    assert payload["reason"] == "user_key_mismatch"

def test_already_validated(monkeypatch):
    # insert_validation renvoie None => déjà validé
    ticket = _make_ticket(user_key="ukey", ticket_id="tid-1")
    monkeypatch.setattr(svc, "get_ticket_by_token", lambda rt: ticket)
    monkeypatch.setattr(svc, "insert_validation", lambda **kw: None)
    last_val = {"status": "validated", "ts": 123}
    monkeypatch.setattr(svc, "get_last_validation", lambda rt: last_val)

    status, payload = svc.validate_ticket_token("ukey.token123", admin_id="admin", admin_token="adm_tok")
    assert status == "already_validated"
    assert payload["token"] == "token123"
    assert payload["commande_id"] == "tid-1"
    assert payload["validation"] == last_val

def test_validated_with_last(monkeypatch):
    # insert_validation renvoie un objet => validé, last non vide
    ticket = _make_ticket(user_key="ukey", ticket_id="tid-2")
    monkeypatch.setattr(svc, "get_ticket_by_token", lambda rt: ticket)
    monkeypatch.setattr(svc, "insert_validation", lambda **kw: {"id": "val-1"})
    last_val = {"status": "validated", "ts": 456}
    monkeypatch.setattr(svc, "get_last_validation", lambda rt: last_val)

    status, payload = svc.validate_ticket_token("ukey.tokenABC", admin_id="admin")
    assert status == "validated"
    assert payload["token"] == "tokenABC"
    assert payload["commande_id"] == "tid-2"
    assert payload["validation"] == last_val

def test_scanned_without_last(monkeypatch):
    # insert ok mais aucun last => retourne "Scanned"
    ticket = _make_ticket(user_key="ukey", ticket_id="tid-3")
    monkeypatch.setattr(svc, "get_ticket_by_token", lambda rt: ticket)
    monkeypatch.setattr(svc, "insert_validation", lambda **kw: {"id": "val-2"})
    monkeypatch.setattr(svc, "get_last_validation", lambda rt: None)

    status, payload = svc.validate_ticket_token("ukey.tokenDEF", admin_id="admin")
    assert status == "Scanned"
    assert payload["token"] == "tokenDEF"