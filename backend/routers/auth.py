from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from starlette.status import HTTP_303_SEE_OTHER
from typing import Optional
from backend.utils.templates import templates
from backend.utils.db import get_supabase
from backend.utils.security import set_session_cookie, clear_session_cookie, determine_role, require_user
from backend.config import RESET_REDIRECT_URL, ADMIN_SIGNUP_CODE, SUPABASE_URL
import os
import logging
from urllib.parse import urlparse

# Active l’affichage détaillé des erreurs d’auth si AUTH_DEBUG=1|true|yes
AUTH_DEBUG = (os.getenv("AUTH_DEBUG", "").lower() in ("1", "true", "yes"))
logger = logging.getLogger(__name__)

# Log du domaine/projet Supabase utilisé par le router d’auth
_supabase_host = None
try:
    _supabase_host = urlparse(SUPABASE_URL).hostname if SUPABASE_URL else None
except Exception:
    _supabase_host = None
logger.info("Auth router using Supabase URL=%s host=%s", SUPABASE_URL, _supabase_host)

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("", response_class=HTMLResponse)
def auth_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    return templates.TemplateResponse("auth.html", {"request": request, "error": error, "message": message})

@router.post("/signup")
async def auth_signup(request: Request):
    email: Optional[str] = None
    password: Optional[str] = None

    ct = (request.headers.get("content-type") or "").lower()
    if "application/json" in ct:
        data = await request.json()
        email = (data.get("email") or "").strip()
        password = data.get("password")
    else:
        form = await request.form()
        email = (form.get("email") or "").strip()
        password = form.get("password")

    if not email or not password:
        return RedirectResponse(url="/auth?error=Champs%20requis", status_code=HTTP_303_SEE_OTHER)

    # L'utilisateur devient admin si le mot de passe == ADMIN_SIGNUP_CODE
    wants_admin = bool(ADMIN_SIGNUP_CODE) and (password == ADMIN_SIGNUP_CODE)

    try:
        payload = {"email": email, "password": password}
        if wants_admin:
            payload["options"] = {"data": {"role": "admin"}}
        res = get_supabase().auth.sign_up(payload)
    except Exception:
        return RedirectResponse(url="/auth?error=Inscription%20impossible", status_code=HTTP_303_SEE_OTHER)

    # Toujours inviter à se connecter après inscription (pas de connexion auto)
    return RedirectResponse(url="/auth?message=Inscription%20reussie%2C%20veuillez%20vous%20connecter", status_code=HTTP_303_SEE_OTHER)
    sess = getattr(res, "session", None)
    user = getattr(res, "user", None)

    # Si une session existe immédiatement, on force/update le metadata au cas où
    if wants_admin and sess:
        try:
            get_supabase().auth.update_user({"data": {"role": "admin"}})
        except Exception:
            pass

    if not sess:
        # Email de confirmation envoyé par Supabase si activé
        return RedirectResponse(url="/auth?message=Email%20de%20confirmation%20envoye", status_code=HTTP_303_SEE_OTHER)

    access_token = getattr(sess, "access_token", None)
    role = determine_role(getattr(user, "email", None), getattr(user, "user_metadata", None))
    target = "/admin" if role == "admin" else "/session"

    redirect = RedirectResponse(url=target, status_code=HTTP_303_SEE_OTHER)
    if access_token:
        set_session_cookie(redirect, access_token)
    return redirect

@router.post("/login")
async def auth_login(email: str = Form(...), password: str = Form(...)):
    logger.info("Login attempt for email=%s against Supabase host=%s", (email or "").strip(), _supabase_host)
    try:
        res = get_supabase().auth.sign_in_with_password({"email": email.strip(), "password": password})
    except Exception as e:
        logger.exception("Erreur lors de sign_in_with_password Supabase")
        if AUTH_DEBUG:
            from urllib.parse import quote_plus
            return RedirectResponse(url=f"/auth?error={quote_plus('Identifiants invalides: ' + str(e))}", status_code=HTTP_303_SEE_OTHER)
        return RedirectResponse(url="/auth?error=Identifiants%20invalides", status_code=HTTP_303_SEE_OTHER)

    sess = getattr(res, "session", None)
    user = getattr(res, "user", None)
    if not sess or not getattr(sess, "access_token", None):
        logger.warning("Login sans session ou sans access_token (email confirmé ?)")
        return RedirectResponse(url="/auth?error=Identifiants%20invalides", status_code=HTTP_303_SEE_OTHER)

    access_token = sess.access_token
    role = determine_role(getattr(user, "email", None), getattr(user, "user_metadata", None))
    target = "/admin" if role == "admin" else "/session"

    redirect = RedirectResponse(url=target, status_code=HTTP_303_SEE_OTHER)
    set_session_cookie(redirect, access_token)
    return redirect

@router.post("/forgot")
async def auth_forgot(request: Request):
    email = None
    ct = (request.headers.get("content-type") or "").lower()
    if "application/json" in ct:
        data = await request.json()
        email = (data.get("email") or "").strip()
    else:
        form = await request.form()
        email = (form.get("email") or "").strip()
    if not email:
        return RedirectResponse(url="/auth?error=Email%20requis", status_code=HTTP_303_SEE_OTHER)
    try:
        # Envoie l’email de reset avec redirection après changement
        get_supabase().auth.reset_password_for_email(email, {"redirect_to": RESET_REDIRECT_URL})
    except Exception:
        return RedirectResponse(url="/auth?error=Echec%20envoi%20email%20de%20reinitialisation", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/auth?message=Email%20de%20reinitialisation%20envoye", status_code=HTTP_303_SEE_OTHER)

@router.get("/reset", response_class=HTMLResponse)
def password_reset_page(request: Request, user = Depends(require_user), error: Optional[str] = None, message: Optional[str] = None):
    return templates.TemplateResponse("reset_password.html", {"request": request, "error": error, "message": message})

@router.post("/reset")
def password_reset(new_password: str = Form(...), user = Depends(require_user)):
    if len(new_password or "") < 6:
        return RedirectResponse(url="/auth/reset?error=Mot%20de%20passe%20trop%20court", status_code=HTTP_303_SEE_OTHER)
    try:
        get_supabase().auth.update_user({"password": new_password})
    except Exception:
        return RedirectResponse(url="/auth/reset?error=Echec%20de%20mise%20a%20jour", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/auth?message=Mot%20de%20passe%20mis%20a%20jour", status_code=HTTP_303_SEE_OTHER)

@router.get("/me")
def auth_me(user = Depends(require_user)):
    return JSONResponse({"email": user["email"], "role": user["role"], "metadata": user["metadata"]})

@router.api_route("/logout", methods=["GET", "POST"])
def auth_logout():
    redirect = RedirectResponse(url="/auth?message=Deconnecte", status_code=HTTP_303_SEE_OTHER)
    clear_session_cookie(redirect)
    return redirect