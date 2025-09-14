from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from backend.config import CORS_ORIGINS, ALLOWED_HOSTS

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