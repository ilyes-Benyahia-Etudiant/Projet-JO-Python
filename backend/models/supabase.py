# Module: backend/models/supabase.py
# Accès données (wrappers Supabase)
from typing import Dict, Any, Optional
import requests
from backend.models.db import get_supabase
from backend.config import SUPABASE_URL, SUPABASE_ANON

def sign_in_password(email: str, password: str):
    return get_supabase().auth.sign_in_with_password({
        "email": email,
        "password": password
    })

def sign_up_account(
    email: str,
    password: str,
    options_data: Optional[Dict[str, Any]],
    email_redirect_to: Optional[str],
):
    options: Dict[str, Any] = {}
    if email_redirect_to:
        # Clé attendue par Supabase pour la redirection post-confirmation
        options["emailRedirectTo"] = email_redirect_to
    # Micro-changement: n’ajouter "data" que si non vide
    if options_data:
        options["data"] = options_data

    payload: Dict[str, Any] = {"email": email, "password": password}
    if options:
        payload["options"] = options

    return get_supabase().auth.sign_up(payload)

def send_reset_password(email: str, redirect_to: str):
    return get_supabase().auth.reset_password_for_email(email, {"redirect_to": redirect_to})

def update_user_password(user_token: str, new_password: str):
    url = f"{SUPABASE_URL}/auth/v1/user"
    headers = {
        "apikey": SUPABASE_ANON,
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }
    return requests.put(url, json={"password": new_password}, headers=headers, timeout=10)