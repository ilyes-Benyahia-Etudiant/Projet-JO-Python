from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel, EmailStr, Field, field_validator
from backend.utils.validators import validate_password_strength
from typing import Optional, Dict, Any
from backend.models import sign_in, sign_up, send_reset_email
from backend.utils.security import require_user, set_session_cookie, clear_session_cookie
from backend.config import RESET_REDIRECT_URL
from backend.models.db import upsert_user_profile
import re
import bcrypt
from backend.models.usecases_auth import update_password as update_password_usecase

router = APIRouter(prefix="/api/v1/auth", tags=["Auth API"])

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

@router.post("/login")
def api_login(req: LoginRequest, response: Response):
    result = sign_in(req.email, req.password)
    if not result.success:
        raise HTTPException(status_code=401, detail=result.error or "Identifiants invalides")

    # Sync DB users.role
    try:
        upsert_user_profile(result.user.get("id"), result.user.get("email"), result.user.get("role"))
    except Exception:
        pass
    
    if result.access_token:
        set_session_cookie(response, result.access_token)

    return {"access_token": result.access_token, "token_type": "bearer", "user": result.user}

@router.post("/signup")
@router.post("/signup_admin")
def api_signup(req: SignupRequest, response: Response):
    from backend.config import ADMIN_SECRET_HASH  # Import local
    wants_admin = bool(ADMIN_SECRET_HASH) and bcrypt.checkpw(req.password.encode('utf-8'), ADMIN_SECRET_HASH.encode('utf-8'))
    result = sign_up(req.email, req.password, req.full_name, wants_admin=wants_admin)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Erreur inscription")

    if result.access_token:
        # Sync DB users.role si session créée
        try:
            upsert_user_profile(result.user.get("id"), result.user.get("email"), result.user.get("role"))
        except Exception:
            pass
        set_session_cookie(response, result.access_token)
        return {"access_token": result.access_token, "token_type": "bearer", "user": result.user}

    return {"message": result.error or "Inscription réussie, vérifiez votre email"}

@router.get("/me")
def api_me(user: Dict[str, Any] = Depends(require_user)):
    return {"id": user["id"], "email": user["email"], "role": user["role"], "metadata": user["metadata"]}

@router.post("/request-password-reset")
def api_request_reset(req: ResetEmailRequest):
    result = send_reset_email(req.email, RESET_REDIRECT_URL)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Erreur envoi email")
    return {"message": "Email de réinitialisation envoyé"}

@router.post("/update-password")
async def update_password(body: UpdatePasswordBody):
    token = (body.token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token manquant")
    result = update_password_usecase(token, body.new_password)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Erreur mise à jour du mot de passe")
    return {"message": "Mot de passe mis à jour"}

@router.post("/logout")
def api_logout(response: Response):
    clear_session_cookie(response)
    return {"message": "Déconnexion réussie"}