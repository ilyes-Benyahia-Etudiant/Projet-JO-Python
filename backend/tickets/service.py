from typing import List, Dict
from .repository import list_user_tickets

def get_user_tickets(user_id: str) -> list[dict]:
    """
    Logique applicative: retourne les billets d'un utilisateur sous une forme normalisée.
    - Délègue à repository.list_user_tickets pour la lecture.
    - Enrichit la sortie: alias offre_title, mapping de champs utiles (token, price_paid, etc.).
    - Point d'extension: ajout futur d'URL/QR inline, filtrage, pagination, etc.
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

def get_user_tickets_count(user_id: str) -> int:
    """
    Retourne le nombre de billets d'un utilisateur.
    - Utilise repository.list_user_tickets puis calcule len(...).
    - Peut être optimisé côté DB si besoin (COUNT).
    """
    tickets = list_user_tickets(user_id)
    return len(tickets)