"""
Accès aux données pour la feature 'payments'.
"""
from typing import Iterable, Dict, Any
from backend.models.db import (
    fetch_offres_by_ids,
    insert_commande as _insert_commande,
    insert_commande_with_token as _insert_commande_with_token,
    insert_commande_service as _insert_commande_service,
)

def get_offers_map(ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    """
    Récupère les offres et renvoie un dict {id: offre}.
    """
    offers = fetch_offres_by_ids(list(ids))
    return {str(o.get("id")): o for o in offers}

def insert_commande(**kwargs):
    return _insert_commande(**kwargs)

def insert_commande_with_token(**kwargs):
    return _insert_commande_with_token(**kwargs)

def insert_commande_service(**kwargs):
    return _insert_commande_service(**kwargs)