import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.utils.security import require_admin

@pytest.fixture(autouse=True)
def _override_admin_dep():
    app.dependency_overrides[require_admin] = lambda: {"id":"admin","email":"admin@test","role":"admin"}
    yield
    app.dependency_overrides.pop(require_admin, None)

def test_create_offre_calls_model_and_redirects(monkeypatch):
    called = {}
    def fake_create_offre(data):
        called["data"] = data
        return {"id":"O1", **data}
    monkeypatch.setattr("backend.models.create_offre", fake_create_offre, raising=True)

    client = TestClient(app)
    res = client.post("/admin/offres", data={
        "title":"Offre A","price":"12.5","category":"cat","stock":"100","active":"on","description":"Desc","image":"img.png"
    }, allow_redirects=False)
    assert res.status_code in (302, 303)
    assert "Offre%20cr%C3%A9%C3%A9e" in (res.headers.get("location","") or "")
    assert called["data"]["title"] == "Offre A"
    assert called["data"]["price"] == "12.5" or called["data"]["price"] == 12.5

def test_update_offre_calls_model_and_redirects(monkeypatch):
    called = {}
    def fake_update_offre(oid, data):
        called["id"] = oid
        called["data"] = data
        return {"id": oid, **data}
    monkeypatch.setattr("backend.models.update_offre", fake_update_offre, raising=True)

    client = TestClient(app)
    res = client.post("/admin/offres/ID123/update", data={
        "title":"Offre B","price":"22","category":"vip","stock":"5","active":"","description":"New","image":"img2.png"
    }, allow_redirects=False)
    assert res.status_code in (302, 303)
    assert "Offre%20mise%20%C3%A0%20jour" in (res.headers.get("location","") or "")
    assert called["id"] == "ID123"
    assert called["data"]["category"] == "vip"

def test_delete_offre_calls_model_and_redirects(monkeypatch):
    called = {"id": None}
    def fake_delete_offre(oid):
        called["id"] = oid
        return True
    monkeypatch.setattr("backend.models.delete_offre", fake_delete_offre, raising=True)

    client = TestClient(app)
    res = client.post("/admin/offres/IDDEL/delete", allow_redirects=False)
    assert res.status_code in (302, 303)
    assert "Offre%20supprim%C3%A9e" in (res.headers.get("location","") or "")
    assert called["id"] == "IDDEL"