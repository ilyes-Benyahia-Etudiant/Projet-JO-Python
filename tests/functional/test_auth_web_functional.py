from backend.models.auth import AuthResponse

def test_auth_page_renders(client):
    r = client.get("/auth")
    assert r.status_code == 200
    assert "<h1>Authentification</h1>" in r.text

def test_web_login_redirects_and_sets_cookie(client, monkeypatch):
    def _fake_sign_in(email, pwd):
        return AuthResponse(True, user={"id":"u1","email":email,"role":"user","metadata":{}}, session={"access_token":"AT"})
    monkeypatch.setattr("backend.models.sign_in", _fake_sign_in, raising=True)

    r = client.post("/auth/login", data={"email":"u@test","password":"x"}, allow_redirects=False)
    assert r.status_code in (303, 302)
    set_cookie = r.headers.get("set-cookie","")
    assert "sb_access=" in set_cookie

def test_web_login_admin_redirects_to_admin(client, monkeypatch):
    def _fake_sign_in(email, pwd):
        return AuthResponse(True, user={"id":"admin","email":email,"role":"admin","metadata":{}}, session={"access_token":"AT"})
    monkeypatch.setattr("backend.models.sign_in", _fake_sign_in, raising=True)

    r = client.post("/auth/login", data={"email":"admin@test","password":"x"}, allow_redirects=False)
    assert r.status_code in (303, 302)
    assert r.headers.get("location","").startswith("/admin")

def test_web_login_invalid_shows_error_redirect(client, monkeypatch):
    def _fake_sign_in(email, pwd): return AuthResponse(False, error="invalid")
    monkeypatch.setattr("backend.models.sign_in", _fake_sign_in, raising=True)
    r = client.post("/auth/login", data={"email":"u@test","password":"bad"}, allow_redirects=False)
    assert r.status_code in (303, 302)
    assert "/auth?error=" in r.headers.get("location","")

def test_web_signup_success_redirects(client, monkeypatch):
    def _fake_sign_up(email, pwd, full_name, wants_admin=False):
        return AuthResponse(True, user={"id":"u2","email":email,"role":"user","metadata":{"full_name":full_name}}, session={"access_token":"AT2"})
    monkeypatch.setattr("backend.models.sign_up", _fake_sign_up, raising=True)

    r = client.post("/auth/signup", data={"email":"x@test","password":"secret123","full_name":"X Test"}, allow_redirects=False)
    assert r.status_code in (303, 302)
    assert r.headers.get("location","").startswith("/session")
    assert "sb_access=" in r.headers.get("set-cookie","")

def test_web_reset_page_renders(client):
    r = client.get("/auth/reset")
    assert r.status_code == 200
    assert "reset_password" in r.text.lower() or "mot de passe" in r.text.lower()

def test_web_reset_password_redirects(client, monkeypatch):
    def _fake_update(tok, newpwd): return AuthResponse(True)
    monkeypatch.setattr("backend.models.update_password", _fake_update, raising=True)
    r = client.post("/auth/reset", data={"new_password":"secret123"}, allow_redirects=False)
    assert r.status_code in (303, 302)
    assert "/auth?message=" in r.headers.get("location","")

def test_recover_session_sets_cookie_and_redirects(client):
    r = client.post("/auth/recover/session", json={"access_token":"ATREC"}, allow_redirects=False)
    assert r.status_code in (303, 302)
    assert r.headers.get("location","").startswith("/auth/reset")
    assert "sb_access=" in r.headers.get("set-cookie","")

def test_web_logout_clears_cookie_and_redirects(client):
    r = client.post("/auth/logout", allow_redirects=False)
    assert r.status_code in (303, 302)
    assert 'Clear-Site-Data' in r.headers


def test_web_signup_without_session_shows_message_redirect(client, monkeypatch):
    def _fake_sign_up(email, pwd, full_name, wants_admin=False):
        # Succès mais pas de session -> doit rediriger vers /auth avec message
        return AuthResponse(True, user={"id":"u3","email":email,"role":"user","metadata":{"full_name":full_name}}, session=None)
    monkeypatch.setattr("backend.models.sign_up", _fake_sign_up, raising=True)

    r = client.post("/auth/signup", data={"email":"no-session@test","password":"secret123","full_name":"No Session"}, allow_redirects=False)
    assert r.status_code in (303, 302)
    loc = r.headers.get("location","")
    assert loc.startswith("/auth?") and "message=" in loc
    # Pas de cookie de session attendu
    set_cookie = r.headers.get("set-cookie","")
    assert "sb_access=" not in set_cookie