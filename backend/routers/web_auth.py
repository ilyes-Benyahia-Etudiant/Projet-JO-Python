from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from starlette.status import HTTP_303_SEE_OTHER
from typing import Optional
from backend.utils.templates import templates
from backend.utils.security import set_session_cookie, clear_session_cookie, require_user
from backend.services.auth_service import sign_in, sign_up, send_reset_email, update_password
from backend.config import RESET_REDIRECT_URL, ADMIN_SIGNUP_CODE

router = APIRouter(prefix="/auth", tags=["Auth Web"])

@router.get("", response_class=HTMLResponse)
def auth_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    return templates.TemplateResponse("auth.html", {"request": request, "error": error, "message": message})

@router.post("/login")
def web_login(email: str = Form(...), password: str = Form(...)):
    result = sign_in(email, password)
    if not result.success:
        return RedirectResponse(url=f"/auth?error={result.error or 'Identifiants invalides'}", status_code=HTTP_303_SEE_OTHER)
    target = "/admin" if result.user["role"] == "admin" else "/session"
    redirect = RedirectResponse(url=target, status_code=HTTP_303_SEE_OTHER)
    set_session_cookie(redirect, result.access_token)
    return redirect

@router.post("/signup")
def web_signup(email: str = Form(...), password: str = Form(...), full_name: str = Form("")):
    # On reproduit l'ancien comportement: admin si password == ADMIN_SIGNUP_CODE (si défini)
    wants_admin = bool(ADMIN_SIGNUP_CODE) and (password == ADMIN_SIGNUP_CODE)
    result = sign_up(email, password, full_name or None, wants_admin=wants_admin)
    if not result.success:
        return RedirectResponse(url=f"/auth?error={result.error}", status_code=HTTP_303_SEE_OTHER)
    if result.access_token:
        target = "/admin" if result.user["role"] == "admin" else "/session"
        redirect = RedirectResponse(url=target, status_code=HTTP_303_SEE_OTHER)
        set_session_cookie(redirect, result.access_token)
        return redirect
    return RedirectResponse(url="/auth?message=Inscription%20reussie%2C%20verifiez%20votre%20email", status_code=HTTP_303_SEE_OTHER)

@router.post("/forgot")
def web_forgot(email: str = Form(...)):
    result = send_reset_email(email, RESET_REDIRECT_URL)
    if not result.success:
        return RedirectResponse(url=f"/auth?error={result.error}", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/auth?message=Email%20de%20reinitialisation%20envoye", status_code=HTTP_303_SEE_OTHER)

@router.get("/reset", response_class=HTMLResponse)
def password_reset_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    return templates.TemplateResponse("reset_password.html", {"request": request, "error": error, "message": message})

@router.post("/reset")
def web_reset_password(new_password: str = Form(...), user = Depends(require_user)):
    if len(new_password or "") < 6:
        return RedirectResponse(url="/auth/reset?error=Mot%20de%20passe%20trop%20court", status_code=HTTP_303_SEE_OTHER)
    result = update_password(user["token"], new_password)
    if not result.success:
        return RedirectResponse(url=f"/auth/reset?error={result.error}", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/auth?message=Mot%20de%20passe%20mis%20a%20jour", status_code=HTTP_303_SEE_OTHER)

@router.api_route("/logout", methods=["GET", "POST"])
def web_logout():
    redirect = RedirectResponse(url="/auth?message=Deconnecte", status_code=HTTP_303_SEE_OTHER)
    clear_session_cookie(redirect)
    # Empêcher toute persistance côté client
    redirect.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    redirect.headers["Pragma"] = "no-cache"
    redirect.headers["Expires"] = "0"
    redirect.headers["Clear-Site-Data"] = '"cache"'
    return redirect

@router.post("/recover/session")
async def recover_session(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
    access_token = (data.get("access_token") or data.get("accessToken") or "").strip()
    if not access_token:
        return JSONResponse({"error": "access_token requis"}, status_code=400)
    redirect = RedirectResponse(url="/auth/reset", status_code=HTTP_303_SEE_OTHER)
    set_session_cookie(redirect, access_token)
    return redirect