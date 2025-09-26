"""
Gestionnaires d’exceptions (version 1).
- Transforme 401/403 en redirection HTML vers /auth avec message (si Accept: text/html et pas /api/*).
- Conserve la réponse JSON standard pour les clients API (Accept JSON ou chemins /api/*).
"""
import urllib.parse
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

def register_exception_handlers(app: FastAPI) -> None:
    """
    Enregistre le handler HTTPException.
    - UX web: redirection vers /auth avec détail encodé (query ?error=...).
    - UX API: code et body JSON FastAPI standards pour debug et intégration front.
    """
    @app.exception_handler(HTTPException)
    async def html_redirect_on_auth_errors(request, exc: HTTPException):
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