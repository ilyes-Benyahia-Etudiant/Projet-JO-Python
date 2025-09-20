# module backend.users.views

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from backend.utils.security import require_user
from backend.utils.templates import templates
from .service import get_user_dashboard
from .repository import get_user_orders
from typing import Dict, Any  # <-- Ajout pour éviter NameError
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from backend.utils.templates import templates
from backend.evenements.repository import list_evenements as _list_evenements
# Ajout: import des offres
from backend.offres.repository import list_offres as _list_offres

web_router = APIRouter(tags=["User Pages"])

@web_router.get("/billeterie", response_class=HTMLResponse)
@web_router.get("/billeterie.html", response_class=HTMLResponse)
def billeterie_page(request: Request) -> HTMLResponse:
    evenements = _list_evenements()
    # Ajout: charger les offres réelles
    offres = _list_offres()
    return templates.TemplateResponse(
        "billeterie.html",
        {
            "request": request,
            "evenements": evenements,
            "offres": offres,
        },
    )

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
api_router = APIRouter(prefix="/api/v1/users", tags=["Users API"])