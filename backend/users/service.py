"""Couche service du domaine Utilisateurs.
Regroupe la logique métier nécessaire aux pages/fonctionnalités côté utilisateur.
Ici, la page /session demande les offres disponibles (peut évoluer pour inclure commandes et autres éléments).
"""
from typing import Any, Dict
from .repository import get_user_orders, get_offers

def get_user_dashboard(user_id: str) -> Dict[str, Any]:
    """Prépare les données affichées dans le tableau de bord utilisateur (/session).
    - Charge actuellement les offres (ex: pour proposer des achats rapides).
    - Peut être étendue pour inclure l’historique de commandes via get_user_orders(user_id).
    """
    # Charger uniquement les offres pour la page /session
    offres = get_offers()
    return {"offres": offres}