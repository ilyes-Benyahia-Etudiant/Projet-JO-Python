from backend.models.auth import AuthResponse, make_auth_response, handle_exception

class _Sess:
    def __init__(self, access_token=None, refresh_token=None):
        self.access_token = access_token
        self.refresh_token = refresh_token

class _User:
    def __init__(self, id="u1", email="u@test", role="user", user_metadata=None):
        self.id = id
        self.email = email
        self.role = role
        self.user_metadata = user_metadata or {"full_name": "Test U"}

class _Res:
    def __init__(self, user=None, session=None):
        self.user = user
        self.session = session

def test_authresponse_accessors():
    resp = AuthResponse(True, user={"id": "u1"}, session={"access_token": "at", "refresh_token": "rt"})
    assert resp.access_token == "at"
    assert resp.refresh_token == "rt"

def test_make_auth_response_success():
    r = _Res(user=_User(), session=_Sess(access_token="abc", refresh_token="def"))
    resp = make_auth_response(r, fallback_error="nope")
    assert resp.success is True
    assert resp.user["id"] == "u1"
    assert resp.session["access_token"] == "abc"

def test_make_auth_response_failure_fallback():
    r = _Res(user=_User(), session=_Sess(access_token=None))
    resp = make_auth_response(r, fallback_error="fallback")
    assert resp.success is False
    assert "fallback" in (resp.error or "")

def test_handle_exception_wraps_error():
    resp = handle_exception("sign_in", Exception("boom"))
    assert resp.success is False
    assert "sign_in" in (resp.error or "")