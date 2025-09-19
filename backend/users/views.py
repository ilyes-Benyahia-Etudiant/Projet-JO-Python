from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Any, Dict
from starlette.status import HTTP_303_SEE_OTHER
from backend.utils.security import require_user
from backend.utils.templates import templates
from .service import get_user_dashboard
from .repository import get_user_orders

# API Router (/api/v1/users)
api_router = APIRouter(prefix="/api/v1/users", tags=["Users API"])

@api_router.get("/orders")
def api_list_orders(user: Dict[str, Any] = Depends(require_user)):
    orders = get_user_orders(user.get("id"))
    return {"orders": orders}

@api_router.get("/dashboard")
def api_dashboard(user: Dict[str, Any] = Depends(require_user)):
    data = get_user_dashboard(user.get("id"))
    return data

# Web Router (pages utilisateurs)
web_router = APIRouter(tags=["User Pages"])

# --- Routes publiques migrées ---
@web_router.get("/accueil", include_in_schema=False)
def accueil_redirect():
    return RedirectResponse(url="/billeterie", status_code=HTTP_303_SEE_OTHER)

@web_router.get("/billeterie", response_class=HTMLResponse)
@web_router.get("/billeterie.html", response_class=HTMLResponse)
def billeterie_page(request: Request):
    return templates.TemplateResponse("billeterie.html", {"request": request})

@web_router.get("/billets.html", include_in_schema=False)
def redirect_billets():
    return RedirectResponse(url="/billeterie", status_code=HTTP_303_SEE_OTHER)

@web_router.get("/session", response_class=HTMLResponse)
def user_session(request: Request, user: Dict[str, Any] = Depends(require_user)):
    from backend.utils.csrf import get_or_create_csrf_token, attach_csrf_cookie_if_missing
    data = get_user_dashboard(user.get("id"))
    csrf = get_or_create_csrf_token(request)
    resp = templates.TemplateResponse(
        "session.html",
        {"request": request, "offres": data["offres"], "user": user, "csrf_token": csrf},
    )
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    attach_csrf_cookie_if_missing(resp, request, csrf)
    return resp

@web_router.get("/mes-billets", response_class=HTMLResponse)
@web_router.get("/mes-billets.html", response_class=HTMLResponse)
def mes_billets_page(request: Request, user: Dict[str, Any] = Depends(require_user)):
    from backend.utils.csrf import get_or_create_csrf_token, attach_csrf_cookie_if_missing
    csrf = get_or_create_csrf_token(request)
    resp = templates.TemplateResponse("mes-billets.html", {"request": request, "user": user, "csrf_token": csrf})
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    attach_csrf_cookie_if_missing(resp, request, csrf)
    return resp