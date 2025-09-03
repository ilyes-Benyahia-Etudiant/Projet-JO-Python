import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.models.auth import AuthResponse

def test_api_signup_with_admin_code_sets_wants_admin(monkeypatch):
    called = {"wants_admin": None}
    def _fake_sign_up(email, password, full_name, wants_admin=False):
        called["wants_admin"] = wants_admin
        return AuthResponse(True, user={"id":"adm1","email":email,"role":"admin","metadata":{}}, session={"access_token":"AT"})
    # ADMIN_SIGNUP_CODE utilisé dans le module API
    monkeypatch.setattr("backend.views.api_v1_auth.ADMIN_SIGNUP_CODE", "Persoadmin18!", raising=False)
    monkeypatch.setattr("backend.models.sign_up", _fake_sign_up, raising=True)

    client = TestClient(app)
    res = client.post("/api/v1/auth/signup", json={"email":"admin@test","password":"xxx123","full_name":"Admin","admin_code":"Persoadmin18!"})
    assert res.status_code == 200
    assert called["wants_admin"] is True
    data = res.json()
    assert data.get("access_token") == "AT"
    assert data.get("user",{}).get("role") == "admin"

def test_web_signup_with_admin_code_redirects_to_admin(client, monkeypatch):
    def _fake_sign_up(email, password, full_name, wants_admin=False):
        assert wants_admin is True
        return AuthResponse(True, user={"id":"adm2","email":email,"role":"admin","metadata":{}}, session={"access_token":"AT2"})
    monkeypatch.setattr("backend.views.web_auth.ADMIN_SIGNUP_CODE", "Persoadmin18!", raising=False)
    monkeypatch.setattr("backend.models.sign_up", _fake_sign_up, raising=True)

    res = client.post("/auth/signup", data={"email":"admin2@test","password":"xxx123","full_name":"Admin 2","admin_code":"Persoadmin18!"}, allow_redirects=False)
    assert res.status_code in (302, 303)
    assert res.headers.get("location","").startswith("/admin")
    assert "sb_access=" in res.headers.get("set-cookie","")