import os
import secrets
import urllib.parse
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
try:
    from starlette.middleware.proxy_headers import ProxyHeadersMiddleware
except Exception:
    ProxyHeadersMiddleware = None
from backend.config import SUPABASE_URL, COOKIE_SECURE, CORS_ORIGINS, ALLOWED_HOSTS

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_EXEMPT_PATHS = {
    "/api/v1/commandes/webhook/stripe",
    "/api/v1/payments/webhook",
}

"""
Middlewares transverses de l’application.
- register_basic_middlewares: session, CORS, TrustedHost et confiance en X-Forwarded-*.
- register_security_middleware: en-têtes de sécurité, CSP, et protection CSRF (cookies + header/form).
- register_no_cache_middleware: empêche la mise en cache sur /session et /admin.
- register_force_https_middleware: force la redirection HTTPS (utile derrière proxy).
Notes:
- L’ordre d’ajout est important: le middleware HTTPS est ajouté en dernier pour s’exécuter en premier.
- Les chemins d’exception CSRF incluent les webhooks Stripe.
"""
def register_basic_middlewares(app: FastAPI) -> None:
    """
    Ajoute les middlewares « de base »:
    - SessionMiddleware: session basée sur cookie pour la navigation web.
    - CORSMiddleware: autorise les origines définies (dev/prod).
    - TrustedHostMiddleware: limite les hôtes acceptés (défense host header).
    - ProxyHeadersMiddleware (si dispo): fait confiance aux en-têtes du proxy (x-forwarded-*).
    """
    app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "replace_me_with_a_long_random_secret"))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=ALLOWED_HOSTS + ["*"] if "*" in CORS_ORIGINS else ALLOWED_HOSTS,
    )
    # Fait confiance aux en-têtes X-Forwarded-* (Render, Nginx, etc.)
    if ProxyHeadersMiddleware:
        app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

def register_security_middleware(app: FastAPI) -> None:
    """
    Middleware de sécurité:
    - CSRF: vérifie X-CSRF-Token (ou champ form) contre le cookie csrf_token sur requêtes mutatives.
      Exemptions: webhooks Stripe et assets statiques.
    - En-têtes: X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, HSTS (si secure).
    - CSP: restreint les origines script/style/connect, ajoute les CDNs nécessaires à la doc Swagger.
    - Dépose un cookie CSRF si manquant (httponly=False pour que le front lise la valeur).
    """
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        method = request.method.upper()
        path = request.url.path
        has_session = bool(request.cookies.get("sb_access"))
        is_state_changing = method in ("POST", "PUT", "PATCH", "DELETE")
        is_exempt = (
            path in CSRF_EXEMPT_PATHS
            or path.startswith("/public/")
            or path.startswith("/static/")
        )
        set_csrf_cookie_value: str | None = None

        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        if not csrf_cookie:
            set_csrf_cookie_value = secrets.token_urlsafe(32)

        if is_state_changing and has_session and not is_exempt:
            header_token = request.headers.get(CSRF_HEADER_NAME, "")
            cookie_token = csrf_cookie or ""
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

            token = header_token or form_token
            if not cookie_token or not token or not secrets.compare_digest(token, cookie_token):
                return JSONResponse(status_code=403, content={"detail": "CSRF verification failed"})

        response = await call_next(request)
        # En-têtes de sécurité
        if "X-Frame-Options" not in response.headers:
            response.headers["X-Frame-Options"] = "DENY"
        if "X-Content-Type-Options" not in response.headers:
            response.headers["X-Content-Type-Options"] = "nosniff"
        if "Referrer-Policy" not in response.headers:
            response.headers["Referrer-Policy"] = "no-referrer"
        if "Permissions-Policy" not in response.headers:
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if COOKIE_SECURE and "Strict-Transport-Security" not in response.headers:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

        csp_connect = ["'self'"]
        if SUPABASE_URL:
            csp_connect.append(SUPABASE_URL.rstrip("/"))
        swagger_cdns = ["https://cdn.jsdelivr.net", "https://unpkg.com", "https://cdn.tailwindcss.com", "https://cdnjs.cloudflare.com", "https://fonts.googleapis.com"]
        csp_connect.extend(swagger_cdns)
        extra_img_sources = ["https://fastapi.tiangolo.com", "https://images.unsplash.com", "https://upload.wikimedia.org", "https://cdn.pixabay.com", "https://media.istockphoto.com"]

        csp = (
            "default-src 'self'; "
            "base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
            f"img-src 'self' data: blob: {' '.join(extra_img_sources)}; "
            f"style-src 'self' 'unsafe-inline' {' '.join(swagger_cdns)}; "
            f"font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            f"script-src 'self' 'unsafe-inline' {' '.join(swagger_cdns)}; "
            f"connect-src {' '.join(csp_connect)}"
        )
        response.headers["Content-Security-Policy"] = csp

        if set_csrf_cookie_value:
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=set_csrf_cookie_value,
                httponly=False,
                secure=COOKIE_SECURE,
                samesite="Lax",
                max_age=60 * 60,
                path="/",
            )
        return response

def register_no_cache_middleware(app: FastAPI) -> None:
    """
    Empêche la mise en cache des pages sensibles:
    - S’applique aux GET sur /session et sous-arbre /admin.
    - Ajoute les en-têtes Cache-Control/Pragma/Expires pour forcer le rechargement.
    """
    @app.middleware("http")
    async def no_cache_for_protected(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path.rstrip("/")
        if request.method == "GET" and (path == "/session" or path.startswith("/admin")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


def register_force_https_middleware(app: FastAPI) -> None:
    """
    Force la redirection HTTP -> HTTPS lorsqu’un proxy place x-forwarded-proto=http.
    - Ajouté en dernier afin qu’il s’exécute en premier dans la pile des middlewares.
    - Important pour éviter les mixed-content et renforcer la sécurité.
    """
    @app.middleware("http")
    async def force_https(request: Request, call_next):
        if request.headers.get("x-forwarded-proto") == "http":
            url = request.url._url.replace("http://", "https://")
            return RedirectResponse(url, status_code=301)
        return await call_next(request)