# imports (haut de fichier)
from typing import Optional, Dict, Any
import logging
from backend.services.auth.models import AuthResponse
from backend.services.auth.helpers import make_auth_response, handle_exception
from backend.services.auth.supabase_client import (
    sign_in_password,
    sign_up_account,
    send_reset_password,
    update_user_password,
)
from backend.utils.db import get_user_by_email
from backend.config import SIGNUP_REDIRECT_URL

logger = logging.getLogger(__name__)





# fonction sign_in
def sign_in(email: str, password: str) -> AuthResponse:
    try:
        email = (email or "").strip()
        res = sign_in_password(email, password)
        return make_auth_response(res, fallback_error="Identifiants invalides ou email non confirmé")
    except Exception as e:
        return handle_exception("sign_in", e)



# fonction sign_up
def sign_up(email: str, password: str, full_name: Optional[str] = None, wants_admin: bool = False) -> AuthResponse:
    try:
        email = (email or "").strip()

        # Vérification côté serveur: utilisateur déjà existant
        try:
            if get_user_by_email(email):
                return AuthResponse(False, error="Utilisateur existe déjà")
        except Exception:
            # En cas d’erreur de lookup, on laisse Supabase décider
            pass

        options_data: Dict[str, Any] = {}
        if full_name:
            options_data["full_name"] = full_name.strip()
        if wants_admin:
            options_data["role"] = "admin"

        res = sign_up_account(
            email=email,
            password=password,
            options_data=options_data if options_data else None,
            email_redirect_to=SIGNUP_REDIRECT_URL,
        )

        sess = getattr(res, "session", None)
        if sess and getattr(sess, "access_token", None):
            return make_auth_response(res)
        return AuthResponse(True, error="Inscription réussie, vérifiez votre email")
    except Exception as e:
        msg = str(e).lower()
        if any(k in msg for k in ["already", "register", "exists", "database error saving new user", "23505"]):
            return AuthResponse(False, error="Utilisateur existe déjà")
        return handle_exception("sign_up", e)



# fonction send_reset_email
def send_reset_email(email: str, redirect_to: str) -> AuthResponse:
    try:
        email = (email or "").strip()
        send_reset_password(email, redirect_to)
        return AuthResponse(True)
    except Exception as e:
        return handle_exception("send_reset_email", e)




# fonction update_password
def update_password(user_token: str, new_password: str) -> AuthResponse:
    try:
        resp = update_user_password(user_token, new_password)

        if 200 <= resp.status_code < 300:
            return AuthResponse(True)

        # Essayer d’extraire un message d’erreur utile
        msg = None
        try:
            body = resp.json()
            msg = body.get("msg") or body.get("message") or body.get("error_description") or body.get("error")
        except Exception:
            msg = resp.text

        return AuthResponse(False, error=f"Erreur mise à jour: {msg or f'status {resp.status_code}'}")
    except Exception as e:
        logger.exception("Erreur update_password")
        return AuthResponse(False, error=f"Erreur mise à jour: {str(e)}")


