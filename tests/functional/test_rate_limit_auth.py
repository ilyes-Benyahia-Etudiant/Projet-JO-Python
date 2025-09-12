import os
import time
import pytest
from fastapi.testclient import TestClient
from fastapi import Request, HTTPException
from fastapi.routing import APIRoute

# Désactive l'init fastapi-limiter (évite toute connexion Redis pendant les tests)
os.environ.setdefault("DISABLE_FASTAPI_LIMITER_INIT_FOR_TESTS", "1")

from backend.app import app


def _make_local_rate_limiter(times: int, seconds: int):
    # Limiteur simple en mémoire: 5 requêtes par 60s par IP et chemin
    def _dep(request: Request):
        now = time.time()
        ip = request.client.host if request.client else "test"
        key = f"{ip}:{request.url.path}"
        store = getattr(app.state, "_rl_store", {})
        hits = [t for t in store.get(key, []) if now - t < seconds]
        if len(hits) >= times:
            raise HTTPException(status_code=429, detail="Too Many Requests")
        hits.append(now)
        store[key] = hits
        app.state._rl_store = store
    return _dep


def test_login_rate_limit_with_redis():
    # Override de la dépendance RateLimiter pour l'endpoint /api/v1/auth/login (POST)
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == "/api/v1/auth/login" and "POST" in route.methods:
            for dep in route.dependant.dependencies:
                app.dependency_overrides[dep.call] = _make_local_rate_limiter(times=5, seconds=60)

    try:
        with TestClient(app) as client:
            payload = {"email": "user@example.com", "password": "password123"}

            # 5 tentatives autorisées dans 60s
            for i in range(5):
                resp = client.post("/api/v1/auth/login", json=payload)
                assert resp.status_code != 429, f"Unexpected 429 on attempt {i+1}"

            # 6e tentative -> 429
            resp = client.post("/api/v1/auth/login", json=payload)
            assert resp.status_code == 429, f"Expected 429 on 6th attempt, got {resp.status_code}"
    finally:
        # Toujours nettoyer les overrides de dépendances
        app.dependency_overrides.clear()