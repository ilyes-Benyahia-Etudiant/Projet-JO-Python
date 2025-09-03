from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from backend.services.auth_service import sign_in, sign_up, send_reset_email, update_password
from backend.utils.security import require_user
from backend.config import RESET_REDIRECT_URL

router = APIRouter(prefix="/api/v1/auth", tags=["Auth API"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None

class ResetEmailRequest(BaseModel):
    email: EmailStr

class UpdatePasswordRequest(BaseModel):
    new_password: str = Field(min_length=6)

@router.post("/login")
def api_login(req: LoginRequest):
    result = sign_in(req.email, req.password)
    if not result.success:
        raise HTTPException(status_code=401, detail=result.error or "Identifiants invalides")
    return {"access_token": (result.session or {}).get("access_token"), "token_type": "bearer", "user": result.user}

@router.post("/signup")
def api_signup(req: SignupRequest):
    result = sign_up(req.email, req.password, req.full_name, wants_admin=False)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Erreur inscription")
    if (result.session or {}).get("access_token"):
        return {"access_token": (result.session or {}).get("access_token"), "token_type": "bearer", "user": result.user}
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
def api_update_password(req: UpdatePasswordRequest, user: Dict[str, Any] = Depends(require_user)):
    result = update_password(user["token"], req.new_password)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Erreur mise à jour")
    return {"message": "Mot de passe mis à jour"}