from fastapi import Request, HTTPException, Depends
from fastapi.responses import Response
from typing import Optional, Dict, Any
from backend.config import COOKIE_SECURE, ADMIN_EMAILS
from backend.utils.db import get_supabase

COOKIE_NAME = "sb_access"

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

def determine_role(email: str, metadata: Dict[str, Any] | None) -> str:
    if not email:
        return "user"
    if email in ADMIN_EMAILS:
        return "admin"
    if str((metadata or {}).get("role", "")).lower() == "admin":
        return "admin"
    return "user"

def get_current_user(request: Request) -> Dict[str, Any]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    try:
        res = get_supabase().auth.get_user(token)
        user = getattr(res, "user", None) or {}
        email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)
        metadata = getattr(user, "user_metadata", None) or (user.get("user_metadata") if isinstance(user, dict) else None)
        role = determine_role(email, metadata)
        uid = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
        return {"id": uid, "email": email, "metadata": metadata or {}, "role": role}
    except Exception:
        raise HTTPException(status_code=401, detail="Session invalide")

def require_user(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return user

def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès interdit")
    return user