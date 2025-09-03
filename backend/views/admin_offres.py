from typing import Optional
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from backend.utils.templates import templates
from backend.utils.security import require_admin
from backend.models import (
    fetch_offres,
    fetch_admin_commandes,
    get_offre,
    create_offre,
    update_offre,
    delete_offre,
)

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def admin_page(request: Request, message: Optional[str] = None, user: dict = Depends(require_admin)):
    offres = fetch_offres()
    commandes = fetch_admin_commandes()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "offres": offres,
        "commandes": commandes,
        "email": user.get("email"),
        "role": user.get("role"),
        "msg": message
    })

@router.get("/offres/new", response_class=HTMLResponse)
@router.get("/offres/new/", response_class=HTMLResponse)
def afficher_formulaire_creation_offre(request: Request, user: dict = Depends(require_admin)):
    values = {}
    return templates.TemplateResponse("offre_form.html", {"request": request, "mode": "create", "action_url": "/admin/offres", "values": values, "user": user})

@router.post("/offres")
@router.post("/offres/")
def creer_offre(
    request: Request,
    title: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    stock: int = Form(...),
    active: Optional[bool] = Form(False),
    description: Optional[str] = Form(""),
    image: Optional[str] = Form(""),
    user: dict = Depends(require_admin),
):
    created = create_offre(
        {"title": title, "price": price, "category": category, "stock": stock, "active": active, "description": description, "image": image}
    )
    if not created:
        return RedirectResponse(url="/admin?error=Echec%20de%20la%20cr%C3%A9ation%20de%20l%27offre", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/admin?message=Offre%20cr%C3%A9%C3%A9e", status_code=HTTP_303_SEE_OTHER)

@router.get("/offres/{offre_id}/edit", response_class=HTMLResponse)
@router.get("/offres/{offre_id}/edit/", response_class=HTMLResponse)
def afficher_formulaire_edition_offre(request: Request, offre_id: str, user: dict = Depends(require_admin)):
    ligne = get_offre(offre_id)
    return templates.TemplateResponse("offre_form.html", {"request": request, "mode": "edit", "action_url": f"/admin/offres/{offre_id}/update", "values": ligne, "user": user})

@router.post("/offres/{offre_id}/update")
@router.post("/offres/{offre_id}/update/")
def mettre_a_jour_offre(
    request: Request,
    offre_id: str,
    title: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    stock: int = Form(...),
    active: Optional[bool] = Form(False),
    description: Optional[str] = Form(""),
    image: Optional[str] = Form(""),
    user: dict = Depends(require_admin),
):
    updated = update_offre(
        offre_id,
        {"title": title, "price": price, "category": category, "stock": stock, "active": active, "description": description, "image": image}
    )
    if not updated:
        return RedirectResponse(url="/admin?error=Echec%20de%20la%20mise%20%C3%A0%20jour%20de%20l%27offre", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/admin?message=Offre%20mise%20%C3%A0%20jour", status_code=HTTP_303_SEE_OTHER)

@router.post("/offres/{offre_id}/delete")
@router.post("/offres/{offre_id}/delete/")
def supprimer_offre(request: Request, offre_id: str, user: dict = Depends(require_admin)):
    ok = delete_offre(offre_id)
    if not ok:
        return RedirectResponse(url="/admin?error=Echec%20de%20la%20suppression%20de%20l%27offre", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/admin?message=Offre%20supprim%C3%A9e", status_code=HTTP_303_SEE_OTHER)