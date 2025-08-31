from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from backend.config import PUBLIC_DIR, CORS_ORIGINS, ALLOWED_HOSTS, SUPABASE_URL
from backend.routers.pages import router as pages_router
from backend.routers.auth import router as auth_router
from backend.routers.admin_offres import router as admin_router
import logging
from urllib.parse import urlparse

def create_app() -> FastAPI:
    app = FastAPI(title="Mon Application Marketplace")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS + ["*"] if "*" in CORS_ORIGINS else ALLOWED_HOSTS)

    app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")
    app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")

    from backend.routers.health import router as health_router
    from backend.routers.payments import router as payments_router
    app.include_router(health_router)
    app.include_router(pages_router)
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(payments_router)

    # Log du domaine/projet Supabase au démarrage
    host = None
    try:
        host = urlparse(SUPABASE_URL).hostname if SUPABASE_URL else None
    except Exception:
        host = None
    logging.getLogger(__name__).info("App configured with Supabase URL=%s host=%s", SUPABASE_URL, host)

    @app.get("/", include_in_schema=False)
    def root_redirect():
        return RedirectResponse(url="/public/index.html", status_code=HTTP_303_SEE_OTHER)

    return app

app = create_app()