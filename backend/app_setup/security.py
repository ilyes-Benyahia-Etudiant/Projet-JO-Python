from fastapi import FastAPI
from backend.config import SUPABASE_URL, COOKIE_SECURE

def register_security_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)

        # En-têtes de sécurité
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        if COOKIE_SECURE:
            response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")

        # CSP
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

        return response