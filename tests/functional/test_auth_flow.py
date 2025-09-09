import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

# Les fixtures `app` et `client` sont fournies par `conftest.py`

@pytest.mark.functional
class TestAuthFlow:
    """
    Tests fonctionnels pour le parcours complet d'authentification (API JSON).
    """

    def test_full_auth_flow(self, client: TestClient, monkeypatch):
        """
        Scénario complet :
        1. Échec de connexion avec un utilisateur inexistant.
        2. Inscription d'un nouvel utilisateur.
        3. Échec de réinscription avec le même email.
        4. Connexion réussie avec le nouvel utilisateur.
        5. Vérification du cookie de session.
        6. Déconnexion.
        7. Vérification de la suppression du cookie.
        """
        unique_email = f"test-user-{uuid4()}@example.com"
        password = "ValidPassword123!"

        # Préparer des mocks pour éviter tout appel réel à Supabase
        user_data = {"id": "mock-id", "email": unique_email, "role": "user"}

        def mk_signup_success(email, password, full_name, wants_admin=False):
            class Result:
                success = True
                user = user_data
                session = {"access_token": "fake-token", "refresh_token": "fake-refresh"}
                @property
                def access_token(self):
                    return self.session.get("access_token")
            return Result()

        def mk_signup_exists(email, password, full_name, wants_admin=False):
            class Result:
                success = False
                error = "Utilisateur existe déjà"
                user = None
                session = None
            return Result()

        def mk_signin_fail(email, password):
            class Result:
                success = False
                error = "Invalid login credentials"
                user = None
                session = None
            return Result()

        def mk_signin_success(email, password):
            class Result:
                success = True
                user = user_data
                session = {"access_token": "fake-token", "refresh_token": "fake-refresh"}
                @property
                def access_token(self):
                    return self.session.get("access_token")
            return Result()

        # 1. Échec de connexion (utilisateur n'existe pas encore)
        monkeypatch.setattr("backend.views.api_v1_auth.sign_in", mk_signin_fail)
        response = client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": password}
        )
        assert response.status_code == 401
        assert "Invalid login credentials" in response.json()["detail"]

        # 2. Inscription (succès avec session)
        monkeypatch.setattr("backend.views.api_v1_auth.sign_up", mk_signup_success)
        signup_data = {"email": unique_email, "password": password, "full_name": "Test User"}
        response = client.post("/api/v1/auth/signup", json=signup_data)
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body and body.get("token_type") == "bearer"
        assert body.get("user", {}).get("email") == unique_email
        # Cookie de session posé
        assert "sb_access" in response.cookies
        assert response.cookies.get("sb_access")
        assert "httponly" in response.headers["set-cookie"].lower()

        # 3. Échec de réinscription (email déjà pris)
        monkeypatch.setattr("backend.views.api_v1_auth.sign_up", mk_signup_exists)
        response = client.post("/api/v1/auth/signup", json=signup_data)
        assert response.status_code == 400
        assert "Utilisateur existe déjà" in response.json()["detail"]

        # 4. Connexion réussie
        monkeypatch.setattr("backend.views.api_v1_auth.sign_in", mk_signin_success)
        login_data = {"email": unique_email, "password": password}
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body and body.get("token_type") == "bearer"
        assert body.get("user", {}).get("email") == unique_email
        # 5. Vérification du cookie de session après connexion
        assert "sb_access" in response.cookies
        session_cookie = response.cookies.get("sb_access")
        assert session_cookie is not None
        assert "httponly" in response.headers["set-cookie"].lower()

        # 6. Déconnexion (le TestClient gère les cookies entre requêtes)
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        assert response.json() == {"message": "Déconnexion réussie"}

        # 7. Vérification de la suppression du cookie (Set-Cookie d'expiration)
        set_cookie_header = response.headers.get("set-cookie", "").lower()
        assert "sb_access=" in set_cookie_header
        assert "expires=" in set_cookie_header or "max-age=0" in set_cookie_header