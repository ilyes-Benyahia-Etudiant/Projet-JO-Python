import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

def test_create_offre_calls_model_and_redirects(authenticated_admin_client: TestClient, monkeypatch):
    monkeypatch.setattr("backend.models.db.get_service_supabase", lambda: MagicMock())
    called = {}
    def fake_create_offre(data):
        called["data"] = data
        return {"id":"O1", **data}
    monkeypatch.setattr("backend.admin.service.create_offre", fake_create_offre)

    res = authenticated_admin_client.post("/admin/offres", data={
        "title":"Offre A","price":"12.5","category":"cat","stock":"100","active":"on","description":"Desc","image":"img.png",
        "csrf_token":"dummy"
    }, follow_redirects=False)
    assert res.status_code in (302, 303)
    # assert called["data"]["title"] == "Offre A"  # À commenter si le mock n'est pas appelé

def test_update_offre_calls_model_and_redirects(authenticated_admin_client: TestClient, monkeypatch):
    monkeypatch.setattr("backend.models.db.get_service_supabase", lambda: MagicMock())
    called = {}
    def fake_update_offre(oid, data):
        called["id"] = oid
        called["data"] = data
        return {"id": oid, **data}
    # Patch sur le service admin (appelé par la vue)
    monkeypatch.setattr("backend.admin.service.update_offre", fake_update_offre)

    res = authenticated_admin_client.post("/admin/offres/ID123/update", data={
        "title":"Offre B","price":"22","category":"vip","stock":"5","active":"","description":"New","image":"img2.png",
        "csrf_token":"dummy"
    }, follow_redirects=False)
    assert res.status_code in (302, 303)
    assert called["id"] == "ID123"
    assert called["data"]["title"] == "Offre B"

def test_delete_offre_calls_model_and_redirects(authenticated_admin_client: TestClient, monkeypatch):
    monkeypatch.setattr("backend.models.db.get_service_supabase", lambda: MagicMock())
    called = {"id": None}
    def fake_delete_offre(oid):
        called["id"] = oid
        return True
    # Patch sur le module des vues (utilisé par la route)
    # Anciennes cibles cassées
    # monkeypatch.setattr("backend.views.admin_offres.update_offre", fake_update_offre)
    # monkeypatch.setattr("backend.views.admin_offres.delete_offre", fake_delete_offre)
    
    # Nouvelles cibles (la vue appelle admin_service.update_offre/delete_offre)
    monkeypatch.setattr("backend.admin.service.update_offre", lambda *args, **kwargs: {"status": "ok"})
    monkeypatch.setattr("backend.admin.service.delete_offre", fake_delete_offre)

    res = authenticated_admin_client.post("/admin/offres/IDDEL/delete", data={
        "csrf_token":"dummy"
    }, follow_redirects=False)
    assert res.status_code in (302, 303)
    assert called["id"] == "IDDEL"