from fastapi import APIRouter, HTTPException, Query
from backend.models.db import get_commande_by_token

router = APIRouter(tags=["Validation"])

@router.get("/validate")
def validate_ticket(token: str = Query(..., description="Token du billet")):
    """
    Valide un billet par son token simple (pas de JWT pour rester minimal).
    - 200 si valide: {"message":"Billet valide","ticket_id":"<id>"}
    - 401 si invalide
    """
    token = (token or "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token invalide")

    row = get_commande_by_token(token)
    if not row:
        raise HTTPException(status_code=401, detail="Billet introuvable ou invalide")

    return {"message": "Billet valide", "ticket_id": str(row.get("id"))}
