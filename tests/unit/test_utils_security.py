import types
import sys
from fastapi import FastAPI, Depends
from fastapi.responses import Response
from fastapi.testclient import TestClient
import pytest

from backend.utils import security as security_mod
from backend.utils.security import (
    determine_role,
    set_session_cookie,
    clear_session_cookie,
    get_current_user,
    require_admin,
    COOKIE_NAME,
)

def _make_app():
    app = FastAPI()

    @app.get("/me")
    def me(user=Depends(get_current_user)):
        return user

    @app.get("/admin")
    def admin(user=Depends(require_admin)):
        return {"ok": True}

    return app

def test_determine_role_fallback(monkeypatch):
    # Simuler l'absence de determine_role dans backend.auth.service pour forcer le fallback
    fake_mod = types.SimpleNamespace()  # pas de determine_role => ImportError
    monkeypatch.setitem(sys.modules, "backend.auth.service", fake_mod)

    assert determine_role(None, {"role": "admin"}) == "admin"
    assert determine_role(None, None) == "user"
    assert determine_role(None, {"role": "USER"}) == "user"

def test_determine_role_delegates(monkeypatch):
    # Simuler la présence de determine_role dans backend.auth.service
    def _delegate(metadata):
        return (metadata or {}).get("role", "user")

    fake_mod = types.SimpleNamespace(determine_role=_delegate)
    monkeypatch.setitem(sys.modules, "backend.auth.service", fake_mod)

    assert determine_role(None, {"role": "scanner"}) == "scanner"
    assert determine_role(None, {}) == "user"

def test_set_and_clear_session_cookie(monkeypatch):
    # Forcer un header Set-Cookie avec Secure pour un test déterministe
    monkeypatch.setattr(security_mod, "COOKIE_SECURE", True, raising=False)
    resp = Response()

    set_session_cookie(resp, "abc123")
    header = resp.headers.get("set-cookie") or ""
    low = header.lower()
    assert "sb_access=abc123" in low
    assert "httponly" in low
    assert "path=/" in low
    assert "samesite=lax" in low
    assert "max-age=" in low
    assert "secure" in low

    # Supprimer le cookie
    resp2 = Response()
    clear_session_cookie(resp2)
    h2 = (resp2.headers.get("set-cookie") or "").lower()
    assert "sb_access=" in h2
    assert "max-age=0" in h2
    assert "path=/" in h2

def test_get_current_user_bearer_success(monkeypatch):
    # Fournir un service d'auth avec get_user_from_token qui renvoie un user valide
    fake_auth = types.SimpleNamespace(
        get_user_from_token=lambda token: {"id": "u1", "email": "a@b", "role": "user"}
    )
    monkeypatch.setitem(sys.modules, "backend.auth.service", fake_auth)

    app = _make_app()
    client = TestClient(app)

    r = client.get("/me", headers={"Authorization": "Bearer tok-123"})
    assert r.status_code == 200
    assert r.json() == {"id": "u1", "email": "a@b", "role": "user"}

def test_get_current_user_cookie_success(monkeypatch):
    fake_auth = types.SimpleNamespace(
        get_user_from_token=lambda token: {"id": "u1", "email": "a@b", "role": "admin"}
    )
    monkeypatch.setitem(sys.modules, "backend.auth.service", fake_auth)

    app = _make_app()
    client = TestClient(app)
    client.cookies.set(COOKIE_NAME, "cookie-token")

    r = client.get("/me")
    assert r.status_code == 200
    assert r.json()["role"] == "admin"

def test_get_current_user_missing_token_401(monkeypatch):
    # Aucun header/cookie => 401 "Non authentifié"
    fake_auth = types.SimpleNamespace(
        get_user_from_token=lambda token: {"id": "u1"}  # ne sera pas appelé
    )
    monkeypatch.setitem(sys.modules, "backend.auth.service", fake_auth)

    app = _make_app()
    client = TestClient(app)

    r = client.get("/me")
    assert r.status_code == 401
    assert "Non authentifié" in r.text

def test_get_current_user_missing_id_401(monkeypatch):
    # Service renvoie un dict sans 'id' => 401 "Session expirée..."
    fake_auth = types.SimpleNamespace(
        get_user_from_token=lambda token: {"email": "x@y"}
    )
    monkeypatch.setitem(sys.modules, "backend.auth.service", fake_auth)

    app = _make_app()
    client = TestClient(app)

    r = client.get("/me", headers={"Authorization": "Bearer tok"})
    assert r.status_code == 401
    assert "Session expirée" in r.text

def test_require_admin_forbidden_and_allowed(monkeypatch):
    # Cas interdit (role=user) puis autorisé (role=admin)
    app = _make_app()
    client = TestClient(app)

    fake_auth_user = types.SimpleNamespace(
        get_user_from_token=lambda token: {"id": "u1", "role": "user"}
    )
    monkeypatch.setitem(sys.modules, "backend.auth.service", fake_auth_user)
    r_forbidden = client.get("/admin", headers={"Authorization": "Bearer tok"})
    assert r_forbidden.status_code == 403

    fake_auth_admin = types.SimpleNamespace(
        get_user_from_token=lambda token: {"id": "u1", "role": "admin"}
    )
    monkeypatch.setitem(sys.modules, "backend.auth.service", fake_auth_admin)
    r_ok = client.get("/admin", headers={"Authorization": "Bearer tok"})
    assert r_ok.status_code == 200
    assert r_ok.json() == {"ok": True}