from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from typing import Optional
from backend.utils.templates import templates
from fastapi import Response  # ajout
from fastapi.responses import RedirectResponse  # ajout
from starlette.status import HTTP_303_SEE_OTHER  # ajout
from backend.utils.security import clear_session_cookie  # ajout

router = APIRouter(prefix="/auth", tags=["Auth Web"])

@router.get("", response_class=HTMLResponse)
def auth_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    return templates.TemplateResponse("auth.html", {"request": request, "error": error, "message": message})

@router.get("/reset", response_class=HTMLResponse)
def password_reset_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    return templates.TemplateResponse("reset_password.html", {"request": request, "error": error, "message": message})

# Nouveau: route pour absorber les redirections de confirmation
@router.get("/confirm", response_class=HTMLResponse)
def auth_confirm_redirect(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    # Le fragment #access_token n’est pas visible côté serveur; on affiche un message générique
    message = message or "Votre email a été confirmé. Vous pouvez maintenant vous connecter."
    return templates.TemplateResponse("auth.html", {"request": request, "error": error, "message": message})

# Optionnel: attraper aussi des sous-chemins sous /auth/confirm/...
@router.get("/confirm/{rest_of_path:path}", response_class=HTMLResponse)
def auth_confirm_fallback(request: Request, rest_of_path: str, error: Optional[str] = None, message: Optional[str] = None):
    message = message or "Votre email a été confirmé. Vous pouvez maintenant vous connecter."
    return templates.TemplateResponse("auth.html", {"request": request, "error": error, "message": message})

# Nouveau: attraper toutes les autres URL sous /auth (ex: /auth/callback, /auth/verify, ...)
@router.get("/{rest_of_path:path}", response_class=HTMLResponse)
def auth_fallback(request: Request, rest_of_path: str, error: Optional[str] = None, message: Optional[str] = None):
    return templates.TemplateResponse("auth.html", {"request": request, "error": error, "message": message})

# Déconnexion HTML: supprime le cookie et redirige vers /auth avec un message
@router.post("/logout", include_in_schema=False)
def auth_logout_post(response: Response):
    clear_session_cookie(response)
    return RedirectResponse(url="/auth?message=D%C3%A9connexion%20r%C3%A9ussie", status_code=HTTP_303_SEE_OTHER)

# Optionnel: support GET pour la déconnexion (liens simples)
@router.get("/logout", include_in_schema=False)
def auth_logout_get(response: Response):
    clear_session_cookie(response)
    return RedirectResponse(url="/auth?message=D%C3%A9connexion%20r%C3%A9ussie", status_code=HTTP_303_SEE_OTHER)