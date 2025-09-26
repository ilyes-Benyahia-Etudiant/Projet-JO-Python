from typing import Optional, Dict, Any
from backend.users.repository import get_user_by_email, get_user_by_id, upsert_user_profile
from backend.infra.supabase_client import (
    get_supabase,
    get_service_supabase,
)

# --- Auth (supabase.auth.*) ---

def auth_sign_in_password(email: str, password: str):
    """Wrapper Supabase Auth: connexion par email/mot de passe (GoTrue)."""
    client = get_supabase()
    return client.auth.sign_in_with_password({"email": email, "password": password})

def auth_sign_up_account(
    email: str,
    password: str,
    options_data: Optional[Dict[str, Any]] = None,
    email_redirect_to: Optional[str] = None
):
    """Wrapper Supabase Auth: inscription d’un compte.
    - options.data: metadata (ex. full_name, role)
    - options.redirect_to: URL de confirmation (ex. SIGNUP_REDIRECT_URL)
    """
    client = get_supabase()
    credentials = {"email": email, "password": password}
    
    if options_data or email_redirect_to:
        credentials["options"] = {}
        if options_data:
            credentials["options"]["data"] = options_data
        if email_redirect_to:
            credentials["options"]["redirect_to"] = email_redirect_to  # Correction : 'redirect_to' au lieu de 'email_redirect_to'
    
    return client.auth.sign_up(credentials)

def auth_send_reset_password(email: str, redirect_to: str):
    """Wrapper Supabase Auth: envoi d’un email de reset avec redirection."""
    client = get_supabase()
    return client.auth.reset_password_for_email(email, options={"redirect_to": redirect_to})

def auth_update_user_password(user_token: str, new_password: str):
    """Appel direct GoTrue pour mettre à jour le mot de passe:
    - Utilise httpx PUT /auth/v1/user avec Authorization: Bearer <user_token>
    - Apikey (SUPABASE_ANON) requis; timeout de 10s
    """
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
    """Récupère et normalise l’utilisateur depuis supabase.auth.get_user(access_token)."""
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