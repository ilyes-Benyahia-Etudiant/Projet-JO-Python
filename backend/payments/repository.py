"""
Accès aux données pour la feature 'payments'.
"""
from typing import Iterable, Dict, Any
from backend.infra.supabase_client import (
    get_supabase,
    get_service_supabase,
    get_user_supabase,
)
from typing import List, Optional
import logging


logger = logging.getLogger(__name__)

def fetch_offres_by_ids(ids: List[str]) -> List[dict]:
    """
    Récupère les offres par leurs IDs.
    """
    if not ids:
        return []
    try:
        res = (
            get_supabase()
            .table("offres")
            .select("*")
            .in_("id", [str(i) for i in ids])
            .execute()
        )
        return res.data or []
    except Exception:
        logger.exception("payments.repository.fetch_offres_by_ids failed ids=%s", ids)
        return []

def get_offers_map(ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    """
    Récupère les offres et renvoie un dict {id: offre}.
    """
    offers = fetch_offres_by_ids(list(ids))
    return {str(o.get("id")): o for o in offers}

def _insert_commande(*, user_id: str, offre_id: str, token: str, price_paid: str) -> Optional[dict]:
    """
    Insert via client utilisateur (RLS active), retourne un dict truthy si succès.
    """
    try:
        (
            get_supabase()
            .table("commandes")
            .insert({"user_id": user_id, "offre_id": offre_id, "token": token, "price_paid": price_paid})
            .execute()
        )
        return {"status": "ok"}
    except Exception:
        logger.exception("payments.repository._insert_commande failed user_id=%s offre_id=%s", user_id, offre_id)
        return None

def _insert_commande_with_token(*, user_id: str, offre_id: str, token: str, price_paid: str, user_token: str) -> Optional[dict]:
    """
    Insert avec le token utilisateur explicite (respecte RLS) — utile côté API.
    """
    try:
        client = get_user_supabase(user_token)
        (
            client
            .table("commandes")
            .insert({"user_id": user_id, "offre_id": offre_id, "token": token, "price_paid": price_paid})
            .execute()
        )
        return {"status": "ok"}
    except Exception:
        logger.exception("payments.repository._insert_commande_with_token failed user_id=%s offre_id=%s", user_id, offre_id)
        return None

def _insert_commande_service(*, user_id: str, offre_id: str, token: str, price_paid: str) -> Optional[dict]:
    """
    Insert via service-role (bypass RLS) — utile côté webhook Stripe.
    """
    try:
        res = (
            get_service_supabase()
            .table("commandes")
            .insert({"user_id": user_id, "offre_id": offre_id, "token": token, "price_paid": price_paid})
            .select("*")
            .execute()
        )
        rows = res.data or []
        return rows[0] if isinstance(rows, list) and rows else res.data or None
    except Exception:
        logger.exception("payments.repository._insert_commande_service failed user_id=%s offre_id=%s", user_id, offre_id)
        return None

def insert_commande(**kwargs):
    return _insert_commande(**kwargs)

def insert_commande_with_token(**kwargs):
    return _insert_commande_with_token(**kwargs)

def insert_commande_service(**kwargs):
    return _insert_commande_service(**kwargs)