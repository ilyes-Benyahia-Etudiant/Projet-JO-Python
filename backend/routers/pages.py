from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.status import HTTP_303_SEE_OTHER
from backend.utils.templates import templates
from backend.utils.db import fetch_offres, fetch_user_commandes
from backend.utils.security import require_user

router = APIRouter(tags=["Pages"])

@router.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/public/index.html", status_code=HTTP_303_SEE_OTHER)

@router.get("/billeterie", response_class=HTMLResponse)
@router.get("/billeterie.html", response_class=HTMLResponse)
def billeterie_page(request: Request):
    return templates.TemplateResponse("billeterie.html", {"request": request})

@router.get("/billets.html", include_in_schema=False)
def redirect_billets():
    return RedirectResponse(url="/billeterie", status_code=HTTP_303_SEE_OTHER)

@router.get("/session", response_class=HTMLResponse)
def user_session(request: Request, user = Depends(require_user)):
    offres = fetch_offres()
    commandes = fetch_user_commandes(user.get("id"))
    resp = templates.TemplateResponse("session.html", {"request": request, "offres": offres, "commandes": commandes, "user": user})
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp