from typing import Optional, Dict, Any
from fastapi import HTTPException
from backend.utils.db import get_supabase
from backend.utils.security import determine_role
import logging

logger = logging.getLogger(__name__)

class AuthResponse:
    def __init__(self, success: bool, user: Optional[Dict] = None, session: Optional[Dict] = None, error: Optional[str] = None):
        self.success = success
        self.user = user
        self.session = session
        self.error = error
        self.access_token = session.get("access_token") if session else None

def sign_in(email: str, password: str) -> AuthResponse:
    try:
        email = (email or "").trim()
        res = get_supabase().auth.sign_in_with_password({"email": email, "password": password})
        sess = getattr(res, "session", None)
        user = getattr(res, "user", None)
        if not sess or not getattr(sess, "access_token", None):
            return AuthResponse(False, error="Identifiants invalides ou email non confirmé")
        user_dict = {
            "id": getattr(user, "id", None),
            "email": getattr(user, "email", None),
            "metadata": getattr(user, "user_metadata", None) or {},
        }
        user_dict["role"] = determine_role(user_dict["email"], user_dict["metadata"])
        session_dict = {
            "access_token": sess.access_token,
            "refresh_token": getattr(sess, "refresh_token", None),
        }
        return AuthResponse(True, user=user_dict, session=session_dict)
    except Exception as e:
        logger.exception("Erreur sign_in")
        return AuthResponse(False, error=f"Erreur de connexion: {str(e)}")

def sign_up(email: str, password: str, full_name: Optional[str] = None, wants_admin: bool = False) -> AuthResponse:
    try:
        email = (email or "").strip()

        # Vérification serveur: email déjà existant
        from backend.utils.db import get_user_by_email
        try:
            existing = get_user_by_email(email)
            if existing:
                return AuthResponse(False, error="Utilisateur existe déjà")
        except Exception:
            # En cas d’erreur de lookup, on laisse l’inscription tenter sa chance
            pass

        payload = {"email": email, "password": password}
        options_data = {}
        if full_name:
            options_data["full_name"] = (full_name or "").strip()
        if wants_admin:
            options_data["role"] = "admin"

        # Ajout: préciser une redirection de confirmation d’email à Supabase
        from backend.config import SIGNUP_REDIRECT_URL
        options: Dict[str, Any] = {}
        if options_data:
            options["data"] = options_data
        options["email_redirect_to"] = SIGNUP_REDIRECT_URL
        payload["options"] = options

        res = get_supabase().auth.sign_up(payload)
        sess = getattr(res, "session", None)
        user = getattr(res, "user", None)
        if sess and getattr(sess, "access_token", None):
            user_dict = {
                "id": getattr(user, "id", None),
                "email": getattr(user, "email", None),
                "metadata": getattr(user, "user_metadata", None) or {},
            }
            user_dict["role"] = determine_role(user_dict["email"], user_dict["metadata"])
            session_dict = {
                "access_token": sess.access_token,
                "refresh_token": getattr(sess, "refresh_token", None),
            }
            return AuthResponse(True, user=user_dict, session=session_dict)
        return AuthResponse(True, error="Inscription réussie, vérifiez votre email")
    except Exception as e:
        # Normaliser certains messages d’erreurs Supabase en “Utilisateur existe déjà”
        msg = str(e)
        low = msg.lower()
        if "already" in low and ("register" in low or "registered" in low or "exists" in low):
            return AuthResponse(False, error="Utilisateur existe déjà")
        if "database error saving new user" in low:
            return AuthResponse(False, error="Utilisateur existe déjà")
        logger.exception("Erreur sign_up")
        return AuthResponse(False, error=f"Erreur d'inscription: {msg}")

def send_reset_email(email: str, redirect_to: str) -> AuthResponse:
    try:
        email = (email or "").strip()
        get_supabase().auth.reset_password_for_email(email, {"redirect_to": redirect_to})
        return AuthResponse(True)
    except Exception as e:
        logger.exception("Erreur send_reset_email")
        return AuthResponse(False, error=f"Erreur envoi email: {str(e)}")

def update_password(user_token: str, new_password: str) -> AuthResponse:
    try:
        import requests
        from backend.config import SUPABASE_URL, SUPABASE_KEY

        url = f"{SUPABASE_URL}/auth/v1/user"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json",
        }
        resp = requests.put(url, json={"password": new_password}, headers=headers, timeout=10)

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