from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from backend.utils.security import require_user
from backend.validation.service import validate_ticket_token
from backend.validation.repository import get_ticket_by_token, get_last_validation

router = APIRouter(prefix="/api/v1/validation", tags=["Validation API"])

def ensure_admin(user: Dict[str, Any]):
    # Adapte cette vérification à ton modèle utilisateur
    # Ex: user.get("role") == "admin" OU user.get("is_admin") is True
    if not (user.get("is_admin") or user.get("role") == "admin"):
        raise HTTPException(status_code=403, detail="Accès admin requis")

@router.post("/scan")
def scan_and_validate(payload: Dict[str, Any], user: dict = Depends(require_user)):
    """
    Scanner/Valider un billet.
    Body: { "token": "<ticket_token>" }
    """
    ensure_admin(user)
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
    ensure_admin(user)
    ticket = get_ticket_by_token(token)
    if not ticket:
        raise HTTPException(status_code=404, detail="Billet introuvable")

    last = get_last_validation(token)
    return {
        "ticket": ticket,
        "validation": last or None,
        "status": (last or {}).get("status") or "not_validated",
    }