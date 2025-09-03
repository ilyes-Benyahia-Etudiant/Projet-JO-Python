import logging
from typing import Dict, Any
from backend.utils.security import determine_role
from .models import AuthResponse

logger = logging.getLogger(__name__)

def build_user_dict(user) -> Dict[str, Any]:
    user_dict = {
        "id": getattr(user, "id", None),
        "email": getattr(user, "email", None),
        "metadata": getattr(user, "user_metadata", None) or {},
    }
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