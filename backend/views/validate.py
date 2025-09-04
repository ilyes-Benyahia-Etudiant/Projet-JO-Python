# backend/views/validate.py
from fastapi import APIRouter, Request, Query
from typing import Optional
from backend.models.db import get_commande_by_token, get_user_by_id, get_offre_by_id
from backend.utils.templates import templates

router = APIRouter(tags=["Validation"])

@router.get("/validate")
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
            "event_name": resolved_event_name,   # affiche le nom de l'offre si event n'est pas fourni
            "event_time": event_time,
            "event_place": event_place,
        },
        status_code=200,
    )
