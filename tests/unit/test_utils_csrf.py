import pytest
from fastapi import FastAPI, Depends, Request
from fastapi.testclient import TestClient

from backend.utils.csrf import (
    register_csrf_middleware,
    csrf_protect,
    get_or_create_csrf_token,
    validate_csrf_token,
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
)


def _make_app():
    app = FastAPI()
    register_csrf_middleware(app)

    @app.get("/simple")
    def simple_get():
        return {"ok": True}

    @app.post("/simple")
    def simple_post():
        return {"ok": True}

    @app.post("/protected", dependencies=[Depends(csrf_protect)])
    def protected_post():
        return {"ok": True}

    # Exempt path (doit passer sans CSRF)
    @app.post("/api/v1/payments/webhook")
    def webhook():
        return {"ok": True}

    # Expose le token pour tests de get_or_create_csrf_token
    @app.get("/token")
    def token_route(request: Request):
        t = get_or_create_csrf_token(request)
        return {"token": t}

    # Expose validate_csrf_token via une route
    @app.post("/validate")
    async def validate_route(request: Request):
        data = await request.json()
        ok = validate_csrf_token(request, data)
        return {"ok": ok}

    return app


def test_csrf_cookie_set_on_get():
    app = _make_app()
    client = TestClient(app)
    r = client.get("/simple")
    assert r.status_code == 200
    # Le cookie csrf_token doit être posé
    assert CSRF_COOKIE_NAME in client.cookies


def test_middleware_blocks_post_without_csrf_when_session_cookie_present():
    app = _make_app()
    client = TestClient(app)
    # Simule une session utilisateur
    client.cookies.set("sb_access", "dummy-session")
    r = client.post("/simple")
    assert r.status_code == 403
    assert r.json().get("detail") == "CSRF verification failed"


def test_middleware_allows_post_with_valid_csrf_header():
    app = _make_app()
    client = TestClient(app)
    # GET pour générer/poser le cookie CSRF
    client.get("/simple")
    token = client.cookies.get(CSRF_COOKIE_NAME)
    assert token
    client.cookies.set("sb_access", "dummy-session")
    r = client.post("/simple", headers={CSRF_HEADER_NAME: token})
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_middleware_allows_post_with_form_token_urlencoded_when_header_missing():
    app = _make_app()
    client = TestClient(app)
    client.get("/simple")
    token = client.cookies.get(CSRF_COOKIE_NAME)
    assert token
    client.cookies.set("sb_access", "dummy-session")
    # Pas de header, mais le token dans le corps x-www-form-urlencoded
    r = client.post(
        "/simple",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"X-CSRF-Token={token}",
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_csrf_protect_dependency_blocks_missing_and_invalid_token_and_allows_valid():
    app = _make_app()
    client = TestClient(app)
    client.get("/simple")
    token = client.cookies.get(CSRF_COOKIE_NAME)
    assert token

    # Avec session mais sans header -> 403
    client.cookies.set("sb_access", "dummy-session")
    r = client.post("/protected")
    assert r.status_code == 403

    # Avec header invalide -> 403
    r = client.post("/protected", headers={CSRF_HEADER_NAME: "wrong"})
    assert r.status_code == 403

    # Avec header valide -> 200
    r = client.post("/protected", headers={CSRF_HEADER_NAME: token})
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_csrf_exempt_path_allows_post_without_csrf():
    app = _make_app()
    client = TestClient(app)
    client.cookies.set("sb_access", "dummy-session")
    r = client.post("/api/v1/payments/webhook")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_get_or_create_csrf_token_returns_existing_or_new():
    app = _make_app()
    client = TestClient(app)
    # Pas de cookie initial, renvoie un nouveau token
    r1 = client.get("/token")
    t1 = r1.json().get("token")
    assert isinstance(t1, str) and len(t1) > 0

    # Pose un cookie et vérifie qu'on récupère le même
    client.cookies.set(CSRF_COOKIE_NAME, "fixed-token")
    r2 = client.get("/token")
    t2 = r2.json().get("token")
    assert t2 == "fixed-token"


def test_validate_csrf_token_logic_cookie_missing_always_true_and_matching_and_mismatch():
    app = _make_app()
    client = TestClient(app)

    # Pas de cookie -> True
    r1 = client.post("/validate", json={"X-CSRF-Token": "whatever"})
    assert r1.status_code == 200
    assert r1.json() == {"ok": True}

    # Cookie + token identique -> True
    client.cookies.set(CSRF_COOKIE_NAME, "match-me")
    r2 = client.post("/validate", json={"X-CSRF-Token": "match-me"})
    assert r2.status_code == 200
    assert r2.json() == {"ok": True}

    # Cookie + token différent -> False
    r3 = client.post("/validate", json={"X-CSRF-Token": "nope"})
    assert r3.status_code == 200
    assert r3.json() == {"ok": False}