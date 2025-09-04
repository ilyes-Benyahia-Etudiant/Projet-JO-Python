from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from backend.utils.security import require_user
from backend.models import fetch_user_commandes
from backend.utils.qrcode_utils import generate_qr_code
from backend.config import BASE_URL

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

@router.get("/")
def get_user_tickets(user: Dict[str, Any] = Depends(require_user)):
    """
    Récupère tous les billets de l'utilisateur avec leurs QR codes.
    """
    commandes = fetch_user_commandes(user.get("id"))
    
    # Ajouter un QR code à chaque commande
    for commande in commandes:
        if "token" in commande:
            validate_url = f"{BASE_URL}/validate?token={commande['token']}"
            commande["qr_code"] = generate_qr_code(validate_url)
    
    return commandes

@router.get("/{ticket_token}/qrcode")
def get_ticket_qrcode(ticket_token: str, user: Dict[str, Any] = Depends(require_user)):
    """
    Génère un QR code pour un billet spécifique.
    """
    # Vérifier que le billet appartient bien à l'utilisateur
    commandes = fetch_user_commandes(user.get("id"))
    ticket = next((c for c in commandes if c.get("token") == ticket_token), None)
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Billet non trouvé")
    
    validate_url = f"{BASE_URL}/validate?token={ticket_token}"
    return {"qr_code": generate_qr_code(validate_url)}