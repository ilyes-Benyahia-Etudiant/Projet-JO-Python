from typing import Optional, Dict, Any
import logging
from backend.utils.security import determine_role

logger = logging.getLogger(__name__)

class AuthResponse:
    def __init__(
        self,
        success: bool,
        user: Optional[Dict[str, Any]] = None,
        session: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.user = user
        self.session = session
        self.error = error

    @property
    def access_token(self):
        return (self.session or {}).get("access_token")

    @property
    def refresh_token(self):
        return (self.session or {}).get("refresh_token")

def build_user_dict(user) -> Dict[str, Any]:
    user_dict = {
        "id": getattr(user, "id", None),
        "email": getattr(user, "email", None),
        "metadata": getattr(user, "user_metadata", None) or {},
    }
    # Conserve l'appel au wrapper pour éviter toute dépendance circulaire
    user_dict["role"] = determine_role(user_dict["email"], user_dict["metadata"])
    return user_dict

def build_session_dict(session) -> Dict[str, Any]:
    return {
        "access_token": getattr(session, "access_token", None),
        "refresh_token": getattr(session, "refresh_token", None),
    }

def make_auth_response(res, fallback_error: str = "Identifiants invalides") -> AuthResponse:
    sess = getattr(res, "session", None)
    user = getattr(res, "user", None)
    if not sess or not getattr(sess, "access_token", None):
        return AuthResponse(False, error=fallback_error)
    return AuthResponse(True, user=build_user_dict(user), session=build_session_dict(sess))

def handle_exception(action: str, e: Exception) -> AuthResponse:
    logger.exception(f"Erreur {action}")
    return AuthResponse(False, error=f"Erreur {action}: {str(e)}")