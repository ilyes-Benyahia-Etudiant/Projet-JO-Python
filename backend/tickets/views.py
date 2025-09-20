from fastapi import APIRouter, Depends, HTTPException, Request, Response
from backend.utils.security import require_user
from .service import get_user_tickets
from .service import get_user_tickets_count
from backend.config import BASE_URL
from backend.utils.qrcode_utils import generate_qr_code
from typing import Any, Dict, List
from .service import get_user_tickets_count

router = APIRouter(prefix="/api/v1/tickets", tags=["Tickets"])

@router.get("/", response_model=List[Dict])
def list_tickets(user: Dict[str, Any] = Depends(require_user)):
    """
    Endpoint pour récupérer les tickets de l'utilisateur authentifié.
    """
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Utilisateur non valide")
    
    tickets = get_user_tickets(user_id)
    return tickets

@router.get("/count")
def tickets_count(user: Dict[str, Any] = Depends(require_user)):
    count = get_user_tickets_count(user.get("id"))
    return {"count": count}

@router.get("/{ticket_token}/qrcode")
def get_ticket_qrcode(ticket_token: str, request: Request, user: dict = Depends(require_user)):
    """
    Génère un QR code pour un billet spécifique de l'utilisateur courant.
    """
    user_id = user.get("id")
    tickets = get_user_tickets(user_id)
    ticket = next((c for c in tickets if c.get("token") == ticket_token), None)
    if not ticket:
        raise HTTPException(status_code=404, detail="Billet non trouvé")

    # Construire l’URL de validation avec la clé composite (user_key + "." + ticket_token)
    from backend.users.repository import get_user_by_id
    user_row = get_user_by_id(user.get("id"))
    user_key = (user_row or {}).get("bio") or ""
    if not user_key:
        # Clé utilisateur obligatoire pour construire le QR (token composite)
        raise HTTPException(status_code=400, detail="user_key_required")
    base = str(request.base_url).rstrip("/")
    final_token = f"{user_key}.{ticket_token}"
    validate_url = f"{base}/admin/scan?token={final_token}"
    return {"qr_code": generate_qr_code(validate_url)}