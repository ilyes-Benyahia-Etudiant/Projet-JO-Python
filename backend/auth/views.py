from fastapi import APIRouter, HTTPException, Depends, Response, Request
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict, Any
import bcrypt

from backend.utils.validators import validate_password_strength
from backend.utils.security import require_user, set_session_cookie, clear_session_cookie
from backend.config import RESET_REDIRECT_URL
from .service import (
    login as svc_login,
    signup as svc_signup,
    request_password_reset as svc_request_reset,
    update_password as svc_update_password,
    sync_user_profile,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from backend.utils.templates import templates

def optional_rate_limit(times: int, seconds: int):
    from backend.utils.rate_limit import optional_rate_limit as _rl
    return _rl(times, seconds)

# --- API Router (/api/v1/auth) ---

api_router = APIRouter(prefix="/api/v1/auth", tags=["Auth API"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None
    @field_validator("password")
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)

class ResetEmailRequest(BaseModel):
    email: EmailStr

class UpdatePasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)
    @field_validator("new_password")
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)

class UpdatePasswordBody(UpdatePasswordRequest):
    token: str

@api_router.post("/login", dependencies=[Depends(optional_rate_limit(times=3, seconds=60))])
def api_login(req: LoginRequest, response: Response):
    result = svc_login(req.email, req.password)
    if not result.success:
        raise HTTPException(status_code=401, detail=result.error or "Identifiants invalides")
    try:
        sync_user_profile(result.user.get("id"), result.user.get("email"), result.user.get("role"))
    except Exception:
        pass
    if result.access_token:
        set_session_cookie(response, result.access_token)
    return {"access_token": result.access_token, "token_type": "bearer", "user": result.user}

@api_router.post("/signup", dependencies=[Depends(optional_rate_limit(times=3, seconds=60))])
@api_router.post("/signup_admin", dependencies=[Depends(optional_rate_limit(times=3, seconds=60))])
def api_signup(req: SignupRequest, response: Response):
    from backend.config import ADMIN_SECRET_HASH
    wants_admin = bool(ADMIN_SECRET_HASH) and bcrypt.checkpw(req.password.encode('utf-8'), ADMIN_SECRET_HASH.encode('utf-8'))
    result = svc_signup(req.email, req.password, req.full_name, wants_admin=wants_admin)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Erreur inscription")
    if result.access_token:
        try:
            sync_user_profile(result.user.get("id"), result.user.get("email"), result.user.get("role"))
        except Exception:
            pass
        set_session_cookie(response, result.access_token)
        return {"access_token": result.access_token, "token_type": "bearer", "user": result.user}
    return {"message": result.error or "Inscription réussie, vérifiez votre email"}

@api_router.get("/me")
def api_me(user: Dict[str, Any] = Depends(require_user)):
    return {"id": user["id"], "email": user["email"], "role": user["role"], "metadata": user["metadata"]}

@api_router.post("/request-password-reset", dependencies=[Depends(optional_rate_limit(times=3, seconds=60))])
def api_request_reset(req: ResetEmailRequest):
    result = svc_request_reset(req.email, RESET_REDIRECT_URL)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Erreur envoi email")
    return {"message": "Email de réinitialisation envoyé"}

@api_router.post("/update-password", dependencies=[Depends(optional_rate_limit(times=3, seconds=60))])
async def api_update_password(body: UpdatePasswordBody):
    token = (body.token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token manquant")
    result = svc_update_password(token, body.new_password)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Erreur mise à jour du mot de passe")
    return {"message": "Mot de passe mis à jour"}

@api_router.post("/logout")
def api_logout(response: Response):
    clear_session_cookie(response)
    return {"message": "Déconnexion réussie"}

# --- Web Router (/auth) ---

web_router = APIRouter(prefix="/auth", tags=["Auth Web"])

@web_router.get("", response_class=HTMLResponse)
def auth_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    return templates.TemplateResponse("auth.html", {"request": request, "error": error, "message": message})

@web_router.get("/reset", response_class=HTMLResponse)
def password_reset_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    return templates.TemplateResponse("reset_password.html", {"request": request, "error": error, "message": message})

@web_router.get("/confirm", response_class=HTMLResponse)
def auth_confirm_redirect(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    message = message or "Votre email a été confirmé. Vous pouvez maintenant vous connecter."
    return templates.TemplateResponse("auth.html", {"request": request, "error": error, "message": message})

@web_router.get("/confirm/{rest_of_path:path}", response_class=HTMLResponse)
def auth_confirm_fallback(request: Request, rest_of_path: str, error: Optional[str] = None, message: Optional[str] = None):
    message = message or "Votre email a été confirmé. Vous pouvez maintenant vous connecter."
    return templates.TemplateResponse("auth.html", {"request": request, "error": error, "message": message})

@web_router.get("/{rest_of_path:path}", response_class=HTMLResponse)
def auth_fallback(request: Request, rest_of_path: str, error: Optional[str] = None, message: Optional[str] = None):
    return templates.TemplateResponse("auth.html", {"request": request, "error": error, "message": message})

@web_router.post("/logout", include_in_schema=False)
def auth_logout_post(response: Response):
    r = RedirectResponse(url="/auth?message=D%C3%A9connexion%20r%C3%A9ussie", status_code=HTTP_303_SEE_OTHER)
    clear_session_cookie(r)
    r.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

@web_router.get("/logout", include_in_schema=False)
def auth_logout_get(response: Response):
    r = RedirectResponse(url="/auth?message=D%C3%A9connexion%20r%C3%A9ussie", status_code=HTTP_303_SEE_OTHER)
    clear_session_cookie(r)
    r.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r