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
    admin_code: Optional[str] = None
    scanner_code: Optional[str] = None
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
    """Point d'entrée de connexion (API JSON).
    - Applique un rate limit (3 requêtes par 60 secondes via la dépendance).
    - Délègue la vérification des identifiants au service (svc_login).
    - En cas de succès, synchronise le profil applicatif (best-effort).
    - Pose le cookie de session (sb_access) si un access_token est fourni.
    - Retourne un JSON {access_token, token_type, user} pour usage côté client.
    """
    result = svc_login(req.email, req.password)
    if not result.success:
        raise HTTPException(status_code=401, detail=result.error or "Identifiants invalides")
    
    user = result.user or {}
    try:
        # Best-effort: si l’utilisateur existe, assure la présence d’une clé bio et du rôle côté table users
        sync_user_profile(user.get("id"), user.get("email"), user.get("role"))
    except Exception:
        pass

    # Cookie HTTPOnly de session posé sur la réponse JSON
    if getattr(result, "access_token", None):
        set_session_cookie(response, result.access_token)

    return {"access_token": result.access_token, "token_type": "bearer", "user": result.user}
    # NOTE: Bloc de redirection legacy ci-dessous (scanner/admin/session) est inatteignable
    # dans le flux actuel, car on a déjà retourné le JSON ci-dessus.


@api_router.post("/signup", dependencies=[Depends(optional_rate_limit(times=3, seconds=60))])
@api_router.post("/signup_admin", dependencies=[Depends(optional_rate_limit(times=3, seconds=60))])
def api_signup(req: SignupRequest, response: Response):
    """Point d’entrée d’inscription (API JSON).
    - Vérifie la force du mot de passe via Pydantic + validate_password_strength.
    - Vérifie les codes secrets admin/scanner contre des hashes bcrypt (ADMIN_SECRET_HASH, SCANNER_SECRET_HASH).
    - Transmet wants_admin/wants_scanner au service pour positionner le rôle dans user_metadata.
    - En cas d’inscription avec session, pose le cookie et retourne le JSON de session.
    - Sinon, retourne un message demandant la confirmation d’email.
    """
    from backend.config import ADMIN_SECRET_HASH, SCANNER_SECRET_HASH
    # Sécuriser les types pour éviter les MagicMock et valeurs non-str
    admin_hash = ADMIN_SECRET_HASH if isinstance(ADMIN_SECRET_HASH, str) else None
    scanner_hash = SCANNER_SECRET_HASH if isinstance(SCANNER_SECRET_HASH, str) else None
    admin_code_val = req.admin_code if isinstance(req.admin_code, str) else None
    scanner_code_val = req.scanner_code if isinstance(req.scanner_code, str) else None
    password_val = req.password if isinstance(req.password, str) else None

    admin_code_ok = bool(admin_hash and admin_code_val) and bcrypt.checkpw(
        admin_code_val.encode('utf-8'),
        admin_hash.encode('utf-8')
    )
    password_is_admin_secret = bool(admin_hash and password_val) and bcrypt.checkpw(
        password_val.encode('utf-8'),
        admin_hash.encode('utf-8')
    )
    wants_admin = admin_code_ok or password_is_admin_secret

    scanner_code_ok = bool(scanner_hash and scanner_code_val) and bcrypt.checkpw(
        scanner_code_val.encode('utf-8'),
        scanner_hash.encode('utf-8')
    )
    password_is_scanner_secret = bool(scanner_hash and password_val) and bcrypt.checkpw(
        password_val.encode('utf-8'),
        scanner_hash.encode('utf-8')
    )
    wants_scanner = scanner_code_ok or password_is_scanner_secret

    result = svc_signup(req.email, req.password, req.full_name, wants_admin=wants_admin, wants_scanner=wants_scanner)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Erreur inscription")
    if result.access_token:
        try:
            # Synchronisation du profil (users.bio / rôle) après inscription
            sync_user_profile(result.user.get("id"), result.user.get("email"), result.user.get("role"))
        except Exception:
            pass
        set_session_cookie(response, result.access_token)
        return {"access_token": result.access_token, "token_type": "bearer", "user": result.user}
    return {"message": result.error or "Inscription réussie, vérifiez votre email"}

@api_router.get("/me")
def api_me(user: Dict[str, Any] = Depends(require_user)):
    """Retourne l’utilisateur courant (id, email, rôle, metadata) après contrôle de session via require_user."""
    return {"id": user["id"], "email": user["email"], "role": user["role"], "metadata": user["metadata"]}

@api_router.post("/request-password-reset", dependencies=[Depends(optional_rate_limit(times=3, seconds=60))])
def api_request_reset(req: ResetEmailRequest):
    result = svc_request_reset(req.email, RESET_REDIRECT_URL)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Erreur envoi email")
    return {"message": "Email de réinitialisation envoyé"}

@api_router.post("/update-password", dependencies=[Depends(optional_rate_limit(times=3, seconds=60))])
async def api_update_password(body: UpdatePasswordBody):
    """Met à jour le mot de passe via GoTrue (httpx PUT sur /auth/v1/user):
    - Exige un token (Bearer) fourni au client dans le flux de reset
    - Retourne un message en cas de succès ou l’erreur détaillée en cas d’échec
    """
    token = (body.token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token manquant")
    result = svc_update_password(token, body.new_password)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Erreur mise à jour du mot de passe")
    return {"message": "Mot de passe mis à jour"}

@api_router.post("/logout")
def api_logout(response: Response):
    """Supprime le cookie de session (sb_access) et renvoie un message JSON."""
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
    # Déconnexion via route web (POST)
    r = RedirectResponse(url="/auth?message=D%C3%A9connexion%20r%C3%A9ussie", status_code=HTTP_303_SEE_OTHER)
    clear_session_cookie(r)
    r.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

@web_router.get("/logout", include_in_schema=False)
def auth_logout_get(response: Response):
    """Déconnexion via route web (GET): efface le cookie et redirige vers l’accueil."""
    r = RedirectResponse(url="/index.html", status_code=HTTP_303_SEE_OTHER)
    clear_session_cookie(r)
    r.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r