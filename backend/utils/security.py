from fastapi import Request, HTTPException, Depends
from fastapi.responses import Response
from typing import Optional, Dict, Any
from backend.config import COOKIE_SECURE

COOKIE_NAME = "sb_access"

def determine_role(email: Optional[str], metadata: Dict[str, Any] | None) -> str:
    """
    Délègue la détermination du rôle au service d'authentification.
    Le paramètre email est conservé pour compatibilité mais n'est pas utilisé.
    """
    try:
        from backend.auth.service import determine_role as _determine_role
        return _determine_role(metadata)
    except Exception:
        # Fallback conservateur si le service n'est pas importable au démarrage
        if str((metadata or {}).get("role", "")).lower() == "admin":
            return "admin"
        return "user"

def set_session_cookie(response: Response, access_token: str):
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="Lax",
        max_age=60 * 60,
        path="/",
    )

def clear_session_cookie(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")

def get_current_user(request: Request) -> Dict[str, Any]:
    # Hybride: priorité au Bearer, fallback cookie
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    if not token:
        token = request.cookies.get(COOKIE_NAME)

    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")

    try:
        # Délégué au service Auth
        from backend.auth.service import get_user_from_token as _svc_get_user_from_token
        user = _svc_get_user_from_token(token)
        if not user.get("id"):
            raise HTTPException(status_code=401, detail="Session expirée, veuillez vous connecter")
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Session expirée, veuillez vous connecter")

def require_user(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return user

def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès interdit")
    return user