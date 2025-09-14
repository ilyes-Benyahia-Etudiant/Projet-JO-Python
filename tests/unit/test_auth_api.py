import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException, Response
from datetime import timedelta

# Cible à mocker
USER_MODEL_PATH = "backend.models.user.User"
SECURITY_PATH = "backend.utils.security"

# Simuler les dépendances avant de les importer
mock_user = MagicMock()
mock_security = MagicMock()

# Appliquer les patchs
@pytest.fixture(autouse=True)
def apply_patches():
    with patch.dict('sys.modules', {
        'backend.models.user': MagicMock(User=mock_user),
        'backend.utils.security': mock_security,
        'backend.utils.db': MagicMock(),
        'backend.config': MagicMock(ADMIN_SECRET_HASH=None),
    }):
        yield

# Importer le module à tester APRES avoir mocké les dépendances
from backend.auth.views import api_login, api_signup, api_logout
from backend.auth.models import AuthResponse


@pytest.fixture
def mock_response():
    return Response()

@pytest.mark.asyncio
async def test_api_login_success(mock_response, monkeypatch):
    """Teste une connexion réussie."""
    form_data = MagicMock()
    form_data.email = "test@example.com"
    form_data.password = "password123"

    user_data = {"id": 1, "email": "test@example.com", "role": "user"}
    mock_signin = MagicMock(return_value=AuthResponse(success=True, user=user_data, session={"access_token": "fake-token"}))
    monkeypatch.setattr("backend.auth.views.svc_login", mock_signin)

    mock_set_cookie = MagicMock()
    monkeypatch.setattr("backend.auth.views.set_session_cookie", mock_set_cookie)

    result = api_login(form_data, mock_response)

    mock_signin.assert_called_once_with("test@example.com", "password123")
    mock_set_cookie.assert_called_once_with(mock_response, "fake-token")
    assert "access_token" in result


@pytest.mark.asyncio
async def test_api_login_failure_invalid_credentials(mock_response, monkeypatch):
    """Teste une connexion échouée (identifiants invalides)."""
    form_data = MagicMock()
    form_data.email = "wrong@example.com"
    form_data.password = "wrongpassword"

    mock_signin = MagicMock(return_value=AuthResponse(success=False, error="Identifiants invalides"))
    monkeypatch.setattr("backend.auth.views.svc_login", mock_signin)

    with pytest.raises(HTTPException) as exc_info:
        api_login(form_data, mock_response)

    assert exc_info.value.status_code == 401
    assert "Identifiants invalides" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_api_signup_success(mock_response, monkeypatch):
    """Teste une inscription réussie."""
    signup_data = MagicMock()
    signup_data.email = "newuser@example.com"
    signup_data.password = "newpassword123"
    signup_data.full_name = "New User"

    user_data = {"id": 2, "email": "newuser@example.com", "role": "user"}

    # Le mock doit être synchrone car api_signup est synchrone
    def mock_sign_up(*args, **kwargs):
        class Result:
            success = True
            user = user_data
            access_token = "fake-token"
            token_type = "bearer"
        return Result()

    monkeypatch.setattr("backend.auth.views.svc_signup", mock_sign_up)

    mock_set_cookie = MagicMock()
    monkeypatch.setattr("backend.auth.views.set_session_cookie", mock_set_cookie)
    monkeypatch.setattr("backend.config.ADMIN_SECRET_HASH", None)

    # api_signup n'est pas async, donc on ne l'attend pas
    response = api_signup(signup_data, mock_response)

    assert response["user"] == user_data
    assert response["access_token"] == "fake-token"
    assert response["token_type"] == "bearer"
    mock_set_cookie.assert_called_once()

@pytest.mark.asyncio
async def test_api_signup_failure_email_exists(mock_response, monkeypatch):
    """Teste une inscription échouée (email déjà utilisé)."""
    signup_data = MagicMock()
    signup_data.email = "existing@example.com"
    signup_data.password = "password123"
    signup_data.full_name = "Existing User"

    # Le mock doit être synchrone
    def mock_sign_up_fail(*args, **kwargs):
        return AuthResponse(success=False, error="Email déjà utilisé")

    monkeypatch.setattr("backend.views.api_v1_auth.sign_up", mock_sign_up_fail)
    monkeypatch.setattr("backend.config.ADMIN_SECRET_HASH", None)

    with pytest.raises(HTTPException) as exc_info:
        # api_signup n'est pas async
        api_signup(signup_data, mock_response)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Email déjà utilisé"


@pytest.mark.asyncio
async def test_api_logout(mock_response, monkeypatch):
    """Teste la déconnexion."""
    mock_clear_cookie = MagicMock()
    monkeypatch.setattr("backend.auth.views.clear_session_cookie", mock_clear_cookie)

    result = api_logout(mock_response)

    mock_clear_cookie.assert_called_once_with(mock_response)
    assert result == {"message": "Déconnexion réussie"}