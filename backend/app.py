from fastapi import FastAPI
from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.status import HTTP_303_SEE_OTHER
from backend.config import PUBLIC_DIR, CORS_ORIGINS, ALLOWED_HOSTS, SUPABASE_URL
from backend.views.pages import router as pages_router
from backend.views.web_auth import router as web_auth_router  # Remplace l'ancien auth_router
from backend.views.api_v1_auth import router as api_auth_router  # Nouveau router API JSON
from backend.views.admin_offres import router as admin_router
import logging
from urllib.parse import urlparse

app = FastAPI(title="Projet JO Python")

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

from backend.views.health import router as health_router
from backend.views.payments import router as payments_router
from backend.views.tickets import router as tickets_router  # Nouvelle ligne

app.include_router(health_router)
app.include_router(pages_router)
app.include_router(web_auth_router)      # /auth (HTML + cookies)
app.include_router(api_auth_router)      # /api/v1/auth (JSON + Bearer)
app.include_router(admin_router)
app.include_router(payments_router)
app.include_router(tickets_router)       # Nouvelle ligne

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

@app.middleware("http")
async def no_cache_for_protected(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path.rstrip("/")
    if request.method == "GET" and (path == "/session" or path.startswith("/admin")):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

@app.exception_handler(HTTPException)
async def html_redirect_on_auth_errors(request: Request, exc: HTTPException):
    # Rediriger vers /auth pour les pages HTML (non /api) afin d'éviter l'affichage JSON brut
    if exc.status_code in (401, 403):
        accept = (request.headers.get("accept") or "").lower()
        is_api = request.url.path.startswith("/api/")
        if "text/html" in accept and not is_api:
            msg = "Veuillez%20vous%20connecter" if exc.status_code == 401 else "Acc%C3%A8s%20interdit"
            return RedirectResponse(url=f"/auth?error={msg}", status_code=HTTP_303_SEE_OTHER)
    # Par défaut, garder le JSON (utile pour l'API)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# Ajouter après les autres routes
from fastapi.responses import FileResponse
import os

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(str(PUBLIC_DIR), "favicon.ico"))