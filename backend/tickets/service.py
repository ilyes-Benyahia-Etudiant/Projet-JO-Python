from typing import List, Dict
from backend.tickets.repository import list_user_tickets

def get_user_tickets(user_id: str) -> List[Dict]:
    """
    Logique applicative pour retourner les billets d'un utilisateur.
    Point d'extension: enrichissement, QR inline, mapping, etc.
    """
    return list_user_tickets(user_id)