from typing import Optional
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from backend.utils.templates import templates
from backend.utils.security import require_admin
from backend.admin import service as admin_service
from backend.utils.rate_limit import optional_rate_limit
from backend.config import COOKIE_SECURE
import secrets
from backend.utils.csrf import get_or_create_csrf_token, attach_csrf_cookie_if_missing, validate_csrf_token

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def admin_page(request: Request, message: Optional[str] = None, user: dict = Depends(require_admin)):
    offres = admin_service.list_offres()
    commandes = admin_service.get_admin_commandes()

    csrf = get_or_create_csrf_token(request)
    resp = templates.TemplateResponse("admin.html", {
        "request": request,
        "offres": offres,
        "commandes": commandes,
        "message": message,
        "user": user,
        "csrf_token": csrf,
    })
    attach_csrf_cookie_if_missing(resp, request, csrf)
    return resp

@router.get("/offres/new", response_class=HTMLResponse)
@router.get("/offres/new/", response_class=HTMLResponse)
def afficher_formulaire_creation_offre(request: Request, user: dict = Depends(require_admin)):
    values = {"title": "", "price": "", "category": "", "stock": "", "active": "on", "description": "", "image": ""}
    csrf = get_or_create_csrf_token(request)
    resp = templates.TemplateResponse("offre_form.html", {
        "request": request,
        "mode": "create",
        "action_url": "/admin/offres",
        "values": values,
        "user": user,
        "csrf_token": csrf,
    })
    attach_csrf_cookie_if_missing(resp, request, csrf)
    return resp

@router.post("/offres", dependencies=[Depends(optional_rate_limit(times=20, seconds=60))])
@router.post("/offres/", dependencies=[Depends(optional_rate_limit(times=20, seconds=60))])
async def creer_offre(
    request: Request,
    user: dict = Depends(require_admin),
):
    form_data = await request.form()
    if not validate_csrf_token(request, form_data):
        return RedirectResponse(url="/admin?error=CSRF%20invalide", status_code=HTTP_303_SEE_OTHER)

    title = (form_data.get("title") or "").strip()

    if not title:
        return RedirectResponse(url="/admin?error=Titre%20requis", status_code=HTTP_303_SEE_OTHER)
    
    price_raw = (form_data.get("price") or "").strip()
    category = (form_data.get("category") or "").strip()
    stock_raw = (form_data.get("stock") or "").strip()
    description = (form_data.get("description") or "").strip()
    image = (form_data.get("image") or "").strip()
    active = "active" in form_data

    try:
        price_f = float(price_raw)
    except Exception:
        return RedirectResponse(url="/admin?error=Prix%20invalide", status_code=HTTP_303_SEE_OTHER)
    try:
        stock_i = int(stock_raw or "0")
    except Exception:
        return RedirectResponse(url="/admin?error=Stock%20invalide", status_code=HTTP_303_SEE_OTHER)

    created = admin_service.create_offre({
        "title": title,
        "price": price_f,
        "category": category,
        "stock": stock_i,
        "active": bool(active),
        "description": description,
        "image": image,
    })
    if not created:
        return RedirectResponse(url="/admin?error=Echec%20de%20la%20cr%C3%A9ation%20de%20l%27offre", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/admin?message=Offre%20cr%C3%A9%C3%A9e", status_code=HTTP_303_SEE_OTHER)

@router.get("/offres/{offre_id}/edit", response_class=HTMLResponse)
@router.get("/offres/{offre_id}/edit/", response_class=HTMLResponse)
def afficher_formulaire_edition_offre(request: Request, offre_id: str, user: dict = Depends(require_admin)):
    ligne = admin_service.get_offre_by_id(offre_id)
    csrf = get_or_create_csrf_token(request)
    resp = templates.TemplateResponse("offre_form.html", {
        "request": request,
        "mode": "edit",
        "action_url": f"/admin/offres/{offre_id}/update",
        "values": ligne,
        "user": user,
        "csrf_token": csrf,
    })
    attach_csrf_cookie_if_missing(resp, request, csrf)
    return resp

@router.post("/offres/{offre_id}/update")
@router.post("/offres/{offre_id}/update/")
async def mettre_a_jour_offre(
    request: Request,
    offre_id: str,
    user: dict = Depends(require_admin),
):
    form_data = await request.form()
    if not validate_csrf_token(request, form_data):
        return RedirectResponse(url="/admin?error=CSRF%20invalide", status_code=HTTP_303_SEE_OTHER)

    title = (form_data.get("title") or "").strip()

    if not title:
        return RedirectResponse(url="/admin?error=Titre%20requis", status_code=HTTP_303_SEE_OTHER)

    price_raw = (form_data.get("price") or "").strip()
    category = (form_data.get("category") or "").strip()
    stock_raw = (form_data.get("stock") or "").strip()
    description = (form_data.get("description") or "").strip()
    image = (form_data.get("image") or "").strip()
    active = "active" in form_data

    try:
        price_f = float(price_raw)
    except Exception:
        return RedirectResponse(url="/admin?error=Prix%20invalide", status_code=HTTP_303_SEE_OTHER)
    try:
        stock_i = int(stock_raw or "0")
    except Exception:
        return RedirectResponse(url="/admin?error=Stock%20invalide", status_code=HTTP_303_SEE_OTHER)

    updated = admin_service.update_offre(
        offre_id,
        {
            "title": title,
            "price": price_f,
            "category": category,
            "stock": stock_i,
            "active": bool(active),
            "description": description,
            "image": image,
        },
    )
    if not updated:
        return RedirectResponse(url="/admin?error=Echec%20de%20la%20mise%20%C3%A0%20jour%20de%20l%27offre", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/admin?message=Offre%20mise%20%C3%A0%20jour", status_code=HTTP_303_SEE_OTHER)

@router.post("/offres/{offre_id}/delete", dependencies=[Depends(optional_rate_limit(times=20, seconds=60))])
@router.post("/offres/{offre_id}/delete/", dependencies=[Depends(optional_rate_limit(times=20, seconds=60))])
async def supprimer_offre(request: Request, offre_id: str, user: dict = Depends(require_admin)):
    form_data = await request.form()
    if not validate_csrf_token(request, form_data):
        return RedirectResponse(url="/admin?error=CSRF%20invalide", status_code=HTTP_303_SEE_OTHER)

    ok = admin_service.delete_offre(offre_id)
    if not ok:
        return RedirectResponse(url="/admin?error=Echec%20de%20la%20suppression%20de%20l%27offre", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/admin?message=Offre%20supprim%C3%A9e", status_code=HTTP_303_SEE_OTHER)

@router.get("/scan", response_class=HTMLResponse)
@router.get("/scan/", response_class=HTMLResponse)
def admin_scan_page(request: Request, user: dict = Depends(require_admin)):
    csrf = get_or_create_csrf_token(request)
    resp = templates.TemplateResponse("admin-scan.html", {
        "request": request,
        "user": user,
        "csrf_token": csrf,
    })
    attach_csrf_cookie_if_missing(resp, request, csrf)
    return resp