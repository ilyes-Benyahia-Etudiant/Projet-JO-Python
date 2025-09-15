from fastapi import APIRouter, Request, Depends, HTTPException
from typing import List, Dict

# On importe depuis notre nouveau module "tickets"
from backend.tickets.service import get_user_tickets as service_get_user_tickets
from backend.utils.security import require_user
from backend.config import BASE_URL
from backend.utils.qrcode_utils import generate_qr_code

# On change le préfixe pour être plus standard (API)
router = APIRouter(prefix="/api/v1/tickets", tags=["Tickets API"])

@router.get("/", response_model=List[Dict])
def get_user_tickets(
    request: Request,
    user: dict = Depends(require_user),
):
    """
    Endpoint pour récupérer les tickets de l'utilisateur authentifié.
    """
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Utilisateur non valide")
    
    tickets = service_get_user_tickets(user_id)
    return tickets

@router.get("/{ticket_token}/qrcode")
def get_ticket_qrcode(ticket_token: str, request: Request, user: dict = Depends(require_user)):
    """
    Génère un QR code pour un billet spécifique de l'utilisateur courant.
    """
    user_id = user.get("id")
    tickets = service_get_user_tickets(user_id)
    ticket = next((c for c in tickets if c.get("token") == ticket_token), None)
    if not ticket:
        raise HTTPException(status_code=404, detail="Billet non trouvé")

    base = (BASE_URL.strip().rstrip("/") if BASE_URL else str(request.base_url).rstrip("/"))
    validate_url = f"{base}/admin/scan?token={ticket_token}"
    return {"qr_code": generate_qr_code(validate_url)}