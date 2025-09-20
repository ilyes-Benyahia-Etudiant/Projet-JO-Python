from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from backend.utils.security import require_user
from backend.validation.service import validate_ticket_token
from backend.validation.repository import get_ticket_by_token, get_last_validation
from fastapi import Request, Query
from typing import Optional
from fastapi.responses import HTMLResponse
from backend.utils.templates import templates
from backend.validation.repository import get_ticket_by_token
from backend.users.repository import get_user_by_id
from backend.admin.service import get_offre_by_id

router = APIRouter(prefix="/api/v1/validation", tags=["Validation API"])

def ensure_can_scan(user: Dict[str, Any]):
    # Autoriser admins et opérateurs 'scanner'
    if not (user.get("is_admin") or user.get("role") in ("admin", "scanner")):
        raise HTTPException(status_code=403, detail="Accès scanner ou admin requis")

@router.post("/scan")
def scan_and_validate(payload: Dict[str, Any], user: dict = Depends(require_user)):
    """
    Scanner/Valider un billet.
    Body: { "token": "<ticket_token>" }
    """
    ensure_can_scan(user)
    token = (payload or {}).get("token")
    if not token:
        raise HTTPException(status_code=400, detail="token manquant")

    status, data = validate_ticket_token(token, admin_id=user.get("id", ""), admin_token=user.get("token"))
    if status == "validated":
        return {"status": "ok", **data}
    if status == "already_validated":
        return {"status": "already_validated", **data}
    if status == "not_found":
        raise HTTPException(status_code=404, detail=data.get("message") or "Billet introuvable")
    raise HTTPException(status_code=400, detail=data.get("message") or "Erreur de validation")

@router.get("/ticket/{token}")
def get_ticket_status(token: str, user: dict = Depends(require_user)):
    """
    Consulter l'état d'un billet pour l'administration.
    """
    ensure_can_scan(user)
    # Accepter 'user_key.token' en entrée et n'utiliser que le token brut
    raw = token or ""
    raw_token = raw.split(".", 1)[1] if "." in raw else raw

    ticket = get_ticket_by_token(raw_token)
    if not ticket:
        raise HTTPException(status_code=404, detail="Billet introuvable")

    last = get_last_validation(raw_token)
    return {
        "ticket": ticket,
        "validation": last or None,
        "status": (last or {}).get("status") or "not_validated",
    }

# --- Web router public pour /validate (migré depuis backend/views/validate.py) ---
web_router = APIRouter(tags=["Validation"])

@web_router.get("/validate", response_class=HTMLResponse)
def validate_ticket(
    request: Request,
    token: str = Query(..., description="Token du billet"),
    event_name: Optional[str] = Query(None, alias="event", description="Nom de l'événement (optionnel)"),
    event_time: Optional[str] = Query(None, alias="time", description="Heure/date de l'événement (optionnel)"),
    event_place: Optional[str] = Query(None, alias="place", description="Lieu de l'événement (optionnel)"),
):
    token = (token or "").strip()
    if not token:
        return templates.TemplateResponse(
            "validate.html",
            {"request": request, "status": "error", "message": "Token invalide"},
            status_code=401,
        )

    row = get_commande_by_token(token)
    if not row:
        return templates.TemplateResponse(
            "validate.html",
            {"request": request, "status": "error", "message": "Billet introuvable ou invalide"},
            status_code=401,
        )

    # Récupérer le nom de l'acheteur
    user = get_user_by_id(str(row.get("user_id") or "")) if row.get("user_id") else None
    buyer_name = None
    if user:
        buyer_name = user.get("full_name") or user.get("name") or user.get("email")
    if not buyer_name:
        uid = str(row.get("user_id") or "")
        buyer_name = f"Acheteur {uid[:8]}" if uid else "Acheteur"

    # Récupérer le titre de l'offre (fallback pour event_name)
    offer_title = None
    offre_id = row.get("offre_id")
    if offre_id:
        offer = get_offre_by_id(str(offre_id))
        if offer:
            offer_title = offer.get("title") or offer.get("name")

    resolved_event_name = event_name or offer_title

    return templates.TemplateResponse(
        "validate.html",
        {
            "request": request,
            "status": "success",
            "message": "Succès : billet valide",
            "ticket_id": str(row.get("id")),
            "buyer_name": buyer_name,
            "event_name": resolved_event_name,
            "event_time": event_time,
            "event_place": event_place,
        },
        status_code=200,
    )