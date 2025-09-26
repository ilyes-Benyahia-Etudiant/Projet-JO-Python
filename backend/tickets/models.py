"""
Shim legacy pour compatibilité: redirige vers repository.list_user_tickets.
À terme, favorise l'appel direct au repository depuis le service.
"""
from typing import List, Dict
from backend.tickets.repository import list_user_tickets

def fetch_user_tickets(user_id: str) -> List[Dict]:
    """
    Legacy shim: délègue désormais au repository.
    - Retourne la liste brute depuis list_user_tickets(user_id).
    """
    return list_user_tickets(user_id)