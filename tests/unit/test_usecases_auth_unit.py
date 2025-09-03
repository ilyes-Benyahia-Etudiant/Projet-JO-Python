import types
from backend.models import usecases_auth as uc

class _DummySession:
    def __init__(self, access_token="AT", refresh_token="RT"):
        self.access_token = access_token
        self.refresh_token = refresh_token

class _DummyUser:
    def __init__(self, id="u1", email="u@test", role="user", user_metadata=None):
        self.id = id
        self.email = email
        self.role = role
        self.user_metadata = user_metadata or {"full_name": "Test U"}

def _mk_auth_result(ok=True):
    obj = types.SimpleNamespace()
    obj.user = _DummyUser()
    obj.session = _DummySession() if ok else types.SimpleNamespace(access_token=None)
    return obj

def test_sign_in_success(monkeypatch):
    monkeypatch.setattr(uc, "sign_in_password", lambda email, pwd: _mk_auth_result(True), raising=True)
    resp = uc.sign_in("u@test", "pwd")
    assert resp.success is True
    assert resp.access_token == "AT"

def test_sign_in_invalid(monkeypatch):
    monkeypatch.setattr(uc, "sign_in_password", lambda email, pwd: _mk_auth_result(False), raising=True)
    resp = uc.sign_in("u@test", "pwd")
    assert resp.success is False
    assert "invalides" in (resp.error or "").lower() or "email" in (resp.error or "").lower()

def test_sign_up_success(monkeypatch):
    monkeypatch.setattr(uc, "sign_up_account", lambda email, pwd, name, redirect_to=None: _mk_auth_result(True), raising=True)
    resp = uc.sign_up("u@test", "secret123", "Test U")
    assert resp.success is True
    assert resp.access_token == "AT"

def test_send_reset_email_success(monkeypatch):
    called = {"ok": False}
    def _fake_send(email, redirect_to): called["ok"] = True
    monkeypatch.setattr(uc, "send_reset_password", _fake_send, raising=True)
    resp = uc.send_reset_email("u@test", "http://example/reset")
    assert resp.success is True and called["ok"] is True

def test_update_password_status_200(monkeypatch):
    class _Resp: status_code = 200; text = ""
    monkeypatch.setattr(uc, "_update_user_password", lambda tok, pw: _Resp(), raising=True)
    resp = uc.update_password("tok", "newpass")
    assert resp.success is True

def test_update_password_status_400_with_json(monkeypatch):
    class _Resp:
        status_code = 400
        text = "bad"
        def json(self): return {"message": "too short"}
    monkeypatch.setattr(uc, "_update_user_password", lambda tok, pw: _Resp(), raising=True)
    resp = uc.update_password("tok", "x")
    assert resp.success is False
    assert "too short" in (resp.error or "")