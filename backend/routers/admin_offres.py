from typing import Optional
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from backend.utils.templates import templates
from backend.utils.db import get_supabase, fetch_offres, fetch_admin_commandes
from backend.utils.security import require_admin

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
    get_supabase().table("offres").insert(
        {"title": title, "price": price, "category": category, "stock": stock, "active": active, "description": description, "image": image}
    ).execute()
    return RedirectResponse(url="/admin?message=Offre%20créée", status_code=HTTP_303_SEE_OTHER)

@router.get("/offres/{offre_id}/edit", response_class=HTMLResponse)
@router.get("/offres/{offre_id}/edit/", response_class=HTMLResponse)
def afficher_formulaire_edition_offre(request: Request, offre_id: str, user: dict = Depends(require_admin)):
    ligne = get_supabase().table("offres").select("*").eq("id", offre_id).single().execute().data
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
    get_supabase().table("offres").update(
        {"title": title, "price": price, "category": category, "stock": stock, "active": active, "description": description, "image": image}
    ).eq("id", offre_id).execute()
    return RedirectResponse(url="/admin?message=Offre%20mise%20à%20jour", status_code=HTTP_303_SEE_OTHER)

@router.post("/offres/{offre_id}/delete")
@router.post("/offres/{offre_id}/delete/")
def supprimer_offre(request: Request, offre_id: str, user: dict = Depends(require_admin)):
    get_supabase().table("offres").delete().eq("id", offre_id).execute()
    return RedirectResponse(url="/admin?message=Offre%20supprimée", status_code=HTTP_303_SEE_OTHER)