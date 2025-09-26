# Top-level module edits in tests/unit/test_admin_service.py
import types
import pytest

import backend.admin.service as svc

def test_fetch_admin_commandes_delegates(monkeypatch):
    calls = {}
    def fake(limit=100):
        calls["limit"] = limit
        return [{"id": "c1"}]
    monkeypatch.setattr("backend.admin.repository.fetch_admin_commandes", fake)
    res = svc.fetch_admin_commandes(limit=50)
    assert res == [{"id": "c1"}]
    assert calls["limit"] == 50

def test_list_users_delegates(monkeypatch):
    calls = {}
    def fake(limit=100):
        calls["limit"] = limit
        return [{"id": "u1"}]
    monkeypatch.setattr("backend.admin.repository.fetch_admin_users", fake)
    res = svc.list_users(limit=10)
    assert res == [{"id": "u1"}]
    assert calls["limit"] == 10

def test_update_user_with_role_calls_set_auth_and_update(monkeypatch):
    calls = {"set_role": [], "update_user": []}
    def fake_set_auth_user_role(user_id, role):
        calls["set_role"].append((user_id, role))
        return True
    def fake_update_user(user_id, data_db):
        calls["update_user"].append((user_id, data_db))
        return {"id": user_id, **data_db}
    monkeypatch.setattr("backend.admin.repository.set_auth_user_role", fake_set_auth_user_role)
    monkeypatch.setattr("backend.admin.repository.update_user", fake_update_user)

    data = {"role": "scanner", "email": "a@b"}
    res = svc.update_user("u123", data)
    assert res == {"id": "u123", "role": "scanner", "email": "a@b"}
    assert calls["set_role"] == [("u123", "scanner")]
    assert calls["update_user"] == [("u123", {"role": "scanner", "email": "a@b"})]

def test_update_user_with_role_exception_swallowed(monkeypatch):
    def boom(user_id, role):
        raise Exception("boom")
    def fake_update_user(user_id, data_db):
        return {"id": user_id, **data_db}
    monkeypatch.setattr("backend.admin.repository.set_auth_user_role", boom)
    monkeypatch.setattr("backend.admin.repository.update_user", fake_update_user)

    res = svc.update_user("u123", {"role": "admin", "email": "x@y"})
    # L'exception de set_auth_user_role est swallow (loggée), et update_user est quand même appelé
    assert res == {"id": "u123", "role": "admin", "email": "x@y"}

def test_update_user_without_role_skips_set_auth(monkeypatch):
    def should_not_be_called(*args, **kwargs):
        raise AssertionError("set_auth_user_role ne devrait pas être appelé sans rôle")
    def fake_update_user(user_id, data_db):
        return {"id": user_id, **data_db}
    monkeypatch.setattr("backend.admin.repository.set_auth_user_role", should_not_be_called)
    monkeypatch.setattr("backend.admin.repository.update_user", fake_update_user)

    # Cas rôle manquant
    res1 = svc.update_user("u1", {"email": "x@y"})
    assert res1 == {"id": "u1", "email": "x@y"}

    # Cas rôle vide/espaces
    res2 = svc.update_user("u2", {"role": "  ", "email": "z@w"})
    assert res2 == {"id": "u2", "role": "  ", "email": "z@w"}

def test_delete_user_delegates(monkeypatch):
    called = {"args": None}
    def fake(user_id):
        called["args"] = user_id
        return True
    monkeypatch.setattr("backend.admin.repository.delete_user", fake)
    assert svc.delete_user("u42") is True
    assert called["args"] == "u42"

def test_update_commande_delegates(monkeypatch):
    called = {"args": None}
    def fake(commande_id, data):
        called["args"] = (commande_id, data)
        return {"id": commande_id, **data}
    monkeypatch.setattr("backend.admin.repository.update_commande", fake)
    res = svc.update_commande("c3", {"price_paid": 99.9})
    assert res == {"id": "c3", "price_paid": 99.9}
    assert called["args"] == ("c3", {"price_paid": 99.9})

def test_delete_commande_delegates(monkeypatch):
    called = {"args": None}
    def fake(commande_id):
        called["args"] = commande_id
        return True
    monkeypatch.setattr("backend.admin.repository.delete_commande", fake)
    assert svc.delete_commande("c4") is True
    assert called["args"] == "c4"

def test_get_commande_by_id_delegates(monkeypatch):
    called = {"args": None}
    def fake(commande_id):
        called["args"] = commande_id
        return {"id": commande_id, "token": "tok"}
    monkeypatch.setattr("backend.admin.repository.get_commande_by_id", fake)
    res = svc.get_commande_by_id("c5")
    assert res == {"id": "c5", "token": "tok"}
    assert called["args"] == "c5"

def test_get_admin_commandes_alias(monkeypatch):
    # get_admin_commandes appelle fetch_admin_commandes dans le même module
    called = {"limit": None}
    def fake(limit=100):
        called["limit"] = limit
        return [{"id": "c1"}]
    monkeypatch.setattr(svc, "fetch_admin_commandes", fake)
    res = svc.get_admin_commandes()
    assert res == [{"id": "c1"}]
    assert called["limit"] == 100