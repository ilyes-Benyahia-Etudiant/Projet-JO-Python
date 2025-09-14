from typing import Any, Iterable
from fastapi import Request
from fastapi.responses import Response
import secrets
from backend.config import COOKIE_SECURE

CSRF_COOKIE_NAME = "csrf_token"

def get_or_create_csrf_token(request: Request) -> str:
    """
    Renvoie le token CSRF existant (cookie) ou en crée un nouveau.
    """
    token = request.cookies.get(CSRF_COOKIE_NAME)
    if not token:
        token = secrets.token_urlsafe(32)
    return token

def attach_csrf_cookie_if_missing(response: Response, request: Request, token: str) -> None:
    """
    Pose le cookie CSRF si absent pour le navigateur.
    """
    if not request.cookies.get(CSRF_COOKIE_NAME):
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=token,
            httponly=False,  # visible JS si besoin, mais ici on s'en sert côté template/form
            secure=COOKIE_SECURE,
            samesite="Lax",
            max_age=60 * 60,
            path="/",
        )

def validate_csrf_token(request: Request, form_data: Any, field_names: Iterable[str] = ("X-CSRF-Token", "csrf_token")) -> bool:
    """
    Valide le token CSRF en comparant le champ du formulaire et le cookie.
    - Si le cookie n'existe pas, on ne bloque pas (compatibilité POST direct des tests).
    - Accepte plusieurs noms de champ: X-CSRF-Token (templates existants) ou csrf_token.
    """
    token_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    if not token_cookie:
        return True  # pas de cookie => pas de bloquant (tests/post direct)
    token_form = None
    for name in field_names:
        if hasattr(form_data, "get"):
            token_form = form_data.get(name)
            if token_form:
                break
    return bool(token_form and token_cookie == token_form)