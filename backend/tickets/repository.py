"""
Accès aux données 'tickets' (table commandes + jointure offre).
- list_user_tickets: récupère les commandes de l'utilisateur avec les champs nécessaires.
- Remarque: la sélection inclut offres(title, price) pour hydrater l'affichage.
"""
from typing import List, Dict
from backend.infra.supabase_client import get_supabase

def list_user_tickets(user_id: str) -> List[Dict]:
    """
    Récupère les tickets (commandes) d'un utilisateur avec la jointure 'offres'.
    - Filtre: eq("user_id", user_id)
    - Tri: par created_at décroissant (les plus récents d'abord)
    - Champs: id, token, created_at, price_paid, offres(title, price)
    - Retour: [] si erreur
    """
    try:
        res = (
            get_supabase()
            .table("commandes")
            .select("id, token, created_at, price_paid, offres(title, price)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception:
        return []