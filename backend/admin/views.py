from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from starlette.status import HTTP_303_SEE_OTHER
from backend.utils.templates import templates
from backend.utils.security import require_admin
from backend.admin import service as admin_service
from backend.utils.rate_limit import optional_rate_limit
from backend.config import COOKIE_SECURE
import secrets
from backend.utils.csrf import get_or_create_csrf_token, attach_csrf_cookie_if_missing, validate_csrf_token
from backend.admin import repository as admin_repository
from backend.offres import repository as offres_repository
from backend.validation.repository import get_ticket_by_token, get_last_validation
from backend.validation.service import validate_ticket_token
# module backend.admin.views
from backend.utils.csrf import csrf_protect
from typing import Dict, Any  # Ajoutez cette ligne pour importer Dict et Any
from backend.evenements import repository as evenements_repository

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def admin_page(
    request: Request,
    message: Optional[str] = None,
    view: Optional[str] = Query(default=None),
    user: dict = Depends(require_admin),
    error: Optional[str] = None,
):
    allowed_views = {"commandes", "users", "offres", "evenements"}
    active_view = view if view in allowed_views else None

    # Compteurs pour le dashboard
    users_count = admin_repository.count_table_rows("users")
    commandes_count = admin_repository.count_table_rows("commandes")
    offres_count = admin_repository.count_table_rows("offres")
    evenements_count = admin_repository.count_table_rows("evenements")

    # Charger uniquement la liste demandée
    commandes = admin_service.get_admin_commandes() if active_view == "commandes" else []
    users_list = admin_repository.fetch_admin_users() if active_view == "users" else []
    offres = admin_service.list_offres() if active_view == "offres" else []
    evenements = evenements_repository.list_evenements() if active_view == "evenements" else []

    csrf = get_or_create_csrf_token(request)
    resp = templates.TemplateResponse("admin.html", {
        "request": request,
        "message": message,
        "error": error,
        "user": user,
        "csrf_token": csrf,
        "active_view": active_view,
        "commandes": commandes,
        "users": users_list,
        "offres": offres,
        "evenements": evenements,
        "commandes_count": commandes_count,
        "users_count": users_count,
        "offres_count": offres_count,
        "evenements_count": evenements_count,
    })
    attach_csrf_cookie_if_missing(resp, request, csrf)
    return resp

# API JSON: stats dashboard (comptes simples)
@router.get("/api/stats")
def admin_stats(user: dict = Depends(require_admin)):
    users_count = admin_repository.count_table_rows("users")
    commandes_count = admin_repository.count_table_rows("commandes")
    offres_count = admin_repository.count_table_rows("offres")
    return JSONResponse({"users_count": users_count, "commandes_count": commandes_count, "offres_count": offres_count})

# API JSON: listes
@router.get("/api/offres")
def admin_list_offres(user: dict = Depends(require_admin)):
    data = offres_repository.list_offres()
    return JSONResponse({"items": data or []})

@router.get("/api/commandes")
def admin_list_commandes(limit: int = 100, user: dict = Depends(require_admin)):
    data = admin_service.get_admin_commandes(limit=limit)
    return JSONResponse({"items": data or []})

@router.get("/api/users")
def admin_list_users(limit: int = 100, user: dict = Depends(require_admin)):
    data = admin_repository.fetch_admin_users(limit=limit)
    return JSONResponse({"items": data or []})

# Actions JSON pour Utilisateurs inscrits
@router.post("/api/users/{user_id}/delete")
async def api_delete_user(user_id: str, user: dict = Depends(require_admin)):
    ok = admin_service.delete_user(user_id)
    if not ok:
        return JSONResponse({"ok": False}, status_code=400)
    return JSONResponse({"ok": True})

@router.post("/api/users/{user_id}/update")
async def api_update_user(user_id: str, request: Request, user: dict = Depends(require_admin)):
    body = await request.json()
    email = (body.get("email") or "").strip()
    if not email:
        return JSONResponse({"ok": False, "error": "email required"}, status_code=400)
    updated = admin_service.update_user(user_id, {"email": email})
    if not updated:
        return JSONResponse({"ok": False}, status_code=400)
    return JSONResponse({"ok": True, "item": updated})

# Actions JSON pour Commandes réalisées
@router.post("/api/commandes/{commande_id}/delete")
async def api_delete_commande(commande_id: str, user: dict = Depends(require_admin)):
    ok = admin_service.delete_commande(commande_id)
    if not ok:
        return JSONResponse({"ok": False}, status_code=400)
    return JSONResponse({"ok": True})

# Dans la route JSON d’update commande (autour des lignes ~110-130)
@router.post("/api/commandes/{commande_id}/update")
async def api_update_commande(commande_id: str, request: Request, user: dict = Depends(require_admin)):
    body = await request.json()
    data = {}
    # SUPPRIMER la prise en charge de 'status' car la colonne n'existe pas
    # if "status" in body:
    #     data["status"] = (body.get("status") or "").strip()
    if "price_paid" in body and body.get("price_paid") is not None:
        try:
            data["price_paid"] = float(body.get("price_paid"))
        except Exception:
            return JSONResponse({"ok": False, "error": "price_paid invalide"}, status_code=400)
    if not data:
        return JSONResponse({"ok": False, "error": "aucune donnée à mettre à jour"}, status_code=400)
    updated = admin_service.update_commande(commande_id, data)
    if not updated:
        return JSONResponse({"ok": False}, status_code=400)
    return JSONResponse({"ok": True, "item": updated})

@router.get("/offres/new", response_class=HTMLResponse)
@router.get("/offres/new/", response_class=HTMLResponse)
def afficher_formulaire_creation_offre(request: Request, user: dict = Depends(require_admin)):
    values = {"title": "", "price": "", "category": "", "stock": "", "description": "", "image": ""}
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
    # (supprimé) active = "active" in form_data

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
    # (supprimé) active = "active" in form_data

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
            "description": description,
            "image": image,
        },
    )
    if not updated:
        return RedirectResponse(url="/admin?error=Echec%20de%20la%20mise%20%C3%A0%20jour", status_code=HTTP_303_SEE_OTHER)
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

# imports en haut du fichier (ajouts)
from fastapi import APIRouter, Request, Depends, Query, HTTPException
from backend.utils.security import require_admin, get_current_user

# La fonction à la ligne 266 devrait maintenant être valide :
def require_scanner(user: Dict[str, Any] = Depends(get_current_user)):
     if not user or user.get("role") not in ("scanner", "admin"):
        raise HTTPException(status_code=403, detail="Accès réservé aux scanners")
     return user

# Applique à la route /admin-scan
@router.get("/scan", response_class=HTMLResponse)
def admin_scan_get(request: Request, token: Optional[str] = Query(None), user: dict = Depends(require_scanner)):
    csrf = get_or_create_csrf_token(request)

    # Contexte par défaut
    context = {
        "request": request,
        "user": user,
        "csrf_token": csrf,
        "token": (token or "").strip(),
        "status": None,
        "message": None,
        "ticket": None,
        "validation": None,
    }

    # Si un token est fourni en query => on calcule l'état côté serveur
    if context["token"]:
        # Normaliser le token composite: user_key.token => token (partie droite)
        composite = context["token"]
        clean_token = composite.rsplit('.', 1)[-1]

        ticket = get_ticket_by_token(clean_token)
        if not ticket:
            context["status"] = "Invalid"
            context["message"] = "Billet introuvable"
        else:
            last = get_last_validation(clean_token)
            context["ticket"] = ticket
            context["validation"] = last or None
            # Afficher "Déjà validé" si une validation existe lors de la recherche
            context["status"] = "AlreadyValidated" if last else "Scanned"

    resp = templates.TemplateResponse("admin-scan.html", context)
    attach_csrf_cookie_if_missing(resp, request, csrf)
    return resp

@router.post("/scan/validate")
@router.post("/scan/validate/", )
async def admin_scan_validate(request: Request, user: dict = Depends(require_scanner)):
    # CSRF + récupération formulaire
    form = await request.form()
    if not validate_csrf_token(request, form):
        return RedirectResponse(url="/admin/scan?error=CSRF%20invalide", status_code=HTTP_303_SEE_OTHER)
    token = (form.get("token") or "").strip()
    if not token:
        return RedirectResponse(url="/admin/scan?error=Token%20manquant", status_code=HTTP_303_SEE_OTHER)

    # Validation serveur
    try:
        status, data = validate_ticket_token(token, admin_id=user.get("id", ""), admin_token=user.get("token"))
        # Peu importe le statut renvoyé, on revient sur la page GET pour afficher l'état à jour
        return RedirectResponse(url=f"/admin/scan?token={token}", status_code=HTTP_303_SEE_OTHER)
    except Exception:
        # En cas d'erreur, on revient sur la page avec le token
        return RedirectResponse(url=f"/admin/scan?token={token}", status_code=HTTP_303_SEE_OTHER)

@router.post("/users/{user_id}/update")
async def srv_update_user(user_id: str, request: Request, user: dict = Depends(require_admin)):
    form_data = await request.form()
    if not validate_csrf_token(request, form_data):
        return RedirectResponse(url="/admin?view=users&error=CSRF%20invalide", status_code=HTTP_303_SEE_OTHER)
    email = (form_data.get("email") or "").strip()
    full_name = (form_data.get("full_name") or "").strip()
    role = (form_data.get("role") or "").strip()
    if not email:
        return RedirectResponse(url="/admin?view=users&error=email%20requis", status_code=HTTP_303_SEE_OTHER)
    data: dict = {"email": email}
    if full_name:
        data["full_name"] = full_name
    if role:
        data["role"] = role
    updated = admin_service.update_user(user_id, data)
    if not updated:
        return RedirectResponse(url="/admin?view=users&error=Echec%20de%20la%20mise%20%C3%A0%20jour", status_code=HTTP_303_SEE_OTHER)
    # Redirection adaptée si l'admin s'auto-rétrograde en 'scanner'
    if (user_id == (user.get("id") or "")) and role and role.lower() == "scanner":
        return RedirectResponse(url="/admin/scan?message=R%C3%B4le%20modifi%C3%A9%20:%20scanner", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/admin?view=users&message=Utilisateur%20mis%20%C3%A0%20jour", status_code=HTTP_303_SEE_OTHER)

@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
def afficher_formulaire_edition_user(request: Request, user_id: str, user: dict = Depends(require_admin)):
    u = admin_service.get_user_by_id(user_id)
    if not u:
        return RedirectResponse(url="/admin?view=users&error=Utilisateur%20introuvable", status_code=HTTP_303_SEE_OTHER)
    csrf = get_or_create_csrf_token(request)
    resp = templates.TemplateResponse("admin_user_form.html", {
        "request": request,
        "user": user,
        "values": u,
        "action_url": f"/admin/users/{user_id}/update",
        "csrf_token": csrf,
    })
    attach_csrf_cookie_if_missing(resp, request, csrf)
    return resp

# --- Actions serveur (POST) pour Commandes ---
@router.post("/commandes/{commande_id}/update")
async def srv_update_commande(commande_id: str, request: Request, user: dict = Depends(require_admin)):
    form_data = await request.form()
    if not validate_csrf_token(request, form_data):
        return RedirectResponse(url="/admin?view=commandes&error=CSRF%20invalide", status_code=HTTP_303_SEE_OTHER)

    data = {}

    price_str = (form_data.get("price_paid") or "").strip()
    if price_str:
        try:
            data["price_paid"] = float(price_str)
        except Exception:
            return RedirectResponse(url="/admin?view=commandes&error=Prix%20invalide", status_code=HTTP_303_SEE_OTHER)

    user_id = (form_data.get("user_id") or "").strip()
    if user_id:
        data["user_id"] = user_id

    offre_id = (form_data.get("offre_id") or "").strip()
    if offre_id:
        data["offre_id"] = offre_id

    if not data:
        return RedirectResponse(url="/admin?view=commandes&error=Aucune%20donn%C3%A9e%20%C3%A0%20mettre%20%C3%A0%20jour", status_code=HTTP_303_SEE_OTHER)

    updated = admin_service.update_commande(commande_id, data)
    if not updated:
        return RedirectResponse(url="/admin?view=commandes&error=Echec%20de%20la%20mise%20%C3%A0%20jour", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/admin?view=commandes&message=Commande%20mise%20%C3%A0%20jour", status_code=HTTP_303_SEE_OTHER)

@router.get("/commandes/{commande_id}/edit", response_class=HTMLResponse)
def afficher_formulaire_edition_commande(request: Request, commande_id: str, user: dict = Depends(require_admin)):
    c = admin_service.get_commande_by_id(commande_id)
    if not c:
        return RedirectResponse(url="/admin?view=commandes&error=Commande%20introuvable", status_code=HTTP_303_SEE_OTHER)
    csrf = get_or_create_csrf_token(request)
    resp = templates.TemplateResponse("admin_commande_form.html", {
        "request": request,
        "user": user,
        "values": c,
        "action_url": f"/admin/commandes/{commande_id}/update",
        "csrf_token": csrf,
    })
    attach_csrf_cookie_if_missing(resp, request, csrf)
    return resp

@router.get("/api/evenements")
def admin_list_evenements(user: dict = Depends(require_admin)):
    data = evenements_repository.list_evenements()
    return JSONResponse({"items": data or []})
@router.get("/evenements/new", response_class=HTMLResponse)
@router.get("/evenements/new/", response_class=HTMLResponse)
def afficher_formulaire_creation_evenement(request: Request, user: dict = Depends(require_admin)):
    values = {"type_evenement": "", "nom_evenement": "", "lieu": "", "date_evenement": ""}
    csrf = get_or_create_csrf_token(request)
    resp = templates.TemplateResponse("admin_evenement_form.html", {
        "request": request,
        "mode": "create",
        "action_url": "/admin/evenements",
        "values": values,
        "user": user,
        "csrf_token": csrf,
    })
    attach_csrf_cookie_if_missing(resp, request, csrf)
    return resp

@router.post("/evenements")
@router.post("/evenements/")
async def creer_evenement(request: Request, user: dict = Depends(require_admin)):
    form_data = await request.form()
    if not validate_csrf_token(request, form_data):
        return RedirectResponse(url="/admin?view=evenements&error=CSRF%20invalide", status_code=HTTP_303_SEE_OTHER)

    type_evenement = (form_data.get("type_evenement") or "").strip()
    nom_evenement = (form_data.get("nom_evenement") or "").strip()
    lieu = (form_data.get("lieu") or "").strip()
    date_evenement = (form_data.get("date_evenement") or "").strip()

    if not type_evenement or not nom_evenement or not lieu or not date_evenement:
        return RedirectResponse(url="/admin?view=evenements&error=Champs%20requis%20manquants", status_code=HTTP_303_SEE_OTHER)

    created = admin_service.create_evenement({
        "type_evenement": type_evenement,
        "nom_evenement": nom_evenement,
        "lieu": lieu,
        "date_evenement": date_evenement,
    })
    if not created:
        return RedirectResponse(url="/admin?view=evenements&error=Echec%20de%20la%20cr%C3%A9ation", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/admin?view=evenements&message=Ev%C3%A9nement%20cr%C3%A9%C3%A9e", status_code=HTTP_303_SEE_OTHER)

@router.get("/evenements/{evenement_id}/edit", response_class=HTMLResponse)
@router.get("/evenements/{evenement_id}/edit/", response_class=HTMLResponse)
def afficher_formulaire_edition_evenement(request: Request, evenement_id: str, user: dict = Depends(require_admin)):
    ligne = admin_service.get_evenement_by_id(evenement_id)
    if not ligne:
        return RedirectResponse(url="/admin?view=evenements&error=Ev%C3%A9nement%20introuvable", status_code=HTTP_303_SEE_OTHER)
    csrf = get_or_create_csrf_token(request)
    resp = templates.TemplateResponse("admin_evenement_form.html", {
        "request": request,
        "mode": "edit",
        "action_url": f"/admin/evenements/{evenement_id}/update",
        "values": ligne,
        "user": user,
        "csrf_token": csrf,
    })
    attach_csrf_cookie_if_missing(resp, request, csrf)
    return resp

@router.post("/evenements/{evenement_id}/update")
@router.post("/evenements/{evenement_id}/update/")
async def mettre_a_jour_evenement(request: Request, evenement_id: str, user: dict = Depends(require_admin)):
    form_data = await request.form()
    if not validate_csrf_token(request, form_data):
        return RedirectResponse(url="/admin?view=evenements&error=CSRF%20invalide", status_code=HTTP_303_SEE_OTHER)

    data = {
        "type_evenement": (form_data.get("type_evenement") or "").strip(),
        "nom_evenement": (form_data.get("nom_evenement") or "").strip(),
        "lieu": (form_data.get("lieu") or "").strip(),
        "date_evenement": (form_data.get("date_evenement") or "").strip(),
    }
    updated = admin_service.update_evenement(evenement_id, data)
    if not updated:
        return RedirectResponse(url="/admin?view=evenements&error=Echec%20de%20la%20mise%20%C3%A0%20jour", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/admin?view=evenements&message=Ev%C3%A9nement%20mis%20%C3%A0%20jour", status_code=HTTP_303_SEE_OTHER)

@router.post("/evenements/{evenement_id}/delete")
@router.post("/evenements/{evenement_id}/delete/")
async def supprimer_evenement(request: Request, evenement_id: str, user: dict = Depends(require_admin)):
    form_data = await request.form()
    if not validate_csrf_token(request, form_data):
        return RedirectResponse(url="/admin?view=evenements&error=CSRF%20invalide", status_code=HTTP_303_SEE_OTHER)

    ok = admin_service.delete_evenement(evenement_id)
    if not ok:
        return RedirectResponse(url="/admin?view=evenements&error=Echec%20de%20la%20suppression", status_code=HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/admin?view=evenements&message=Ev%C3%A9nement%20supprim%C3%A9", status_code=HTTP_303_SEE_OTHER)