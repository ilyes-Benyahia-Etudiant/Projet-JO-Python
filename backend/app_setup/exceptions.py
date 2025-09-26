"""
Gestionnaires d’exceptions (version 2, utilisée par la factory).
- Même logique que exception_handlers.py, typée avec Request.
- Raison du doublon: compat/factorisation progressive; les deux sont alignés fonctionnellement.
"""
import urllib.parse
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

def register_exception_handlers(app: FastAPI) -> None:
    """
    Enregistre le handler HTTPException pour 401/403.
    - Web: redirection avec message vers /auth.
    - API: JSON immuable pour clients programmatiques.
    """
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