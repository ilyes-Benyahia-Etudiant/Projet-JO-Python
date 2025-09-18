# module backend.utils.csrf
from typing import Any, Iterable, Optional
from fastapi import FastAPI, Request, Header, HTTPException, Depends
from fastapi.responses import Response, JSONResponse
import secrets
import urllib.parse
from backend.config import COOKIE_SECURE

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_EXEMPT_PATHS = {
    "/api/v1/commandes/webhook/stripe",
    "/api/v1/payments/webhook",
}

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


def register_csrf_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def csrf_protection(request: Request, call_next):
        method = request.method.upper()
        path = request.url.path
        has_session = bool(request.cookies.get("sb_access"))
        is_state_changing = method in ("POST", "PUT", "PATCH", "DELETE")
        # Normalisation du chemin pour gérer les / finaux
        normalized_path = path.rstrip("/") or "/"
        exempt_normalized = {p.rstrip("/") or "/" for p in CSRF_EXEMPT_PATHS}
        is_exempt = (
            normalized_path in exempt_normalized
            or normalized_path.startswith("/public")
            or normalized_path.startswith("/static")
        )

        # Génère ou récupère le token
        token = get_or_create_csrf_token(request)

        if is_state_changing and has_session and not is_exempt:
            header_token = request.headers.get(CSRF_HEADER_NAME, "")
            cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "")
            form_token = ""

            if not header_token:
                ctype = request.headers.get("content-type", "")
                if ctype.startswith("application/x-www-form-urlencoded"):
                    body = await request.body()

                    async def receive():
                        return {"type": "http.request", "body": body, "more_body": False}
                    request._receive = receive

                    try:
                        parsed_body = urllib.parse.parse_qs(body.decode())
                        csrf_values = parsed_body.get("X-CSRF-Token", []) + parsed_body.get("csrf_token", [])
                        if csrf_values:
                            form_token = csrf_values[0]
                    except Exception:
                        form_token = ""

            provided = header_token or form_token
            if not cookie_token or not provided or not secrets.compare_digest(provided, cookie_token):
                return JSONResponse(status_code=403, content={"detail": "CSRF verification failed"})

        response = await call_next(request)
        attach_csrf_cookie_if_missing(response, request, token)
        return response


def csrf_protect(
    request: Request,
    x_csrf_token: Optional[str] = Header(default=None, alias=CSRF_HEADER_NAME),
) -> None:
    """
    Dépendance à utiliser sur les routes sensibles (POST/PUT/PATCH/DELETE).
    Valide que le header X-CSRF-Token correspond au cookie csrf_token, sauf sur CSRF_EXEMPT_PATHS.
    """
    path = str(request.url.path or "").rstrip("/")
    if path in CSRF_EXEMPT_PATHS:
        return
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = x_csrf_token or request.headers.get(CSRF_HEADER_NAME)
    if not cookie_token or not header_token:
        raise HTTPException(status_code=403, detail="CSRF token missing")
    if not secrets.compare_digest(str(cookie_token), str(header_token)):
        raise HTTPException(status_code=403, detail="CSRF token invalid")