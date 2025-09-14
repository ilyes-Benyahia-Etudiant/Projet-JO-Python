from typing import Optional, Dict, Any
from backend.users.repository import get_user_by_email, get_user_by_id, upsert_user_profile
from backend.infra.supabase_client import (
    get_supabase,
    get_service_supabase,
)
from backend.models.supabase import (
    sign_in_password as _auth_sign_in_password,
    sign_up_account as _auth_sign_up_account,
    send_reset_password as _auth_send_reset_password,
    update_user_password as _auth_update_user_password,
)

# --- Auth (supabase.auth.*) ---

def auth_sign_in_password(email: str, password: str):
    return _auth_sign_in_password(email, password)

def auth_sign_up_account(email: str, password: str, options_data: Optional[Dict[str, Any]] = None, email_redirect_to: Optional[str] = None):
    return _auth_sign_up_account(
        email=email,
        password=password,
        options_data=options_data,
        email_redirect_to=email_redirect_to,
    )

def auth_send_reset_password(email: str, redirect_to: str):
    return _auth_send_reset_password(email, redirect_to)

def auth_update_user_password(user_token: str, new_password: str):
    return _auth_update_user_password(user_token, new_password)

def get_user_from_access_token(access_token: str) -> Dict[str, Any]:
    """
    Récupère l'utilisateur via supabase.auth.get_user(access_token).
    Retourne un dict homogène {id,email,user_metadata}.
    """
    res = get_supabase().auth.get_user(access_token)
    user = getattr(res, "user", None) or {}
    if not isinstance(user, dict):
        user = {
            "id": getattr(user, "id", None),
            "email": getattr(user, "email", None),
            "user_metadata": getattr(user, "user_metadata", None),
        }
    return user or {}

# --- Table users (profil applicatif) ---

# Les fonctions get_user_by_email, get_user_by_id, upsert_user_profile sont désormais importées depuis backend.users.repository