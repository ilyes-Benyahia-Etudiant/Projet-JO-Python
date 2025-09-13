from typing import List, Dict
from backend.models.db import get_supabase

def list_user_tickets(user_id: str) -> List[Dict]:
    """
    Récupère les tickets (commandes) d'un utilisateur avec les détails de l'offre associée.
    """
    try:
        res = (
            get_supabase()
            .table("commandes")
            .select("id, token, created_at, offres(title, description, image)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception:
        return []