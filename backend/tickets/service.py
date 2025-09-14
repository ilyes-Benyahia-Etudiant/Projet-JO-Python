from typing import List, Dict
from backend.tickets.repository import list_user_tickets

def get_user_tickets(user_id: str) -> List[Dict]:
    """
    Logique applicative pour retourner les billets d'un utilisateur.
    Point d'extension: enrichissement, QR inline, mapping, etc.
    """
    raw = list_user_tickets(user_id)
    
    tickets: List[Dict] = []
    for row in raw:
        offre = row.get("offres") or {}
        tickets.append({
            "token": row.get("token"),
            "price_paid": row.get("price_paid"),
            "offre_title": offre.get("title"),
            # Champs supplémentaires conservés si utiles
            "id": row.get("id"),
            "created_at": row.get("created_at"),
        })
    return tickets