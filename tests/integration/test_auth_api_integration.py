from backend.models.auth import AuthResponse

def test_api_login_success(client, monkeypatch):
    def _fake_sign_in(email, pwd):
        return AuthResponse(True, user={"id":"u1","email":email,"role":"user","metadata":{}}, session={"access_token":"AT"})
    monkeypatch.setattr("backend.models.sign_in", _fake_sign_in, raising=True)

    res = client.post("/api/v1/auth/login", json={"email":"u@test","password":"x"})
    assert res.status_code == 200
    data = res.json()
    assert data["access_token"] == "AT"
    assert data["user"]["id"] == "u1"

def test_api_login_invalid(client, monkeypatch):
    def _fake_sign_in(email, pwd): return AuthResponse(False, error="bad creds")
    monkeypatch.setattr("backend.models.sign_in", _fake_sign_in, raising=True)
    res = client.post("/api/v1/auth/login", json={"email":"u@test","password":"bad"})
    assert res.status_code == 401

def test_api_me_returns_user_info(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "user"

def test_api_request_password_reset(client, monkeypatch):
    def _fake_send(email, redirect): 
        from backend.models.auth import AuthResponse
        return AuthResponse(True)
    monkeypatch.setattr("backend.models.send_reset_email", _fake_send, raising=True)

    res = client.post("/api/v1/auth/request-password-reset", json={"email":"u@test"})
    assert res.status_code == 200
    assert "envoy" in res.json()["message"].lower()

def test_api_update_password(client, monkeypatch):
    def _fake_update(token, newpwd):
        from backend.models.auth import AuthResponse
        return AuthResponse(True)
    monkeypatch.setattr("backend.models.update_password", _fake_update, raising=True)

    res = client.post("/api/v1/auth/update-password", json={"new_password":"secret123"})
    assert res.status_code == 200
    assert "mis" in res.json()["message"].lower()


def test_api_signup_without_session_returns_message(client, monkeypatch):
    def _fake_sign_up(email, password, full_name, wants_admin=False):
        # Succès mais pas de session avec access_token -> nécessite vérification email
        return AuthResponse(
            True,
            user={"id": "u2", "email": email, "role": "user", "metadata": {"full_name": full_name}},
            session=None
        )

    monkeypatch.setattr("backend.models.sign_up", _fake_sign_up, raising=True)

    res = client.post("/api/v1/auth/signup", json={"email": "new@test", "password": "secret123", "full_name": "New User"})
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    # Tolérance d'accents/min pour la chaîne
    assert "vérifi" in data["message"].lower() or "verifi" in data["message"].lower()

def test_api_login_success(client, monkeypatch):
    def _fake_sign_in(email, pwd):
        return AuthResponse(True, user={"id":"u1","email":email,"role":"user","metadata":{}}, session={"access_token":"AT"})
    monkeypatch.setattr("backend.models.sign_in", _fake_sign_in, raising=True)

    res = client.post("/api/v1/auth/login", json={"email":"u@test","password":"x"})
    assert res.status_code == 200
    data = res.json()
    assert data["access_token"] == "AT"
    assert data["user"]["id"] == "u1"

def test_api_login_invalid(client, monkeypatch):
    def _fake_sign_in(email, pwd): return AuthResponse(False, error="bad creds")
    monkeypatch.setattr("backend.models.sign_in", _fake_sign_in, raising=True)
    res = client.post("/api/v1/auth/login", json={"email":"u@test","password":"bad"})
    assert res.status_code == 401

def test_api_me_returns_user_info(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "user"

def test_api_request_password_reset(client, monkeypatch):
    def _fake_send(email, redirect): 
        from backend.models.auth import AuthResponse
        return AuthResponse(True)
    monkeypatch.setattr("backend.models.send_reset_email", _fake_send, raising=True)

    res = client.post("/api/v1/auth/request-password-reset", json={"email":"u@test"})
    assert res.status_code == 200
    assert "envoy" in res.json()["message"].lower()

def test_api_update_password(client, monkeypatch):
    def _fake_update(token, newpwd):
        from backend.models.auth import AuthResponse
        return AuthResponse(True)
    monkeypatch.setattr("backend.models.update_password", _fake_update, raising=True)

    res = client.post("/api/v1/auth/update-password", json={"new_password":"secret123"})
    assert res.status_code == 200
    assert "mis" in res.json()["message"].lower()