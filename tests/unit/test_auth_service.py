import types
import pytest
from backend.auth.models import AuthResponse
from backend.auth import service as svc

def test_login_success(monkeypatch):
    calls = {}
    def fake_sign_in(email, password):
        calls["email"] = email
        calls["password"] = password
        return {"ok": True}

    def fake_make_auth_response(res, fallback_error=None):
        return AuthResponse(True, user={"id": "u1"}, session={"access_token": "t"})

    monkeypatch.setattr(svc, "sign_in_password", fake_sign_in)
    monkeypatch.setattr(svc, "make_auth_response", fake_make_auth_response)

    res = svc.login(" user@example.com ", "pwd")
    assert res.success is True
    assert calls["email"] == "user@example.com"
    assert calls["password"] == "pwd"

def test_login_exception(monkeypatch):
    def fake_sign_in(email, password):
        raise RuntimeError("boom")

    def fake_handle(op, e):
        return AuthResponse(False, error="handled")

    monkeypatch.setattr(svc, "sign_in_password", fake_sign_in)
    monkeypatch.setattr(svc, "handle_exception", fake_handle)

    res = svc.login("x@y", "z")
    assert res.success is False
    assert res.error == "handled"

def test_signup_user_exists(monkeypatch):
    monkeypatch.setattr(svc, "get_user_by_email", lambda email: {"id": "exists"})
    res = svc.signup("exists@example.com", "pwd", full_name="Name", wants_admin=True)
    assert res.success is False
    assert "existe déjà" in res.error

def test_signup_success_with_session(monkeypatch):
    calls = {}
    monkeypatch.setattr(svc, "get_user_by_email", lambda email: None)

    def fake_sign_up_account(email, password, options_data=None, email_redirect_to=None):
        calls["options_data"] = options_data
        return types.SimpleNamespace(session=types.SimpleNamespace(access_token="abc"))

    def fake_make_auth_response(res, fallback_error=None):
        return AuthResponse(True, user={"id": "new@example.com"}, session={"access_token": "abc"})

    monkeypatch.setattr(svc, "sign_up_account", fake_sign_up_account)
    monkeypatch.setattr(svc, "make_auth_response", fake_make_auth_response)

    res = svc.signup("new@example.com", "pwd", full_name="New User", wants_scanner=True)
    assert res.success is True
    assert res.session["access_token"] == "abc"
    # Vérifie la construction de options_data
    assert calls["options_data"] == {"full_name": "New User", "role": "scanner"}

def test_signup_success_needs_email_verification(monkeypatch):
    monkeypatch.setattr(svc, "get_user_by_email", lambda email: None)
    # Pas de session => message de vérification email
    monkeypatch.setattr(svc, "sign_up_account", lambda **kw: types.SimpleNamespace(session=None))
    res = svc.signup("x@example.com", "pwd")
    assert res.success is True
    assert "vérifiez votre email" in res.error.lower()

def test_signup_exception_already(monkeypatch):
    monkeypatch.setattr(svc, "get_user_by_email", lambda email: None)
    def fake_sign_up(**kw):
        raise Exception("Database error saving new user")
    monkeypatch.setattr(svc, "sign_up_account", fake_sign_up)
    res = svc.signup("x@example.com", "pwd")
    assert res.success is False
    assert "existe déjà" in res.error

def test_request_password_reset_success(monkeypatch):
    called = {"ok": False}
    def fake_send(email, redirect_to):
        called["ok"] = True
    monkeypatch.setattr(svc, "send_reset_password", fake_send)

    res = svc.request_password_reset("x@example.com", "https://cb/")
    assert res.success is True
    assert called["ok"] is True

def test_request_password_reset_exception(monkeypatch):
    def fake_send(email, redirect_to):
        raise RuntimeError("boom")
    monkeypatch.setattr(svc, "send_reset_password", fake_send)
    monkeypatch.setattr(svc, "handle_exception", lambda op, e: AuthResponse(False, error="handled"))
    res = svc.request_password_reset("x@example.com", "https://cb/")
    assert res.success is False
    assert res.error == "handled"

def test_update_password_success_2xx(monkeypatch):
    fake_resp = types.SimpleNamespace(status_code=204, json=lambda: {}, text="")
    monkeypatch.setattr(svc, "_update_user_password", lambda tok, pwd: fake_resp)

    res = svc.update_password("utok", "newpwd")
    assert res.success is True

def test_update_password_non_2xx_json_message(monkeypatch):
    fake_resp = types.SimpleNamespace(
        status_code=400,
        json=lambda: {"message": "bad request"},
        text="ignored",
    )
    monkeypatch.setattr(svc, "_update_user_password", lambda tok, pwd: fake_resp)

    res = svc.update_password("utok", "newpwd")
    assert res.success is False
    assert "bad request" in res.error

def test_update_password_non_2xx_text_fallback(monkeypatch):
    def _json_raises():
        raise ValueError("no json")
    fake_resp = types.SimpleNamespace(
        status_code=500,
        json=_json_raises,
        text="ERR",
    )
    monkeypatch.setattr(svc, "_update_user_password", lambda tok, pwd: fake_resp)

    res = svc.update_password("utok", "newpwd")
    assert res.success is False
    assert "ERR" in res.error

def test_update_password_exception(monkeypatch):
    def _raise(tok, pwd):
        raise RuntimeError("boom")
    monkeypatch.setattr(svc, "_update_user_password", _raise)
    monkeypatch.setattr(svc, "handle_exception", lambda op, e: AuthResponse(False, error="handled"))

    res = svc.update_password("utok", "newpwd")
    assert res.success is False
    assert res.error == "handled"