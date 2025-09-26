from typing import Optional, Dict, Any
from backend.auth.models import AuthResponse, make_auth_response, handle_exception
from backend.users.repository import get_user_by_email
from backend.config import SIGNUP_REDIRECT_URL
from .repository import (
    auth_sign_in_password as sign_in_password,
    auth_sign_up_account as sign_up_account,
    auth_send_reset_password as send_reset_password,
    auth_update_user_password as _update_user_password,
    get_user_from_access_token as _repo_get_user_from_token,
    upsert_user_profile as _repo_upsert_user_profile,
)

def determine_role(metadata: Dict[str, Any] | None) -> str:
    role_lower = str((metadata or {}).get("role", "")).lower()
    if role_lower == "admin":
        return "admin"
    if role_lower == "scanner":  # Ajout du nouveau rôle
        return "scanner"
    return "user"

# --- Cas d’usage Auth exposés ---

def login(email: str, password: str) -> AuthResponse:
    """Connexion:
    - Délègue à supabase.auth.sign_in_with_password via repository
    - Normalise la réponse en AuthResponse
    - Message de fallback: identifiants invalides ou email non confirmé
    """
    try:
        email = (email or "").strip()
        res = sign_in_password(email, password)
        return make_auth_response(res, fallback_error="Identifiants invalides ou email non confirmé")
    except Exception as e:
        return handle_exception("sign_in", e)

def signup(email: str, password: str, full_name: Optional[str] = None, wants_admin: bool = False, wants_scanner: bool = False) -> AuthResponse:
    """Inscription:
    - Vérifie côté serveur si l’email existe déjà (best-effort)
    - Injecte full_name et rôle (admin/scanner) dans user_metadata
    - Redirige de confirmation via SIGNUP_REDIRECT_URL
    - Retourne soit une session (access_token) soit un message de succès invitant à confirmer l’email
    - Capture et transforme les erreurs "utilisateur existe déjà"
    """
    try:
        email = (email or "").strip()

        # Vérification côté serveur: utilisateur déjà existant
        try:
            if get_user_by_email(email):
                return AuthResponse(False, error="Utilisateur existe déjà")
        except Exception:
            pass

        options_data: Dict[str, Any] = {}
        if full_name:
            options_data["full_name"] = full_name.strip()
        if wants_admin:
            options_data["role"] = "admin"
        elif wants_scanner:
            options_data["role"] = "scanner"

        res = sign_up_account(
            email=email,
            password=password,
            options_data=options_data if options_data else None,
            email_redirect_to=SIGNUP_REDIRECT_URL,
        )

        sess = getattr(res, "session", None)
        if sess and getattr(sess, "access_token", None):
            return make_auth_response(res)
        # Succès sans session (vérification email)
        return AuthResponse(True, error="Inscription réussie, vérifiez votre email")
    except Exception as e:
        msg = str(e).lower()
        if any(k in msg for k in ["already", "register", "exists", "database error saving new user", "23505"]):
            return AuthResponse(False, error="Utilisateur existe déjà")
        return handle_exception("sign_up", e)

def request_password_reset(email: str, redirect_to: str) -> AuthResponse:
    """Demande de reset:
    - Envoie l’email de reset via supabase.auth.reset_password_for_email
    - Retourne succès sans corps ou une erreur normalisée
    """
    try:
        email = (email or "").strip()
        send_reset_password(email, redirect_to)
        return AuthResponse(True)
    except Exception as e:
        return handle_exception("send_reset_email", e)

def update_password(user_token: str, new_password: str) -> AuthResponse:
    """Mise à jour du mot de passe:
    - Appelle directement GoTrue (httpx PUT sur /auth/v1/user) avec token utilisateur (Bearer)
    - Considère succès si status HTTP 2xx, sinon tente d’extraire un message d’erreur utile
    """
    try:
        resp = _update_user_password(user_token, new_password)

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
        return handle_exception("update_password", e)

# --- Intégration sécurité / profil ---

def get_user_from_token(access_token: str) -> Dict[str, Any]:
    """Normalise user issu de supabase.auth.get_user(access_token):
    - Retourne {id, email, metadata, role, token}
    - Calcule le rôle via determine_role et synchronise le profil (bio) en best-effort
    """
    raw = _repo_get_user_from_token(access_token)
    email = raw.get("email")
    metadata = raw.get("user_metadata") or {}
    uid = raw.get("id")
    role = determine_role(metadata)

    # Garantir la présence d'une clé utilisateur (bio) si manquante
    try:
        sync_user_profile(uid, email, role)
    except Exception:
        pass

    return {"id": uid, "email": email, "metadata": metadata, "role": role, "token": access_token}

def sync_user_profile(user_id: str, email: str, role: Optional[str] = None) -> bool:
    """Synchronisation profil applicatif (table users):
    - Assure la présence d’une clé bio stable (secrets.token_urlsafe) si absente
    - Met à jour le profil (email, rôle, bio) via upsert_user_profile
    """
    # Génère une clé utilisateur si absente (stockée dans users.bio)
    from backend.users.repository import get_user_by_id as _repo_get_user_by_id
    import secrets
    bio_to_set: Optional[str] = None
    try:
        row = _repo_get_user_by_id(user_id)
        existing_bio = (row or {}).get("bio") or ""
        if not existing_bio:
            # Clé utilisateur stable, non réversible
            bio_to_set = secrets.token_urlsafe(24)
    except Exception:
        pass
    return _repo_upsert_user_profile(user_id, email, role, bio=bio_to_set)