import logging
import os
import secrets
import urllib.parse
import redis
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.status import HTTP_303_SEE_OTHER, HTTP_204_NO_CONTENT
from contextlib import asynccontextmanager
try:
    from starlette.middleware.proxy_headers import ProxyHeadersMiddleware
except Exception:
    ProxyHeadersMiddleware = None

from backend.config import PUBLIC_DIR, CORS_ORIGINS, ALLOWED_HOSTS, SUPABASE_URL, COOKIE_SECURE
from backend.auth.views import web_router as auth_web_router, api_router as auth_api_router
from backend.users.views import web_router as users_web_router, api_router as users_api_router
from backend.admin.views import router as admin_router
from backend.health.router import router as health_router
from backend.validation.views import web_router as validate_web_router
from backend.commandes import views as commandes_views
from backend.tickets import views as tickets_views
from backend.validation import views as validation_views
from fastapi_limiter import FastAPILimiter
from backend.payments import views as payments_views

try:
    from fakeredis.aioredis import FakeRedis  # fallback tests-only
except Exception:
    FakeRedis = None

# --- Constantes sécurité ---
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_EXEMPT_PATHS = {
    "/api/v1/commandes/webhook/stripe",
    "/api/v1/payments/webhook",
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Migration de l'init du rate limiter ici (anciennement on_event('startup'))
    logger = logging.getLogger("uvicorn.error")
    try:
        if os.getenv("DISABLE_FASTAPI_LIMITER_INIT_FOR_TESTS") == "1":
            app.state.rate_limit_enabled = False
            logger.info("Rate limiting disabled by DISABLE_FASTAPI_LIMITER_INIT_FOR_TESTS")
            yield
            return

        use_fake = os.getenv("USE_FAKE_REDIS_FOR_TESTS") == "1"
        if use_fake:
            if not FakeRedis:
                raise RuntimeError("USE_FAKE_REDIS_FOR_TESTS=1 mais fakeredis n'est pas installé.")
            r = FakeRedis(decode_responses=True)
        else:
            redis_url = os.getenv("RATE_LIMIT_REDIS_URL", "redis://127.0.0.1:6379/0")
            r = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

        await FastAPILimiter.init(r)
        app.state.rate_limit_enabled = True
        logger.info("Rate limiting enabled")
    except Exception as e:
        if os.getenv("LOCAL_RATE_LIMIT_FALLBACK") == "1":
            app.state.rate_limit_enabled = True
            logger.warning(f"Rate limiting falling back to local in-memory due to init error: {e}")
        else:
            app.state.rate_limit_enabled = False
            logger.warning(f"Rate limiting disabled due to init error: {e}")

    # Phase shutdown
    yield

# --- Regroupements de configuration ---
def register_basic_middlewares(app: FastAPI) -> None:
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

def mount_static_files(app: FastAPI) -> None:
    app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")
    app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")
    app.mount("/js", StaticFiles(directory=str(PUBLIC_DIR / "js")), name="js")

def register_security_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def security_headers_and_csrf(request: Request, call_next):
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
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        if COOKIE_SECURE:
            response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")

        csp_connect = ["'self'"]
        if SUPABASE_URL:
            csp_connect.append(SUPABASE_URL.rstrip("/"))
        swagger_cdns = ["https://cdn.jsdelivr.net", "https://unpkg.com", "https://cdn.tailwindcss.com"]
        csp_connect.extend(swagger_cdns)
        extra_img_sources = ["https://fastapi.tiangolo.com"]

        csp = (
            "default-src 'self'; "
            "base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
            f"img-src 'self' data: blob: {' '.join(extra_img_sources)}; "
            f"style-src 'self' 'unsafe-inline' {' '.join(swagger_cdns)}; "
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
    @app.middleware("http")
    async def no_cache_for_protected(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path.rstrip("/")
        if request.method == "GET" and (path == "/session" or path.startswith("/admin")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def html_redirect_on_auth_errors(request: Request, exc: HTTPException):
        if exc.status_code in (401, 403):
            accept = (request.headers.get("accept") or "").lower()
            is_api = request.url.path.startswith("/api/")
            if "text/html" in accept and not is_api:
                detail = str(getattr(exc, "detail", "")) or (
                    "Veuillez vous connecter" if exc.status_code == 401 else "Accès interdit"
                )
                msg = urllib.parse.quote_plus(detail)
                return RedirectResponse(url=f"/auth?error={msg}", status_code=HTTP_303_SEE_OTHER)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

def register_routes(app: FastAPI) -> None:
    @app.get("/", include_in_schema=False)
    def root_redirect():
        index_path = PUBLIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return RedirectResponse(url="/public/index.html", status_code=HTTP_303_SEE_OTHER)

    @app.get("/index.html", include_in_schema=False)
    def index_alias():
        index_path = PUBLIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return RedirectResponse(url="/public/index.html", status_code=HTTP_303_SEE_OTHER)

    @app.get("/accueil", include_in_schema=False)
    def accueil_alias():
        index_path = PUBLIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return RedirectResponse(url="/public/index.html", status_code=HTTP_303_SEE_OTHER)

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return Response(status_code=HTTP_204_NO_CONTENT)

def register_routers(app: FastAPI) -> None:
    # Pages web (HTML)
    app.include_router(users_web_router)
    app.include_router(auth_web_router)
    app.include_router(validate_web_router)
    # API v1
    app.include_router(auth_api_router)
    app.include_router(commandes_views.router)
    app.include_router(tickets_views.router)
    app.include_router(validation_views.router)
    app.include_router(payments_views.router)
    app.include_router(users_api_router)
    # Admin
    app.include_router(admin_router)
    # Health & monitoring
    app.include_router(health_router)

def create_app() -> FastAPI:
    app = FastAPI(title="Projet JO Python", lifespan=lifespan)
    register_basic_middlewares(app)
    mount_static_files(app)
    register_security_middleware(app)
    register_no_cache_middleware(app)
    register_exception_handlers(app)
    register_routes(app)
    register_routers(app)
    return app

app = create_app()

# Ancienne fonction conservée pour compat éventuelle (n’effectue plus rien)
async def init_rate_limiter():
    return
