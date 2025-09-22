# module backend.app
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
from starlette.middleware.sessions import SessionMiddleware
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
from backend.evenements.views import router as evenements_router

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

def mount_static_files(app: FastAPI) -> None:
    app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")
    app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")
    app.mount("/js", StaticFiles(directory=str(PUBLIC_DIR / "js")), name="js")

# Remplace les définitions locales par des imports factorisés
from backend.app_setup.middlewares import register_security_middleware, register_no_cache_middleware, register_basic_middlewares, register_force_https_middleware
from backend.app_setup.exception_handlers import register_exception_handlers
from backend.app_setup.routes import register_routes
from backend.app_setup.static import mount_static_files
from backend.app_setup.lifespan import lifespan as app_lifespan

def create_app() -> FastAPI:
    app = FastAPI(title="JO API", lifespan=app_lifespan)
    register_basic_middlewares(app)
    mount_static_files(app)
    register_security_middleware(app)
    register_no_cache_middleware(app)
    register_exception_handlers(app)
    register_routes(app)
    # Remplace les inclusions dispersées par l’appel centralisé
    from backend.app_setup.routers import register_routers
    register_routers(app)
    app.include_router(evenements_router)
    # Ajouter le middleware HTTPS en dernier pour qu'il s’exécute en premier
    register_force_https_middleware(app)
    return app

# App globale
app = create_app()



# Ancienne fonction conservée pour compat éventuelle (n’effectue plus rien)
async def init_rate_limiter():
    return
