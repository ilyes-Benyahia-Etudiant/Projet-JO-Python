# Import section
import os
import sys
import time
import types
import pytest
from fastapi import FastAPI, Depends, Request
from fastapi.testclient import TestClient
from backend.utils.rate_limit import optional_rate_limit, rate_limit_health_info


def _make_app(times=2, seconds=60):
    app = FastAPI()

    @app.get("/limited", dependencies=[Depends(optional_rate_limit(times, seconds))])
    def limited():
        return {"ok": True}

    @app.get("/limitedA", dependencies=[Depends(optional_rate_limit(times, seconds))])
    def limited_a():
        return {"ok": True}

    @app.get("/limitedB", dependencies=[Depends(optional_rate_limit(times, seconds))])
    def limited_b():
        return {"ok": True}

    @app.get("/rl_info")
    def rl_info(request: Request):
        return rate_limit_health_info(request)

    return app


def test_rate_limit_fallback_blocks_after_limit(monkeypatch):
    app = _make_app(times=2, seconds=60)
    client = TestClient(app)
    monkeypatch.setenv("LOCAL_RATE_LIMIT_FALLBACK", "1")

    r1 = client.get("/limited")
    r2 = client.get("/limited")
    r3 = client.get("/limited")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 429


def test_rate_limit_is_per_path_and_cookie(monkeypatch):
    app = _make_app(times=2, seconds=60)
    client = TestClient(app)
    monkeypatch.setenv("LOCAL_RATE_LIMIT_FALLBACK", "1")

    # Avec cookie de session, la clé inclut le hash + path
    client.cookies.set("sb_access", "some-session")

    # path A: 2 OK, 3e bloque
    assert client.get("/limitedA").status_code == 200
    assert client.get("/limitedA").status_code == 200
    assert client.get("/limitedA").status_code == 429

    # path B: indépendant de A -> 2 OK, 3e bloque
    assert client.get("/limitedB").status_code == 200
    assert client.get("/limitedB").status_code == 200
    assert client.get("/limitedB").status_code == 429


def test_rate_limit_resets_after_window_sleep(monkeypatch):
    # Petite fenêtre pour éviter monkeypatch time
    app = _make_app(times=2, seconds=1)
    client = TestClient(app)
    monkeypatch.setenv("LOCAL_RATE_LIMIT_FALLBACK", "1")

    assert client.get("/limited").status_code == 200
    assert client.get("/limited").status_code == 200
    assert client.get("/limited").status_code == 429

    # Attendre > 1s pour vider la fenêtre
    time.sleep(1.1)
    assert client.get("/limited").status_code == 200
    assert client.get("/limited").status_code == 200


def test_rate_limit_disabled_flag_bypasses_limit(monkeypatch):
    app = _make_app(times=2, seconds=60)
    # Ne pas activer le fallback pour atteindre la branche disabled_flag
    client = TestClient(app)
    app.state.rate_limit_enabled = False

    # Sans fallback, et RateLimiter non dispo, la dépendance ne renverra pas 429
    assert client.get("/limited").status_code == 200
    assert client.get("/limited").status_code == 200
    assert client.get("/limited").status_code == 200


def test_rate_limit_health_info(monkeypatch):
    app = _make_app()
    client = TestClient(app)

    # Cas sans fastapi_limiter -> ready False, backend None
    app.state.rate_limit_enabled = True
    info = client.get("/rl_info").json()
    assert info["enabled"] is True
    assert info["ready"] is False
    assert info["backend"] is None

    # Injecter un faux module fastapi_limiter avec redis prêt
    dummy = types.ModuleType("fastapi_limiter")
    class FastAPILimiter:
        redis = object()
    dummy.FastAPILimiter = FastAPILimiter
    sys.modules["fastapi_limiter"] = dummy

    # Définir une URL redis pour les détails
    monkeypatch.setenv("RATE_LIMIT_REDIS_URL", "redis://localhost:6379/0")
    info2 = client.get("/rl_info").json()
    assert info2["enabled"] is True
    assert info2["ready"] is True
    assert info2["backend"] == "redis"
    assert info2["redis"]["scheme"] == "redis"
    assert info2["redis"]["host"] == "localhost"
    assert info2["redis"]["port"] == 6379