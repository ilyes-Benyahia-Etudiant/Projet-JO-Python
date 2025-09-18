from typing import Optional, Dict, Any
from backend.users.repository import get_user_by_email, get_user_by_id, upsert_user_profile
from backend.infra.supabase_client import (
    get_supabase,
    get_service_supabase,
)

# --- Auth (supabase.auth.*) ---

def auth_sign_in_password(email: str, password: str):
    client = get_supabase()
    return client.auth.sign_in_with_password({"email": email, "password": password})

def auth_sign_up_account(
    email: str,
    password: str,
    options_data: Optional[Dict[str, Any]] = None,
    email_redirect_to: Optional[str] = None
):
    client = get_supabase()
    options: Dict[str, Any] = {}
    if options_data:
        options["data"] = options_data
    if email_redirect_to:
        options["email_redirect_to"] = email_redirect_to
    if options:
        return client.auth.sign_up({"email": email, "password": password}, options=options)
    return client.auth.sign_up({"email": email, "password": password})

def auth_send_reset_password(email: str, redirect_to: str):
    client = get_supabase()
    return client.auth.reset_password_for_email(email, options={"redirect_to": redirect_to})

def auth_update_user_password(user_token: str, new_password: str):
    # Appel direct GoTrue avec le token utilisateur (Bearer)
    import httpx
    from backend.config import SUPABASE_URL, SUPABASE_ANON
    url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {user_token}",
        "apikey": SUPABASE_ANON,
        "Content-Type": "application/json",
    }
    return httpx.put(url, json={"password": new_password}, headers=headers, timeout=10)

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
# Les fonctions get_user_by_email, get_user_by_id, upsert_user_profile restent importées depuis backend.users.repository